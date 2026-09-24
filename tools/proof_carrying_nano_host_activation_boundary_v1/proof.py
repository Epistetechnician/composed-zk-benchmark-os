"""Lean proof attempts for the declared read-only activation semantics.

State slice: proof-carrying-nano-host-activation-boundary-v1.

The proof establishes only that the captured action declares a reached hook,
unchanged parameter digest, and non-empty activation digest. It does not prove
that the digest is a faithful model-level explanation.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .adapter import (
    ACTION_STATUS,
    CLAIM_CEILING,
    PROTOCOL_ID,
    STATE_SLICE,
    canonical_digest,
)


class ActivationProofError(ValueError):
    """Raised when an activation proof attempt cannot be formed."""


@dataclass(frozen=True)
class ActivationProofAttempt:
    state_slice: str
    protocol_identity: str
    action_digest: str
    status: str
    theorem_name: str
    statement: str
    source: str
    checker: str
    checker_version: str
    diagnostics: tuple[str, ...]
    proof_digest: str

    @classmethod
    def create(
        cls,
        *,
        action_digest: str,
        status: str,
        theorem_name: str,
        statement: str,
        source: str,
        checker: str,
        checker_version: str,
        diagnostics: Sequence[str] = (),
    ) -> "ActivationProofAttempt":
        if status not in {"checked", "failed"}:
            raise ActivationProofError("proof status must be checked or failed")
        unsigned = {
            "action_digest": action_digest,
            "checker": checker,
            "checker_version": checker_version,
            "diagnostics": list(diagnostics),
            "protocol_identity": PROTOCOL_ID,
            "source": source,
            "state_slice": STATE_SLICE,
            "statement": statement,
            "status": status,
            "theorem_name": theorem_name,
        }
        return cls(
            state_slice=STATE_SLICE,
            protocol_identity=PROTOCOL_ID,
            action_digest=action_digest,
            status=status,
            theorem_name=theorem_name,
            statement=statement,
            source=source,
            checker=checker,
            checker_version=checker_version,
            diagnostics=tuple(diagnostics),
            proof_digest=canonical_digest(unsigned),
        )

    def to_dict(self) -> dict[str, Any]:
        unsigned = {
            "action_digest": self.action_digest,
            "checker": self.checker,
            "checker_version": self.checker_version,
            "diagnostics": list(self.diagnostics),
            "protocol_identity": self.protocol_identity,
            "source": self.source,
            "state_slice": self.state_slice,
            "statement": self.statement,
            "status": self.status,
            "theorem_name": self.theorem_name,
        }
        return {**unsigned, "proof_digest": self.proof_digest}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ActivationProofAttempt":
        if not isinstance(payload, Mapping) or set(payload) != {
            "action_digest", "checker", "checker_version", "diagnostics", "proof_digest",
            "protocol_identity", "source", "state_slice", "statement", "status", "theorem_name",
        }:
            raise ActivationProofError("activation proof schema is not closed")
        unsigned = {key: value for key, value in payload.items() if key != "proof_digest"}
        if payload["proof_digest"] != canonical_digest(unsigned):
            raise ActivationProofError("activation proof digest mismatch")
        if payload["state_slice"] != STATE_SLICE or payload["protocol_identity"] != PROTOCOL_ID:
            raise ActivationProofError("activation proof identity mismatch")
        return cls(
            state_slice=payload["state_slice"],
            protocol_identity=payload["protocol_identity"],
            action_digest=payload["action_digest"],
            status=payload["status"],
            theorem_name=payload["theorem_name"],
            statement=payload["statement"],
            source=payload["source"],
            checker=payload["checker"],
            checker_version=payload["checker_version"],
            diagnostics=tuple(payload["diagnostics"]),
            proof_digest=payload["proof_digest"],
        )


def _identifier(value: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return identifier if identifier and identifier[0].isalpha() else f"claim_{identifier}"


def expected_lean_artifact(action: Mapping[str, Any]) -> tuple[str, str, str]:
    outputs = action["outputs"]
    theorem_name = _identifier(f"host_activation_{action['action_digest'][7:19]}")
    activation = outputs["activation_digest"]
    parameter_before = outputs["parameter_digest_before"]
    parameter_after = outputs["parameter_digest_after"]
    statement = (
        f'readOnlyActivationBinding true true "{activation}" '
        f'"{parameter_before}" "{parameter_after}"'
    )
    source = f'''import Std

namespace NanoInterpHostActivation

/- State slice: {STATE_SLICE}. -/
def readOnlyActivationBinding (hookReached parametersUnchanged : Bool)
    (activationDigest parameterDigestBefore parameterDigestAfter : String) : Prop :=
  hookReached = true ∧ parametersUnchanged = true ∧ activationDigest ≠ "" ∧
    parameterDigestBefore = parameterDigestAfter

def actionDigest : String := "{action["action_digest"]}"

theorem action_digest_bound : actionDigest = "{action["action_digest"]}" := by
  rfl

theorem {theorem_name} : {statement} := by
  simp [readOnlyActivationBinding]

end NanoInterpHostActivation
'''
    return theorem_name, statement, source


class ActivationLeanProofEngine:
    """Generate and kernel-check the local activation-binding theorem."""

    def __init__(
        self,
        *,
        project_dir: Path | None = None,
        command: Sequence[str] = ("lake", "env", "lean"),
        timeout_seconds: int = 30,
    ) -> None:
        self.project_dir = project_dir or Path(__file__).parents[2] / "formal" / "proof-carrying-nano-interp-v1"
        self.command = tuple(command)
        self.timeout_seconds = timeout_seconds

    def attempt(self, action: Mapping[str, Any]) -> ActivationProofAttempt:
        theorem_name, statement, source = expected_lean_artifact(action)
        if action.get("outputs", {}).get("status") != ACTION_STATUS:
            return ActivationProofAttempt.create(
                action_digest=action.get("action_digest", "invalid"),
                status="failed",
                theorem_name=theorem_name,
                statement=statement,
                source=source,
                checker="lean-kernel",
                checker_version="unavailable",
                diagnostics=("activation action status is not ActivationCaptured",),
            )
        if shutil.which(self.command[0]) is None:
            return ActivationProofAttempt.create(
                action_digest=action["action_digest"],
                status="failed",
                theorem_name=theorem_name,
                statement=statement,
                source=source,
                checker="lean-kernel",
                checker_version="unavailable",
                diagnostics=(f"Lean checker unavailable: {self.command[0]}",),
            )
        try:
            with tempfile.TemporaryDirectory(prefix="host-activation-proof-") as directory:
                proof_path = Path(directory) / f"{theorem_name}.lean"
                proof_path.write_text(source, encoding="utf-8")
                result = subprocess.run(
                    [*self.command, str(proof_path)],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return ActivationProofAttempt.create(
                action_digest=action["action_digest"],
                status="failed",
                theorem_name=theorem_name,
                statement=statement,
                source=source,
                checker="lean-kernel",
                checker_version="unavailable",
                diagnostics=(str(exc),),
            )
        if result.returncode != 0:
            diagnostic = (result.stderr or result.stdout or "Lean returned a nonzero status").strip()
            return ActivationProofAttempt.create(
                action_digest=action["action_digest"],
                status="failed",
                theorem_name=theorem_name,
                statement=statement,
                source=source,
                checker="lean-kernel",
                checker_version="unknown",
                diagnostics=(diagnostic,),
            )
        return ActivationProofAttempt.create(
            action_digest=action["action_digest"],
            status="checked",
            theorem_name=theorem_name,
            statement=statement,
            source=source,
            checker="lean-kernel",
            checker_version="lake-env-lean",
        )

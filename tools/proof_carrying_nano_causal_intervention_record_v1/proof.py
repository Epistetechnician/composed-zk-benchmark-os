"""Lean proof attempts for causal-intervention record binding only.

State slice: proof-carrying-nano-causal-intervention-record-v1.

The generated theorem checks declared record identity, exact replacement syntax,
digest presence and binding, unchanged host parameters, and proof status. It
does not prove that a measured effect is causal or that the host model matches
the declared semantics.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.proof_carrying_nano_interp_v1.protocol import canonical_digest

from .record import (
    ASSESSMENT_STATUS,
    CLAIM_SEMANTICS,
    PROTOCOL_ID,
    RECORD_SCHEMA,
    RECORD_STATUS,
    STATE_SLICE,
    validate_record,
)


class CausalInterventionProofError(ValueError):
    """Raised when a causal record proof attempt cannot be formed."""


@dataclass(frozen=True)
class CausalInterventionProofAttempt:
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
    ) -> "CausalInterventionProofAttempt":
        if status not in {"checked", "failed"}:
            raise CausalInterventionProofError("proof status must be checked or failed")
        if not isinstance(action_digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", action_digest) is None:
            raise CausalInterventionProofError("proof record digest is invalid")
        if not isinstance(checker, str) or not checker:
            raise CausalInterventionProofError("proof checker is invalid")
        if not isinstance(checker_version, str) or not checker_version:
            raise CausalInterventionProofError("proof checker version is invalid")
        if not isinstance(theorem_name, str) or not theorem_name:
            raise CausalInterventionProofError("proof theorem name is invalid")
        if not isinstance(statement, str) or not isinstance(source, str):
            raise CausalInterventionProofError("proof statement or source is invalid")
        if not isinstance(diagnostics, Sequence) or isinstance(diagnostics, (str, bytes)) or not all(isinstance(item, str) for item in diagnostics):
            raise CausalInterventionProofError("proof diagnostics are invalid")
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
    def from_dict(cls, payload: Mapping[str, Any]) -> "CausalInterventionProofAttempt":
        expected = {
            "action_digest", "checker", "checker_version", "diagnostics", "proof_digest",
            "protocol_identity", "source", "state_slice", "statement", "status", "theorem_name",
        }
        if not isinstance(payload, Mapping) or set(payload) != expected:
            raise CausalInterventionProofError("causal intervention proof schema is not closed")
        if not isinstance(payload["action_digest"], str) or re.fullmatch(r"sha256:[0-9a-f]{64}", payload["action_digest"]) is None:
            raise CausalInterventionProofError("proof record digest is invalid")
        diagnostics = payload["diagnostics"]
        if not isinstance(diagnostics, list) or any(not isinstance(item, str) for item in diagnostics):
            raise CausalInterventionProofError("proof diagnostics are invalid")
        for key in ("checker", "checker_version", "theorem_name", "statement", "source", "state_slice", "protocol_identity", "status"):
            if not isinstance(payload[key], str):
                raise CausalInterventionProofError(f"proof {key} is invalid")
        if not payload["checker"] or not payload["checker_version"] or not payload["theorem_name"]:
            raise CausalInterventionProofError("proof metadata is invalid")
        unsigned = {key: value for key, value in payload.items() if key != "proof_digest"}
        if payload["proof_digest"] != canonical_digest(unsigned):
            raise CausalInterventionProofError("causal intervention proof digest mismatch")
        if payload["state_slice"] != STATE_SLICE or payload["protocol_identity"] != PROTOCOL_ID:
            raise CausalInterventionProofError("causal intervention proof identity mismatch")
        if payload["status"] not in {"checked", "failed"}:
            raise CausalInterventionProofError("proof status is invalid")
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
            diagnostics=tuple(diagnostics),
            proof_digest=payload["proof_digest"],
        )


def _identifier(value: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return identifier if identifier and identifier[0].isalpha() else f"claim_{identifier}"


def checker_environment_identity(project_dir: Path) -> str:
    """Return the exact checker-input file identities used by ``lake env lean``."""

    digests: list[str] = []
    for filename in ("lean-toolchain", "lake-manifest.json"):
        path = project_dir / filename
        if not path.is_file() or path.is_symlink():
            raise CausalInterventionProofError(f"Lean checker environment file is unavailable: {filename}")
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise CausalInterventionProofError(f"Lean checker environment cannot be read: {filename}") from exc
        digests.append(f"{filename}=sha256:{hashlib.sha256(content).hexdigest()}")
    return "lake-env-lean;" + ";".join(digests)


def expected_lean_artifact(record: Mapping[str, Any]) -> tuple[str, str, str]:
    """Return the deterministic theorem statement and source for one record."""

    record = validate_record(record)
    theorem_name = _identifier(f"causal_intervention_{record['record_digest'][7:19]}")
    operator = record["intervention_operator"]
    parameters = operator["parameters"]
    claim = record["claim"]
    host_unchanged = record["host_parameter_digest_before"] == record["host_parameter_digest_after"]
    statement = (
        f'NanoInterpCausalInterventionRecord.causalInterventionRecordBinding "{record["state_slice"]}" '
        f'"{record["protocol_identity"]}" "{record["record_schema"]}" '
        f'"{record["claim"]["semantics"]}" "{operator["type"]}" '
        f'"{parameters["interpolation"]}" true "{record["proof_status"]}" '
        f'{str(host_unchanged).lower()} "{record["parent_activation_action_digest"]}" '
        f'"{record["donor"]["activation_digest"]}" "{record["target"]["activation_digest"]}" '
        f'"{record["effect"]["effect_digest"]}" "{claim["controls_digest"]}" '
        f'"{record["record_digest"]}"'
    )
    source = f'''import Std
import NanoInterp.CausalInterventionRecord

namespace NanoInterpCausalInterventionRecordProof

/- State slice: {STATE_SLICE}. -/
def recordDigest : String := "{record["record_digest"]}"

theorem record_digest_bound : recordDigest = "{record["record_digest"]}" := by
  rfl

theorem {_identifier(theorem_name)} : {statement} := by
  simp [NanoInterpCausalInterventionRecord.causalInterventionRecordBinding]

end NanoInterpCausalInterventionRecordProof
'''
    return theorem_name, statement, source


class CausalInterventionLeanProofEngine:
    """Generate and kernel-check the declared record-binding theorem."""

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

    def attempt(self, record: Mapping[str, Any]) -> CausalInterventionProofAttempt:
        try:
            theorem_name, statement, source = expected_lean_artifact(record)
        except (CausalInterventionProofError, ValueError, KeyError, TypeError) as exc:
            candidate_digest = record.get("record_digest") if isinstance(record, Mapping) else None
            action_digest = (
                candidate_digest
                if isinstance(candidate_digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", candidate_digest)
                else "sha256:" + "0" * 64
            )
            return CausalInterventionProofAttempt.create(
                action_digest=action_digest,
                status="failed",
                theorem_name="invalid_causal_intervention_record",
                statement="",
                source="",
                checker="lean-kernel",
                checker_version="unavailable",
                diagnostics=(str(exc),),
            )
        if record.get("record_status") != RECORD_STATUS or record.get("assessment_status") != ASSESSMENT_STATUS:
            return CausalInterventionProofAttempt.create(
                action_digest=record["record_digest"], status="failed", theorem_name=theorem_name,
                statement=statement, source=source, checker="lean-kernel", checker_version="unavailable",
                diagnostics=("record is not an unreviewed, review-sealed observation",),
            )
        if record.get("proof_status") != "checked":
            return CausalInterventionProofAttempt.create(
                action_digest=record["record_digest"], status="failed", theorem_name=theorem_name,
                statement=statement, source=source, checker="lean-kernel", checker_version="unavailable",
                diagnostics=("record proof status is not checked",),
            )
        if shutil.which(self.command[0]) is None:
            return CausalInterventionProofAttempt.create(
                action_digest=record["record_digest"], status="failed", theorem_name=theorem_name,
                statement=statement, source=source, checker="lean-kernel", checker_version="unavailable",
                diagnostics=(f"Lean checker unavailable: {self.command[0]}",),
            )
        try:
            checker_version = checker_environment_identity(self.project_dir)
        except CausalInterventionProofError as exc:
            return CausalInterventionProofAttempt.create(
                action_digest=record["record_digest"], status="failed", theorem_name=theorem_name,
                statement=statement, source=source, checker="lean-kernel", checker_version="unavailable",
                diagnostics=(str(exc),),
            )
        try:
            with tempfile.TemporaryDirectory(prefix="causal-intervention-proof-") as directory:
                proof_path = Path(directory) / f"{theorem_name}.lean"
                proof_path.write_text(source, encoding="utf-8")
                result = subprocess.run(
                    [*self.command, str(proof_path)], cwd=self.project_dir,
                    capture_output=True, text=True, timeout=self.timeout_seconds, check=False,
                )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return CausalInterventionProofAttempt.create(
                action_digest=record["record_digest"], status="failed", theorem_name=theorem_name,
                statement=statement, source=source, checker="lean-kernel", checker_version="unavailable",
                diagnostics=(str(exc),),
            )
        if result.returncode != 0:
            diagnostic = (result.stderr or result.stdout or "Lean returned a nonzero status").strip()
            return CausalInterventionProofAttempt.create(
                action_digest=record["record_digest"], status="failed", theorem_name=theorem_name,
                statement=statement, source=source, checker="lean-kernel", checker_version="unknown",
                diagnostics=(diagnostic,),
            )
        return CausalInterventionProofAttempt.create(
            action_digest=record["record_digest"], status="checked", theorem_name=theorem_name,
            statement=statement, source=source, checker="lean-kernel", checker_version=checker_version,
        )

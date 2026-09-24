"""Lean proof attempts for captured Jevlike arithmetic.

State slice: proof-carrying-nano-interp-jevlike-adapter-v1.

The kernel theorem deliberately says nothing about Jevlike, its checkpoint, or
the host model. Those are digest-bound provenance fields; the theorem proves
only normalization and selected-index consistency for the captured fixed-point
weights.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Sequence

from tools.proof_carrying_nano_interp_v1.protocol import (
    ProtocolError,
    canonical_digest,
)
from tools.proof_carrying_nano_interp_v1.ranking import HypothesisOptionSet
from tools.proof_carrying_nano_interp_v1.runtime import MiniAction

from .adapter import (
    ADAPTER_CONFIG_SCHEMA,
    PINNED_JEVLIKE_REVISION,
    PROTOCOL_ID,
    QUANTIZATION_SCHEMA,
    STATE_SLICE,
)


class ProofError(ProtocolError):
    """Raised when a captured external ranking cannot be proven."""


@dataclass(frozen=True)
class JevlikeProofAttempt:
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
    ) -> "JevlikeProofAttempt":
        if status not in {"checked", "failed"}:
            raise ProofError("proof status must be checked or failed")
        if not isinstance(action_digest, str) or not action_digest.startswith("sha256:"):
            raise ProofError("proof action digest is invalid")
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
    def from_dict(cls, payload: dict[str, Any]) -> "JevlikeProofAttempt":
        cls.assert_digest(payload)
        expected_keys = {
            "action_digest",
            "checker",
            "checker_version",
            "diagnostics",
            "proof_digest",
            "protocol_identity",
            "source",
            "state_slice",
            "statement",
            "status",
            "theorem_name",
        }
        if set(payload) != expected_keys:
            raise ProofError("proof schema is not closed")
        diagnostics = payload.get("diagnostics")
        if not isinstance(diagnostics, list) or any(not isinstance(item, str) for item in diagnostics):
            raise ProofError("proof diagnostics are invalid")
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

    @staticmethod
    def assert_digest(payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise ProofError("proof payload is invalid")
        provided = payload.get("proof_digest")
        unsigned = {key: value for key, value in payload.items() if key != "proof_digest"}
        if provided != canonical_digest(unsigned):
            raise ProofError("proof digest mismatch")
        if payload.get("state_slice") != STATE_SLICE or payload.get("protocol_identity") != PROTOCOL_ID:
            raise ProofError("proof identity mismatch")
        if payload.get("status") not in {"checked", "failed"}:
            raise ProofError("proof status is invalid")


def _identifier(value: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value)
    return identifier if identifier and identifier[0].isalpha() else f"claim_{identifier}"


def _decimal_text(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ProofError("external scores must be decimal strings")
    try:
        decimal = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ProofError("external score is not decimal text") from exc
    if not decimal.is_finite() or decimal < 0:
        raise ProofError("external scores must be finite and non-negative")
    return decimal


class JevlikeLeanProofEngine:
    """Generate and kernel-check the post-capture fixed-point theorem."""

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

    @staticmethod
    def _validate_action(action: MiniAction) -> tuple[list[int], HypothesisOptionSet, int]:
        if not isinstance(action, MiniAction):
            raise ProofError("Jevlike action is invalid")
        if (
            not isinstance(action.claim, dict)
            or not isinstance(action.inputs, dict)
            or not isinstance(action.outputs, dict)
        ):
            raise ProofError("Jevlike action maps are invalid")
        payload = action.to_dict()
        if payload.get("state_slice") != STATE_SLICE or payload.get("protocol_identity") != PROTOCOL_ID:
            raise ProofError("Jevlike action identity mismatch")
        if payload.get("action_digest") != canonical_digest(
            {key: value for key, value in payload.items() if key != "action_digest"}
        ):
            raise ProofError("Jevlike action digest mismatch")
        if action.claim.get("type") != "jevlike_hypothesis_ranking" or action.claim.get("kind") != "hypothesis":
            raise ProofError("Jevlike action claim type is invalid")
        if action.outputs.get("status") != "HypothesisOnly":
            raise ProofError("Jevlike output status must be HypothesisOnly")
        inputs = action.inputs
        scores = inputs.get("quantized_scores")
        external_scores = inputs.get("external_scores")
        option_set_payload = inputs.get("option_set")
        quantization = inputs.get("quantization")
        provenance = inputs.get("external_provenance")
        if (
            not isinstance(scores, list)
            or not scores
            or not isinstance(external_scores, list)
            or not isinstance(option_set_payload, dict)
            or not isinstance(quantization, dict)
            or not isinstance(provenance, dict)
        ):
            raise ProofError("Jevlike action arithmetic inputs are invalid")
        if any(isinstance(score, bool) or not isinstance(score, int) or score < 0 for score in scores):
            raise ProofError("Jevlike quantized scores are invalid")
        try:
            option_set = HypothesisOptionSet.from_dict(option_set_payload)
        except (KeyError, ProtocolError, TypeError) as exc:
            raise ProofError(f"Jevlike option set is invalid: {exc}") from exc
        claim = action.claim
        if (
            claim.get("option_set_digest") != option_set.option_set_digest
            or claim.get("context_digest") != option_set.context_digest
            or claim.get("scorer_identity") != option_set.scorer_identity
            or claim.get("option_ids") != [option.candidate_id for option in option_set.options]
            or inputs.get("context_digest") != option_set.context_digest
            or not isinstance(inputs.get("context"), str)
            or canonical_digest(inputs["context"]) != option_set.context_digest
        ):
            raise ProofError("Jevlike option or context binding is invalid")
        if len(scores) != len(option_set.options) or len(external_scores) != len(scores):
            raise ProofError("Jevlike score count does not match ordered options")
        config = provenance.get("config")
        if not isinstance(config, dict) or config.get("schema") != ADAPTER_CONFIG_SCHEMA:
            raise ProofError("Jevlike adapter configuration is missing")
        if set(config) != {
            "context_tokens",
            "device",
            "encoder_identity",
            "option_tokens",
            "quantization_scale",
            "rounding",
            "runtime_identity",
            "schema",
            "scorer_checkpoint_digest",
            "seed",
            "upstream_revision",
        }:
            raise ProofError("Jevlike adapter configuration schema is not closed")
        if provenance.get("config_digest") != canonical_digest(config):
            raise ProofError("Jevlike adapter configuration digest mismatch")
        if config.get("upstream_revision") != PINNED_JEVLIKE_REVISION:
            raise ProofError("Jevlike revision is not the pinned revision")
        expected_provenance = {
            "adapter_identity": action.nano_identity,
            "config_digest": canonical_digest(config),
            "device": config.get("device"),
            "encoder_identity": config.get("encoder_identity"),
            "quantization_schema": QUANTIZATION_SCHEMA,
            "runtime_identity": config.get("runtime_identity"),
            "scorer_checkpoint_digest": config.get("scorer_checkpoint_digest"),
            "seed": config.get("seed"),
            "upstream_revision": config.get("upstream_revision"),
            "config": config,
        }
        if provenance != expected_provenance:
            raise ProofError("Jevlike external provenance is not config-bound")
        if set(quantization) != {"rounding", "scale", "schema"}:
            raise ProofError("Jevlike quantization schema is not closed")
        if (
            quantization.get("schema") != QUANTIZATION_SCHEMA
            or quantization.get("scale") != config.get("quantization_scale")
            or quantization.get("rounding") != config.get("rounding")
        ):
            raise ProofError("Jevlike quantization configuration is not bound")
        rounding_name = quantization.get("rounding")
        rounding = {
            "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
            "ROUND_HALF_UP": ROUND_HALF_UP,
        }.get(rounding_name)
        scale = quantization.get("scale")
        if rounding is None or isinstance(scale, bool) or not isinstance(scale, int) or scale < 1:
            raise ProofError("Jevlike quantization configuration is invalid")
        expected_scores: list[int] = []
        for raw in external_scores:
            decimal = _decimal_text(raw)
            expected_scores.append(int((decimal * scale).to_integral_value(rounding=rounding)))
        if expected_scores != scores:
            raise ProofError("Jevlike quantized scores do not match captured probabilities")
        denominator = sum(scores)
        probabilities = action.outputs.get("probabilities")
        if denominator <= 0 or probabilities != [
            {"denominator": denominator, "numerator": score} for score in scores
        ]:
            raise ProofError("Jevlike normalization does not match captured scores")
        selected_index = action.outputs.get("selected_index")
        if (
            isinstance(selected_index, bool)
            or not isinstance(selected_index, int)
            or selected_index < 0
            or selected_index >= len(scores)
        ):
            raise ProofError("Jevlike selected index is invalid")
        expected_index = max(range(len(scores)), key=scores.__getitem__)
        selected = option_set.options[selected_index]
        if (
            selected_index != expected_index
            or action.outputs.get("selected_option") != selected.candidate_id
            or action.outputs.get("selected_option_kind") != selected.kind
            or action.claim.get("selected_index") != selected_index
            or action.claim.get("selected_option") != selected.candidate_id
            or action.claim.get("selected_option_kind") != selected.kind
        ):
            raise ProofError("Jevlike selected option is inconsistent with scores")
        return scores, option_set, denominator

    def source_for(self, action: MiniAction) -> tuple[str, str, str]:
        scores, _option_set, denominator = self._validate_action(action)
        selected_index = action.outputs["selected_index"]
        theorem_name = _identifier(f"jevlike_ranking_{action.action_digest[7:19]}")
        score_list = "[" + ", ".join(str(score) for score in scores) + "]"
        comparisons = [
            f"nthOrZero {score_list} {index} ≤ nthOrZero {score_list} {selected_index}"
            for index in range(len(scores))
            if index != selected_index
        ]
        statement = " ∧ ".join(
            [
                f"weightSum {score_list} = {denominator}",
                f"nthOrZero {score_list} {selected_index} = {scores[selected_index]}",
                *comparisons,
            ]
        )
        source = f"""import Std

namespace NanoInterpJevlikeAdapter

/- State slice: {STATE_SLICE}. -/
def weightSum (values : List Nat) : Nat :=
  match values with
  | [] => 0
  | value :: rest => value + weightSum rest

def nthOrZero (values : List Nat) (index : Nat) : Nat :=
  match values, index with
  | value :: _, 0 => value
  | _ :: rest, index + 1 => nthOrZero rest index
  | _, _ => 0

def actionDigest : String := "{action.action_digest}"

theorem action_digest_bound : actionDigest = "{action.action_digest}" := by
  rfl

theorem {theorem_name} : {statement} := by
  decide

end NanoInterpJevlikeAdapter
"""
        return theorem_name, statement, source

    def attempt(self, action: MiniAction) -> JevlikeProofAttempt:
        theorem_name, statement, source = self.source_for(action)
        if shutil.which(self.command[0]) is None:
            return JevlikeProofAttempt.create(
                action_digest=action.action_digest,
                status="failed",
                theorem_name=theorem_name,
                statement=statement,
                source=source,
                checker="lean-kernel",
                checker_version="unavailable",
                diagnostics=(f"executable not found: {self.command[0]}",),
            )
        try:
            with tempfile.TemporaryDirectory(prefix="nano-interp-jevlike-proof-") as temp_dir:
                source_path = Path(temp_dir) / f"{theorem_name}.lean"
                source_path.write_text(source, encoding="utf-8")
                result = subprocess.run(
                    [*self.command, str(source_path)],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return JevlikeProofAttempt.create(
                action_digest=action.action_digest,
                status="failed",
                theorem_name=theorem_name,
                statement=statement,
                source=source,
                checker="lean-kernel",
                checker_version="unknown",
                diagnostics=(str(exc),),
            )
        diagnostics = tuple(line for line in (result.stdout + result.stderr).splitlines() if line)
        return JevlikeProofAttempt.create(
            action_digest=action.action_digest,
            status="checked" if result.returncode == 0 else "failed",
            theorem_name=theorem_name,
            statement=statement,
            source=source,
            checker="lean-kernel",
            checker_version="4.30.0",
            diagnostics=diagnostics,
        )

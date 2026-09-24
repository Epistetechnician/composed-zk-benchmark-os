"""Lean proof attempts and kernel integration for V1.

State slice: proof-carrying-nano-interp-v1.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .intervention import InterventionSpec
from .protocol import PROTOCOL_ID, STATE_SLICE, ProtocolError, canonical_digest
from .ranking import HypothesisOptionSet
from .runtime import MiniAction


@dataclass(frozen=True)
class ProofAttempt:
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
    ) -> "ProofAttempt":
        if status not in {"checked", "failed"}:
            raise ProtocolError("proof status must be checked or failed")
        if not action_digest.startswith("sha256:"):
            raise ProtocolError("proof action digest is invalid")
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

    @classmethod
    def checked(
        cls,
        *,
        action_digest: str,
        theorem_name: str,
        statement: str,
        source: str,
        checker: str,
        checker_version: str,
    ) -> "ProofAttempt":
        return cls.create(
            action_digest=action_digest,
            status="checked",
            theorem_name=theorem_name,
            statement=statement,
            source=source,
            checker=checker,
            checker_version=checker_version,
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
    def from_dict(cls, payload: dict[str, Any]) -> "ProofAttempt":
        cls.assert_digest(payload)
        diagnostics = payload.get("diagnostics")
        if not isinstance(diagnostics, list) or any(not isinstance(item, str) for item in diagnostics):
            raise ProtocolError("proof diagnostics are invalid")
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
        provided = payload.get("proof_digest")
        unsigned = {key: value for key, value in payload.items() if key != "proof_digest"}
        if provided != canonical_digest(unsigned):
            raise ProtocolError("proof digest mismatch")
        if payload.get("state_slice") != STATE_SLICE or payload.get("protocol_identity") != PROTOCOL_ID:
            raise ProtocolError("proof identity mismatch")
        if payload.get("status") not in {"checked", "failed"}:
            raise ProtocolError("proof status is invalid")


class LeanProofEngine:
    """Generate and optionally kernel-check exact feature-value claims."""

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
    def _identifier(value: str) -> str:
        identifier = re.sub(r"[^A-Za-z0-9_]", "_", value)
        return identifier if identifier and identifier[0].isalpha() else f"claim_{identifier}"

    def source_for(self, action: MiniAction) -> tuple[str, str, str]:
        claim = action.claim
        if claim.get("type") == "hypothesis_ranking":
            return self._ranking_source_for(action)
        if claim.get("type") == "intervention_effect_exact":
            return self._intervention_source_for(action)
        if claim.get("type") != "feature_activation_exact":
            raise ProtocolError("V1 Lean engine does not handle this claim type")
        values = action.inputs.get("activation")
        index = claim.get("feature_index")
        value = claim.get("value")
        if not isinstance(values, list) or not isinstance(index, int) or not isinstance(value, int):
            raise ProtocolError("exact feature claim has invalid numeric inputs")
        if index < 0 or index >= len(values) or values[index] != value:
            raise ProtocolError("feature claim is inconsistent with action inputs")
        lean_values = ", ".join(str(item) for item in values)
        theorem_name = self._identifier(f"action_{action.action_digest[7:19]}")
        statement = f"featureActivation [{lean_values}] {index} = {value}"
        source = f"""import Std

namespace NanoInterp

/- State slice: {STATE_SLICE}. -/
def featureActivation (values : List Int) (index : Nat) : Int :=
  match values, index with
  | value :: _, 0 => value
  | _ :: rest, index + 1 => featureActivation rest index
  | _, _ => 0

def actionDigest : String := "{action.action_digest}"

theorem action_digest_bound : actionDigest = "{action.action_digest}" := by
  rfl

theorem {theorem_name} : {statement} := by
  rfl

end NanoInterp
"""
        return theorem_name, statement, source

    def _intervention_source_for(self, action: MiniAction) -> tuple[str, str, str]:
        inputs = action.inputs
        outputs = action.outputs
        claim = action.claim
        pre_activation = inputs.get("activation")
        spec_payload = inputs.get("intervention_spec")
        if not isinstance(pre_activation, list) or not isinstance(spec_payload, dict):
            raise ProtocolError("intervention claim has invalid inputs")
        if any(
            isinstance(value, bool) or not isinstance(value, int) for value in pre_activation
        ):
            raise ProtocolError("intervention activation values are invalid")
        try:
            spec = InterventionSpec.from_dict(spec_payload)
        except (KeyError, ProtocolError, TypeError) as exc:
            raise ProtocolError(f"intervention specification is invalid: {exc}") from exc
        if (
            spec.context_digest != action.host_context_hash
            or claim.get("type") != "intervention_effect_exact"
            or claim.get("kind") != "intervention_observation"
            or claim.get("intervention_id") != spec.intervention_id
            or claim.get("intervention_spec_digest") != spec.spec_digest
            or outputs.get("status") != "InterventionObserved"
        ):
            raise ProtocolError("intervention claim binding is invalid")
        if spec.index >= len(pre_activation):
            raise ProtocolError("intervention index is outside activation")
        post_activation = list(pre_activation)
        post_activation[spec.index] = spec.replacement
        expected_delta = [
            after - before for before, after in zip(pre_activation, post_activation)
        ]
        expected_control = {
            "delta": [0 for _ in pre_activation],
            "effect": 0,
            "kind": "no_op",
            "post_activation": list(pre_activation),
        }
        if (
            outputs.get("pre_activation") != pre_activation
            or outputs.get("post_activation") != post_activation
            or outputs.get("delta") != expected_delta
            or outputs.get("effect_index") != spec.index
            or outputs.get("effect") != expected_delta[spec.index]
            or outputs.get("control") != expected_control
            or claim.get("effect_index") != spec.index
            or claim.get("effect") != expected_delta[spec.index]
            or claim.get("hypothesis_action_digest")
            != inputs.get("hypothesis_action_digest")
        ):
            raise ProtocolError("intervention observation is inconsistent with specification")
        hypothesis_digest = inputs.get("hypothesis_action_digest")
        if hypothesis_digest is not None and (
            not isinstance(hypothesis_digest, str) or not hypothesis_digest.startswith("sha256:")
        ):
            raise ProtocolError("intervention hypothesis reference is invalid")
        lean_pre = ", ".join(str(value) for value in pre_activation)
        lean_post = ", ".join(str(value) for value in post_activation)
        lean_delta = ", ".join(str(value) for value in expected_delta)
        theorem_name = self._identifier(f"intervention_{action.action_digest[7:19]}")
        pre_list = f"[{lean_pre}]"
        post_list = f"[{lean_post}]"
        delta_list = f"[{lean_delta}]"
        statement = (
            f"replaceAt {pre_list} {spec.index} {spec.replacement} = {post_list} ∧ "
            f"vectorDelta {pre_list} {post_list} = {delta_list} ∧ "
            f"({spec.replacement} : Int) - {pre_activation[spec.index]} = "
            f"{expected_delta[spec.index]} ∧ "
            f"vectorDelta {pre_list} {pre_list} = "
            f"[{', '.join('0' for _ in pre_activation)}]"
        )
        source = f"""import Std

namespace NanoInterp

/- State slice: {STATE_SLICE}. -/
def replaceAt (values : List Int) (index : Nat) (replacement : Int) : List Int :=
  match values, index with
  | [], _ => []
  | _ :: rest, 0 => replacement :: rest
  | value :: rest, index + 1 => value :: replaceAt rest index replacement

def vectorDelta (before : List Int) (after : List Int) : List Int :=
  match before, after with
  | beforeValue :: beforeRest, afterValue :: afterRest =>
      (afterValue - beforeValue) :: vectorDelta beforeRest afterRest
  | _, _ => []

def actionDigest : String := "{action.action_digest}"

theorem action_digest_bound : actionDigest = "{action.action_digest}" := by
  rfl

theorem {theorem_name} : {statement} := by
  decide

end NanoInterp
"""
        return theorem_name, statement, source

    def _ranking_source_for(self, action: MiniAction) -> tuple[str, str, str]:
        scores = action.inputs.get("scores")
        option_set_payload = action.inputs.get("option_set")
        probabilities = action.outputs.get("probabilities")
        if (
            not isinstance(scores, list)
            or not isinstance(probabilities, list)
            or not scores
            or not isinstance(option_set_payload, dict)
        ):
            raise ProtocolError("ranking claim has invalid score inputs")
        if any(isinstance(score, bool) or not isinstance(score, int) or score < 0 for score in scores):
            raise ProtocolError("ranking scores are invalid")
        try:
            option_set = HypothesisOptionSet.from_dict(option_set_payload)
        except (KeyError, ProtocolError, TypeError) as exc:
            raise ProtocolError(f"ranking option set is invalid: {exc}") from exc
        claim = action.claim
        if claim.get("type") != "hypothesis_ranking" or claim.get("kind") != "hypothesis":
            raise ProtocolError("ranking claim type is invalid")
        if action.outputs.get("status") != "HypothesisOnly":
            raise ProtocolError("ranking output status must be HypothesisOnly")
        if claim.get("option_set_digest") != option_set.option_set_digest:
            raise ProtocolError("ranking claim option-set binding mismatch")
        if claim.get("context_digest") != option_set.context_digest:
            raise ProtocolError("ranking claim context binding mismatch")
        if claim.get("scorer_identity") != option_set.scorer_identity:
            raise ProtocolError("ranking claim scorer binding mismatch")
        if claim.get("option_ids") != [option.candidate_id for option in option_set.options]:
            raise ProtocolError("ranking claim option ordering mismatch")
        denominator = sum(scores)
        if denominator <= 0 or len(scores) != len(probabilities):
            raise ProtocolError("ranking normalization is invalid")
        expected_probabilities = [
            {"denominator": denominator, "numerator": score} for score in scores
        ]
        if probabilities != expected_probabilities:
            raise ProtocolError("ranking probabilities do not match scores")
        selected_index = action.outputs.get("selected_index")
        selected_option = action.outputs.get("selected_option")
        selected_option_kind = action.outputs.get("selected_option_kind")
        if (
            isinstance(selected_index, bool)
            or not isinstance(selected_index, int)
            or selected_index < 0
            or selected_index >= len(scores)
        ):
            raise ProtocolError("ranking selected index is invalid")
        expected_index = max(range(len(scores)), key=scores.__getitem__)
        expected_option = option_set.options[selected_index]
        if selected_index != expected_index or selected_option != expected_option.candidate_id:
            raise ProtocolError("ranking selected option is inconsistent with scores")
        if selected_option_kind != expected_option.kind:
            raise ProtocolError("ranking selected option kind is inconsistent")
        if (
            claim.get("selected_index") != selected_index
            or claim.get("selected_option") != selected_option
            or claim.get("selected_option_kind") != selected_option_kind
        ):
            raise ProtocolError("ranking claim selection binding mismatch")
        theorem_name = self._identifier(f"ranking_{action.action_digest[7:19]}")
        lean_scores = ", ".join(str(score) for score in scores)
        score_list = f"[{lean_scores}]"
        comparisons = [
            f"nthOrZero {score_list} {index} ≤ nthOrZero {score_list} {selected_index}"
            for index in range(len(scores))
            if index != selected_index
        ]
        clauses = [
            f"weightSum {score_list} = {denominator}",
            f"nthOrZero {score_list} {selected_index} = {scores[selected_index]}",
            *comparisons,
        ]
        statement = " ∧ ".join(clauses)
        source = f"""import Std

namespace NanoInterp

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

end NanoInterp
"""
        return theorem_name, statement, source

    def attempt(self, action: MiniAction) -> ProofAttempt:
        theorem_name, statement, source = self.source_for(action)
        if shutil.which(self.command[0]) is None:
            return ProofAttempt.create(
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
            with tempfile.TemporaryDirectory(prefix="nano-interp-proof-") as temp_dir:
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
            return ProofAttempt.create(
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
        return ProofAttempt.create(
            action_digest=action.action_digest,
            status="checked" if result.returncode == 0 else "failed",
            theorem_name=theorem_name,
            statement=statement,
            source=source,
            checker="lean-kernel",
            checker_version="4.30.0",
            diagnostics=diagnostics,
        )

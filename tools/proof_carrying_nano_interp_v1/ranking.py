"""Deterministic hypothesis-ranking nano for the V1 synthetic boundary.

State slice: proof-carrying-nano-interp-v1.
This adapter derives stable integer scores or consumes caller-supplied integer
scores; it does not load a model.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Sequence

from .protocol import PROTOCOL_ID, STATE_SLICE, ProtocolError, canonical_bytes, canonical_digest
from .runtime import ActivationTrace, MiniAction, ToyHostSlice


OPTION_SET_SCHEMA = "hypothesis-option-set-v1"
OPTION_KINDS = frozenset({"feature", "circuit", "intervention"})


def context_digest(context: Any) -> str:
    return canonical_digest(context)


@dataclass(frozen=True)
class HypothesisOption:
    candidate_id: str
    kind: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.candidate_id, str)
            or not isinstance(self.kind, str)
            or not self.candidate_id
            or self.kind not in OPTION_KINDS
        ):
            raise ProtocolError("hypothesis option fields must be non-empty and use a supported kind")

    def to_dict(self) -> dict[str, str]:
        return {"candidate_id": self.candidate_id, "kind": self.kind}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HypothesisOption":
        if not isinstance(payload, dict) or set(payload) != {"candidate_id", "kind"}:
            raise ProtocolError("hypothesis option schema is not closed")
        return cls(candidate_id=payload["candidate_id"], kind=payload["kind"])


@dataclass(frozen=True)
class HypothesisOptionSet:
    context_digest: str
    scorer_identity: str
    options: tuple[HypothesisOption, ...]
    option_set_digest: str

    @classmethod
    def create(
        cls,
        *,
        context_digest: str,
        scorer_identity: str,
        options: Sequence[HypothesisOption],
    ) -> "HypothesisOptionSet":
        normalized = tuple(options)
        if (
            not isinstance(context_digest, str)
            or not context_digest.startswith("sha256:")
            or not isinstance(scorer_identity, str)
            or not scorer_identity
        ):
            raise ProtocolError("hypothesis option-set identity is invalid")
        if not normalized or any(not isinstance(option, HypothesisOption) for option in normalized):
            raise ProtocolError("hypothesis options must be non-empty and typed")
        if len({option.candidate_id for option in normalized}) != len(normalized):
            raise ProtocolError("hypothesis options must be non-empty and unique")
        unsigned = {
            "context_digest": context_digest,
            "options": [option.to_dict() for option in normalized],
            "schema": OPTION_SET_SCHEMA,
            "scorer_identity": scorer_identity,
        }
        return cls(
            context_digest=context_digest,
            scorer_identity=scorer_identity,
            options=normalized,
            option_set_digest=canonical_digest(unsigned),
        )

    def to_dict(self) -> dict[str, Any]:
        unsigned = {
            "context_digest": self.context_digest,
            "options": [option.to_dict() for option in self.options],
            "schema": OPTION_SET_SCHEMA,
            "scorer_identity": self.scorer_identity,
        }
        return {**unsigned, "option_set_digest": self.option_set_digest}

    def assert_digest(self) -> None:
        """Reject direct-constructor or payload mutations before scoring."""

        try:
            expected = type(self).create(
                context_digest=self.context_digest,
                scorer_identity=self.scorer_identity,
                options=self.options,
            )
        except (ProtocolError, TypeError) as exc:
            raise ProtocolError(f"option set is invalid: {exc}") from exc
        if self.option_set_digest != expected.option_set_digest:
            raise ProtocolError("option set digest mismatch")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HypothesisOptionSet":
        if not isinstance(payload, dict):
            raise ProtocolError("option set payload is invalid")
        if set(payload) != {
            "context_digest",
            "options",
            "option_set_digest",
            "schema",
            "scorer_identity",
        }:
            raise ProtocolError("option set schema is not closed")
        if payload["schema"] != OPTION_SET_SCHEMA:
            raise ProtocolError("option set schema version is unsupported")
        options_value = payload["options"]
        if not isinstance(options_value, list):
            raise ProtocolError("option set options are invalid")
        try:
            options = tuple(HypothesisOption.from_dict(option) for option in options_value)
        except (KeyError, TypeError) as exc:
            raise ProtocolError("option set option is invalid") from exc
        if not isinstance(payload["context_digest"], str) or not isinstance(
            payload["scorer_identity"], str
        ) or not isinstance(payload["option_set_digest"], str):
            raise ProtocolError("option set identity fields are invalid")
        if not payload["context_digest"].startswith("sha256:") or not payload["scorer_identity"]:
            raise ProtocolError("option set identity fields are invalid")
        if not options or len({option.candidate_id for option in options}) != len(options):
            raise ProtocolError("hypothesis options must be non-empty and unique")
        expected = cls.create(
            context_digest=payload["context_digest"],
            scorer_identity=payload["scorer_identity"],
            options=options,
        )
        if payload["option_set_digest"] != expected.option_set_digest:
            raise ProtocolError("option set digest mismatch")
        return expected


@dataclass(frozen=True)
class DeterministicOptionScorer:
    identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity:
            raise ProtocolError("scorer identity must be non-empty")

    def score(self, option_set: HypothesisOptionSet) -> tuple[int, ...]:
        """Derive stable positive integer weights without loading a model."""

        weights = []
        for index, option in enumerate(option_set.options):
            digest = hashlib.sha256(
                canonical_bytes(
                    {
                        "candidate_id": option.candidate_id,
                        "context_digest": option_set.context_digest,
                        "index": index,
                        "kind": option.kind,
                        "scorer_identity": self.identity,
                    }
                )
            ).digest()
            weights.append(int.from_bytes(digest[:8], "big") % 1000 + 1)
        return tuple(weights)

    def rank(
        self,
        option_set: HypothesisOptionSet,
        *,
        scores: Sequence[object] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(option_set, HypothesisOptionSet):
            raise ProtocolError("option set is invalid")
        option_set.assert_digest()
        if option_set.scorer_identity != self.identity:
            raise ProtocolError("option-set scorer does not match scorer adapter")
        normalized_scores = self.score(option_set) if scores is None else tuple(scores)
        if len(normalized_scores) != len(option_set.options) or any(
            isinstance(score, bool) or not isinstance(score, int) or score < 0 for score in normalized_scores
        ):
            raise ProtocolError("scores must be non-negative integer score weights matching options")
        denominator = sum(normalized_scores)
        if denominator <= 0:
            raise ProtocolError("score weights must have a positive sum")
        selected_index = max(range(len(normalized_scores)), key=normalized_scores.__getitem__)
        return {
            "probabilities": [
                {"denominator": denominator, "numerator": score} for score in normalized_scores
            ],
            "selected_index": selected_index,
            "selected_option": option_set.options[selected_index].candidate_id,
            "selected_option_kind": option_set.options[selected_index].kind,
        }


@dataclass(frozen=True)
class HypothesisRankingNano:
    identity: str
    scorer: DeterministicOptionScorer

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity:
            raise ProtocolError("ranking nano identity must be non-empty")

    def attach(self, host: ToyHostSlice, *, layer: int, site: str) -> "HypothesisRankingAttachment":
        if layer < 0 or not site:
            raise ProtocolError("attachment location is invalid")
        return HypothesisRankingAttachment(self, host, layer, site)


@dataclass(frozen=True)
class HypothesisRankingAttachment:
    nano: HypothesisRankingNano
    host: ToyHostSlice
    layer: int
    site: str

    def run(
        self,
        trace: ActivationTrace,
        option_set: HypothesisOptionSet,
        *,
        scores: Sequence[object] | None = None,
        timestamp: str,
        action_version: int = 1,
    ) -> MiniAction:
        if not timestamp or isinstance(action_version, bool) or action_version < 1:
            raise ProtocolError("action timestamp and positive version are required")
        if trace.checkpoint_id != self.host.checkpoint_id:
            raise ProtocolError("trace checkpoint does not match attached host")
        if trace.layer != self.layer or trace.site != self.site:
            raise ProtocolError("trace location does not match attachment")
        if not isinstance(option_set, HypothesisOptionSet):
            raise ProtocolError("option set is invalid")
        if option_set.scorer_identity != self.nano.scorer.identity:
            raise ProtocolError("option-set scorer does not match nano scorer")
        option_set.assert_digest()
        normalized_scores = self.nano.scorer.score(option_set) if scores is None else tuple(scores)
        ranking = self.nano.scorer.rank(option_set, scores=normalized_scores)
        claim = {
            "claim_key": (
                f"{trace.checkpoint_id}:{self.layer}:{self.site}:"
                f"hypothesis-ranking:{option_set.option_set_digest}"
            ),
            "kind": "hypothesis",
            "context_digest": option_set.context_digest,
            "option_ids": [option.candidate_id for option in option_set.options],
            "option_set_digest": option_set.option_set_digest,
            "selected_index": ranking["selected_index"],
            "selected_option": ranking["selected_option"],
            "selected_option_kind": ranking["selected_option_kind"],
            "scorer_identity": self.nano.scorer.identity,
            "type": "hypothesis_ranking",
        }
        inputs = {
            "activation": list(trace.activation),
            "option_set": option_set.to_dict(),
            "prompt": trace.prompt,
            "scores": list(normalized_scores),
            "seed": trace.seed,
        }
        outputs = {
            "probabilities": ranking["probabilities"],
            "selected_index": ranking["selected_index"],
            "selected_option": ranking["selected_option"],
            "selected_option_kind": ranking["selected_option_kind"],
            "status": "HypothesisOnly",
        }
        unsigned = {
            "action_version": action_version,
            "claim": claim,
            "host_checkpoint_id": trace.checkpoint_id,
            "host_context_hash": trace.host_context_hash,
            "inputs": inputs,
            "layer": self.layer,
            "nano_identity": self.nano.identity,
            "outputs": outputs,
            "protocol_identity": PROTOCOL_ID,
            "site": self.site,
            "state_slice": STATE_SLICE,
            "timestamp": timestamp,
        }
        return MiniAction(
            state_slice=STATE_SLICE,
            protocol_identity=PROTOCOL_ID,
            action_version=action_version,
            timestamp=timestamp,
            inputs=inputs,
            outputs=outputs,
            host_context_hash=trace.host_context_hash,
            host_checkpoint_id=trace.checkpoint_id,
            nano_identity=self.nano.identity,
            layer=self.layer,
            site=self.site,
            claim=claim,
            action_digest=canonical_digest(unsigned),
        )

    def run_and_record(
        self,
        trace: ActivationTrace,
        option_set: HypothesisOptionSet,
        *,
        scores: Sequence[object] | None = None,
        store: Any,
        timestamp: str,
        action_version: int = 1,
        proof_engine: Any = None,
    ) -> tuple[MiniAction, Any]:
        from .proof import LeanProofEngine

        action = self.run(
            trace,
            option_set,
            scores=scores,
            timestamp=timestamp,
            action_version=action_version,
        )
        proof = (proof_engine or LeanProofEngine()).attempt(action)
        store.commit_action(action)
        store.commit_proof(proof)
        return action, proof

    def replay(self, action: MiniAction) -> MiniAction:
        """Reconstruct a ranking action from its logged inputs."""

        if action.nano_identity != self.nano.identity:
            raise ProtocolError("action nano identity does not match attachment")
        if action.layer != self.layer or action.site != self.site:
            raise ProtocolError("action location does not match attachment")
        try:
            activation = tuple(action.inputs["activation"])
            prompt = action.inputs["prompt"]
            seed = action.inputs["seed"]
            option_set = HypothesisOptionSet.from_dict(action.inputs["option_set"])
            scores = tuple(action.inputs["scores"])
        except (KeyError, TypeError) as exc:
            raise ProtocolError("action inputs cannot be replayed") from exc
        trace = self.host.capture(
            prompt=prompt,
            activation=activation,
            seed=seed,
            layer=action.layer,
            site=action.site,
        )
        return self.run(
            trace,
            option_set,
            scores=scores,
            timestamp=action.timestamp,
            action_version=action.action_version,
        )

"""Deterministic toy causal intervention nano for the V1 boundary.

State slice: proof-carrying-nano-interp-v1.
This module applies a pure replacement to a captured activation tuple. It does
not mutate or execute a host model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .protocol import PROTOCOL_ID, STATE_SLICE, ProtocolError, canonical_digest
from .runtime import ActivationTrace, MiniAction, ToyHostSlice


INTERVENTION_SPEC_SCHEMA = "toy-replace-intervention-v1"
INTERVENTION_OPERATION = "replace_activation"


@dataclass(frozen=True)
class InterventionSpec:
    context_digest: str
    intervention_id: str
    index: int
    replacement: int
    spec_digest: str

    @classmethod
    def create(
        cls,
        *,
        context_digest: str,
        intervention_id: str,
        index: int,
        replacement: int,
    ) -> "InterventionSpec":
        if (
            not isinstance(context_digest, str)
            or not context_digest.startswith("sha256:")
            or not isinstance(intervention_id, str)
            or not intervention_id
            or isinstance(index, bool)
            or not isinstance(index, int)
            or index < 0
            or isinstance(replacement, bool)
            or not isinstance(replacement, int)
        ):
            raise ProtocolError("intervention specification fields are invalid")
        unsigned = {
            "context_digest": context_digest,
            "index": index,
            "intervention_id": intervention_id,
            "operation": INTERVENTION_OPERATION,
            "replacement": replacement,
            "schema": INTERVENTION_SPEC_SCHEMA,
        }
        return cls(
            context_digest=context_digest,
            intervention_id=intervention_id,
            index=index,
            replacement=replacement,
            spec_digest=canonical_digest(unsigned),
        )

    def to_dict(self) -> dict[str, Any]:
        unsigned = {
            "context_digest": self.context_digest,
            "index": self.index,
            "intervention_id": self.intervention_id,
            "operation": INTERVENTION_OPERATION,
            "replacement": self.replacement,
            "schema": INTERVENTION_SPEC_SCHEMA,
        }
        return {**unsigned, "spec_digest": self.spec_digest}

    def assert_digest(self) -> None:
        try:
            expected = type(self).create(
                context_digest=self.context_digest,
                intervention_id=self.intervention_id,
                index=self.index,
                replacement=self.replacement,
            )
        except (ProtocolError, TypeError) as exc:
            raise ProtocolError(f"intervention specification is invalid: {exc}") from exc
        if self.spec_digest != expected.spec_digest:
            raise ProtocolError("intervention specification digest mismatch")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InterventionSpec":
        if not isinstance(payload, dict) or set(payload) != {
            "context_digest",
            "index",
            "intervention_id",
            "operation",
            "replacement",
            "schema",
            "spec_digest",
        }:
            raise ProtocolError("intervention specification schema is not closed")
        if (
            payload["schema"] != INTERVENTION_SPEC_SCHEMA
            or payload["operation"] != INTERVENTION_OPERATION
        ):
            raise ProtocolError("intervention specification identity is invalid")
        try:
            expected = cls.create(
                context_digest=payload["context_digest"],
                intervention_id=payload["intervention_id"],
                index=payload["index"],
                replacement=payload["replacement"],
            )
        except (KeyError, TypeError) as exc:
            raise ProtocolError("intervention specification fields are invalid") from exc
        if payload["spec_digest"] != expected.spec_digest:
            raise ProtocolError("intervention specification digest mismatch")
        return expected


@dataclass(frozen=True)
class CausalInterventionNano:
    identity: str

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity:
            raise ProtocolError("intervention nano identity must be non-empty")

    def attach(
        self,
        host: ToyHostSlice,
        *,
        layer: int,
        site: str,
    ) -> "CausalInterventionAttachment":
        if isinstance(layer, bool) or not isinstance(layer, int) or layer < 0 or not site:
            raise ProtocolError("attachment location is invalid")
        return CausalInterventionAttachment(self, host, layer, site)


@dataclass(frozen=True)
class CausalInterventionAttachment:
    nano: CausalInterventionNano
    host: ToyHostSlice
    layer: int
    site: str

    @staticmethod
    def _validate_hypothesis(
        hypothesis_action: MiniAction | None,
        *,
        trace: ActivationTrace,
    ) -> str | None:
        if hypothesis_action is None:
            return None
        if not isinstance(hypothesis_action, MiniAction):
            raise ProtocolError("hypothesis reference is invalid")
        try:
            MiniAction.from_dict(hypothesis_action.to_dict())
        except (KeyError, ProtocolError) as exc:
            raise ProtocolError(f"hypothesis reference is invalid: {exc}") from exc
        if (
            hypothesis_action.claim.get("type") != "hypothesis_ranking"
            or hypothesis_action.host_checkpoint_id != trace.checkpoint_id
            or hypothesis_action.host_context_hash != trace.host_context_hash
            or hypothesis_action.layer != trace.layer
            or hypothesis_action.site != trace.site
        ):
            raise ProtocolError("hypothesis reference does not match intervention context")
        return hypothesis_action.action_digest

    def run(
        self,
        trace: ActivationTrace,
        spec: InterventionSpec,
        *,
        timestamp: str,
        hypothesis_action: MiniAction | None = None,
        action_version: int = 1,
    ) -> MiniAction:
        if not timestamp or isinstance(action_version, bool) or action_version < 1:
            raise ProtocolError("action timestamp and positive version are required")
        if trace.checkpoint_id != self.host.checkpoint_id:
            raise ProtocolError("trace checkpoint does not match attached host")
        if trace.layer != self.layer or trace.site != self.site:
            raise ProtocolError("trace location does not match attachment")
        if not isinstance(spec, InterventionSpec):
            raise ProtocolError("intervention specification is invalid")
        spec.assert_digest()
        if spec.context_digest != trace.host_context_hash:
            raise ProtocolError("intervention specification context does not match trace")
        if spec.index >= len(trace.activation):
            raise ProtocolError("intervention index is outside activation")
        hypothesis_digest = self._validate_hypothesis(hypothesis_action, trace=trace)
        pre_activation = list(trace.activation)
        post_activation = list(pre_activation)
        post_activation[spec.index] = spec.replacement
        delta = [after - before for before, after in zip(pre_activation, post_activation)]
        control_delta = [0 for _ in pre_activation]
        claim = {
            "claim_key": (
                f"{trace.checkpoint_id}:{self.layer}:{self.site}:"
                f"intervention:{spec.spec_digest}"
            ),
            "effect": delta[spec.index],
            "effect_index": spec.index,
            "hypothesis_action_digest": hypothesis_digest,
            "intervention_id": spec.intervention_id,
            "intervention_spec_digest": spec.spec_digest,
            "kind": "intervention_observation",
            "type": "intervention_effect_exact",
        }
        inputs = {
            "activation": pre_activation,
            "hypothesis_action_digest": hypothesis_digest,
            "intervention_spec": spec.to_dict(),
            "prompt": trace.prompt,
            "seed": trace.seed,
        }
        outputs = {
            "control": {
                "delta": control_delta,
                "effect": 0,
                "kind": "no_op",
                "post_activation": pre_activation,
            },
            "delta": delta,
            "effect": delta[spec.index],
            "effect_index": spec.index,
            "post_activation": post_activation,
            "pre_activation": pre_activation,
            "status": "InterventionObserved",
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
        spec: InterventionSpec,
        *,
        store: Any,
        timestamp: str,
        hypothesis_action: MiniAction | None = None,
        action_version: int = 1,
        proof_engine: Any = None,
    ) -> tuple[MiniAction, Any]:
        from .proof import LeanProofEngine

        action = self.run(
            trace,
            spec,
            timestamp=timestamp,
            hypothesis_action=hypothesis_action,
            action_version=action_version,
        )
        proof = (proof_engine or LeanProofEngine()).attempt(action)
        store.commit_action(action)
        store.commit_proof(proof)
        return action, proof

    def replay(
        self,
        action: MiniAction,
        *,
        hypothesis_action: MiniAction | None = None,
    ) -> MiniAction:
        if action.nano_identity != self.nano.identity:
            raise ProtocolError("action nano identity does not match attachment")
        if action.layer != self.layer or action.site != self.site:
            raise ProtocolError("action location does not match attachment")
        try:
            activation = tuple(action.inputs["activation"])
            prompt = action.inputs["prompt"]
            seed = action.inputs["seed"]
            spec = InterventionSpec.from_dict(action.inputs["intervention_spec"])
            expected_hypothesis_digest = action.inputs["hypothesis_action_digest"]
        except (KeyError, TypeError) as exc:
            raise ProtocolError("action inputs cannot be replayed") from exc
        if expected_hypothesis_digest is not None:
            if hypothesis_action is None or hypothesis_action.action_digest != expected_hypothesis_digest:
                raise ProtocolError("replay requires the referenced hypothesis action")
        trace = self.host.capture(
            prompt=prompt,
            activation=activation,
            seed=seed,
            layer=action.layer,
            site=action.site,
        )
        return self.run(
            trace,
            spec,
            timestamp=action.timestamp,
            hypothesis_action=hypothesis_action,
            action_version=action.action_version,
        )

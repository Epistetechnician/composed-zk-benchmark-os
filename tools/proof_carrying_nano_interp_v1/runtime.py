"""Deterministic toy host and read-only feature nano for V1.

State slice: proof-carrying-nano-interp-v1.
This module is a synthetic contract fixture, not a frontier-model adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .protocol import PROTOCOL_ID, STATE_SLICE, ProtocolError, canonical_digest


@dataclass(frozen=True)
class ActivationTrace:
    checkpoint_id: str
    layer: int
    site: str
    prompt: str
    activation: tuple[int, ...]
    seed: int
    host_context_hash: str

    def to_inputs(self) -> dict[str, Any]:
        return {
            "activation": list(self.activation),
            "prompt": self.prompt,
            "seed": self.seed,
        }


@dataclass(frozen=True)
class ToyHostSlice:
    """A deterministic host slice exposing activation capture only."""

    checkpoint_id: str
    width: int = 2
    architecture: str = "toy-residual-v1"

    def __post_init__(self) -> None:
        if not self.checkpoint_id:
            raise ProtocolError("checkpoint_id must be non-empty")
        if self.width < 1:
            raise ProtocolError("width must be positive")

    def capture(
        self,
        *,
        prompt: str,
        activation: Sequence[int],
        seed: int,
        layer: int,
        site: str,
    ) -> ActivationTrace:
        if layer < 0:
            raise ProtocolError("layer must be non-negative")
        if not site:
            raise ProtocolError("site must be non-empty")
        if len(activation) != self.width:
            raise ProtocolError("activation width does not match host slice")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in activation):
            raise ProtocolError("activations must be integers")
        context = {
            "architecture": self.architecture,
            "checkpoint_id": self.checkpoint_id,
            "layer": layer,
            "seed": seed,
            "site": site,
            "width": self.width,
        }
        return ActivationTrace(
            checkpoint_id=self.checkpoint_id,
            layer=layer,
            site=site,
            prompt=prompt,
            activation=tuple(activation),
            seed=seed,
            host_context_hash=canonical_digest(context),
        )

    def snapshot(self) -> tuple[str, int, str]:
        """Expose the immutable host identity for read-only attachment checks."""

        return self.checkpoint_id, self.width, self.architecture


@dataclass(frozen=True)
class MiniAction:
    state_slice: str
    protocol_identity: str
    action_version: int
    timestamp: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    host_context_hash: str
    host_checkpoint_id: str
    nano_identity: str
    layer: int
    site: str
    claim: dict[str, Any]
    action_digest: str

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "action_version": self.action_version,
            "claim": self.claim,
            "host_checkpoint_id": self.host_checkpoint_id,
            "host_context_hash": self.host_context_hash,
            "inputs": self.inputs,
            "layer": self.layer,
            "nano_identity": self.nano_identity,
            "outputs": self.outputs,
            "protocol_identity": self.protocol_identity,
            "site": self.site,
            "state_slice": self.state_slice,
            "timestamp": self.timestamp,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.unsigned_dict(), "action_digest": self.action_digest}


@dataclass(frozen=True)
class FeatureDetectorNano:
    identity: str
    feature_id: str
    feature_index: int
    threshold: int

    def __post_init__(self) -> None:
        if not self.identity or not self.feature_id:
            raise ProtocolError("nano identity and feature_id must be non-empty")
        if self.feature_index < 0:
            raise ProtocolError("feature_index must be non-negative")

    def attach(self, host: ToyHostSlice, *, layer: int, site: str) -> "NanoAttachment":
        if self.feature_index >= host.width:
            raise ProtocolError("feature_index is outside host width")
        if layer < 0 or not site:
            raise ProtocolError("attachment location is invalid")
        return NanoAttachment(self, host, layer, site)


@dataclass(frozen=True)
class NanoAttachment:
    nano: FeatureDetectorNano
    host: ToyHostSlice
    layer: int
    site: str

    def run(self, trace: ActivationTrace, *, timestamp: str, action_version: int = 1) -> MiniAction:
        if trace.checkpoint_id != self.host.checkpoint_id:
            raise ProtocolError("trace checkpoint does not match attached host")
        if trace.layer != self.layer or trace.site != self.site:
            raise ProtocolError("trace location does not match attachment")
        feature_value = trace.activation[self.nano.feature_index]
        unsigned = {
            "action_version": action_version,
            "claim": {
                "claim_key": (
                    f"{trace.checkpoint_id}:{trace.layer}:{trace.site}:{self.nano.feature_id}"
                ),
                "feature_id": self.nano.feature_id,
                "feature_index": self.nano.feature_index,
                "type": "feature_activation_exact",
                "value": feature_value,
            },
            "host_checkpoint_id": trace.checkpoint_id,
            "host_context_hash": trace.host_context_hash,
            "inputs": trace.to_inputs(),
            "layer": self.layer,
            "nano_identity": self.nano.identity,
            "outputs": {
                "detected": feature_value >= self.nano.threshold,
                "feature_value": feature_value,
            },
            "protocol_identity": PROTOCOL_ID,
            "site": self.site,
            "state_slice": STATE_SLICE,
            "timestamp": timestamp,
        }
        action_digest = canonical_digest(unsigned)
        return MiniAction(
            state_slice=STATE_SLICE,
            protocol_identity=PROTOCOL_ID,
            action_version=action_version,
            timestamp=timestamp,
            inputs=unsigned["inputs"],
            outputs=unsigned["outputs"],
            host_context_hash=trace.host_context_hash,
            host_checkpoint_id=trace.checkpoint_id,
            nano_identity=self.nano.identity,
            layer=self.layer,
            site=self.site,
            claim=unsigned["claim"],
            action_digest=action_digest,
        )

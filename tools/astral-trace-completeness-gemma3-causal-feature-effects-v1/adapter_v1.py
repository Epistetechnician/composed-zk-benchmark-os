"""Native/instrumented adapter with typed causal-intervention metadata.

State slice: astral-trace-completeness-gemma3-causal-feature-effects-v1.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
V2_ROOT = HERE.parent / "astral-trace-completeness-v2"
V4_ROOT = HERE.parent / "astral-trace-completeness-v4"
for root in (V2_ROOT, V4_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

import protocol_v1 as protocol
import registry_v1 as registry
import torch_adapter_v2 as legacy

_DONOR_METADATA: dict[str, dict[str, Any]] = {}
# GiveMeANode execution is deliberately serial: the active plan is bound for
# one isolated run and cleared before the next run begins. This keeps the
# inherited V2 hook ABI while typing controls that have no donor.
_ACTIVE_INTERVENTION_METADATA: dict[str, Any] | None = None
_ACTIVE_RUN_METADATA: dict[str, Any] | None = None


class TraceEmitter(legacy.TraceEmitter):
    """Replace the V2 event constructor with the V1 typed event schema."""

    def emit(self, kind: str, **kwargs: Any) -> protocol.TraceEvent:
        metadata = dict(kwargs.pop("metadata", {}))
        event_step = kwargs.pop("step", self.step)
        if kind == "run_start" and _ACTIVE_RUN_METADATA is not None:
            metadata.update(_ACTIVE_RUN_METADATA)
        if kind == "intervention":
            metadata.update(_DONOR_METADATA.get(str(kwargs.get("value_sha256")), {}))
            if _ACTIVE_INTERVENTION_METADATA is not None:
                metadata.update(_ACTIVE_INTERVENTION_METADATA)
        event = protocol.TraceEvent(
            run_id=self.run_id,
            trial_id=self.trial_id,
            sequence=len(self.events),
            kind=kind,
            step=event_step,
            metadata=metadata,
            **kwargs,
        )
        event.validate()
        self.events.append(event)
        return event


@dataclasses.dataclass(frozen=True)
class CausalIntervention:
    module_path: str
    step: int
    kind: str
    donor: Any | None = None
    feature_index: int | None = None
    path_id: str | None = None
    donor_trial_id: str | None = None

    def __post_init__(self) -> None:
        if self.donor is not None:
            _DONOR_METADATA[legacy.tensor_digest(self.donor)] = intervention_metadata(self)

    @property
    def mode(self) -> str:
        if self.kind == "noop":
            return "noop"
        if self.kind == "zero":
            return "zero"
        return "replace"

    def validate(self, paths: Sequence[str]) -> None:
        if self.module_path not in paths or self.step < 0:
            raise protocol.ProtocolError("causal intervention is outside the frozen registry")
        if self.kind not in protocol.INTERVENTION_KINDS or self.kind == "natural":
            raise protocol.ProtocolError("unsupported causal intervention")
        if self.kind not in {"noop", "zero"} and self.donor is None:
            raise protocol.ProtocolError("causal replacement requires a donor")
        if self.kind in {"feature_ablation", "feature_replacement", "shuffled", "constant"}:
            if self.feature_index is None or not 0 <= self.feature_index < protocol.FEATURE_WIDTH:
                raise protocol.ProtocolError("feature intervention requires a valid feature index")
        if self.kind == "path_patch" and not self.path_id:
            raise protocol.ProtocolError("path patch requires a frozen path id")


def as_legacy_plan(intervention: CausalIntervention) -> Any:
    """Convert a V1 plan to the V2 hook ABI without changing the recipient."""

    if intervention.kind == "natural":
        return None
    return legacy.InterventionPlan(
        module_path=intervention.module_path,
        step=intervention.step,
        mode=intervention.mode,
        donor=intervention.donor,
    )


def feature_donor(
    transcoder: Any,
    input_activation: Any,
    recipient_activation: Any,
    *,
    feature_index: int,
    mode: str,
    donor_features: Any | None = None,
    position: int = -1,
) -> Any:
    """Construct an exact recipient-shaped donor from a feature transform.

    The transform changes only one locked feature at one locked sequence
    position, then carries the delta through the fixed transcoder decoder.
    The downstream model receives the resulting full activation tensor.
    """

    import torch

    if mode not in {"ablate", "replace", "shuffle", "constant"}:
        raise protocol.ProtocolError("unsupported feature donor mode")
    with torch.no_grad():
        model_input = input_activation.to(transcoder.dtype)
        encoded = transcoder.encode(model_input)
        changed = encoded.detach().clone()
        if mode == "ablate":
            changed[..., position, feature_index] = 0
        elif mode == "replace" or mode == "shuffle":
            if donor_features is None:
                raise protocol.ProtocolError("replacement feature donor is missing")
            changed[..., position, feature_index] = donor_features.to(changed.device, changed.dtype)[
                ..., position, feature_index
            ]
        else:
            changed[..., position, feature_index] = protocol.CONSTANT_FEATURE_VALUE
        baseline_reconstruction = transcoder.decode(encoded, model_input)
        changed_reconstruction = transcoder.decode(changed, model_input)
        donor = recipient_activation.detach().clone()
        donor[..., position, :] = donor[..., position, :] + (
            changed_reconstruction[..., position, :] - baseline_reconstruction[..., position, :]
        ).to(donor.dtype)
        if not bool(torch.isfinite(donor).all().item()):
            raise protocol.ProtocolError("feature donor is nonfinite")
        return donor


def intervention_metadata(intervention: CausalIntervention) -> dict[str, Any]:
    operator = f"exact-{intervention.kind}-v1"
    return {
        "intervention_kind": intervention.kind,
        "operator": operator,
        "operator_digest": protocol.digest_json(
            {
                "operator": operator,
                "module_path": intervention.module_path,
                "step": intervention.step,
                "feature_index": intervention.feature_index,
                "path_id": intervention.path_id,
            }
        ),
        "feature_index": intervention.feature_index,
        "path_id": intervention.path_id,
        "donor_trial_id": intervention.donor_trial_id,
    }


legacy.protocol = protocol
legacy.registry = registry
legacy.TraceEmitter = TraceEmitter

InterventionPlan = legacy.InterventionPlan


class InstrumentedGenerator(legacy.InstrumentedGenerator):
    """V2 generator with a V1 plan binding for every intervention event."""

    def run(
        self,
        *args: Any,
        intervention: CausalIntervention | Any | None = None,
        repeat_index: int = 0,
        **kwargs: Any,
    ) -> Any:
        global _ACTIVE_INTERVENTION_METADATA, _ACTIVE_RUN_METADATA
        if not isinstance(repeat_index, int) or repeat_index < 0:
            raise protocol.ProtocolError("repeat index must be a nonnegative integer")
        plan = intervention
        metadata: dict[str, Any] | None = None
        if isinstance(intervention, CausalIntervention):
            intervention.validate(tuple(self.registry["module_input_paths"]))
            plan = as_legacy_plan(intervention)
            metadata = intervention_metadata(intervention)
        previous = _ACTIVE_INTERVENTION_METADATA
        previous_run = _ACTIVE_RUN_METADATA
        _ACTIVE_INTERVENTION_METADATA = metadata
        _ACTIVE_RUN_METADATA = {"repeat_index": repeat_index}
        try:
            return super().run(*args, intervention=plan, **kwargs)
        finally:
            _ACTIVE_INTERVENTION_METADATA = previous
            _ACTIVE_RUN_METADATA = previous_run


TraceRun = legacy.TraceRun
native_generate = legacy.native_generate
tensor_digest = legacy.tensor_digest

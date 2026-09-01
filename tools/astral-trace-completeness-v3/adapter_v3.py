"""V3 state-bound adapter over the qualified native capture implementation.

State slice: astral-trace-completeness-gemma3-end-to-end-v3.
"""

from __future__ import annotations

from pathlib import Path
import sys

_V2_ROOT = Path(__file__).resolve().parents[1] / "astral-trace-completeness-v2"
if str(_V2_ROOT) not in sys.path:
    sys.path.insert(0, str(_V2_ROOT))

import protocol_v3 as protocol
import registry_v3 as registry
import torch_adapter_v2 as _legacy_adapter


class TraceEmitter(_legacy_adapter.TraceEmitter):
    def emit(self, kind: str, **kwargs):
        event = protocol.TraceEvent(
            run_id=self.run_id,
            trial_id=self.trial_id,
            sequence=len(self.events),
            kind=kind,
            step=self.step,
            **kwargs,
        )
        event.validate()
        self.events.append(event)
        return event


_legacy_adapter.protocol = protocol
_legacy_adapter.registry = registry
_legacy_adapter.TraceEmitter = TraceEmitter

InterventionPlan = _legacy_adapter.InterventionPlan
InstrumentedGenerator = _legacy_adapter.InstrumentedGenerator
TraceRun = _legacy_adapter.TraceRun
native_generate = _legacy_adapter.native_generate
tensor_digest = _legacy_adapter.tensor_digest

"""Fail-closed source gate for public benchmark execution CLIs.

State slice: verified-self-model-benchmark-execution-gate-v1.

The pure protocol evaluator remains usable for deterministic contract tests.
The public run and validation CLIs accept only the checked-in contract-smoke
source until a separately authorized release binds a live capture to custody,
review, and release evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .protocol import BenchmarkProtocolError, LIVE_SOURCE, SMOKE_SOURCE


EXECUTION_GATE_STATE_SLICE = "verified-self-model-benchmark-execution-gate-v1"


def require_public_execution_source(manifest: Mapping[str, Any]) -> None:
    """Reject live or unknown sources at the public CLI boundary."""

    source_type = manifest.get("source_type")
    if source_type == LIVE_SOURCE:
        raise BenchmarkProtocolError(
            "public benchmark execution for live captures requires a separately authorized release"
        )
    if source_type != SMOKE_SOURCE:
        raise BenchmarkProtocolError(
            "public benchmark execution accepts only contract_smoke_fixture input"
        )

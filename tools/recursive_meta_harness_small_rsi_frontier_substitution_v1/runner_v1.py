"""Run only the deterministic, model-free contract fixture.

State slice: ``recursive-meta-harness-small-rsi-frontier-substitution-v1``.

This runner intentionally cannot call a model, provider, network, subprocess,
or accepted-evidence writer.  Its output is a contract fixture, not a result
about any model or task distribution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .compiler_v1 import compile_manifest
from .protocol_v1 import (
    ARM_IDS,
    CLAIM_CEILING,
    FIXTURE_CLAIM_CEILING,
    FIXTURE_SCHEMA_VERSION,
    PROTOCOL_ID,
    STATE_SLICE,
    TASK_FAMILIES,
    digest,
    summarize,
    validate_observation,
)


def _unit(*parts: object) -> float:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") / float(1 << 64)


def _cost(arm_id: str, family_id: str, split: str, replicate: int, task_index: int) -> dict[str, int]:
    base = {
        "frontier_single": 52000,
        "small_single": 33000,
        "small_swarm_fixed": 44000,
        "small_swarm_rsi": 56000,
    }[arm_id]
    variation = int(4000 * _unit(STATE_SLICE, "cost", arm_id, family_id, split, replicate, task_index))
    values = {
        "uncached_model_micros": base // 2 + variation,
        "cached_model_micros": base // 10,
        "reasoning_micros": base // 12,
        "router_micros": base // 40 if "swarm" in arm_id else 0,
        "verifier_micros": base // 18,
        "retry_micros": base // 35 if arm_id == "small_swarm_rsi" else base // 60,
        "compaction_micros": base // 50 if "swarm" in arm_id else base // 80,
        "memory_micros": base // 55 if "swarm" in arm_id else base // 100,
        "tool_api_micros": base // 70,
        "compute_micros": base // 65,
        "storage_micros": base // 250,
        "cleanup_micros": base // 300,
        "human_review_micros": 0,
    }
    return values


def _observation(arm_id: str, family_id: str, split: str, replicate: int, task_index: int) -> dict[str, Any]:
    variation = int(22000 * _unit(STATE_SLICE, "score", family_id, split, replicate, task_index))
    score = min(999000, 500000 + variation)
    task_id = f"fixture-{split}-{family_id}-{task_index}-{replicate}"
    trace_digest = digest({"state_slice": STATE_SLICE, "task_id": task_id, "arm_id": arm_id, "fixture": True})
    return {
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "task_id": task_id,
        "family_id": family_id,
        "split": split,
        "replicate": replicate,
        "arm_id": arm_id,
        "status": "completed",
        "objective_score_micros": score,
        "constraint_results": {
            "safety": True,
            "integrity": True,
            "authority": True,
            "leakage": True,
            "audit_completeness": True,
        },
        "cost": _cost(arm_id, family_id, split, replicate, task_index),
        "latency_ms": 100 + int(100 * _unit(STATE_SLICE, "latency", task_id, arm_id)),
        "trace_digest": trace_digest,
    }


def run_contract_fixture() -> dict[str, Any]:
    """Build a deterministic development/tune fixture with assessment sealed."""

    manifest = compile_manifest()
    observations = [
        _observation(arm_id, family_id, split, replicate, task_index)
        for split in ("fit", "tune")
        for family_id in TASK_FAMILIES
        for task_index in range(2)
        for replicate in range(3)
        for arm_id in ARM_IDS
    ]
    evaluated = [validate_observation(observation) for observation in observations]
    body: dict[str, Any] = {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "protocol_id": PROTOCOL_ID,
        "claim_ceiling": FIXTURE_CLAIM_CEILING,
        "manifest_sha256": manifest["manifest_sha256"],
        "mode": "contract_fixture",
        "scientific_claim": False,
        "execution_authorized": False,
        "assessment_open": False,
        "observations": observations,
        "evaluated": evaluated,
        "summary": summarize(evaluated),
        "boundary": {
            "model_execution": "not_run",
            "provider_calls": "not_run",
            "network": "not_used",
            "accepted_evidence": "not_written",
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    return {**body, "fixture_sha256": digest(body)}


def write_fixture(fixture: dict[str, Any], output: Path) -> None:
    """Write a contract fixture to a new path without overwriting existing data."""

    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing fixture: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(fixture, ensure_ascii=True, sort_keys=True, indent=2).encode("utf-8") + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="write the model-free small-RSI contract fixture")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_fixture(run_contract_fixture(), args.output)
    print(json.dumps({"state_slice": STATE_SLICE, "mode": "contract_fixture", "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

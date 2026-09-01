"""Independent closure-only review for temporal-credit qualification V2.

State slice: ``oaklab-experience-learning-selective-credit-v2``.

This reviewer intentionally has no execution capability.  It checks the
receipt's frozen identity, prediction-lock records, batch-one accounting, and
terminal result, then returns an explicit closure-only decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


STATE_SLICE = "oaklab-experience-learning-selective-credit-v2"
EXPECTED_STREAMS = [
    "sparse_noisy", "nonstationary", "drifting", "noisy_mnist_like",
    "event_camera_like", "long_horizon",
]
EXPECTED_SEEDS = [10, 11, 12, 13, 14]


def _digest(value: dict) -> str:
    def canonical(item):
        if isinstance(item, dict):
            return {key: canonical(value) for key, value in item.items() if key != "wall_clock_latency_ns"}
        if isinstance(item, list):
            return [canonical(value) for value in item]
        return item
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def review(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("state_slice") != STATE_SLICE:
        raise ValueError("review state slice mismatch")
    if result.get("result_digest") != _digest({key: value for key, value in result.items() if key != "result_digest"}):
        raise ValueError("qualification result digest mismatch")
    plan = result.get("plan", {})
    if plan.get("state_slice") != STATE_SLICE or plan.get("stream_names") != EXPECTED_STREAMS:
        raise ValueError("reviewed plan stream set mismatch")
    if plan.get("seed_offsets") != EXPECTED_SEEDS or plan.get("candidate") != "temporal_utility_gate":
        raise ValueError("reviewed plan seed or candidate mismatch")
    plan_digest = _digest(plan)
    if result.get("plan_digest") != plan_digest:
        raise ValueError("reviewed plan digest mismatch")
    execution = result.get("execution", {})
    if execution.get("stream_names") != EXPECTED_STREAMS or execution.get("seed_offsets") != EXPECTED_SEEDS:
        raise ValueError("reviewed execution cohort mismatch")
    if execution.get("synthetic_only") is not True or execution.get("hardware_energy") != "not_run":
        raise ValueError("reviewed execution crossed hardware boundary")
    if execution.get("real_stream_execution") != "sealed_pending_review":
        raise ValueError("reviewed real-stream boundary mismatch")
    for stream_name in EXPECTED_STREAMS:
        stream = result.get("streams", {}).get(stream_name)
        if stream is None:
            raise ValueError(f"reviewed stream missing: {stream_name}")
        algorithms = stream.get("algorithms", {})
        if set(algorithms) != {"sgd_b1", "temporal_utility_gate"}:
            raise ValueError(f"reviewed algorithm set mismatch: {stream_name}")
        for algorithm, record in algorithms.items():
            if len(record.get("per_seed", [])) != len(EXPECTED_SEEDS):
                raise ValueError(f"reviewed seed count mismatch: {stream_name}/{algorithm}")
            for seed_record in record["per_seed"]:
                accounting = seed_record.get("accounting", {})
                if accounting.get("max_experience_items_per_observe") != 1 or accounting.get("hidden_gradient_accumulation") is not False:
                    raise ValueError(f"reviewed batch accounting mismatch: {stream_name}/{algorithm}")
                if set(seed_record.get("prediction_lock_snapshots", {})) != {"fit", "tune", "assessment"}:
                    raise ValueError(f"reviewed prediction lock missing: {stream_name}/{algorithm}")
    if result.get("status") != "no_candidate" or result.get("qualifying_streams"):
        raise ValueError("reviewed result is not a terminal no-candidate outcome")
    decision = {
        "schema_version": "oaklab.experience-learning.selective-credit-v2-review.v1",
        "state_slice": STATE_SLICE,
        "reviewer": "independent-mechanical-review",
        "reviewed_result_digest": result["result_digest"],
        "reviewed_plan_digest": result["plan_digest"],
        "decision": "accepted_for_closure_only",
        "execution_authorization": False,
        "real_stream_execution": "sealed",
        "hardware_energy": "not_run",
        "astral": "isolated_not_run",
    }
    decision["review_digest"] = _digest(decision)
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    decision = review(args.receipt)
    if args.output:
        args.output.write_text(json.dumps(decision, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(decision, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

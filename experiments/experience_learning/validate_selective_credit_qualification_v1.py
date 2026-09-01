"""Independent aggregate-only validator for selective-credit qualification.

State slice: ``oaklab-experience-learning-selective-credit-v1``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from .benchmark import _canonical_for_digest
from .selective_credit_qualification_v1 import PLAN, PLAN_DIGEST, SCHEMA_VERSION, STATE_SLICE


def validate(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("schema_version") != SCHEMA_VERSION or result.get("state_slice") != STATE_SLICE:
        raise ValueError("selective-credit schema or state slice mismatch")
    if result.get("plan_digest") != PLAN_DIGEST or result.get("plan") != PLAN:
        raise ValueError("qualification plan is not frozen")
    actual = hashlib.sha256(json.dumps(_canonical_for_digest({key: value for key, value in result.items() if key != "result_digest"}), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    if result.get("result_digest") != actual:
        raise ValueError("qualification digest mismatch")
    execution = result.get("execution", {})
    if execution.get("synthetic_only") is not True or execution.get("hardware_energy") != "not_run":
        raise ValueError("qualification escaped its synthetic-only boundary")
    if execution.get("seed_offsets") != PLAN["seed_offsets"]:
        raise ValueError("seed cohort mismatch")
    for stream_name, stream in result.get("streams", {}).items():
        algorithms = stream.get("algorithms", {})
        if set(algorithms) != {PLAN["reference"], PLAN["candidate"]}:
            raise ValueError(f"algorithm matrix mismatch for {stream_name}")
        for algorithm, record in algorithms.items():
            per_seed = record.get("per_seed", [])
            if len(per_seed) != len(PLAN["seed_offsets"]):
                raise ValueError(f"seed count mismatch for {stream_name}/{algorithm}")
            if not all(item.get("accounting", {}).get("max_experience_items_per_observe") == 1 for item in per_seed):
                raise ValueError(f"batch-one accounting mismatch for {stream_name}/{algorithm}")
            if not all(_finite(item.get("assessment_metrics", {}).get("mean_loss")) for item in per_seed):
                raise ValueError(f"non-finite loss for {stream_name}/{algorithm}")
        paired = stream.get("paired_test_candidate_minus_reference", {})
        if paired.get("n") != len(PLAN["seed_offsets"]) or not _finite(paired.get("p_value")):
            raise ValueError(f"paired test mismatch for {stream_name}")
    if result.get("status") not in {"candidate", "no_candidate"}:
        raise ValueError("invalid qualification status")
    return {
        "status": "valid",
        "state_slice": STATE_SLICE,
        "result_digest": actual,
        "qualification_status": result["status"],
        "qualifying_streams": result.get("qualifying_streams", []),
        "claim_ceiling": result.get("claim_ceiling"),
    }


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.receipt), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

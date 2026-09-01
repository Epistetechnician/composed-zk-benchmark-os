"""Independent validator for transformed real-stream matrix receipts.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from .benchmark import ALGORITHM_IDS
from .derive_real_streams_v1 import validate_manifest
from .real_benchmark_v1 import ASSESSMENT_COHORTS, CONTROL_NAMES, _digest


def validate(path: Path, custody_root: Path) -> dict:
    matrix = json.loads(path.read_text(encoding="utf-8"))
    if matrix.get("schema_version") != "oaklab.experience-learning.real-derived-matrix.v1":
        raise ValueError("derived matrix schema mismatch")
    if matrix.get("result_digest") != _digest({key: value for key, value in matrix.items() if key != "result_digest"}):
        raise ValueError("derived matrix digest mismatch")
    custody = validate_manifest(custody_root)
    if matrix.get("custody", {}).get("manifest_sha256") != custody["manifest_sha256"]:
        raise ValueError("derived matrix custody mismatch")
    datasets = matrix.get("datasets")
    if not isinstance(datasets, dict) or set(datasets) != {item["name"] for item in custody["datasets"]}:
        raise ValueError("derived matrix dataset coverage mismatch")
    for name, result in datasets.items():
        if result.get("result_digest") != _digest({key: value for key, value in result.items() if key != "result_digest"}):
            raise ValueError(f"{name}: result digest mismatch")
        count = result.get("assessment_cohort_count")
        if not isinstance(count, int) or count < ASSESSMENT_COHORTS:
            raise ValueError(f"{name}: powered assessment count missing")
        algorithms = result.get("algorithms", {})
        if set(algorithms) != set(ALGORITHM_IDS):
            raise ValueError(f"{name}: algorithm coverage mismatch")
        for algorithm, record in algorithms.items():
            if record.get("status") in {"not_applicable", "diverged"}:
                continue
            if record.get("status") != "executed":
                raise ValueError(f"{name}/{algorithm}: invalid status")
            cohorts = record.get("assessment_cohorts", [])
            if len(cohorts) != count or any(not isinstance(item.get("mean_loss"), (int, float)) or not math.isfinite(float(item["mean_loss"])) for item in cohorts):
                raise ValueError(f"{name}/{algorithm}: assessment cohort payload invalid")
        controls = result.get("controls", {})
        if set(controls) != set(CONTROL_NAMES) or controls["noise_floor"].get("status") != "executed":
            raise ValueError(f"{name}: controls incomplete")
    return {"status": "valid", "state_slice": matrix.get("state_slice"), "result_digest": matrix["result_digest"],
            "datasets": sorted(datasets)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.receipt, args.root), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

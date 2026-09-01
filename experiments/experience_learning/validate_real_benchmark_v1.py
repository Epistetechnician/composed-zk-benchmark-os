"""Independent validator for all-baseline real-panel receipts.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from .acquire_real_data_v1 import validate_manifest
from .benchmark import ALGORITHM_IDS
from .real_benchmark_v1 import (ASSESSMENT_COHORTS, CONTROL_NAMES, REQUIRED_ROWS,
                                SCHEMA_VERSION, STATE_SLICE, _digest)


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate(path: Path, custody_root: Path | None = None) -> dict:
    matrix = json.loads(path.read_text(encoding="utf-8"))
    if matrix.get("schema_version") != "oaklab.experience-learning.real-matrix.v1" or matrix.get("state_slice") != STATE_SLICE:
        raise ValueError("real matrix schema or state mismatch")
    if matrix.get("result_digest") != _digest({key: value for key, value in matrix.items() if key != "result_digest"}):
        raise ValueError("real matrix digest mismatch")
    if custody_root is not None:
        custody = validate_manifest(custody_root)
        if matrix.get("custody", {}).get("manifest_sha256") != custody["manifest_sha256"]:
            raise ValueError("real matrix custody digest mismatch")
    datasets = matrix.get("datasets")
    if not isinstance(datasets, dict) or not datasets:
        raise ValueError("real matrix contains no datasets")
    for dataset, result in datasets.items():
        if result.get("schema_version") != SCHEMA_VERSION or result.get("state_slice") != STATE_SLICE:
            raise ValueError(f"{dataset}: result schema or state mismatch")
        if result.get("result_digest") != _digest({key: value for key, value in result.items() if key != "result_digest"}):
            raise ValueError(f"{dataset}: result digest mismatch")
        assessment_count = result.get("assessment_cohort_count")
        if not isinstance(assessment_count, int) or assessment_count < ASSESSMENT_COHORTS:
            raise ValueError(f"{dataset}: assessment cohort count is below powered minimum")
        if result.get("algorithm_names") != list(ALGORITHM_IDS):
            raise ValueError(f"{dataset}: algorithm list mismatch")
        if result.get("control_names") != list(CONTROL_NAMES):
            raise ValueError(f"{dataset}: control list mismatch")
        algorithms = result.get("algorithms", {})
        if set(algorithms) != set(ALGORITHM_IDS):
            raise ValueError(f"{dataset}: algorithm coverage mismatch")
        for algorithm, record in algorithms.items():
            if record.get("status") == "not_applicable":
                if algorithm != "tidbd":
                    raise ValueError(f"{dataset}/{algorithm}: unexpected not_applicable")
                continue
            if record.get("status") == "diverged":
                if not isinstance(record.get("step"), int) or not isinstance(record.get("reason"), str):
                    raise ValueError(f"{dataset}/{algorithm}: divergence record is incomplete")
                continue
            if record.get("status") != "executed":
                raise ValueError(f"{dataset}/{algorithm}: invalid status")
            cohorts = record.get("assessment_cohorts")
            if not isinstance(cohorts, list) or len(cohorts) != assessment_count:
                raise ValueError(f"{dataset}/{algorithm}: cohort count mismatch")
            if any(not _finite(item.get("mean_loss")) or item["mean_loss"] < 0 for item in cohorts):
                raise ValueError(f"{dataset}/{algorithm}: invalid cohort losses")
            paired = record.get("paired_vs_sgd_b1")
            if algorithm != "sgd_b1" and (record.get("status") == "executed") and (not isinstance(paired, dict) or paired.get("n") != assessment_count or not _finite(paired.get("p_value"))):
                raise ValueError(f"{dataset}/{algorithm}: paired test missing")
        controls = result.get("controls", {})
        if set(controls) != set(CONTROL_NAMES):
            raise ValueError(f"{dataset}: control coverage mismatch")
        if controls["noise_floor"].get("status") != "executed" or controls["fit_only_topk_feature_sgd_b1"].get("status") != "executed":
            raise ValueError(f"{dataset}: required control not executed")
    return {"status": "valid", "state_slice": STATE_SLICE, "result_digest": matrix["result_digest"],
            "datasets": sorted(datasets), "required_rows_per_dataset": REQUIRED_ROWS}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.receipt, args.root), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

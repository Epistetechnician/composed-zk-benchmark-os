#!/usr/bin/env python3
"""Independent validator for the V33 read-only diagnosis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.diagnose_qwen25_acquisition_v33 import (
    CLAIM_CEILING,
    MODEL,
    SOURCE_STATE_SLICE,
    STATE_SLICE,
    SEEDS,
)


def validate(root: Path) -> dict:
    report = json.loads((root / "diagnosis.json").read_text(encoding="utf8"))
    if report["state_slice"] != STATE_SLICE or report["source_state_slice"] != SOURCE_STATE_SLICE:
        raise ValueError("diagnosis state drift")
    if report["claim_ceiling"] != CLAIM_CEILING or report["model"] != str(MODEL):
        raise ValueError("diagnosis claim/model drift")
    if report["report_sha256"] != base.digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("diagnosis digest mismatch")
    if [case["seed"] for case in report["cases"]] != list(SEEDS):
        raise ValueError("diagnosis case ordering drift")
    if report["network_access"] is not False or report["training"] is not False or report["retention_executed"] is not False:
        raise ValueError("diagnosis execution boundary drift")
    if report["all_cases_valid"] is not True or report["target_acquisition_robust"] is not True:
        raise ValueError("diagnosis validity/target conclusion drift")
    if report["diagnostic_classification"] != "NonTargetAcquisitionInstabilityNotTargetFailure":
        raise ValueError("diagnosis classification drift")
    if not report["non_target_failures"]:
        raise ValueError("diagnosis lost non-target failure")
    if any(item["task_id"] == 0 for item in report["non_target_failures"]):
        raise ValueError("diagnosis incorrectly assigns failure to target")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "diagnostic_classification": report["diagnostic_classification"],
        "target_acquisition_robust": report["target_acquisition_robust"],
        "non_target_failures": report["non_target_failures"],
        "claim_ceiling": CLAIM_CEILING,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

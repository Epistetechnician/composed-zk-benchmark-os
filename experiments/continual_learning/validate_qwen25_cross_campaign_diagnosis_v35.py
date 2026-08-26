#!/usr/bin/env python3
"""Independent validator for the V35 cross-campaign diagnosis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.diagnose_qwen25_cross_campaign_v35 import CLAIM_CEILING, STATE_SLICE


def validate(root: Path) -> dict:
    report = json.loads((root / "diagnosis.json").read_text(encoding="utf8"))
    if report["state_slice"] != STATE_SLICE or report["claim_ceiling"] != CLAIM_CEILING:
        raise ValueError("diagnosis state or claim ceiling drift")
    if report["report_sha256"] != base.digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("diagnosis digest mismatch")
    if report["network_access"] is not False or report["training"] is not False or report["retention_executed"] is not False:
        raise ValueError("diagnosis execution boundary drift")
    sources = report["source_campaigns"]
    if [source["version"] for source in sources] != ["v32", "v34"]:
        raise ValueError("source ordering drift")
    if any(source["all_cases_valid"] is not True for source in sources):
        raise ValueError("source validation drift")
    if report["primary_metric"] != "non_target_nonconstant_acquisition_stability_rate":
        raise ValueError("primary metric drift")
    if report["v32_summary"]["non_target_stable_cases"] != 7 or report["v32_summary"]["non_target_case_count"] != 9:
        raise ValueError("V32 stability baseline drift")
    if report["v34_summary"]["non_target_stable_cases"] != 9 or report["v34_summary"]["non_target_case_count"] != 9:
        raise ValueError("V34 stability result drift")
    if report["v32_summary"]["target_stable_cases"] != 3 or report["v34_summary"]["target_stable_cases"] != 2:
        raise ValueError("target sensitivity result drift")
    if report["diagnostic_classification"] != "NonTargetStabilityImprovedTargetSeedSensitivityRemains":
        raise ValueError("diagnostic classification drift")
    if report["causal_status"] != "DisjointSeedComparisonNotCausalProof":
        raise ValueError("causal-boundary drift")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "diagnostic_classification": report["diagnostic_classification"],
        "v32_summary": report["v32_summary"],
        "v34_summary": report["v34_summary"],
        "causal_status": report["causal_status"],
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

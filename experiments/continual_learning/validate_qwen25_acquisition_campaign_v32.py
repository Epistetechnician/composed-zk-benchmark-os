#!/usr/bin/env python3
"""Independent campaign-level validator for V32 case receipts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.validate_qwen25_acquisition_eligibility_v32 import validate as validate_case


STATE_SLICE = "continual-learning-qwen25-acquisition-eligibility-v32"
PROTOCOL = "v32-qwen25-routed-bank-acquisition-eligibility-v1"
MODEL = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
SEEDS = (20260853, 20260854, 20260855)


def validate(root: Path) -> dict:
    root = root.resolve()
    contract = json.loads((root / "campaign_contract.json").read_text(encoding="utf8"))
    report = json.loads((root / "campaign_report.json").read_text(encoding="utf8"))
    if contract["state_slice"] != STATE_SLICE or contract["protocol"] != PROTOCOL:
        raise ValueError("campaign contract state drift")
    if contract["model"] != MODEL or contract["seeds"] != list(SEEDS) or contract["order"] != [0, 1, 2, 3]:
        raise ValueError("campaign fixed contract drift")
    if contract["contract_sha256"] != base.digest({key: value for key, value in contract.items() if key != "contract_sha256"}):
        raise ValueError("campaign contract digest mismatch")
    if report["state_slice"] != STATE_SLICE or report["protocol"] != PROTOCOL or report["model"] != MODEL:
        raise ValueError("campaign report state drift")
    if report["report_sha256"] != base.digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("campaign report digest mismatch")
    if report["case_count"] != len(SEEDS) or report["expected_case_count"] != len(SEEDS):
        raise ValueError("campaign case cardinality drift")
    if report["training"] is not True or report["retention_executed"] is not False or report["interference_executed"] is not False:
        raise ValueError("campaign execution boundary drift")
    rows = []
    for seed in SEEDS:
        row = next((item for item in report["cases"] if item["seed"] == seed), None)
        if row is None or row["status"] != "validated":
            raise ValueError(f"missing validated case: {seed}")
        case = root / f"seed-{seed}-order-0123"
        validation = validate_case(case, Path(MODEL), seed)
        result = json.loads((case / "result.json").read_text(encoding="utf8"))
        if row["result_sha256"] != result["result_sha256"] or row["eligible"] != validation["eligible"]:
            raise ValueError(f"case receipt mismatch: {seed}")
        rows.append({"seed": seed, "eligible": validation["eligible"], "eligibility_gates": validation["eligibility_gates"]})
    all_eligible = all(row["eligible"] for row in rows)
    if report["all_cases_valid"] is not True or report["all_cases_eligible"] != all_eligible or report["campaign_eligible"] != all_eligible:
        raise ValueError("campaign eligibility aggregation drift")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "case_count": len(rows),
        "all_cases_valid": True,
        "campaign_eligible": all_eligible,
        "cases": rows,
        "claim_ceiling": "LocalDevelopmentModelAcquisitionEligibilityPreflight",
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

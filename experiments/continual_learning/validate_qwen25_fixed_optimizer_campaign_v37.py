#!/usr/bin/env python3
"""Independent campaign validator for V37 fixed-optimizer receipts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.qwen25_fixed_optimizer_acquisition_v37 import (
    FIXED_OPTIMIZER_SEED,
    MODEL_DEFAULT,
    PROTOCOL,
    STATE_SLICE,
    TASK_SEEDS,
)
from experiments.continual_learning.validate_qwen25_fixed_optimizer_acquisition_v37 import validate as validate_case


def validate(root: Path) -> dict:
    root = root.resolve()
    contract = json.loads((root / "campaign_contract.json").read_text(encoding="utf8"))
    report = json.loads((root / "campaign_report.json").read_text(encoding="utf8"))
    if contract["state_slice"] != STATE_SLICE or contract["protocol"] != PROTOCOL:
        raise ValueError("campaign state/protocol drift")
    if contract["model"] != str(MODEL_DEFAULT) or contract["task_seeds"] != list(TASK_SEEDS):
        raise ValueError("campaign model/task seed drift")
    if contract["optimizer_seed_base"] != FIXED_OPTIMIZER_SEED:
        raise ValueError("campaign optimizer seed drift")
    if contract["contract_sha256"] != base.digest({key: value for key, value in contract.items() if key != "contract_sha256"}):
        raise ValueError("campaign contract digest mismatch")
    if report["state_slice"] != STATE_SLICE or report["protocol"] != PROTOCOL or report["optimizer_seed_base"] != FIXED_OPTIMIZER_SEED:
        raise ValueError("campaign report binding drift")
    if report["report_sha256"] != base.digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("campaign report digest mismatch")
    if report["case_count"] != len(TASK_SEEDS) or report["expected_case_count"] != len(TASK_SEEDS):
        raise ValueError("campaign case cardinality drift")
    if report["independence_status"] != "post_diagnosis_repair_validation_not_independent_confirmation":
        raise ValueError("independence boundary drift")
    for key in ("network_access", "retention_executed", "interference_executed", "provider_executed", "production_claim_eligible"):
        if report[key] is not False:
            raise ValueError(f"campaign execution boundary drift: {key}")
    rows = []
    for task_seed in TASK_SEEDS:
        row = next((item for item in report["cases"] if item["task_seed"] == task_seed), None)
        if row is None or row["status"] != "validated":
            raise ValueError(f"missing validated case: {task_seed}")
        case = root / f"task-seed-{task_seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"
        validation = validate_case(case, Path(MODEL_DEFAULT), task_seed)
        result = json.loads((case / "result.json").read_text(encoding="utf8"))
        if row["result_sha256"] != result["result_sha256"] or row["eligible"] != validation["eligible"]:
            raise ValueError(f"case receipt mismatch: {task_seed}")
        rows.append({"task_seed": task_seed, "eligible": validation["eligible"], "eligibility_gates": validation["eligibility_gates"]})
    all_eligible = all(row["eligible"] for row in rows)
    if report["all_cases_valid"] is not True or report["all_cases_eligible"] != all_eligible or report["campaign_eligible"] != all_eligible:
        raise ValueError("campaign aggregation drift")
    return {"valid": True, "state_slice": STATE_SLICE, "protocol": PROTOCOL, "case_count": len(rows), "all_cases_valid": True, "campaign_eligible": all_eligible, "cases": rows, "independence_status": report["independence_status"], "claim_ceiling": report["claim_ceiling"]}


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

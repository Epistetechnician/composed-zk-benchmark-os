#!/usr/bin/env python3
"""Independent campaign validator for V41 order-replication receipts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.qwen25_fresh_fixed_optimizer_acquisition_v40 import MODEL_DEFAULT, TASK_SEEDS
from experiments.continual_learning.qwen25_fresh_fixed_optimizer_order_retention_v41 import (
    CLAIM_CEILING,
    FIXED_OPTIMIZER_SEED,
    ORDERS,
    PROTOCOL,
    SOURCE_STATE_SLICE,
    STATE_SLICE,
    case_name,
    order_code,
)
from experiments.continual_learning.validate_qwen25_fresh_fixed_optimizer_order_retention_v41 import validate as validate_case


def validate(root: Path) -> dict:
    root = root.resolve()
    contract = json.loads((root / "campaign_contract.json").read_text(encoding="utf8"))
    report = json.loads((root / "campaign_report.json").read_text(encoding="utf8"))
    if contract["state_slice"] != STATE_SLICE or contract["protocol"] != PROTOCOL:
        raise ValueError("campaign state/protocol drift")
    if contract["model"] != str(MODEL_DEFAULT) or contract["task_seeds"] != list(TASK_SEEDS):
        raise ValueError("campaign model/task seed drift")
    if contract["orders"] != [list(order) for order in ORDERS] or contract["optimizer_seed_base"] != FIXED_OPTIMIZER_SEED:
        raise ValueError("campaign order/optimizer drift")
    if contract["source_state_slice"] != SOURCE_STATE_SLICE:
        raise ValueError("campaign source state drift")
    if contract["contract_sha256"] != base.digest({key: value for key, value in contract.items() if key != "contract_sha256"}):
        raise ValueError("campaign contract digest mismatch")
    if report["state_slice"] != STATE_SLICE or report["protocol"] != PROTOCOL or report["claim_ceiling"] != CLAIM_CEILING:
        raise ValueError("campaign report binding drift")
    if report["report_sha256"] != base.digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("campaign report digest mismatch")
    expected_count = len(TASK_SEEDS) * len(ORDERS)
    if report["case_count"] != expected_count or report["expected_case_count"] != expected_count:
        raise ValueError("campaign case cardinality drift")
    for key in ("network_access", "provider_executed", "production_claim_eligible"):
        if report[key] is not False:
            raise ValueError(f"campaign boundary drift: {key}")
    rows = []
    for task_seed in TASK_SEEDS:
        for order in ORDERS:
            code = order_code(order)
            row = next((item for item in report["cases"] if item["task_seed"] == task_seed and item["order"] == code), None)
            if row is None or row["status"] != "validated":
                raise ValueError(f"missing validated case: {task_seed}/{code}")
            case = root / case_name(task_seed, order)
            source_case = Path(contract["source_artifact_root"]) / f"task-seed-{task_seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"
            validation = validate_case(case, source_case, Path(MODEL_DEFAULT), task_seed, order)
            result = json.loads((case / "result.json").read_text(encoding="utf8"))
            if row["result_sha256"] != result["result_sha256"] or row["eligible"] != validation["eligible"]:
                raise ValueError(f"case receipt mismatch: {task_seed}/{code}")
            rows.append({"task_seed": task_seed, "order": code, "eligible": validation["eligible"], "gates": validation["gates"]})
    all_eligible = all(row["eligible"] for row in rows)
    if report["all_cases_valid"] is not True or report["all_cases_eligible"] != all_eligible or report["campaign_eligible"] != all_eligible:
        raise ValueError("campaign aggregation drift")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "case_count": len(rows),
        "all_cases_valid": True,
        "campaign_eligible": all_eligible,
        "cases": rows,
        "claim_ceiling": report["claim_ceiling"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

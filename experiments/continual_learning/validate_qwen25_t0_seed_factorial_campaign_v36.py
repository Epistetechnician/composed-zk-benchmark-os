#!/usr/bin/env python3
"""Independent validator for the V36 factorial campaign."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.qwen25_t0_seed_factorial_v36 import (
    ARMS,
    FAILING_TASK_SEED,
    FIXED_OPTIMIZER_SEED,
    MODEL_DEFAULT,
    PROTOCOL,
    SEEDS,
    STATE_SLICE,
)
from experiments.continual_learning.validate_qwen25_t0_seed_factorial_v36 import validate as validate_case


def validate(root: Path) -> dict:
    root = root.resolve()
    contract = json.loads((root / "campaign_contract.json").read_text(encoding="utf8"))
    report = json.loads((root / "campaign_report.json").read_text(encoding="utf8"))
    if contract["state_slice"] != STATE_SLICE or contract["protocol"] != PROTOCOL:
        raise ValueError("campaign state/protocol drift")
    if contract["model"] != str(MODEL_DEFAULT) or contract["arms"] != list(ARMS):
        raise ValueError("campaign model/arm drift")
    if contract["optimizer_seed_arm"] != {"fixed_task_seed": FAILING_TASK_SEED, "optimizer_seeds": list(SEEDS)}:
        raise ValueError("optimizer arm contract drift")
    if contract["task_seed_arm"] != {"fixed_optimizer_seed": FIXED_OPTIMIZER_SEED, "task_seeds": list(SEEDS)}:
        raise ValueError("task arm contract drift")
    if contract["contract_sha256"] != base.digest({key: value for key, value in contract.items() if key != "contract_sha256"}):
        raise ValueError("campaign contract digest mismatch")
    if report["state_slice"] != STATE_SLICE or report["protocol"] != PROTOCOL:
        raise ValueError("report state/protocol drift")
    if report["report_sha256"] != base.digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("report digest mismatch")
    if report["case_count"] != 6 or report["expected_case_count"] != 6 or report["all_cases_valid"] is not True:
        raise ValueError("campaign cardinality/validity drift")
    for key in ("network_access", "retention_executed", "interference_executed", "provider_executed", "production_claim_eligible"):
        if report[key] is not False:
            raise ValueError(f"campaign boundary drift: {key}")
    validated = []
    for record in report["records"]:
        if record["status"] != "validated":
            raise ValueError("unvalidated case in campaign")
        case = root / f"{record['arm']}-task-{record['task_seed']}-opt-{record['optimizer_seed']}"
        case_validation = validate_case(case, record["arm"], record["task_seed"], record["optimizer_seed"], MODEL_DEFAULT)
        if record["result_sha256"] != case_validation["result_sha256"] or record["eligible"] != case_validation["eligible"]:
            raise ValueError("case receipt mismatch")
        validated.append(record)
    for arm in ARMS:
        rows = [record for record in validated if record["arm"] == arm]
        outcomes = [record["eligible"] for record in rows]
        if len(rows) != 3 or report["arms"][arm]["eligible_outcomes"] != outcomes:
            raise ValueError(f"arm aggregation drift: {arm}")
        if report["arms"][arm]["unique_eligible_outcomes"] != sorted(set(outcomes)):
            raise ValueError(f"arm outcome-set drift: {arm}")
        if report["arms"][arm]["outcome_variation"] != len(set(outcomes)):
            raise ValueError(f"arm variation drift: {arm}")
    return {"valid": True, "state_slice": STATE_SLICE, "diagnostic_classification": report["diagnostic_classification"], "arms": report["arms"], "causal_status": report["causal_status"], "claim_ceiling": report["claim_ceiling"]}


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

#!/usr/bin/env python3
"""Independent campaign validator for V38 retention artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.qwen25_fixed_optimizer_retention_v38 import (
    CLAIM_CEILING,
    MODEL_DEFAULT,
    PROTOCOL,
    SOURCE_ARTIFACT_ROOT,
    SOURCE_STATE_SLICE,
    STATE_SLICE,
    TASK_SEEDS,
    case_name,
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf8"))


def validate(root: Path, model: Path) -> dict:
    contract = load(root / "campaign_contract.json")
    report = load(root / "campaign_report.json")
    if contract["state_slice"] != STATE_SLICE or report["state_slice"] != STATE_SLICE:
        raise ValueError("V38 campaign state slice drift")
    if contract["protocol"] != PROTOCOL or report["protocol"] != PROTOCOL:
        raise ValueError("V38 campaign protocol drift")
    if contract["model"] != str(model.resolve()) or report["model"] != str(model.resolve()):
        raise ValueError("V38 campaign model drift")
    if contract["source_state_slice"] != SOURCE_STATE_SLICE:
        raise ValueError("V38 source state slice drift")
    if contract["source_artifact_root"] != str(SOURCE_ARTIFACT_ROOT.resolve()):
        raise ValueError("V38 source custody drift")
    if report["task_seeds"] != list(TASK_SEEDS) or report["expected_case_count"] != len(TASK_SEEDS):
        raise ValueError("V38 campaign seed drift")
    if report["claim_ceiling"] != CLAIM_CEILING:
        raise ValueError("V38 campaign claim ceiling drift")
    expected_contract = base.digest({key: value for key, value in contract.items() if key != "contract_sha256"})
    if contract["contract_sha256"] != expected_contract:
        raise ValueError("V38 campaign contract digest drift")
    records = []
    for task_seed in TASK_SEEDS:
        name = case_name(task_seed)
        case_root = root / name
        source_case = SOURCE_ARTIFACT_ROOT / name
        command = [
            sys.executable,
            str(Path(__file__).with_name("validate_qwen25_fixed_optimizer_retention_v38.py")),
            str(case_root),
            "--source-case",
            str(source_case),
            "--model",
            str(model),
            "--expected-task-seed",
            str(task_seed),
        ]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            raise ValueError(f"V38 case validation failed for {task_seed}: {completed.stdout} {completed.stderr}")
        validation = json.loads(completed.stdout.strip().splitlines()[-1])
        result = load(case_root / "result.json")
        records.append({
            "task_seed": task_seed,
            "status": "validated",
            "valid": validation["valid"],
            "eligible": validation["eligible"],
            "gates": validation["gates"],
            "result_sha256": result["result_sha256"],
        })
    if report["cases"] != records:
        raise ValueError("V38 campaign case report drift")
    expected_all = all(record["valid"] for record in records)
    expected_eligible = expected_all and all(record["eligible"] for record in records)
    if report["all_cases_valid"] != expected_all or report["all_cases_eligible"] != expected_eligible:
        raise ValueError("V38 campaign eligibility summary drift")
    if report["campaign_eligible"] != expected_eligible:
        raise ValueError("V38 campaign eligibility drift")
    for key in ("network_access", "provider_executed", "production_claim_eligible"):
        if report[key] is not False:
            raise ValueError(f"V38 campaign boundary drift: {key}")
    if report["retention_executed"] is not True or report["interference_executed"] is not True:
        raise ValueError("V38 campaign execution marker missing")
    expected_report = base.digest({key: value for key, value in report.items() if key != "report_sha256"})
    if report["report_sha256"] != expected_report:
        raise ValueError("V38 campaign report digest drift")
    return {
        "valid": True,
        "campaign_eligible": expected_eligible,
        "case_count": len(records),
        "claim_ceiling": CLAIM_CEILING,
        "protocol": PROTOCOL,
        "state_slice": STATE_SLICE,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign_root", type=Path)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    args = parser.parse_args()
    print(json.dumps(validate(args.campaign_root.resolve(), args.model), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

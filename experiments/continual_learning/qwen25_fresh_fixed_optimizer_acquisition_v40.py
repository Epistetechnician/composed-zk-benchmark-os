#!/usr/bin/env python3
"""V40 Qwen2.5 fresh-task fixed-optimizer acquisition campaign.

State slice: continual-learning-qwen25-fresh-fixed-optimizer-acquisition-v40.

V40 executes the frozen fresh-task policy from the V37 optimizer-seed
boundary. It changes only the task-seed set from the completed V37 repair
validation; the model, raw-text seam, optimizer seed, task order, update
budget, and eligibility gates remain unchanged. This is acquisition
eligibility evidence only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import qwen25_fixed_optimizer_acquisition_v37 as v37


STATE_SLICE = "continual-learning-qwen25-fresh-fixed-optimizer-acquisition-v40"
PROTOCOL = "v40-qwen25-fresh-fixed-optimizer-acquisition-v1"
MODEL_DEFAULT = v37.MODEL_DEFAULT
TASK_SEEDS = (20260859, 20260860, 20260861)
FIXED_OPTIMIZER_SEED = v37.FIXED_OPTIMIZER_SEED
ORDER = v37.ORDER
ITERS = v37.ITERS
UPDATE_BUDGET = v37.UPDATE_BUDGET
CLAIM_CEILING = "LocalDevelopmentFreshModelAcquisitionEligibilityPreflight"
PARENT_STATE_SLICE = v37.STATE_SLICE


def write_json(path: Path, value) -> None:
    if path.exists():
        raise RuntimeError(f"refusing overwrite of immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def case_name(task_seed: int) -> str:
    return f"task-seed-{task_seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"


def run_case(output: Path, model: Path, task_seed: int) -> dict:
    output = output.resolve()
    model = model.resolve()
    if task_seed not in TASK_SEEDS:
        raise ValueError("V40 task seed is not in the frozen fresh-task set")
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V40 fixed Qwen2.5 model drift")

    originals = {
        "STATE_SLICE": v37.STATE_SLICE,
        "PROTOCOL": v37.PROTOCOL,
        "MODEL_DEFAULT": v37.MODEL_DEFAULT,
        "TASK_SEEDS": v37.TASK_SEEDS,
        "CLAIM_CEILING": v37.CLAIM_CEILING,
    }
    v37.STATE_SLICE = STATE_SLICE
    v37.PROTOCOL = PROTOCOL
    v37.MODEL_DEFAULT = MODEL_DEFAULT
    v37.TASK_SEEDS = TASK_SEEDS
    v37.CLAIM_CEILING = CLAIM_CEILING
    try:
        result = v37.run_case(output, model, task_seed)
    finally:
        for key, value in originals.items():
            setattr(v37, key, value)

    config = result["config"]
    config.update(
        {
            "state_slice": STATE_SLICE,
            "protocol": PROTOCOL,
            "model": str(model),
            "task_seed": task_seed,
            "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
            "optimizer_seed_policy": "fixed_v36_first_declared_seed_plus_task_id_v1",
            "parent_state_slice": PARENT_STATE_SLICE,
            "independence_status": "fresh_task_seed_campaign_under_frozen_repair_policy",
        }
    )
    config["contract_sha256"] = base.digest(
        {key: value for key, value in config.items() if key != "contract_sha256"}
    )
    result.update(
        {
            "state_slice": STATE_SLICE,
            "protocol": PROTOCOL,
            "claim_ceiling": CLAIM_CEILING,
            "classification": "Qwen25FreshFixedOptimizerAcquisitionEligibilityPreflight",
            "config": config,
            "task_seed": task_seed,
            "independence_status": "fresh_task_seed_campaign_under_frozen_repair_policy",
        }
    )
    audit = json.loads((output / "audit" / "task_adapter_bank.json").read_text(encoding="utf8"))
    result["audit_sha256"] = base.digest(audit)
    result["manifest_sha256"] = base.digest({"config": config, "tasks": result["tasks"], "audit": audit})
    result["result_sha256"] = base.digest(
        {key: value for key, value in result.items() if key != "result_sha256"}
    )
    (output / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf8")
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return result


def run_campaign(artifact_root: Path, model: Path) -> dict:
    artifact_root = artifact_root.resolve()
    model = model.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable V40 campaign: {artifact_root}")
    if not artifact_root.is_absolute() or Path(__file__).resolve().parents[2] in artifact_root.parents:
        raise ValueError("V40 artifacts must remain outside the repository")
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V40 model binding is unavailable or drifted")

    artifact_root.mkdir(parents=True)
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "task_seeds": list(TASK_SEEDS),
        "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
        "optimizer_seed_policy": "fixed_v36_first_declared_seed_plus_task_id_v1",
        "order": list(ORDER),
        "iters": ITERS,
        "update_budget": UPDATE_BUDGET,
        "dataset_format": "raw_text_prompt_plus_completion_v1",
        "completion_masking": False,
        "primary_metric": "all_task_train_above_no_update_and_target_floors",
        "parent_state_slice": PARENT_STATE_SLICE,
        "independence_status": "fresh_task_seed_campaign_under_frozen_repair_policy",
        "training": True,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "network_access": False,
    }
    contract["contract_sha256"] = base.digest(contract)
    write_json(artifact_root / "campaign_contract.json", contract)
    records = []
    environment = os.environ.copy()
    environment.update(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    )
    for task_seed in TASK_SEEDS:
        name = case_name(task_seed)
        case_root = artifact_root / name
        runner = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--case-output",
                str(case_root),
                "--model",
                str(model),
                "--task-seed",
                str(task_seed),
            ],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        (artifact_root / f"{name}.runner.log").write_text(
            runner.stdout + "\n" + runner.stderr, encoding="utf8"
        )
        if runner.returncode != 0:
            records.append({"task_seed": task_seed, "status": "runner_failed", "valid": False})
            break
        validator = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("validate_qwen25_fresh_fixed_optimizer_acquisition_v40.py")),
                str(case_root),
                "--model",
                str(model),
                "--expected-task-seed",
                str(task_seed),
            ],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        (artifact_root / f"{name}.validator.log").write_text(
            validator.stdout + "\n" + validator.stderr, encoding="utf8"
        )
        if validator.returncode != 0:
            records.append({"task_seed": task_seed, "status": "validator_failed", "valid": False})
            break
        validation = json.loads(validator.stdout.strip().splitlines()[-1])
        result = json.loads((case_root / "result.json").read_text(encoding="utf8"))
        records.append(
            {
                "task_seed": task_seed,
                "order": "0123",
                "status": "validated",
                "valid": validation["valid"],
                "eligible": validation["eligible"],
                "eligibility_gates": validation["eligibility_gates"],
                "result_sha256": result["result_sha256"],
            }
        )
    report = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "task_seeds": list(TASK_SEEDS),
        "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
        "independence_status": "fresh_task_seed_campaign_under_frozen_repair_policy",
        "case_count": len(records),
        "expected_case_count": len(TASK_SEEDS),
        "cases": records,
        "all_cases_valid": len(records) == len(TASK_SEEDS) and all(row["valid"] for row in records),
        "all_cases_eligible": len(records) == len(TASK_SEEDS) and all(row.get("eligible") is True for row in records),
        "campaign_eligible": len(records) == len(TASK_SEEDS) and all(row.get("eligible") is True for row in records),
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
    }
    report["report_sha256"] = base.digest(report)
    write_json(artifact_root / "campaign_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--case-output", type=Path)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--task-seed", type=int)
    args = parser.parse_args()
    if args.case_output is not None:
        if args.task_seed is None:
            raise ValueError("V40 case mode requires task-seed")
        result = run_case(args.case_output, args.model, args.task_seed)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["eligible"] else 1
    if args.artifact_root is None:
        raise ValueError("V40 campaign mode requires artifact-root")
    result = run_campaign(args.artifact_root, args.model)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["campaign_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""V37 Qwen2.5 full acquisition campaign with a fixed optimizer seed.

State slice: continual-learning-qwen25-fixed-optimizer-acquisition-v37.

V37 reuses the validated V34 raw-text mechanism and changes only the seed
binding: task construction uses the three V34 task seeds while adapter
training uses one fixed optimizer-seed base plus the explicit task id offset.
The fixed base is the first declared V36 optimizer seed, 20260856. This is a
post-diagnosis repair validation, not independent confirmation. Retention,
interference, provider, and production work remain outside this slice.
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
from experiments.continual_learning import qwen25_raw_text_acquisition_v34 as v34


STATE_SLICE = "continual-learning-qwen25-fixed-optimizer-acquisition-v37"
PROTOCOL = "v37-qwen25-fixed-optimizer-acquisition-preflight-v1"
MODEL_DEFAULT = v34.MODEL_DEFAULT
TASK_SEEDS = v34.SEEDS
FIXED_OPTIMIZER_SEED = 20260856
ORDER = v34.ORDER
ITERS = v34.ITERS
UPDATE_BUDGET = v34.UPDATE_BUDGET
CLAIM_CEILING = "LocalDevelopmentModelAcquisitionEligibilityPreflight"


def write_json(path: Path, value) -> None:
    if path.exists():
        raise RuntimeError(f"refusing overwrite of immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def _train_fixed_optimizer_bank(root: Path, model: Path, tasks, ignored_task_seed: int):
    data_root = root / "data" / "task_adapter_bank"
    adapter_root = root / "adapters" / "task_adapter_bank"
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    audit_root.mkdir(parents=True, exist_ok=True)
    task_by_id = {task.task_id: task for task in tasks}
    adapters = {}
    audit = []
    for step, task_id in enumerate(ORDER):
        task = task_by_id[task_id]
        rows = [v34.raw_text_training_example(fact) for fact in task.train_facts]
        rows = (rows * ((UPDATE_BUDGET + len(rows) - 1) // len(rows)))[:UPDATE_BUDGET]
        dataset = data_root / f"task-{task_id}"
        base.write_dataset(dataset, rows)
        adapter_path = adapter_root / f"task-{task_id}"
        training_seed = FIXED_OPTIMIZER_SEED + task_id
        command = v34.raw_text_training_command(model, dataset, adapter_path, training_seed, ITERS, None)
        environment = os.environ.copy()
        environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=environment, text=True, capture_output=True, check=False)
        (adapter_root / f"task-{task_id}.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf8"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"fixed-optimizer adapter training failed for task {task_id}: {completed.returncode}")
        adapters[task_id] = adapter_path
        audit.append(
            {
                "step": step,
                "task_id": task_id,
                "route_key": task.task_token,
                "adapter_relative_path": str(adapter_path.relative_to(root)),
                "resumed_from": None,
                "train_fact_ids": [fact.fact_id for fact in task.train_facts],
                "dataset_row_count": len(rows),
                "target_task_id": 0,
                "dataset_format": "raw_text_prompt_plus_completion_v1",
                "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
                "training_seed": training_seed,
            }
        )
    base.write_json(audit_root / "task_adapter_bank.json", audit)
    return adapters, audit


def run_case(output: Path, model: Path, task_seed: int) -> dict:
    output = output.resolve()
    model = model.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable case: {output}")
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V37 fixed Qwen2.5 model drift")
    if task_seed not in TASK_SEEDS:
        raise ValueError("V37 task seed is not in the preregistered set")

    patched = {
        "STATE_SLICE": v34.STATE_SLICE,
        "PROTOCOL": v34.PROTOCOL,
        "CLAIM_CEILING": v34.CLAIM_CEILING,
        "MODEL_DEFAULT": v34.MODEL_DEFAULT,
        "SEEDS": v34.SEEDS,
        "_train_adapter_bank": v34._train_adapter_bank,
    }
    v34.STATE_SLICE = STATE_SLICE
    v34.PROTOCOL = PROTOCOL
    v34.CLAIM_CEILING = CLAIM_CEILING
    v34.MODEL_DEFAULT = model
    v34.SEEDS = TASK_SEEDS
    v34._train_adapter_bank = _train_fixed_optimizer_bank
    try:
        result = v34.run_case(output, model, task_seed)
    finally:
        for key, value in patched.items():
            setattr(v34, key, value)

    config = result["config"]
    config.pop("seed", None)
    config.update(
        {
            "state_slice": STATE_SLICE,
            "protocol": PROTOCOL,
            "model": str(model),
            "task_seed": task_seed,
            "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
            "optimizer_seed_policy": "fixed_v36_first_declared_seed_plus_task_id_v1",
            "parent_state_slice": "continual-learning-qwen25-raw-text-acquisition-v34",
            "independence_status": "post_diagnosis_repair_validation_not_independent_confirmation",
        }
    )
    config["contract_sha256"] = base.digest({key: value for key, value in config.items() if key != "contract_sha256"})
    result.update(
        {
            "state_slice": STATE_SLICE,
            "protocol": PROTOCOL,
            "claim_ceiling": CLAIM_CEILING,
            "classification": "Qwen25FixedOptimizerAcquisitionPreflightNoRetentionClaim",
            "config": config,
            "task_seed": task_seed,
            "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
            "independence_status": "post_diagnosis_repair_validation_not_independent_confirmation",
        }
    )
    audit = json.loads((output / "audit" / "task_adapter_bank.json").read_text(encoding="utf8"))
    result["audit_sha256"] = base.digest(audit)
    result["manifest_sha256"] = base.digest({"config": config, "tasks": result["tasks"], "audit": audit})
    result["result_sha256"] = base.digest({key: value for key, value in result.items() if key != "result_sha256"})
    (output / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf8")
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return result


def run_campaign(artifact_root: Path, model: Path) -> dict:
    artifact_root = artifact_root.resolve()
    model = model.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable campaign: {artifact_root}")
    if not artifact_root.is_absolute() or Path(__file__).resolve().parents[2] in artifact_root.parents:
        raise ValueError("V37 artifacts must remain outside the repository")
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V37 model binding is unavailable or drifted")

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
        "parent_state_slice": "continual-learning-qwen25-raw-text-acquisition-v34",
        "independence_status": "post_diagnosis_repair_validation_not_independent_confirmation",
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
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    for task_seed in TASK_SEEDS:
        case_name = f"task-seed-{task_seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"
        case_root = artifact_root / case_name
        runner = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--case-output", str(case_root), "--model", str(model), "--task-seed", str(task_seed)],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        (artifact_root / f"{case_name}.runner.log").write_text(runner.stdout + "\n" + runner.stderr, encoding="utf8")
        if runner.returncode != 0:
            records.append({"task_seed": task_seed, "status": "runner_failed", "valid": False})
            break
        validator = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("validate_qwen25_fixed_optimizer_acquisition_v37.py")),
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
        (artifact_root / f"{case_name}.validator.log").write_text(validator.stdout + "\n" + validator.stderr, encoding="utf8")
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
        "independence_status": "post_diagnosis_repair_validation_not_independent_confirmation",
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
            raise ValueError("case mode requires task-seed")
        print(json.dumps(run_case(args.case_output, args.model, args.task_seed), indent=2, sort_keys=True))
        return 0
    if args.artifact_root is None:
        raise ValueError("campaign mode requires artifact-root")
    report = run_campaign(args.artifact_root, args.model)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["campaign_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

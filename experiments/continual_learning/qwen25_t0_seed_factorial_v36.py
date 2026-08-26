#!/usr/bin/env python3
"""V36 target-only Qwen2.5 task-seed versus optimizer-seed diagnosis.

State slice: continual-learning-qwen25-t0-seed-factorial-diagnosis-v36.

V34 coupled the task-construction seed and the trainer seed. V36 separates
them in two bounded arms while preserving the raw-text dataset, route-bound
prompt, model, target task, optimizer, iteration budget, and readout. It does
not execute the adapter bank, retention, interference, provider, or
production paths.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import routed_adapter_bank_acquisition_v29 as v29
from experiments.continual_learning.routed_adapter_bank_candidate_v26 import route_bound_prompt_for


STATE_SLICE = "continual-learning-qwen25-t0-seed-factorial-diagnosis-v36"
PROTOCOL = "v36-qwen25-t0-task-vs-optimizer-seed-factorial-v1"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")
SEEDS = (20260856, 20260857, 20260858)
FAILING_TASK_SEED = 20260857
FIXED_OPTIMIZER_SEED = 20260857
ITERS = 160
UPDATE_BUDGET = 32
TARGET_TASK_ID = 0
TARGET_FLOOR = 0.75
CLAIM_CEILING = "LocalDevelopmentQwen25T0SeedSensitivityDiagnosis"
ARMS = ("optimizer_seed_arm", "task_seed_arm")


def write_json(path: Path, value) -> None:
    if path.exists():
        raise RuntimeError(f"refusing overwrite of immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def raw_text_training_example(fact) -> dict[str, str]:
    return {"text": route_bound_prompt_for(fact) + f" {fact.label}"}


def raw_text_training_command(model: Path, dataset: Path, adapter: Path, seed: int) -> list[str]:
    return [
        arg
        for arg in base.training_command(model, dataset, adapter, seed, ITERS, None)
        if arg != "--mask-prompt"
    ]


def _tasks_json(tasks) -> list[dict]:
    return [
        {
            "task_id": task.task_id,
            "task_token": task.task_token,
            "mapping": list(task.mapping),
            "train_facts": [asdict(fact) for fact in task.train_facts],
            "test_facts": [asdict(fact) for fact in task.test_facts],
        }
        for task in tasks
    ]


def _isolated_metric(model: Path, tasks_path: Path, adapter: Path | None, split: str) -> dict:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--evaluate",
        "--model",
        str(model),
        "--tasks-json",
        str(tasks_path),
        "--task-id",
        str(TARGET_TASK_ID),
        "--split",
        split,
    ]
    if adapter is not None:
        command.extend(["--adapter", str(adapter)])
    environment = os.environ.copy()
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    completed = subprocess.run(command, env=environment, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"isolated T0 readout failed for {split}: {completed.returncode}\n{completed.stderr}")
    return json.loads(completed.stdout)


def _metric_with_constant(metric: dict) -> dict:
    metric["constant_output"] = len({row["observed"] for row in metric["rows"]}) == 1
    return metric


def run_case(output: Path, arm: str, task_seed: int, optimizer_seed: int, model: Path) -> dict:
    output = output.resolve()
    model = model.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable case: {output}")
    if arm not in ARMS:
        raise ValueError("V36 arm drift")
    if task_seed not in SEEDS or optimizer_seed not in SEEDS:
        raise ValueError("V36 seed outside fixed set")
    if arm == "optimizer_seed_arm" and task_seed != FAILING_TASK_SEED:
        raise ValueError("optimizer arm must hold the V34 failing task seed")
    if arm == "task_seed_arm" and optimizer_seed != FIXED_OPTIMIZER_SEED:
        raise ValueError("task arm must hold the fixed optimizer seed")
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V36 model binding is unavailable or drifted")

    output.mkdir(parents=True)
    tasks = base.make_tasks(task_seed, 4)
    tasks_json = _tasks_json(tasks)
    config = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "arm": arm,
        "task_seed": task_seed,
        "optimizer_seed": optimizer_seed,
        "task_count": 4,
        "target_task_id": TARGET_TASK_ID,
        "order": [0, 1, 2, 3],
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "dataset_format": "raw_text_prompt_plus_completion_v1",
        "completion_masking": False,
        "update_budget": UPDATE_BUDGET,
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "iters": ITERS,
        "assessment": "exact_t0_train_and_heldout_acquisition_diagnosis_v1",
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "prompt_contract": {
            "training_prefix_equals_assessment_prefix": True,
            "dataset_chat_template_wrapping": False,
            "derived_residue_visible": True,
            "raw_pair_present": False,
            "route_binding_at_answer_boundary": True,
        },
    }
    config["contract_sha256"] = base.digest(config)
    base.write_json(output / "tasks.json", tasks_json)
    base.write_json(output / "config.json", config)

    target = next(task for task in tasks if task.task_id == TARGET_TASK_ID)
    rows = [raw_text_training_example(fact) for fact in target.train_facts]
    rows = (rows * ((UPDATE_BUDGET + len(rows) - 1) // len(rows)))[:UPDATE_BUDGET]
    dataset = output / "data" / "target-task-0"
    base.write_dataset(dataset, rows)
    adapter = output / "adapters" / "target-task-0"
    command = raw_text_training_command(model, dataset, adapter, optimizer_seed)
    environment = os.environ.copy()
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    completed = subprocess.run(command, env=environment, text=True, capture_output=True, check=False)
    adapter.parent.mkdir(parents=True, exist_ok=True)
    (adapter.parent / "training.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
    if completed.returncode != 0:
        raise RuntimeError(f"V36 T0 training failed: {completed.returncode}")

    no_update_train = _metric_with_constant(_isolated_metric(model, output / "tasks.json", None, "train"))
    adapter_train = _metric_with_constant(_isolated_metric(model, output / "tasks.json", adapter, "train"))
    adapter_test = _metric_with_constant(_isolated_metric(model, output / "tasks.json", adapter, "test"))
    gates = {
        "train_above_no_update": adapter_train["accuracy"] > no_update_train["accuracy"],
        "heldout_floor": adapter_test["accuracy"] >= TARGET_FLOOR,
        "not_constant_output": adapter_train["constant_output"] is False,
    }
    audit = {
        "arm": arm,
        "task_seed": task_seed,
        "optimizer_seed": optimizer_seed,
        "task_id": TARGET_TASK_ID,
        "train_fact_ids": [fact.fact_id for fact in target.train_facts],
        "dataset_row_count": len(rows),
        "dataset_format": "raw_text_prompt_plus_completion_v1",
        "adapter_relative_path": str(adapter.relative_to(output)),
        "resumed_from": None,
    }
    base.write_json(output / "audit.json", audit)
    result = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "classification": "T0SeedSensitivityDiagnosisCase",
        "config": config,
        "tasks": tasks_json,
        "no_update_train": no_update_train,
        "adapter_train": adapter_train,
        "adapter_test": adapter_test,
        "diagnostic_gates": gates,
        "eligible": all(gates.values()),
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "audit_sha256": base.digest(audit),
        "manifest_sha256": base.digest({"config": config, "tasks": tasks_json, "audit": audit}),
    }
    result["result_sha256"] = base.digest(result)
    base.write_json(output / "result.json", result)
    return result


def _arm_cells(arm: str) -> tuple[tuple[int, int], ...]:
    if arm == "optimizer_seed_arm":
        return tuple((FAILING_TASK_SEED, seed) for seed in SEEDS)
    if arm == "task_seed_arm":
        return tuple((seed, FIXED_OPTIMIZER_SEED) for seed in SEEDS)
    raise ValueError("V36 arm drift")


def run_campaign(artifact_root: Path, model: Path) -> dict:
    artifact_root = artifact_root.resolve()
    model = model.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable campaign: {artifact_root}")
    if not artifact_root.is_absolute() or Path(__file__).resolve().parents[2] in artifact_root.parents:
        raise ValueError("V36 artifacts must remain outside the repository")
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V36 model binding is unavailable or drifted")
    artifact_root.mkdir(parents=True)
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "arms": list(ARMS),
        "optimizer_seed_arm": {"fixed_task_seed": FAILING_TASK_SEED, "optimizer_seeds": list(SEEDS)},
        "task_seed_arm": {"fixed_optimizer_seed": FIXED_OPTIMIZER_SEED, "task_seeds": list(SEEDS)},
        "target_task_id": TARGET_TASK_ID,
        "iters": ITERS,
        "update_budget": UPDATE_BUDGET,
        "dataset_format": "raw_text_prompt_plus_completion_v1",
        "primary_metric": "within_arm_t0_eligibility_outcome_variation",
        "training": True,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "network_access": False,
    }
    contract["contract_sha256"] = base.digest(contract)
    write_json(artifact_root / "campaign_contract.json", contract)
    environment = os.environ.copy()
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    records = []
    for arm in ARMS:
        for task_seed, optimizer_seed in _arm_cells(arm):
            case_name = f"{arm}-task-{task_seed}-opt-{optimizer_seed}"
            case_root = artifact_root / case_name
            runner = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--case-output",
                    str(case_root),
                    "--arm",
                    arm,
                    "--task-seed",
                    str(task_seed),
                    "--optimizer-seed",
                    str(optimizer_seed),
                    "--model",
                    str(model),
                ],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            (artifact_root / f"{case_name}.runner.log").write_text(runner.stdout + "\n" + runner.stderr, encoding="utf8")
            if runner.returncode != 0:
                records.append({"arm": arm, "task_seed": task_seed, "optimizer_seed": optimizer_seed, "status": "runner_failed", "valid": False})
                continue
            validator = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("validate_qwen25_t0_seed_factorial_v36.py")),
                    str(case_root),
                    "--arm",
                    arm,
                    "--task-seed",
                    str(task_seed),
                    "--optimizer-seed",
                    str(optimizer_seed),
                    "--model",
                    str(model),
                ],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            (artifact_root / f"{case_name}.validator.log").write_text(validator.stdout + "\n" + validator.stderr, encoding="utf8")
            if validator.returncode != 0:
                records.append({"arm": arm, "task_seed": task_seed, "optimizer_seed": optimizer_seed, "status": "validator_failed", "valid": False})
                continue
            validation = json.loads(validator.stdout.strip().splitlines()[-1])
            result = json.loads((case_root / "result.json").read_text(encoding="utf8"))
            records.append(
                {
                    "arm": arm,
                    "task_seed": task_seed,
                    "optimizer_seed": optimizer_seed,
                    "status": "validated",
                    "valid": validation["valid"],
                    "eligible": validation["eligible"],
                    "diagnostic_gates": validation["diagnostic_gates"],
                    "result_sha256": result["result_sha256"],
                }
            )
    report = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "records": records,
        "expected_case_count": 6,
        "case_count": len(records),
        "all_cases_valid": len(records) == 6 and all(record["valid"] for record in records),
        "arms": {},
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
    }
    for arm in ARMS:
        arm_records = [record for record in records if record["arm"] == arm]
        outcomes = [record.get("eligible") for record in arm_records]
        report["arms"][arm] = {
            "case_count": len(arm_records),
            "all_cases_valid": len(arm_records) == 3 and all(record["valid"] for record in arm_records),
            "eligible_outcomes": outcomes,
            "unique_eligible_outcomes": sorted(set(outcomes)),
            "outcome_variation": len(set(outcomes)),
        }
    optimizer_varies = report["arms"]["optimizer_seed_arm"]["outcome_variation"] > 1
    task_varies = report["arms"]["task_seed_arm"]["outcome_variation"] > 1
    if optimizer_varies and task_varies:
        classification = "BothTaskAndOptimizerSeedSensitivityObserved"
    elif optimizer_varies:
        classification = "OptimizerSeedSensitivityObserved"
    elif task_varies:
        classification = "TaskSplitSeedSensitivityObserved"
    else:
        classification = "NoT0SeedSensitivityObserved"
    report["diagnostic_classification"] = classification
    report["causal_status"] = "ControlledOneFactorArmsWithinLocalDiagnosis"
    report["next_hypothesis"] = "Do not promote retention from a target-only diagnosis; require campaign-wide acquisition eligibility after the controlling factor is fixed."
    report["report_sha256"] = base.digest(report)
    write_json(artifact_root / "campaign_report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--case-output", type=Path)
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--task-seed", type=int)
    parser.add_argument("--optimizer-seed", type=int)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--tasks-json", type=Path)
    parser.add_argument("--task-id", type=int)
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--split", choices=("train", "test"))
    args = parser.parse_args()
    if args.evaluate:
        if args.tasks_json is None or args.task_id != TARGET_TASK_ID or args.split is None:
            raise ValueError("evaluation requires tasks-json, target task-id, and split")
        tasks = json.loads(args.tasks_json.read_text(encoding="utf8"))
        task = next(item for item in tasks if item["task_id"] == TARGET_TASK_ID)
        facts = task["train_facts"] if args.split == "train" else task["test_facts"]
        model = base.ChoiceModel(args.model.resolve(), args.adapter.resolve() if args.adapter else None)
        from experiments.continual_learning.compositional_model_benchmark import Fact

        print(json.dumps(v29._metric(model, tuple(Fact(**fact) for fact in facts)), sort_keys=True))
        return 0
    if args.case_output is not None:
        if args.arm is None or args.task_seed is None or args.optimizer_seed is None:
            raise ValueError("case mode requires arm and both seeds")
        print(json.dumps(run_case(args.case_output, args.arm, args.task_seed, args.optimizer_seed, args.model), indent=2, sort_keys=True))
        return 0
    if args.artifact_root is None:
        raise ValueError("campaign mode requires artifact-root")
    print(json.dumps(run_campaign(args.artifact_root, args.model), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

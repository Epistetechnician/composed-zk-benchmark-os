#!/usr/bin/env python3
"""V34 Qwen2.5 raw-text acquisition-only campaign.

State slice: continual-learning-qwen25-raw-text-acquisition-v34.

V34 changes exactly one training boundary from V32: each update row is a
single raw-text field containing the unchanged route-bound prompt followed by
the completion, and the trainer does not receive ``--mask-prompt``.  The
assessment readout and task construction remain unchanged.  Retention,
interference, provider, and production work are outside this slice.
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


STATE_SLICE = "continual-learning-qwen25-raw-text-acquisition-v34"
PROTOCOL = "v34-qwen25-raw-text-acquisition-eligibility-v1"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")
ORDER = (0, 1, 2, 3)
SEEDS = (20260856, 20260857, 20260858)
ITERS = 160
UPDATE_BUDGET = 32
TARGET_TASK_ID = 0
TARGET_FLOOR = 0.75
CLAIM_CEILING = "LocalDevelopmentModelAcquisitionEligibilityPreflight"


def write_json(path: Path, value) -> None:
    if path.exists():
        raise RuntimeError(f"refusing overwrite of immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def raw_text_training_example(fact) -> dict[str, str]:
    return {"text": route_bound_prompt_for(fact) + f" {fact.label}"}


def raw_text_training_command(
    model: Path, dataset: Path, adapter_path: Path, seed: int, iters: int, resume: Path | None
) -> list[str]:
    return [
        arg
        for arg in base.training_command(model, dataset, adapter_path, seed, iters, resume)
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


def _train_adapter_bank(root: Path, model: Path, tasks, seed: int) -> tuple[dict[int, Path], list[dict]]:
    data_root = root / "data" / "task_adapter_bank"
    adapter_root = root / "adapters" / "task_adapter_bank"
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    audit_root.mkdir(parents=True, exist_ok=True)
    task_by_id = {task.task_id: task for task in tasks}
    adapters: dict[int, Path] = {}
    audit: list[dict] = []
    for step, task_id in enumerate(ORDER):
        task = task_by_id[task_id]
        rows = [raw_text_training_example(fact) for fact in task.train_facts]
        rows = (rows * ((UPDATE_BUDGET + len(rows) - 1) // len(rows)))[:UPDATE_BUDGET]
        dataset = data_root / f"task-{task_id}"
        base.write_dataset(dataset, rows)
        adapter_path = adapter_root / f"task-{task_id}"
        command = raw_text_training_command(model, dataset, adapter_path, seed + task_id, ITERS, None)
        env = os.environ.copy()
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (adapter_root / f"task-{task_id}.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf8"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"raw-text adapter training failed for task {task_id}: {completed.returncode}")
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
                "target_task_id": TARGET_TASK_ID,
                "dataset_format": "raw_text_prompt_plus_completion_v1",
            }
        )
    base.write_json(audit_root / "task_adapter_bank.json", audit)
    return adapters, audit


def _isolated_metric(model: Path, tasks_path: Path, task_id: int, adapter: Path | None, split: str) -> dict:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--evaluate",
        "--model",
        str(model),
        "--tasks-json",
        str(tasks_path),
        "--task-id",
        str(task_id),
        "--split",
        split,
    ]
    if adapter is not None:
        command.extend(["--adapter", str(adapter)])
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"isolated readout failed for task {task_id}/{split}: {completed.returncode}\n{completed.stderr}")
    return json.loads(completed.stdout)


def eligibility_gates(task_results: list[dict]) -> dict[str, bool]:
    target = next(item for item in task_results if item["task_id"] == TARGET_TASK_ID)
    return {
        "all_task_train_above_no_update": all(
            item["adapter_train"]["accuracy"] > item["no_update_train"]["accuracy"] for item in task_results
        ),
        "target_train_floor": target["adapter_train"]["accuracy"] >= TARGET_FLOOR,
        "target_heldout_floor": target["adapter_test"]["accuracy"] >= TARGET_FLOOR,
        "target_not_constant_output": target["adapter_train"]["constant_output"] is False,
    }


def run_case(output: Path, model: Path, seed: int) -> dict:
    output = output.resolve()
    model = model.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable case: {output}")
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V34 fixed Qwen2.5 model drift")
    if seed not in SEEDS:
        raise ValueError("V34 seed is not in the preregistered disjoint set")
    if not model.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model}")

    output.mkdir(parents=True)
    tasks = base.make_tasks(seed, 4)
    tasks_json = _tasks_json(tasks)
    config = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "seed": seed,
        "order": list(ORDER),
        "task_count": 4,
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "memory_mechanism": "append_only_task_routed_adapter_bank_v1",
        "route_policy": "task_token_exact_v1",
        "dataset_format": "raw_text_prompt_plus_completion_v1",
        "update_budget": UPDATE_BUDGET,
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "mask_prompt": False,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "iters": ITERS,
        "assessment": "exact_train_and_heldout_acquisition_only_v1",
        "target_task_id": TARGET_TASK_ID,
        "target_floor": TARGET_FLOOR,
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
            "completion_masking": False,
        },
    }
    config["contract_sha256"] = base.digest(config)
    base.write_json(output / "tasks.json", tasks_json)
    base.write_json(output / "config.json", config)
    adapters, audit = _train_adapter_bank(output, model, tasks, seed)

    task_results = []
    task_by_id = {task.task_id: task for task in tasks}
    for task_id in range(4):
        task = task_by_id[task_id]
        no_update_train = _isolated_metric(model, output / "tasks.json", task_id, None, "train")
        adapter_train = _isolated_metric(model, output / "tasks.json", task_id, adapters[task_id], "train")
        adapter_test = _isolated_metric(model, output / "tasks.json", task_id, adapters[task_id], "test")
        for metric in (no_update_train, adapter_train, adapter_test):
            metric["constant_output"] = len({row["observed"] for row in metric["rows"]}) == 1
        task_results.append(
            {
                "task_id": task_id,
                "route_key": task.task_token,
                "no_update_train": no_update_train,
                "adapter_train": adapter_train,
                "adapter_test": adapter_test,
            }
        )
    gates = eligibility_gates(task_results)
    result = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "classification": "Qwen25RawTextAcquisitionEligibilityPreflightNoRetentionClaim",
        "config": config,
        "tasks": tasks_json,
        "task_results": task_results,
        "eligibility_gates": gates,
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


def run_campaign(artifact_root: Path, model: Path) -> dict:
    artifact_root = artifact_root.resolve()
    model = model.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable campaign: {artifact_root}")
    if not artifact_root.is_absolute() or Path(__file__).resolve().parents[2] in artifact_root.parents:
        raise ValueError("V34 artifacts must remain outside the repository")
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V34 model binding is unavailable or drifted")

    artifact_root.mkdir(parents=True)
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "seeds": list(SEEDS),
        "order": list(ORDER),
        "iters": ITERS,
        "update_budget": UPDATE_BUDGET,
        "dataset_format": "raw_text_prompt_plus_completion_v1",
        "completion_masking": False,
        "primary_metric": "all_task_train_above_no_update_and_target_floors",
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
    for seed in SEEDS:
        case_name = f"seed-{seed}-order-0123"
        case_root = artifact_root / case_name
        runner_log = artifact_root / f"{case_name}.runner.log"
        validator_log = artifact_root / f"{case_name}.validator.log"
        runner = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--case-output", str(case_root), "--model", str(model), "--seed", str(seed)],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        runner_log.write_text(runner.stdout + "\n" + runner.stderr, encoding="utf8")
        if runner.returncode != 0:
            records.append({"seed": seed, "order": "0123", "status": "runner_failed", "valid": False})
            break
        validator = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("validate_qwen25_raw_text_acquisition_v34.py")),
                str(case_root),
                "--model",
                str(model),
                "--expected-seed",
                str(seed),
            ],
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        validator_log.write_text(validator.stdout + "\n" + validator.stderr, encoding="utf8")
        if validator.returncode != 0:
            records.append({"seed": seed, "order": "0123", "status": "validator_failed", "valid": False})
            break
        validation = json.loads(validator.stdout.strip().splitlines()[-1])
        result = json.loads((case_root / "result.json").read_text(encoding="utf8"))
        records.append(
            {
                "seed": seed,
                "order": "0123",
                "status": "validated",
                "valid": validation["valid"],
                "eligible": validation["eligible"],
                "eligibility_gates": validation["eligibility_gates"],
                "result_sha256": result["result_sha256"],
            }
        )
        if not validation["valid"]:
            break

    report = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "case_count": len(records),
        "expected_case_count": len(SEEDS),
        "cases": records,
        "all_cases_valid": len(records) == len(SEEDS) and all(row["valid"] for row in records),
        "all_cases_eligible": len(records) == len(SEEDS) and all(row.get("eligible") is True for row in records),
        "campaign_eligible": len(records) == len(SEEDS) and all(row.get("eligible") is True for row in records),
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
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--case-output", type=Path)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--tasks-json", type=Path)
    parser.add_argument("--task-id", type=int)
    parser.add_argument("--adapter", type=Path)
    parser.add_argument("--split", choices=("train", "test"))
    args = parser.parse_args()
    if args.evaluate:
        if args.tasks_json is None or args.task_id is None or args.split is None:
            raise ValueError("evaluation requires tasks-json, task-id, and split")
        tasks = json.loads(args.tasks_json.read_text(encoding="utf8"))
        task = next(item for item in tasks if item["task_id"] == args.task_id)
        facts = task["train_facts"] if args.split == "train" else task["test_facts"]
        model = base.ChoiceModel(args.model.resolve(), args.adapter.resolve() if args.adapter else None)
        from experiments.continual_learning.compositional_model_benchmark import Fact

        print(json.dumps(v29._metric(model, tuple(Fact(**fact) for fact in facts)), sort_keys=True))
        return 0
    if args.case_output is not None:
        if args.seed is None:
            raise ValueError("case mode requires --seed")
        result = run_case(args.case_output, args.model, args.seed)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.artifact_root is None:
        raise ValueError("campaign mode requires artifact-root")
    report = run_campaign(args.artifact_root, args.model)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["campaign_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

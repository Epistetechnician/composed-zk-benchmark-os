#!/usr/bin/env python3
"""V29 offline acquisition-only preflight for the cached Qwen3.6 model.

State slice: continual-learning-model-acquisition-eligibility-v29.

This phase trains one fresh task adapter per frozen task and evaluates exact
train/held-out acquisition. It does not run retention, interference,
reacquisition, provider, or production work.
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
from experiments.continual_learning.routed_adapter_bank_candidate_v26 import (
    route_bound_accuracy,
    route_bound_training_example,
)


STATE_SLICE = "continual-learning-model-acquisition-eligibility-v29"
CLAIM_CEILING = "LocalDevelopmentModelAcquisitionEligibilityPreflight"
PROTOCOL = "v29-qwen36-acquisition-preflight-v1"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit")
SEED = 20260861
ORDER = (0, 1, 2, 3)
ITERS = 160
UPDATE_BUDGET = 32
TARGET_TASK_ID = 0
TARGET_FLOOR = 0.75


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


def _metric(model, facts) -> dict:
    result = route_bound_accuracy(model, facts)
    result["constant_output"] = len({row["observed"] for row in result["rows"]}) == 1
    return result


def _train_adapter_bank(root: Path, model: Path, tasks, order: tuple[int, ...], seed: int, iters: int, update_budget: int):
    data_root = root / "data" / "task_adapter_bank"
    adapter_root = root / "adapters" / "task_adapter_bank"
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    audit_root.mkdir(parents=True, exist_ok=True)
    task_by_id = {task.task_id: task for task in tasks}
    adapters = {}
    audit = []
    for step, task_id in enumerate(order):
        task = task_by_id[task_id]
        rows = [route_bound_training_example(fact) for fact in task.train_facts]
        rows = (rows * ((update_budget + len(rows) - 1) // len(rows)))[:update_budget]
        dataset = data_root / f"task-{task_id}"
        base.write_dataset(dataset, rows)
        adapter_path = adapter_root / f"task-{task_id}"
        command = base.training_command(model, dataset, adapter_path, seed + task_id, iters, None)
        env = os.environ.copy()
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (adapter_root / f"task-{task_id}.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf8"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"adapter-bank training failed for task {task_id}: {completed.returncode}")
        adapters[task_id] = adapter_path
        audit.append(
            {
                "step": step,
                "task_id": task_id,
                "route_key": task.task_token,
                "adapter_relative_path": str(adapter_path.relative_to(root)),
                "resumed_from": None,
                "train_fact_ids": [fact.fact_id for fact in task.train_facts],
                "replay_counts_by_task": {},
                "dataset_row_count": len(rows),
                "target_task_id": TARGET_TASK_ID,
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
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"isolated readout failed for task {task_id}/{split}: {completed.returncode}\n{completed.stderr}")
    return json.loads(completed.stdout)


def eligibility_gates(task_results: list[dict]) -> dict[str, bool]:
    target = next(item for item in task_results if item["task_id"] == TARGET_TASK_ID)
    return {
        "all_task_train_above_no_update": all(
            item["adapter_train"]["accuracy"] > item["no_update_train"]["accuracy"]
            for item in task_results
        ),
        "target_train_floor": target["adapter_train"]["accuracy"] >= TARGET_FLOOR,
        "target_heldout_floor": target["adapter_test"]["accuracy"] >= TARGET_FLOOR,
        "target_not_constant_output": target["adapter_train"]["constant_output"] is False,
    }


def run(args: argparse.Namespace) -> dict:
    root = args.output.resolve()
    model = args.model.resolve()
    order = tuple(int(value) for value in args.order.split(","))
    if root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {root}")
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V29 fixed model drift")
    if args.seed != SEED or args.task_count != 4 or args.iters != ITERS or args.update_budget != UPDATE_BUDGET:
        raise ValueError("V29 fixed acquisition contract drift")
    if order != ORDER:
        raise ValueError("V29 fixed task order drift")
    if not model.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model}")

    root.mkdir(parents=True)
    tasks = base.make_tasks(args.seed, args.task_count)
    tasks_json = _tasks_json(tasks)
    config = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "seed": args.seed,
        "order": list(order),
        "task_count": args.task_count,
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "memory_mechanism": "append_only_task_routed_adapter_bank_v1",
        "route_policy": "task_token_exact_v1",
        "update_budget": UPDATE_BUDGET,
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "mask_prompt": True,
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
            "training_prompt_equals_assessment_prompt": True,
            "derived_residue_visible": True,
            "raw_pair_present": False,
            "route_binding_at_answer_boundary": True,
        },
    }
    config["contract_sha256"] = base.digest(config)
    base.write_json(root / "tasks.json", tasks_json)
    base.write_json(root / "config.json", config)

    adapters, audit = _train_adapter_bank(root, model, tasks, order, args.seed, args.iters, args.update_budget)

    task_by_id = {task.task_id: task for task in tasks}
    task_results = []
    for task_id in range(args.task_count):
        task = task_by_id[task_id]
        no_update_train = _isolated_metric(model, root / "tasks.json", task_id, None, "train")
        adapter_train = _isolated_metric(model, root / "tasks.json", task_id, adapters[task_id], "train")
        adapter_test = _isolated_metric(model, root / "tasks.json", task_id, adapters[task_id], "test")
        adapter_train["constant_output"] = len({row["observed"] for row in adapter_train["rows"]}) == 1
        adapter_test["constant_output"] = len({row["observed"] for row in adapter_test["rows"]}) == 1
        no_update_train["constant_output"] = len({row["observed"] for row in no_update_train["rows"]}) == 1
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
        "classification": "Qwen36AcquisitionEligibilityPreflightNoRetentionClaim",
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
    base.write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--order", default=",".join(str(value) for value in ORDER))
    parser.add_argument("--task-count", type=int, default=4)
    parser.add_argument("--iters", type=int, default=ITERS)
    parser.add_argument("--update-budget", type=int, default=UPDATE_BUDGET)
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

        metric = _metric(model, tuple(Fact(**fact) for fact in facts))
        print(json.dumps(metric, sort_keys=True))
        return 0
    if args.output is None:
        raise ValueError("acquisition requires output")
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

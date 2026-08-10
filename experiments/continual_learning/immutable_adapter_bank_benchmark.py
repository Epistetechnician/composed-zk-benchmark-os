#!/usr/bin/env python3
"""V9 immutable task-keyed adapter-bank continual-learning pilot."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_calibration_benchmark import make_tasks  # noqa: E402
from experiments.continual_learning.compositional_model_benchmark import (  # noqa: E402
    ChoiceModel,
    accuracy,
    digest,
    evaluate_strategy,
    prompt_for,
    training_command,
    training_example,
    train_sequence,
    write_dataset,
)


STATE_SLICE = "continual-learning-model-adapter-v9-immutable-task-adapter-bank"
STRATEGIES = ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora", "task_adapter_bank")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def train_adapter_bank(
    root: Path,
    model: Path,
    tasks,
    order: tuple[int, ...],
    seed: int,
    iters: int,
    update_budget: int,
) -> tuple[dict[int, Path], list[dict]]:
    data_root = root / "data" / "task_adapter_bank"
    adapter_root = root / "adapters" / "task_adapter_bank"
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    audit_root.mkdir(exist_ok=True)
    task_by_id = {task.task_id: task for task in tasks}
    adapters: dict[int, Path] = {}
    audit: list[dict] = []
    for step, task_id in enumerate(order):
        task = task_by_id[task_id]
        rows = [training_example(fact) for fact in task.train_facts]
        rows = (rows * ((update_budget + len(rows) - 1) // len(rows)))[:update_budget]
        dataset = data_root / f"task-{task_id}"
        write_dataset(dataset, rows)
        adapter_path = adapter_root / f"task-{task_id}"
        command = training_command(model, dataset, adapter_path, seed + task_id, iters, None)
        env = os.environ.copy()
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (adapter_root / f"task-{task_id}.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
        if completed.returncode != 0:
            raise RuntimeError(f"adapter-bank training failed for task {task_id}: {completed.returncode}")
        adapter_model = ChoiceModel(model, adapter_path)
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
                "heldout_task_accuracy": accuracy(adapter_model, task.test_facts),
            }
        )
    write_json(audit_root / "task_adapter_bank.json", audit)
    return adapters, audit


def evaluate_adapter_bank(model: Path, tasks, adapters: dict[int, Path]) -> dict:
    target = {task.task_id: task for task in tasks}[0].test_facts
    routed = ChoiceModel(model, adapters[0])
    metric = accuracy(routed, target)
    return {
        "acquisition": metric,
        "retention_after_interference": metric,
        "recovery_after_reacquisition": metric,
        "route_policy": "task_token_exact_v1",
        "route_key": "T0",
    }


def run(args: argparse.Namespace) -> dict:
    root = args.output.resolve()
    if root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {root}")
    root.mkdir(parents=True)
    model = args.model.resolve()
    order = tuple(int(value) for value in args.order.split(","))
    tasks = make_tasks(args.seed, args.task_count)
    if sorted(order) != list(range(args.task_count)) or order[0] != 0:
        raise ValueError("order must be a permutation with target task 0 first")
    tasks_json = [
        {
            "task_id": task.task_id,
            "task_token": task.task_token,
            "mapping": list(task.mapping),
            "train_facts": [asdict(fact) for fact in task.train_facts],
            "test_facts": [asdict(fact) for fact in task.test_facts],
        }
        for task in tasks
    ]
    write_json(root / "tasks.json", tasks_json)
    config = {
        "state_slice": STATE_SLICE,
        "model": str(model),
        "seed": args.seed,
        "order": order,
        "task_count": args.task_count,
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "memory_mechanism": "immutable_task_keyed_adapter_bank_v1",
        "route_policy": "task_token_exact_v1",
        "replay_capacity": 24,
        "update_budget": 32,
        "current_examples_per_update": 8,
        "replay_examples_per_update": 24,
        "replay_policy": "balanced_full_memory_v1",
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "mask_prompt": True,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "audit_schema": "immutable_adapter_bank_audit_v1",
        "checkpoint_target_task_id": 0,
        "checkpoint_assessment_context_mode": "none",
        "prompt_contract": {"training_prompt_equals_assessment_prompt": True, "answer_suffix": "\nAnswer:"},
        "iters": args.iters,
        "source_context_removed_for": ["acquisition", "retention_after_interference", "recovery_after_reacquisition"],
        "assessment_effects_generated_before_prediction_lock": False,
    }
    config["contract_sha256"] = digest(config)
    write_json(root / "config.json", config)
    shared_adapters = {
        strategy: train_sequence(root, model, tasks, order, strategy, args.seed, args.iters, 24, 32)
        for strategy in ("naive_sequential_lora", "replay_lora")
    }
    bank_adapters, bank_audit = train_adapter_bank(root, model, tasks, order, args.seed, args.iters, 32)
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in shared_adapters
    }
    audits["task_adapter_bank"] = bank_audit
    results = {
        strategy: evaluate_strategy(model, tasks, shared_adapters.get(strategy), order, root, strategy)
        for strategy in ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora")
    }
    results["task_adapter_bank"] = evaluate_adapter_bank(model, tasks, bank_adapters)
    result = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentImmutableTaskAdapterBankPilot",
        "classification": "ImmutableTaskAdapterBankPilotNoBreakthroughClaim",
        "config": config,
        "results": results,
        "audit_sha256": {strategy: digest(audit) for strategy, audit in audits.items()},
        "manifest_sha256": digest({"config": config, "tasks": tasks_json, "audits": audits}),
        "breakthrough_claim_eligible": False,
    }
    write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"))
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--order", default="0,1,2,3")
    parser.add_argument("--task-count", type=int, default=4)
    parser.add_argument("--iters", type=int, default=40)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

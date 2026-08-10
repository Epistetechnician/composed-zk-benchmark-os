#!/usr/bin/env python3
"""V8 one-variable solvability calibration for the held-out task."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_model_benchmark import (  # noqa: E402
    LABELS,
    Task,
    Fact,
    evaluate_strategy,
    train_sequence,
)
from experiments.continual_learning.compositional_model_benchmark import digest  # noqa: E402


STATE_SLICE = "continual-learning-model-adapter-v8-heldout-compositional-solvability-calibration"


def make_tasks(seed: int, task_count: int = 4) -> tuple[Task, ...]:
    tasks: list[Task] = []
    for task_id in range(task_count):
        task_token = f"T{task_id}"
        mapping = tuple(LABELS[(residue + task_id) % 4] for residue in range(4))
        train_facts: list[Fact] = []
        test_facts: list[Fact] = []
        for residue in range(4):
            pairs = [
                (left, right)
                for left in range(4)
                for right in range(4)
                if (left + right) % 4 == residue
            ]
            ranked = sorted(
                pairs,
                key=lambda pair: digest([seed, task_id, pair[0], pair[1]]),
            )
            for pair_index, (left, right) in enumerate(ranked):
                split = "train" if pair_index < 2 else "test"
                fact = Fact(
                    task_id=task_id,
                    task_token=task_token,
                    fact_id=f"{task_token}-P{left}{right}-{digest([seed, task_id, left, right])[:6]}",
                    left=left,
                    right=right,
                    residue=residue,
                    label=mapping[residue],
                    split=split,
                )
                (train_facts if split == "train" else test_facts).append(fact)
        tasks.append(Task(task_id, task_token, mapping, tuple(train_facts), tuple(test_facts)))
    return tuple(tasks)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


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
        "replay_capacity": args.replay_capacity,
        "update_budget": args.update_budget,
        "current_examples_per_update": 8,
        "replay_examples_per_update": args.update_budget - 8,
        "replay_policy": "balanced_full_memory_v1",
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "mask_prompt": True,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "audit_schema": "replay_exposure_audit_v1",
        "checkpoint_target_task_id": 0,
        "checkpoint_assessment_context_mode": "none",
        "prompt_contract": {"training_prompt_equals_assessment_prompt": True, "answer_suffix": "\nAnswer:"},
        "iters": args.iters,
        "source_context_removed_for": ["acquisition", "retention_after_interference", "recovery_after_reacquisition"],
        "assessment_effects_generated_before_prediction_lock": False,
    }
    config["contract_sha256"] = digest(config)
    write_json(root / "config.json", config)
    adapters = {
        strategy: train_sequence(
            root, model, tasks, order, strategy, args.seed, args.iters, args.replay_capacity, args.update_budget
        )
        for strategy in ("naive_sequential_lora", "replay_lora")
    }
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in adapters
    }
    results = {
        strategy: evaluate_strategy(model, tasks, adapters.get(strategy), order, root, strategy)
        for strategy in ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora")
    }
    result = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentHeldoutCompositionalSolvabilityCalibration",
        "classification": "HeldoutCompositionalSolvabilityCalibrationNoBreakthroughClaim",
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
    parser.add_argument("--replay-capacity", type=int, default=24)
    parser.add_argument("--update-budget", type=int, default=32)
    parser.add_argument("--iters", type=int, default=40)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

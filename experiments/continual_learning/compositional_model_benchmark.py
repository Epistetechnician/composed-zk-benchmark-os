#!/usr/bin/env python3
"""Offline continual-learning pilot with held-out compositional assessment."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from experiments.continual_learning.model_benchmark import (
    ChoiceModel,
    digest,
    training_command,
)


STATE_SLICE = "continual-learning-model-adapter-v7-heldout-compositional-task"
LABELS = ("A", "B", "C", "D")
SYMBOLS = ("zero", "one", "two", "three")
ANSWER_SUFFIX = "\nAnswer:"
STRATEGIES = ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora")


@dataclass(frozen=True)
class Fact:
    task_id: int
    task_token: str
    fact_id: str
    left: int
    right: int
    residue: int
    label: str
    split: str


@dataclass(frozen=True)
class Task:
    task_id: int
    task_token: str
    mapping: tuple[str, ...]
    train_facts: tuple[Fact, ...]
    test_facts: tuple[Fact, ...]


def make_tasks(seed: int, task_count: int = 4) -> tuple[Task, ...]:
    if task_count < 4:
        raise ValueError("task_count must be >= 4")
    tasks = []
    for task_id in range(task_count):
        task_token = f"T{task_id}"
        mapping = tuple(
            sorted(
                LABELS,
                key=lambda label: hashlib.sha256(
                    f"{seed}:task:{task_id}:mapping:{label}".encode()
                ).hexdigest(),
            )
        )
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
                key=lambda pair: hashlib.sha256(
                    f"{seed}:task:{task_id}:pair:{pair[0]}:{pair[1]}".encode()
                ).hexdigest(),
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
        tasks.append(
            Task(
                task_id=task_id,
                task_token=task_token,
                mapping=mapping,
                train_facts=tuple(train_facts),
                test_facts=tuple(test_facts),
            )
        )
    return tuple(tasks)


def prompt_for(fact: Fact, context: Iterable[Fact] = ()) -> str:
    context = tuple(context)
    reference = ""
    if context:
        reference = "Reference examples:\n" + "\n".join(
            f"- {item.task_token}: {SYMBOLS[item.left]} + {SYMBOLS[item.right]} -> option {item.label}."
            for item in context
        ) + "\n\n"
    return (
        "Answer with exactly one letter: A, B, C, or D.\n"
        f"Task token: {fact.task_token}.\n"
        f"{reference}"
        f"Compose {SYMBOLS[fact.left]} + {SYMBOLS[fact.right]}.\n"
        "Apply the task's modular-four rule and return only the option letter."
        f"{ANSWER_SUFFIX}"
    )


def training_example(fact: Fact) -> dict[str, str]:
    return {"prompt": prompt_for(fact), "completion": f" {fact.label}"}


def choose_balanced_full_replay(
    previous: Iterable[Fact], capacity: int, limit: int | None = None
) -> list[Fact]:
    facts = sorted(previous, key=lambda fact: (fact.task_id, fact.fact_id))
    selected = facts[: max(0, capacity)]
    return selected if limit is None else selected[:limit]


def replay_counts_by_task(facts: Iterable[Fact]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for fact in facts:
        key = str(fact.task_id)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def write_dataset(path: Path, rows: list[dict[str, str]]) -> None:
    path.mkdir(parents=True, exist_ok=False)
    for name in ("train.jsonl", "valid.jsonl", "test.jsonl"):
        with (path / name).open("w", encoding="utf8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")


def accuracy(model: ChoiceModel, facts: Iterable[Fact], context: Iterable[Fact] = ()) -> dict[str, Any]:
    facts = tuple(facts)
    context = tuple(context)
    rows = []
    correct = 0
    for fact in facts:
        outcome = model.answer(prompt_for(fact, context))
        hit = outcome["prediction"] == fact.label
        correct += int(hit)
        rows.append({"fact_id": fact.fact_id, "expected": fact.label, "observed": outcome["prediction"], "correct": hit})
    return {"correct": correct, "n": len(facts), "accuracy": correct / len(facts) if facts else None, "rows": rows}


def oracle_accuracy(facts: Iterable[Fact]) -> dict[str, Any]:
    facts = tuple(facts)
    return {
        "correct": len(facts),
        "n": len(facts),
        "accuracy": 1.0 if facts else None,
        "rows": [
            {"fact_id": fact.fact_id, "expected": fact.label, "observed": fact.label, "correct": True}
            for fact in facts
        ],
    }


def train_sequence(
    root: Path,
    model: Path,
    tasks: tuple[Task, ...],
    order: tuple[int, ...],
    strategy: str,
    seed: int,
    iters: int,
    replay_capacity: int,
    update_budget: int,
) -> list[Path]:
    data_root = root / "data" / strategy
    adapter_root = root / "adapters" / strategy
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    audit_root.mkdir(exist_ok=True)
    task_by_id = {task.task_id: task for task in tasks}
    observed: list[Fact] = []
    previous_adapter: Path | None = None
    adapter_paths: list[Path] = []
    updates: list[dict[str, Any]] = []
    for step, task_id in enumerate(order):
        current = list(task_by_id[task_id].train_facts)
        if strategy == "naive_sequential_lora":
            selected = current
        elif strategy == "replay_lora":
            selected = current + choose_balanced_full_replay(
                observed, replay_capacity, limit=update_budget - len(current)
            )
        else:
            raise ValueError(f"unsupported training strategy: {strategy}")
        replay_facts = [fact for fact in selected if fact not in current]
        rows = [training_example(fact) for fact in selected]
        rows = (rows * ((update_budget + len(rows) - 1) // len(rows)))[:update_budget]
        dataset = data_root / f"step-{step}"
        write_dataset(dataset, rows)
        adapter_path = adapter_root / f"step-{step}"
        command = training_command(
            model,
            dataset,
            adapter_path,
            seed + step,
            iters,
            previous_adapter / "adapters.safetensors" if previous_adapter else None,
        )
        env = os.environ.copy()
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (adapter_path.parent / f"step-{step}.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
        if completed.returncode != 0:
            raise RuntimeError(f"training failed for {strategy}/step-{step}: {completed.returncode}")
        checkpoint = ChoiceModel(model, adapter_path)
        checkpoint_result = accuracy(checkpoint, task_by_id[0].test_facts)
        updates.append(
            {
                "step": step,
                "task_id": task_id,
                "current_fact_ids": [fact.fact_id for fact in current],
                "replay_fact_ids": [fact.fact_id for fact in replay_facts],
                "selected_fact_ids": [fact.fact_id for fact in selected],
                "replay_counts_by_task": replay_counts_by_task(replay_facts),
                "dataset_row_count": len(rows),
                "target_task_id": 0,
                "target_task_accuracy_after_update": checkpoint_result,
            }
        )
        previous_adapter = adapter_path
        adapter_paths.append(adapter_path)
        observed.extend(current)
    write_json(audit_root / f"{strategy}.json", updates)
    return adapter_paths


def evaluate_strategy(
    model: Path,
    tasks: tuple[Task, ...],
    adapters: list[Path] | None,
    order: tuple[int, ...],
    root: Path,
    strategy: str,
) -> dict[str, Any]:
    target = {task.task_id: task for task in tasks}[0].test_facts
    base = ChoiceModel(model)
    if strategy == "no_update":
        result = accuracy(base, target)
        return {
            "acquisition": result,
            "retention_after_interference": result,
            "recovery_after_reacquisition": result,
        }
    if strategy == "context_only":
        acquisition = accuracy(base, target, {task.task_id: task for task in tasks}[0].train_facts)
        retention = accuracy(base, target)
        return {
            "acquisition": acquisition,
            "retention_after_interference": retention,
            "recovery_after_reacquisition": retention,
        }
    if strategy == "retrieval":
        result = oracle_accuracy(target)
        return {
            "acquisition": result,
            "retention_after_interference": result,
            "recovery_after_reacquisition": result,
        }
    assert adapters
    acquired = accuracy(ChoiceModel(model, adapters[0]), target)
    retained_model = ChoiceModel(model, adapters[-1])
    retained = accuracy(retained_model, target)
    recovery_data = root / "data" / strategy / "recovery"
    recovery_adapter = root / "adapters" / strategy / "recovery"
    train_target = {task.task_id: task for task in tasks}[0].train_facts
    write_dataset(recovery_data, [training_example(fact) for fact in train_target] * 4)
    command = training_command(
        model,
        recovery_data,
        recovery_adapter,
        int(digest({"strategy": strategy, "order": order})[:8], 16),
        20,
        adapters[-1] / "adapters.safetensors",
    )
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    (recovery_adapter.parent / "recovery.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
    if completed.returncode != 0:
        raise RuntimeError(f"recovery training failed for {strategy}: {completed.returncode}")
    recovered = accuracy(ChoiceModel(model, recovery_adapter), target)
    return {
        "acquisition": acquired,
        "retention_after_interference": retained,
        "recovery_after_reacquisition": recovered,
        "retention_paraphrase": accuracy(retained_model, target),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = args.output.resolve()
    if root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {root}")
    root.mkdir(parents=True)
    model = args.model.resolve()
    if not model.is_dir():
        raise RuntimeError(f"model path does not exist: {model}")
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
        "task_rule": "mod4_sum_then_task_permutation_v1",
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
        "prompt_contract": {"training_prompt_equals_assessment_prompt": True, "answer_suffix": ANSWER_SUFFIX},
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
        for strategy in STRATEGIES
    }
    result = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentHeldoutCompositionalContinualLearningPilot",
        "classification": "HeldoutCompositionalContinualLearningPilotNoBreakthroughClaim",
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

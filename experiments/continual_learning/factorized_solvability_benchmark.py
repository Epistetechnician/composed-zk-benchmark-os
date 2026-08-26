#!/usr/bin/env python3
"""V10 factorized solvability-control continual-learning preflight."""

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
    ANSWER_SUFFIX,
    LABELS,
    SYMBOLS,
    ChoiceModel,
    Task,
    choose_balanced_full_replay,
    digest,
    oracle_accuracy,
    replay_counts_by_task,
    training_command,
    write_dataset,
)


STATE_SLICE = "continual-learning-protocol-v10-factorized-solvability-control"
STRATEGIES = (
    "no_update",
    "context_only",
    "retrieval",
    "naive_sequential_lora",
    "replay_lora",
    "task_adapter_bank",
)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def factorized_prompt_for(fact, context=()) -> str:
    context = tuple(context)
    reference = ""
    if context:
        reference = "Reference examples:\n" + "\n".join(
            f"- {item.task_token}: residue {item.residue} -> option {item.label}."
            for item in context
        ) + "\n\n"
    return (
        "Answer with exactly one letter: A, B, C, or D.\n"
        f"Task token: {fact.task_token}.\n"
        f"Derived residue: {fact.residue}.\n"
        f"{reference}"
        "Use the task's residue-to-option codebook and return only the option letter.\n"
        f"Compose {SYMBOLS[fact.left]} + {SYMBOLS[fact.right]}; the derived residue is supplied."
        f"{ANSWER_SUFFIX}"
    )


def factorized_training_example(fact) -> dict[str, str]:
    return {"prompt": factorized_prompt_for(fact), "completion": f" {fact.label}"}


def factorized_accuracy(model: ChoiceModel, facts, context=()) -> dict:
    facts = tuple(facts)
    context = tuple(context)
    rows = []
    correct = 0
    for fact in facts:
        outcome = model.answer(factorized_prompt_for(fact, context))
        hit = outcome["prediction"] == fact.label
        correct += int(hit)
        rows.append(
            {
                "fact_id": fact.fact_id,
                "expected": fact.label,
                "observed": outcome["prediction"],
                "correct": hit,
            }
        )
    return {"correct": correct, "n": len(facts), "accuracy": correct / len(facts) if facts else None, "rows": rows}


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
    observed = []
    previous_adapter: Path | None = None
    adapter_paths = []
    updates = []
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
        rows = [factorized_training_example(fact) for fact in selected]
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
        (adapter_path.parent / f"step-{step}.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf8"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"training failed for {strategy}/step-{step}: {completed.returncode}")
        checkpoint = ChoiceModel(model, adapter_path)
        target_accuracy = factorized_accuracy(checkpoint, task_by_id[0].test_facts)
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
                "target_task_accuracy_after_update": target_accuracy,
            }
        )
        previous_adapter = adapter_path
        adapter_paths.append(adapter_path)
        observed.extend(current)
    write_json(audit_root / f"{strategy}.json", updates)
    return adapter_paths


def train_adapter_bank(
    root: Path,
    model: Path,
    tasks: tuple[Task, ...],
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
    target = task_by_id[0].test_facts
    adapters: dict[int, Path] = {}
    audit = []
    for step, task_id in enumerate(order):
        task = task_by_id[task_id]
        rows = [factorized_training_example(fact) for fact in task.train_facts]
        rows = (rows * ((update_budget + len(rows) - 1) // len(rows)))[:update_budget]
        dataset = data_root / f"task-{task_id}"
        write_dataset(dataset, rows)
        adapter_path = adapter_root / f"task-{task_id}"
        command = training_command(model, dataset, adapter_path, seed + task_id, iters, None)
        env = os.environ.copy()
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (adapter_root / f"task-{task_id}.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf8"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"adapter-bank training failed for task {task_id}: {completed.returncode}")
        adapter_model = ChoiceModel(model, adapter_path)
        adapters[task_id] = adapter_path
        target_adapter_model = ChoiceModel(model, adapters[0])
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
                "target_task_id": 0,
                "target_task_accuracy_after_update": factorized_accuracy(target_adapter_model, target),
                "task_accuracy_after_update": factorized_accuracy(adapter_model, task.test_facts),
            }
        )
    write_json(audit_root / "task_adapter_bank.json", audit)
    return adapters, audit


def evaluate_strategy(
    model: Path,
    tasks: tuple[Task, ...],
    adapters: list[Path] | None,
    order: tuple[int, ...],
    root: Path,
    strategy: str,
) -> dict:
    task_by_id = {task.task_id: task for task in tasks}
    target = task_by_id[0].test_facts
    base = ChoiceModel(model)
    if strategy == "no_update":
        result = factorized_accuracy(base, target)
        return {"acquisition": result, "retention_after_interference": result, "recovery_after_reacquisition": result}
    if strategy == "context_only":
        acquisition = factorized_accuracy(base, target, task_by_id[0].train_facts)
        retention = factorized_accuracy(base, target)
        return {"acquisition": acquisition, "retention_after_interference": retention, "recovery_after_reacquisition": retention}
    if strategy == "retrieval":
        result = oracle_accuracy(target)
        return {"acquisition": result, "retention_after_interference": result, "recovery_after_reacquisition": result}
    assert adapters
    acquired = factorized_accuracy(ChoiceModel(model, adapters[0]), target)
    retained_model = ChoiceModel(model, adapters[-1])
    retained = factorized_accuracy(retained_model, target)
    recovery_data = root / "data" / strategy / "recovery"
    recovery_adapter = root / "adapters" / strategy / "recovery"
    train_target = task_by_id[0].train_facts
    write_dataset(recovery_data, [factorized_training_example(fact) for fact in train_target] * 4)
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
    (recovery_adapter.parent / "recovery.log").write_text(
        completed.stdout + "\n" + completed.stderr, encoding="utf8"
    )
    if completed.returncode != 0:
        raise RuntimeError(f"recovery training failed for {strategy}: {completed.returncode}")
    recovered = factorized_accuracy(ChoiceModel(model, recovery_adapter), target)
    return {
        "acquisition": acquired,
        "retention_after_interference": retained,
        "recovery_after_reacquisition": recovered,
        "retention_paraphrase": factorized_accuracy(retained_model, target),
    }


def evaluate_adapter_bank(model: Path, tasks, adapters: dict[int, Path]) -> dict:
    target = {task.task_id: task for task in tasks}[0].test_facts
    routed = ChoiceModel(model, adapters[0])
    metric = factorized_accuracy(routed, target)
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
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "solvability_control": "residue_visible_v1",
        "memory_mechanism": "factorized_task_memory_panel_v1",
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
        "audit_schema": "factorized_solvability_audit_v1",
        "checkpoint_target_task_id": 0,
        "checkpoint_assessment_context_mode": "none",
        "solvability_guard_accuracy": 0.75,
        "primary_metric": "replay_retention_delta_vs_naive",
        "prompt_contract": {
            "training_prompt_equals_assessment_prompt": True,
            "answer_suffix": ANSWER_SUFFIX,
            "derived_residue_visible": True,
            "raw_pair_present": True,
        },
        "iters": args.iters,
        "source_context_removed_for": [
            "acquisition",
            "retention_after_interference",
            "recovery_after_reacquisition",
        ],
        "assessment_effects_generated_before_prediction_lock": False,
    }
    config["contract_sha256"] = digest(config)
    write_json(root / "config.json", config)
    shared_adapters = {
        strategy: train_sequence(
            root, model, tasks, order, strategy, args.seed, args.iters, 24, 32
        )
        for strategy in ("naive_sequential_lora", "replay_lora")
    }
    bank_adapters, bank_audit = train_adapter_bank(root, model, tasks, order, args.seed, args.iters, 32)
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in shared_adapters
    }
    audits["task_adapter_bank"] = bank_audit
    results = {
        strategy: evaluate_strategy(
            model, tasks, shared_adapters.get(strategy), order, root, strategy
        )
        for strategy in ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora")
    }
    results["task_adapter_bank"] = evaluate_adapter_bank(model, tasks, bank_adapters)
    naive = results["naive_sequential_lora"]
    replay = results["replay_lora"]
    bank = results["task_adapter_bank"]
    solvability_floor = naive["acquisition"]["accuracy"] >= config["solvability_guard_accuracy"]
    replay_gain = replay["retention_after_interference"]["accuracy"] > naive["retention_after_interference"]["accuracy"]
    bank_gain = bank["retention_after_interference"]["accuracy"] > naive["retention_after_interference"]["accuracy"]
    candidate_gates = {
        "solvability_floor": solvability_floor,
        "replay_retention_above_naive": replay_gain,
        "bank_retention_above_naive": bank_gain,
    }
    result = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentFactorizedSolvabilityControlPilot",
        "classification": "FactorizedSolvabilityControlPilotNoBreakthroughClaim",
        "config": config,
        "results": results,
        "candidate_gates": candidate_gates,
        "candidate_eligible": solvability_floor and replay_gain,
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

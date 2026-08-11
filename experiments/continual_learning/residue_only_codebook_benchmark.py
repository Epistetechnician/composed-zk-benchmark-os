#!/usr/bin/env python3
"""V11 residue-only task-codebook solvability-control preflight."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base


STATE_SLICE = "continual-learning-protocol-v11-residue-only-codebook"
STRATEGIES = base.STRATEGIES


def residue_only_prompt_for(fact, context=()) -> str:
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
        "Use the task's residue-to-option codebook and return only the option letter."
        f"{base.ANSWER_SUFFIX}"
    )


def residue_only_training_example(fact) -> dict[str, str]:
    return {"prompt": residue_only_prompt_for(fact), "completion": f" {fact.label}"}


def residue_only_accuracy(model, facts, context=()) -> dict:
    facts = tuple(facts)
    context = tuple(context)
    rows = []
    correct = 0
    for fact in facts:
        prediction = model.answer(residue_only_prompt_for(fact, context))["prediction"]
        hit = prediction == fact.label
        correct += int(hit)
        rows.append(
            {
                "fact_id": fact.fact_id,
                "expected": fact.label,
                "observed": prediction,
                "correct": hit,
            }
        )
    return {"correct": correct, "n": len(facts), "accuracy": correct / len(facts) if facts else None, "rows": rows}


def run(args: argparse.Namespace) -> dict:
    # The V10 training/evaluation machinery is reused unchanged; only its
    # prompt and accuracy functions are replaced in this process.
    base.factorized_prompt_for = residue_only_prompt_for
    base.factorized_training_example = residue_only_training_example
    base.factorized_accuracy = residue_only_accuracy

    root = args.output.resolve()
    if root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {root}")
    root.mkdir(parents=True)
    model = args.model.resolve()
    if not model.is_dir():
        raise RuntimeError(f"model path does not exist: {model}")
    order = tuple(int(value) for value in args.order.split(","))
    tasks = base.make_tasks(args.seed, args.task_count)
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
    base.write_json(root / "tasks.json", tasks_json)
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
        "solvability_control": "residue_only_v1",
        "memory_mechanism": "residue_only_task_memory_panel_v1",
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
        "audit_schema": "residue_only_solvability_audit_v1",
        "checkpoint_target_task_id": 0,
        "checkpoint_assessment_context_mode": "none",
        "solvability_guard_accuracy": 0.75,
        "primary_metric": "replay_retention_delta_vs_naive",
        "prompt_contract": {
            "training_prompt_equals_assessment_prompt": True,
            "answer_suffix": base.ANSWER_SUFFIX,
            "derived_residue_visible": True,
            "raw_pair_present": False,
        },
        "iters": args.iters,
        "source_context_removed_for": [
            "acquisition",
            "retention_after_interference",
            "recovery_after_reacquisition",
        ],
        "assessment_effects_generated_before_prediction_lock": False,
    }
    config["contract_sha256"] = base.digest(config)
    base.write_json(root / "config.json", config)
    shared_adapters = {
        strategy: base.train_sequence(root, model, tasks, order, strategy, args.seed, args.iters, 24, 32)
        for strategy in ("naive_sequential_lora", "replay_lora")
    }
    bank_adapters, bank_audit = base.train_adapter_bank(root, model, tasks, order, args.seed, args.iters, 32)
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in shared_adapters
    }
    audits["task_adapter_bank"] = bank_audit
    results = {
        strategy: base.evaluate_strategy(model, tasks, shared_adapters.get(strategy), order, root, strategy)
        for strategy in ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora")
    }
    results["task_adapter_bank"] = base.evaluate_adapter_bank(model, tasks, bank_adapters)
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
        "claim_ceiling": "LocalDevelopmentResidueOnlyCodebookPilot",
        "classification": "ResidueOnlyCodebookPilotNoBreakthroughClaim",
        "config": config,
        "results": results,
        "candidate_gates": candidate_gates,
        "candidate_eligible": solvability_floor and replay_gain,
        "audit_sha256": {strategy: base.digest(audit) for strategy, audit in audits.items()},
        "manifest_sha256": base.digest({"config": config, "tasks": tasks_json, "audits": audits}),
        "breakthrough_claim_eligible": False,
    }
    base.write_json(root / "result.json", result)
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

#!/usr/bin/env python3
"""V26 bounded candidate preflight for append-only task-routed adapters.

State slice: continual-learning-candidate-task-routed-adapter-bank-v26.

This module reuses the frozen local MLX seam and V11 task generator. The sole
scientific change is the memory/update mechanism: each task is trained from
the frozen base into a fresh LoRA adapter, and assessment resolves the target
task to that adapter by its exact task token. Shared sequential and replay
baselines remain in the panel for comparison.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import residue_only_codebook_benchmark as v11


STATE_SLICE = "continual-learning-candidate-task-routed-adapter-bank-v26"
SOURCE_STATE_SLICE = "continual-learning-protocol-v18-route-boundary-representation"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")


def route_bound_prompt_for(fact, context=()) -> str:
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
        f"Task route binding: {fact.task_token}."
        f"{v11.base.ANSWER_SUFFIX}"
    )


def route_bound_training_example(fact) -> dict[str, str]:
    return {"prompt": route_bound_prompt_for(fact), "completion": f" {fact.label}"}


def route_bound_accuracy(model, facts, context=()) -> dict:
    facts = tuple(facts)
    context = tuple(context)
    rows = []
    correct = 0
    for fact in facts:
        prediction = model.answer(route_bound_prompt_for(fact, context))["prediction"]
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


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def run(args: argparse.Namespace) -> dict:
    model = args.model.resolve()
    order = tuple(int(value) for value in args.order.split(","))
    if model != MODEL_DEFAULT.resolve() or args.task_count != 4 or args.iters != 160:
        raise ValueError("V26 fixed contract drift")
    if sorted(order) != list(range(args.task_count)) or order[0] != 0:
        raise ValueError("order must be a permutation with target task 0 first")

    original_state_slice = v11.STATE_SLICE
    original_prompt = v11.residue_only_prompt_for
    original_training_example = v11.residue_only_training_example
    original_accuracy = v11.residue_only_accuracy
    v11.STATE_SLICE = STATE_SLICE
    v11.residue_only_prompt_for = route_bound_prompt_for
    v11.residue_only_training_example = route_bound_training_example
    v11.residue_only_accuracy = route_bound_accuracy
    try:
        result = v11.run(args)
    finally:
        v11.STATE_SLICE = original_state_slice
        v11.residue_only_prompt_for = original_prompt
        v11.residue_only_training_example = original_training_example
        v11.residue_only_accuracy = original_accuracy

    root = args.output.resolve()
    config = result["config"]
    config.update(
        {
            "source_state_slice": SOURCE_STATE_SLICE,
            "memory_mechanism": "append_only_task_routed_adapter_bank_v1",
            "task_update_redesign": "fresh_adapter_per_task_from_frozen_base_v1",
            "route_policy": "task_token_exact_v1",
            "prompt_contract": {
                "training_prompt_equals_assessment_prompt": True,
                "answer_suffix": v11.base.ANSWER_SUFFIX,
                "derived_residue_visible": True,
                "raw_pair_present": False,
                "route_binding_at_answer_boundary": True,
                "route_binding_policy": "task_route_suffix_v1",
            },
            "candidate_metric": "task_adapter_bank_heldout_retention_vs_naive",
            "candidate_claim_ceiling": "LocalDevelopmentTaskRoutedAdapterBankCandidate",
        }
    )
    config["contract_sha256"] = v11.base.digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(root / "config.json", config)
    tasks = json.loads((root / "tasks.json").read_text())
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in ("naive_sequential_lora", "replay_lora", "task_adapter_bank")
    }
    no_update = result["results"]["no_update"]
    naive = result["results"]["naive_sequential_lora"]
    bank = result["results"]["task_adapter_bank"]
    gates = {
        "retrieval_above_no_update": result["results"]["retrieval"]["acquisition"]["accuracy"] > no_update["acquisition"]["accuracy"],
        "bank_acquisition_above_no_update": bank["acquisition"]["accuracy"] > no_update["acquisition"]["accuracy"],
        "bank_retention_above_naive": bank["retention_after_interference"]["accuracy"] > naive["retention_after_interference"]["accuracy"],
        "bank_heldout_solubility_floor": bank["retention_after_interference"]["accuracy"] >= 0.75,
    }
    result.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "claim_ceiling": "LocalDevelopmentTaskRoutedAdapterBankCandidate",
            "classification": "TaskRoutedAdapterBankCandidateNoProductionClaim",
            "config": config,
            "tasks": tasks,
            "candidate_gates": gates,
            "candidate_eligible": all(gates.values()),
            "breakthrough_claim_eligible": False,
            "production_claim_eligible": False,
            "manifest_sha256": v11.base.digest({"config": config, "tasks": tasks, "audits": audits}),
        }
    )
    result["result_sha256"] = v11.base.digest({key: value for key, value in result.items() if key != "result_sha256"})
    write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--order", required=True)
    parser.add_argument("--task-count", type=int, default=4)
    parser.add_argument("--iters", type=int, default=160)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""V18 route-boundary representation preflight.

The only changed scientific variable is a repeated task route marker placed
immediately before the answer boundary. V14's data, optimizer, update budget,
seed, order, model, and training machinery remain fixed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import repaired_objective_retention_preflight as v14  # noqa: E402
from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v18-route-boundary-representation"
SOURCE_STATE_SLICE = "continual-learning-protocol-v17-task-keyed-readout-feasibility"
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
    if (
        args.seed != 20260810
        or order != (0, 1, 2, 3)
        or args.task_count != 4
        or args.iters != 160
        or model != MODEL_DEFAULT.resolve()
    ):
        raise ValueError("V18 fixed contract drift")

    original_state_slice = v14.STATE_SLICE
    original_source_state_slice = v14.SOURCE_STATE_SLICE
    original_prompt = v11.residue_only_prompt_for
    original_training_example = v11.residue_only_training_example
    original_accuracy = v11.residue_only_accuracy
    v14.STATE_SLICE = STATE_SLICE
    v14.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    v11.residue_only_prompt_for = route_bound_prompt_for
    v11.residue_only_training_example = route_bound_training_example
    v11.residue_only_accuracy = route_bound_accuracy
    try:
        result = v14.run(args)
    finally:
        v14.STATE_SLICE = original_state_slice
        v14.SOURCE_STATE_SLICE = original_source_state_slice
        v11.residue_only_prompt_for = original_prompt
        v11.residue_only_training_example = original_training_example
        v11.residue_only_accuracy = original_accuracy

    root = args.output.resolve()
    config = result["config"]
    config.update(
        {
            "source_state_slice": SOURCE_STATE_SLICE,
            "representation_redesign": "route_binding_at_answer_boundary_v1",
            "prompt_contract": {
                "training_prompt_equals_assessment_prompt": True,
                "answer_suffix": v11.base.ANSWER_SUFFIX,
                "derived_residue_visible": True,
                "raw_pair_present": False,
                "route_binding_at_answer_boundary": True,
                "route_binding_policy": "task_route_suffix_v1",
            },
        }
    )
    config["contract_sha256"] = v11.base.digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(root / "config.json", config)
    tasks = json.loads((root / "tasks.json").read_text())
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in ("naive_sequential_lora", "replay_lora", "task_adapter_bank")
    }
    result.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "claim_ceiling": "LocalDevelopmentRouteBoundaryRepresentationPilot",
            "classification": "RouteBoundaryRepresentationPilotNoBreakthroughClaim",
            "config": config,
            "tasks": tasks,
            "representation_redesign": "route_binding_at_answer_boundary_v1",
            "retention_comparison_run": True,
            "breakthrough_claim_eligible": False,
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
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--order", default="0,1,2,3")
    parser.add_argument("--task-count", type=int, default=4)
    parser.add_argument("--iters", type=int, default=160)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

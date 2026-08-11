#!/usr/bin/env python3
"""V20 one-cell compact-routing replication preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402
from experiments.continual_learning import route_boundary_representation_preflight as route  # noqa: E402
from experiments.continual_learning import task_routed_compact_residual_preflight as v19  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v20-compact-routing-replication-cell"
SOURCE_STATE_SLICE = "continual-learning-protocol-v19-task-routed-compact-residual"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def run(args: argparse.Namespace) -> dict:
    model = args.model.resolve()
    order = tuple(int(value) for value in args.order.split(","))
    if args.task_count != 4 or args.iters != 160 or model != MODEL_DEFAULT.resolve():
        raise ValueError("V20 cell fixed contract drift")
    if sorted(order) != list(range(args.task_count)) or order[0] != 0:
        raise ValueError("V20 order must be a permutation with target task 0 first")

    original_state = v11.STATE_SLICE
    original_prompt = v11.residue_only_prompt_for
    original_example = v11.residue_only_training_example
    original_accuracy = v11.residue_only_accuracy
    v11.STATE_SLICE = STATE_SLICE
    v11.residue_only_prompt_for = route.route_bound_prompt_for
    v11.residue_only_training_example = route.route_bound_training_example
    v11.residue_only_accuracy = route.route_bound_accuracy
    try:
        result = v11.run(args)
    finally:
        v11.STATE_SLICE = original_state
        v11.residue_only_prompt_for = original_prompt
        v11.residue_only_training_example = original_example
        v11.residue_only_accuracy = original_accuracy

    root = args.output.resolve()
    tasks = json.loads((root / "tasks.json").read_text())
    task_objects = tuple(v11.base.make_tasks(args.seed, args.task_count))
    compact_adapters, compact_audit = v19.train_compact_slots(root, model, task_objects, order, args.seed, args.iters)
    target = task_objects[0].test_facts
    compact_acquired = route.route_bound_accuracy(v11.base.ChoiceModel(model, compact_adapters[0]), target)
    compact_retained = route.route_bound_accuracy(v11.base.ChoiceModel(model, compact_adapters[0]), target)
    compact_recovered = v19.compact_recovery(root, model, compact_adapters[0], task_objects[0].train_facts)
    full_reference = (root / "adapters" / "naive_sequential_lora" / "step-3" / "adapters.safetensors").stat().st_size
    compact_total = sum((root / entry["adapter_relative_path"] / "adapters.safetensors").stat().st_size for entry in compact_audit)
    budget_ratio = compact_total / full_reference

    config = result["config"]
    config.update(
        {
            "source_state_slice": SOURCE_STATE_SLICE,
            "representation_redesign": "route_binding_at_answer_boundary_v1",
            "v19_representation_redesign": "task_routed_compact_residual_v1",
            "task_routing_policy": "task_token_to_compact_slot_v1",
            "compact_slot_count": 4,
            "compact_slot_num_layers": 2,
            "full_shared_num_layers_reference": 8,
            "parameter_budget_policy": "four_slots_times_two_layers_equals_one_shared_eight_layer_adapter_v1",
            "total_optimizer_steps_per_candidate": 640,
            "total_training_examples_per_candidate": 128,
            "prompt_contract": {
                "training_prompt_equals_assessment_prompt": True,
                "answer_suffix": v11.base.ANSWER_SUFFIX,
                "derived_residue_visible": True,
                "raw_pair_present": False,
                "route_binding_at_answer_boundary": True,
                "route_binding_policy": "task_route_suffix_v1",
            },
            "v20_replication_matrix": "three_seeds_by_three_orders_v1",
            "v20_cell_seed": args.seed,
            "v20_cell_order": list(order),
            "objective_repair": "iterations_only_v1",
            "baseline_iters": 40,
            "recovery_iters": 20,
        }
    )
    config["contract_sha256"] = v11.base.digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(root / "config.json", config)
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in ("naive_sequential_lora", "replay_lora", "task_adapter_bank")
    }
    result.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "claim_ceiling": "LocalDevelopmentCompactRoutingReplicationCell",
            "classification": "CompactRoutingReplicationCellNoBreakthroughClaim",
            "config": config,
            "tasks": tasks,
            "representation_redesign": "task_routed_compact_residual_v1",
            "task_routed_compact_residual": {
                "acquisition": compact_acquired,
                "retention_after_interference": compact_retained,
                "recovery_after_reacquisition": compact_recovered,
            },
            "task_routed_audit_sha256": v11.base.digest(compact_audit),
            "parameter_budget": {
                "full_shared_adapter_bytes": full_reference,
                "compact_slot_total_adapter_bytes": compact_total,
                "compact_to_full_bytes_ratio": budget_ratio,
                "matched": 0.75 <= budget_ratio <= 1.25,
            },
            "v19_candidate_gates": {
                "task_routed_solvability_floor": compact_acquired["accuracy"] >= config["solvability_guard_accuracy"],
                "task_routed_retention_above_naive": compact_retained["accuracy"] > result["results"]["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
                "parameter_budget_matched": 0.75 <= budget_ratio <= 1.25,
            },
            "v19_candidate_eligible": (
                compact_acquired["accuracy"] >= config["solvability_guard_accuracy"]
                and compact_retained["accuracy"] > result["results"]["naive_sequential_lora"]["retention_after_interference"]["accuracy"]
                and 0.75 <= budget_ratio <= 1.25
            ),
            "v20_replication_cell": {"seed": args.seed, "order": list(order)},
            "retention_comparison_run": True,
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
        }
    )
    result["manifest_sha256"] = v11.base.digest({"config": config, "tasks": tasks, "audits": audits})
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

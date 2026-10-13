#!/usr/bin/env python3
"""V19 compact task-routed residual preflight."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import route_boundary_representation_preflight as v18  # noqa: E402
from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v19-task-routed-compact-residual"
SOURCE_STATE_SLICE = "continual-learning-protocol-v18-route-boundary-representation"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")
COMPACT_SLOT_LAYERS = 2
FULL_SHARED_LAYERS = 8


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def compact_training_command(model: Path, dataset: Path, adapter_path: Path, seed: int, iters: int) -> list[str]:
    command = v11.base.training_command(model, dataset, adapter_path, seed, iters, None)
    command[command.index("--num-layers") + 1] = str(COMPACT_SLOT_LAYERS)
    return command


def train_compact_slots(root: Path, model: Path, tasks, order, seed: int, iters: int) -> tuple[list[Path], list[dict]]:
    data_root = root / "data" / "task_routed_compact_residual"
    adapter_root = root / "adapters" / "task_routed_compact_residual"
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    audit_root.mkdir(exist_ok=True)
    task_by_id = {task.task_id: task for task in tasks}
    target = task_by_id[0].test_facts
    adapters = []
    audit = []
    for step, task_id in enumerate(order):
        task = task_by_id[task_id]
        rows = [v18.route_bound_training_example(fact) for fact in task.train_facts]
        rows = (rows * ((32 + len(rows) - 1) // len(rows)))[:32]
        dataset = data_root / f"task-{task_id}"
        v11.base.write_dataset(dataset, rows)
        adapter_path = adapter_root / f"task-{task_id}"
        command = compact_training_command(model, dataset, adapter_path, seed + task_id, iters)
        env = os.environ.copy()
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (adapter_root / f"task-{task_id}.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
        if completed.returncode != 0:
            raise RuntimeError(f"compact task slot training failed for task {task_id}: {completed.returncode}")
        adapter_model = v11.base.ChoiceModel(model, adapter_path)
        target_model = v11.base.ChoiceModel(model, adapters[0]) if adapters else adapter_model
        audit.append(
            {
                "step": step,
                "task_id": task_id,
                "route_key": task.task_token,
                "route_policy": "task_token_exact_v1",
                "adapter_relative_path": str(adapter_path.relative_to(root)),
                "resumed_from": None,
                "slot_num_layers": COMPACT_SLOT_LAYERS,
                "train_fact_ids": [fact.fact_id for fact in task.train_facts],
                "selected_fact_ids": [fact.fact_id for fact in task.train_facts],
                "replay_fact_ids": [],
                "replay_counts_by_task": {},
                "dataset_row_count": len(rows),
                "target_task_id": 0,
                "target_task_accuracy_after_update": v18.route_bound_accuracy(target_model, target),
                "task_accuracy_after_update": v18.route_bound_accuracy(adapter_model, task.test_facts),
            }
        )
        adapters.append(adapter_path)
    write_json(audit_root / "task_routed_compact_residual.json", audit)
    return adapters, audit


def compact_recovery(root: Path, model: Path, adapter: Path, facts) -> dict:
    dataset = root / "data" / "task_routed_compact_residual" / "recovery"
    v11.base.write_dataset(dataset, [v18.route_bound_training_example(fact) for fact in facts] * 4)
    recovery = root / "adapters" / "task_routed_compact_residual" / "recovery"
    command = v11.base.training_command(model, dataset, recovery, 19082026, 20, adapter / "adapters.safetensors")
    command[command.index("--num-layers") + 1] = str(COMPACT_SLOT_LAYERS)
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    (recovery.parent / "recovery.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
    if completed.returncode != 0:
        raise RuntimeError(f"compact task slot recovery failed: {completed.returncode}")
    return v18.route_bound_accuracy(v11.base.ChoiceModel(model, recovery), facts)


def run(args: argparse.Namespace) -> dict:
    model = args.model.resolve()
    order = tuple(int(value) for value in args.order.split(","))
    if args.seed != 20260810 or order != (0, 1, 2, 3) or args.task_count != 4 or args.iters != 160 or model != MODEL_DEFAULT.resolve():
        raise ValueError("V19 fixed contract drift")

    original_state = v18.STATE_SLICE
    original_source = v18.SOURCE_STATE_SLICE
    v18.STATE_SLICE = STATE_SLICE
    v18.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    try:
        result = v18.run(args)
    finally:
        v18.STATE_SLICE = original_state
        v18.SOURCE_STATE_SLICE = original_source

    root = args.output.resolve()
    tasks = tuple(v11.base.make_tasks(args.seed, args.task_count))
    compact_adapters, compact_audit = train_compact_slots(root, model, tasks, order, args.seed, args.iters)
    target = tasks[0].test_facts
    compact_acquired = v18.route_bound_accuracy(v11.base.ChoiceModel(model, compact_adapters[0]), target)
    compact_retained = v18.route_bound_accuracy(v11.base.ChoiceModel(model, compact_adapters[0]), target)
    compact_recovered = compact_recovery(root, model, compact_adapters[0], tasks[0].train_facts)
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
            "compact_slot_num_layers": COMPACT_SLOT_LAYERS,
            "full_shared_num_layers_reference": FULL_SHARED_LAYERS,
            "parameter_budget_policy": "four_slots_times_two_layers_equals_one_shared_eight_layer_adapter_v1",
            "total_optimizer_steps_per_candidate": 640,
            "total_training_examples_per_candidate": 128,
        }
    )
    config["contract_sha256"] = v11.base.digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(root / "config.json", config)
    result.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "claim_ceiling": "LocalDevelopmentTaskRoutedCompactResidualPilot",
            "classification": "TaskRoutedCompactResidualPilotNoBreakthroughClaim",
            "config": config,
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
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
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

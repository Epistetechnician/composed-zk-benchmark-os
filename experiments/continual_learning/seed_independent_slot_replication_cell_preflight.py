#!/usr/bin/env python3
"""V22 one-cell preflight with seed-independent compact slot state."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import compact_routing_replication_cell_preflight as v20  # noqa: E402
from experiments.continual_learning import route_boundary_representation_preflight as route  # noqa: E402
from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402
from experiments.continual_learning import task_routed_compact_residual_preflight as v19  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v22-seed-independent-init-replication-cell"
SOURCE_STATE_SLICE = "continual-learning-protocol-v21-seed-sensitivity-diagnosis"
SLOT_SEED_BASE = 22000000
SLOT_INITIALIZATION_POLICY = "task_keyed_fixed_seed_v1"
OPTIMIZER_STATE_POLICY = "fresh_zero_state_task_keyed_seed_v1"
MODEL_DEFAULT = v20.MODEL_DEFAULT


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixed_slot_seed(task_id: int) -> int:
    return SLOT_SEED_BASE + task_id


def train_seed_independent_slots(root: Path, model: Path, tasks, order, seed: int, iters: int) -> tuple[list[Path], list[dict]]:
    """Train each slot from the same task-keyed initial/optimizer state in every cell."""

    del seed
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
        rows = [route.route_bound_training_example(fact) for fact in task.train_facts]
        rows = (rows * ((32 + len(rows) - 1) // len(rows)))[:32]
        dataset = data_root / f"task-{task_id}"
        v11.base.write_dataset(dataset, rows)
        adapter_path = adapter_root / f"task-{task_id}"
        slot_seed = fixed_slot_seed(task_id)
        command = v19.compact_training_command(model, dataset, adapter_path, slot_seed, iters)
        env = os.environ.copy()
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (adapter_root / f"task-{task_id}.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
        if completed.returncode != 0:
            raise RuntimeError(f"seed-independent compact slot training failed for task {task_id}: {completed.returncode}")
        adapter_file = adapter_path / "adapters.safetensors"
        adapter_model = v11.base.ChoiceModel(model, adapter_path)
        target_model = v11.base.ChoiceModel(model, adapters[0]) if adapters else adapter_model
        audit.append(
            {
                "step": step,
                "task_id": task_id,
                "route_key": task.task_token,
                "route_policy": "task_token_exact_v1",
                "adapter_relative_path": str(adapter_path.relative_to(root)),
                "adapter_bytes": adapter_file.stat().st_size,
                "adapter_sha256": file_digest(adapter_file),
                "resumed_from": None,
                "slot_num_layers": v19.COMPACT_SLOT_LAYERS,
                "slot_seed": slot_seed,
                "slot_initialization_policy": SLOT_INITIALIZATION_POLICY,
                "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
                "train_fact_ids": [fact.fact_id for fact in task.train_facts],
                "selected_fact_ids": [fact.fact_id for fact in task.train_facts],
                "replay_fact_ids": [],
                "replay_counts_by_task": {},
                "dataset_row_count": len(rows),
                "target_task_id": 0,
                "target_task_accuracy_after_update": route.route_bound_accuracy(target_model, target),
                "task_accuracy_after_update": route.route_bound_accuracy(adapter_model, task.test_facts),
            }
        )
        adapters.append(adapter_path)
    write_json(audit_root / "task_routed_compact_residual.json", audit)
    return adapters, audit


def run(args: argparse.Namespace) -> dict:
    original_state = v20.STATE_SLICE
    original_source = v20.SOURCE_STATE_SLICE
    original_train = v20.v19.train_compact_slots
    v20.STATE_SLICE = STATE_SLICE
    v20.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    v20.v19.train_compact_slots = train_seed_independent_slots
    try:
        result = v20.run(args)
    finally:
        v20.STATE_SLICE = original_state
        v20.SOURCE_STATE_SLICE = original_source
        v20.v19.train_compact_slots = original_train

    root = args.output.resolve()
    config = result["config"]
    for key in ("v20_replication_matrix", "v20_cell_seed", "v20_cell_order"):
        config.pop(key, None)
    config.update(
        {
            "source_state_slice": SOURCE_STATE_SLICE,
            "v22_replication_matrix": "three_seeds_by_three_orders_v1",
            "v22_cell_seed": args.seed,
            "v22_cell_order": list(int(value) for value in args.order.split(",")),
            "slot_initialization_policy": SLOT_INITIALIZATION_POLICY,
            "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
            "slot_seed_base": SLOT_SEED_BASE,
            "candidate_slot_seed_depends_on_experiment_seed": False,
        }
    )
    config["contract_sha256"] = v11.base.digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(root / "config.json", config)
    audit = json.loads((root / "audit" / "task_routed_compact_residual.json").read_text())
    tasks = json.loads((root / "tasks.json").read_text())
    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in ("naive_sequential_lora", "replay_lora", "task_adapter_bank")
    }
    result.pop("v20_replication_cell", None)
    result.update(
        {
            "state_slice": STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "claim_ceiling": "LocalDevelopmentSeedIndependentSlotStabilityReplicationCell",
            "classification": "SeedIndependentSlotStabilityReplicationCellNoBreakthroughClaim",
            "config": config,
            "v22_replication_cell": {"seed": args.seed, "order": list(int(value) for value in args.order.split(","))},
            "slot_state_contract": {
                "slot_initialization_policy": SLOT_INITIALIZATION_POLICY,
                "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
                "slot_seed_base": SLOT_SEED_BASE,
                "slot_seed_depends_on_experiment_seed": False,
            },
            "task_routed_audit_sha256": v11.base.digest(audit),
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
    parser.add_argument("--model", type=Path, default=v20.MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--order", required=True)
    parser.add_argument("--task-count", type=int, default=4)
    parser.add_argument("--iters", type=int, default=160)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""V24 pure-data protocol for shared-adapter task-keyed optimizer state.

This module constructs only deterministic schedules. It does not load a model,
invoke MLX, or authorize a replication campaign.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402
from experiments.continual_learning import route_boundary_representation_preflight as route  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v24-shared-adapter-task-keyed-optimizer-state"
SOURCE_STATE_SLICE = "continual-learning-protocol-v23-task-routed-replay-consolidation-preflight"
MODEL_DEFAULT = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
SEEDS = (20260811, 20260812, 20260813)
ORDERS = ((0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2))
TASK_COUNT = 4
TRAIN_FACTS_PER_TASK = 8
TEST_FACTS_PER_TASK = 8
UPDATE_BUDGET = 32
REPLAY_CAPACITY = 24
ITERS_PER_UPDATE = 160
SHARED_ADAPTER_LAYERS = 8
FULL_SHARED_LAYERS = 8
SLOT_SEED_BASE = 22000000
SHARED_ADAPTER_ID = "shared-eight-layer-adapter-v1"
OPTIMIZER_STATE_POLICY = "task_keyed_fresh_zero_on_first_activation_persistent_shared_adapter_v1"
UPDATE_ROUTE_POLICY = "fact_task_token_to_matching_optimizer_state_shared_adapter_v1"
REPLAY_SELECTION_POLICY = "balanced_full_memory_v1"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def fixed_task_seed(task_id: int) -> int:
    return SLOT_SEED_BASE + task_id


def row_plan(fact) -> dict:
    row = route.route_bound_training_example(fact)
    return {
        "fact_id": fact.fact_id,
        "task_id": fact.task_id,
        "route_key": fact.task_token,
        "prompt_sha256": hashlib.sha256(row["prompt"].encode()).hexdigest(),
        "completion": row["completion"],
    }


def repeated_rows(facts: list) -> list[dict]:
    if not facts:
        raise ValueError("cannot build an empty update")
    rows = [row_plan(fact) for fact in facts]
    return (rows * ((UPDATE_BUDGET + len(rows) - 1) // len(rows)))[:UPDATE_BUDGET]


def allocate_optimizer_iterations(route_counts: dict[str, int]) -> dict[str, int]:
    if not route_counts or sum(route_counts.values()) != UPDATE_BUDGET:
        raise ValueError("optimizer allocation requires the complete update row budget")
    total = ITERS_PER_UPDATE
    denominator = sum(route_counts.values())
    base = {task: total * count // denominator for task, count in route_counts.items()}
    remainder = total - sum(base.values())
    for task in sorted(route_counts)[:remainder]:
        base[task] += 1
    if any(value < 1 for value in base.values()) or sum(base.values()) != total:
        raise ValueError("optimizer iteration allocation drift")
    return dict(sorted(base.items()))


def make_schedule(seed: int, order: tuple[int, ...], replay_enabled: bool) -> list[dict]:
    if seed not in SEEDS or order not in ORDERS:
        raise ValueError("V24 matrix identity drift")
    tasks = tuple(v11.base.make_tasks(seed, TASK_COUNT))
    task_by_id = {task.task_id: task for task in tasks}
    observed = []
    schedule = []
    for step, task_id in enumerate(order):
        current = list(task_by_id[task_id].train_facts)
        replay = (
            v11.base.choose_balanced_full_replay(observed, REPLAY_CAPACITY, limit=REPLAY_CAPACITY)
            if replay_enabled
            else []
        )
        selected = current + replay
        rows = repeated_rows(selected)
        route_counts = {}
        for row in rows:
            key = str(row["task_id"])
            route_counts[key] = route_counts.get(key, 0) + 1
        iterations = allocate_optimizer_iterations(route_counts)
        schedule.append(
            {
                "step": step,
                "task_id": task_id,
                "current_fact_ids": [fact.fact_id for fact in current],
                "replay_fact_ids": [fact.fact_id for fact in replay],
                "selected_fact_ids": [fact.fact_id for fact in selected],
                "dataset_row_count": len(rows),
                "rows": rows,
                "route_counts_by_task": dict(sorted(route_counts.items())),
                "optimizer_iterations_by_task": iterations,
                "active_optimizer_state_task_ids": [int(task) for task in iterations],
                "optimizer_state_key_by_task": {
                    str(active_task): f"task-{active_task}"
                    for active_task in sorted(int(task) for task in iterations)
                },
                "task_seed_by_task": {
                    str(active_task): fixed_task_seed(int(active_task))
                    for active_task in sorted(int(task) for task in iterations)
                },
                "shared_adapter_id": SHARED_ADAPTER_ID,
                "shared_adapter_layers": SHARED_ADAPTER_LAYERS,
                "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
                "update_route_policy": UPDATE_ROUTE_POLICY,
                "optimizer_iterations": ITERS_PER_UPDATE,
            }
        )
        observed.extend(current)
    return schedule


def validate_schedule(seed: int, order: tuple[int, ...], schedule: list[dict], replay_enabled: bool) -> dict:
    expected = make_schedule(seed, order, replay_enabled)
    if schedule != expected:
        raise ValueError("schedule is not the deterministic V24 derivation")
    seen = set()
    for entry in schedule:
        current = set(entry["current_fact_ids"])
        replay_ids = set(entry["replay_fact_ids"])
        if entry["dataset_row_count"] != UPDATE_BUDGET or len(entry["rows"]) != UPDATE_BUDGET:
            raise ValueError(f"update budget drift at step {entry['step']}")
        if replay_ids & current or not replay_ids.issubset(seen):
            raise ValueError(f"replay custody drift at step {entry['step']}")
        if any(row["route_key"] != f"T{row['task_id']}" for row in entry["rows"]):
            raise ValueError(f"route key drift at step {entry['step']}")
        computed = {}
        for row in entry["rows"]:
            key = str(row["task_id"])
            computed[key] = computed.get(key, 0) + 1
        if dict(sorted(computed.items())) != entry["route_counts_by_task"]:
            raise ValueError(f"route count drift at step {entry['step']}")
        if sum(entry["optimizer_iterations_by_task"].values()) != ITERS_PER_UPDATE:
            raise ValueError(f"optimizer budget drift at step {entry['step']}")
        if entry["shared_adapter_id"] != SHARED_ADAPTER_ID or entry["shared_adapter_layers"] != SHARED_ADAPTER_LAYERS:
            raise ValueError(f"shared adapter drift at step {entry['step']}")
        if entry["task_seed_by_task"] != {
            str(task): fixed_task_seed(int(task)) for task in entry["optimizer_iterations_by_task"]
        }:
            raise ValueError(f"task seed drift at step {entry['step']}")
        seen.update(current)
    return {"valid": True, "steps": len(schedule), "rows": sum(e["dataset_row_count"] for e in schedule)}


def build_plan() -> dict:
    cells = []
    for seed in SEEDS:
        for order in ORDERS:
            replay_schedule = make_schedule(seed, order, True)
            no_replay_schedule = make_schedule(seed, order, False)
            cells.append(
                {
                    "cell": f"seed-{seed}-order-{''.join(str(value) for value in order)}",
                    "seed": seed,
                    "order": list(order),
                    "shared_replay_schedule": replay_schedule,
                    "shared_no_replay_schedule": no_replay_schedule,
                    "shared_replay_schedule_sha256": digest(replay_schedule),
                    "shared_no_replay_schedule_sha256": digest(no_replay_schedule),
                }
            )
    gates = {
        "cell_count_exact": len(cells) == 9,
        "matrix_identity_exact": all(cell["seed"] in SEEDS and tuple(cell["order"]) in ORDERS for cell in cells),
        "shared_replay_schedule_deterministic": all(validate_schedule(cell["seed"], tuple(cell["order"]), cell["shared_replay_schedule"], True)["valid"] for cell in cells),
        "shared_no_replay_schedule_deterministic": all(validate_schedule(cell["seed"], tuple(cell["order"]), cell["shared_no_replay_schedule"], False)["valid"] for cell in cells),
        "same_update_row_budget": all(
            [entry["dataset_row_count"] for entry in cell["shared_replay_schedule"]]
            == [entry["dataset_row_count"] for entry in cell["shared_no_replay_schedule"]]
            == [UPDATE_BUDGET] * TASK_COUNT
            for cell in cells
        ),
        "same_total_examples": all(
            sum(entry["dataset_row_count"] for entry in cell["shared_replay_schedule"])
            == sum(entry["dataset_row_count"] for entry in cell["shared_no_replay_schedule"])
            == UPDATE_BUDGET * TASK_COUNT
            for cell in cells
        ),
        "same_total_optimizer_steps": ITERS_PER_UPDATE * TASK_COUNT == 640,
        "shared_adapter_fixed": all(
            entry["shared_adapter_id"] == SHARED_ADAPTER_ID
            and entry["shared_adapter_layers"] == SHARED_ADAPTER_LAYERS
            for cell in cells for entry in cell["shared_replay_schedule"]
        ),
        "optimizer_state_task_keyed": all(
            entry["optimizer_state_policy"] == OPTIMIZER_STATE_POLICY
            for cell in cells for entry in cell["shared_replay_schedule"]
        ),
        "replay_routes_to_own_optimizer_state": all(
            all(row["route_key"] == f"T{row['task_id']}" for entry in cell["shared_replay_schedule"] for row in entry["rows"])
            for cell in cells
        ),
        "not_rerunning_v23_isolated_slot_design": True,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    plan = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "SharedAdapterTaskKeyedOptimizerStateProtocolOnlyNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentSharedAdapterTaskKeyedOptimizerStateProtocol",
        "model": MODEL_DEFAULT,
        "matrix_policy": "three_seeds_by_three_orders_v1",
        "seeds": list(SEEDS),
        "orders": [list(order) for order in ORDERS],
        "task_count": TASK_COUNT,
        "train_facts_per_task": TRAIN_FACTS_PER_TASK,
        "test_facts_per_task": TEST_FACTS_PER_TASK,
        "update_budget": UPDATE_BUDGET,
        "replay_capacity": REPLAY_CAPACITY,
        "iters_per_update": ITERS_PER_UPDATE,
        "shared_adapter_layers": SHARED_ADAPTER_LAYERS,
        "total_examples_per_cell": UPDATE_BUDGET * TASK_COUNT,
        "total_optimizer_steps_per_cell": ITERS_PER_UPDATE * TASK_COUNT,
        "changed_protocol_variable": "shared_adapter_task_keyed_optimizer_state_v1",
        "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
        "update_route_policy": UPDATE_ROUTE_POLICY,
        "replay_selection_policy": REPLAY_SELECTION_POLICY,
        "task_seed_base": SLOT_SEED_BASE,
        "cells": cells,
        "gates": gates,
        "model_training_authorized": False,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
        "next_run_condition": "one_corrected_local_preflight_after_independent_schedule_validation",
    }
    plan["plan_sha256"] = digest({key: value for key, value in plan.items() if key != "plan_sha256"})
    return plan


def validate_plan(plan: dict) -> dict:
    expected = build_plan()
    if plan != expected:
        raise ValueError("V24 protocol plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V24 plan digest mismatch")
    contract_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_keys):
        raise ValueError("V24 protocol gate failure")
    if plan["h100_authorized"] or plan["breakthrough_claim_eligible"]:
        raise ValueError("V24 authority boundary drift")
    return {
        "valid": True,
        "state_slice": plan["state_slice"],
        "cell_count": len(plan["cells"]),
        "gates": plan["gates"],
        "model_training_authorized": plan["model_training_authorized"],
        "h100_authorized": plan["h100_authorized"],
        "plan_sha256": plan["plan_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    plan = build_plan()
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, plan)
    print(json.dumps(validate_plan(plan), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

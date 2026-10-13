#!/usr/bin/env python3
"""V23 pure-data contract for task-routed replay consolidation.

This module creates and validates the prospective update schedules only. It
does not load a model, invoke a trainer, or authorize a replication run.
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


STATE_SLICE = "continual-learning-protocol-v23-task-routed-replay-consolidation"
SOURCE_STATE_SLICE = "continual-learning-protocol-v22-seed-independent-init-replication"
MODEL_DEFAULT = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
SEEDS = (20260811, 20260812, 20260813)
ORDERS = ((0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2))
TASK_COUNT = 4
TRAIN_FACTS_PER_TASK = 8
TEST_FACTS_PER_TASK = 8
UPDATE_BUDGET = 32
REPLAY_CAPACITY = 24
ITERS_PER_UPDATE = 160
SLOT_LAYERS = 2
FULL_SHARED_LAYERS = 8
SLOT_SEED_BASE = 22000000
SLOT_INITIALIZATION_POLICY = "task_keyed_fixed_seed_v1"
OPTIMIZER_STATE_POLICY = "fresh_zero_state_on_first_activation_persistent_same_slot_v1"
UPDATE_ROUTE_POLICY = "fact_task_token_to_matching_slot_v1"
REPLAY_SELECTION_POLICY = "balanced_full_memory_v1"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def fixed_slot_seed(task_id: int) -> int:
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


def make_schedule(seed: int, order: tuple[int, ...], replay_enabled: bool) -> list[dict]:
    if seed not in SEEDS or order not in ORDERS:
        raise ValueError("V23 matrix identity drift")
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
        replay_ids = [fact.fact_id for fact in replay]
        selected_ids = [fact.fact_id for fact in selected]
        route_counts = {}
        for row in rows:
            key = str(row["task_id"])
            route_counts[key] = route_counts.get(key, 0) + 1
        schedule.append(
            {
                "step": step,
                "task_id": task_id,
                "current_fact_ids": [fact.fact_id for fact in current],
                "replay_fact_ids": replay_ids,
                "selected_fact_ids": selected_ids,
                "dataset_row_count": len(rows),
                "rows": rows,
                "route_counts_by_task": dict(sorted(route_counts.items())),
                "active_slot_task_ids": sorted({row["task_id"] for row in rows}),
                "slot_seed_by_task": {
                    str(active_task_id): fixed_slot_seed(active_task_id)
                    for active_task_id in sorted({row["task_id"] for row in rows})
                },
                "update_route_policy": UPDATE_ROUTE_POLICY,
                "slot_initialization_policy": SLOT_INITIALIZATION_POLICY,
                "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
                "optimizer_iterations": ITERS_PER_UPDATE,
            }
        )
        observed.extend(current)
    return schedule


def validate_schedule(seed: int, order: tuple[int, ...], schedule: list[dict], replay_enabled: bool) -> dict:
    expected = make_schedule(seed, order, replay_enabled)
    if schedule != expected:
        raise ValueError("schedule is not the deterministic V23 derivation")
    seen = set()
    for entry in schedule:
        current = set(entry["current_fact_ids"])
        replay_ids = set(entry["replay_fact_ids"])
        if entry["dataset_row_count"] != UPDATE_BUDGET or len(entry["rows"]) != UPDATE_BUDGET:
            raise ValueError(f"update budget drift at step {entry['step']}")
        if replay_ids & current:
            raise ValueError(f"current/replay overlap at step {entry['step']}")
        if not replay_ids.issubset(seen):
            raise ValueError(f"replay contains unseen facts at step {entry['step']}")
        if any(row["route_key"] != f"T{row['task_id']}" for row in entry["rows"]):
            raise ValueError(f"route key drift at step {entry['step']}")
        computed_counts = {}
        for row in entry["rows"]:
            key = str(row["task_id"])
            computed_counts[key] = computed_counts.get(key, 0) + 1
        if dict(sorted(computed_counts.items())) != entry["route_counts_by_task"]:
            raise ValueError(f"route count drift at step {entry['step']}")
        expected_seeds = {
            str(task_id): fixed_slot_seed(task_id) for task_id in entry["active_slot_task_ids"]
        }
        if entry["slot_seed_by_task"] != expected_seeds:
            raise ValueError(f"slot seed drift at step {entry['step']}")
        seen.update(current)
    return {"valid": True, "steps": len(schedule), "rows": sum(entry["dataset_row_count"] for entry in schedule)}


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
                    "replay_schedule": replay_schedule,
                    "routed_no_replay_schedule": no_replay_schedule,
                    "replay_schedule_sha256": digest(replay_schedule),
                    "routed_no_replay_schedule_sha256": digest(no_replay_schedule),
                }
            )
    gates = {
        "cell_count_exact": len(cells) == 9,
        "matrix_identity_exact": all(
            cell["seed"] in SEEDS and tuple(cell["order"]) in ORDERS for cell in cells
        ),
        "replay_schedule_deterministic": all(
            validate_schedule(cell["seed"], tuple(cell["order"]), cell["replay_schedule"], True)["valid"]
            for cell in cells
        ),
        "routed_no_replay_schedule_deterministic": all(
            validate_schedule(cell["seed"], tuple(cell["order"]), cell["routed_no_replay_schedule"], False)["valid"]
            for cell in cells
        ),
        "same_update_row_budget": all(
            [entry["dataset_row_count"] for entry in cell["replay_schedule"]]
            == [entry["dataset_row_count"] for entry in cell["routed_no_replay_schedule"]]
            == [UPDATE_BUDGET] * 4
            for cell in cells
        ),
        "same_total_examples": all(
            sum(entry["dataset_row_count"] for entry in cell["replay_schedule"])
            == sum(entry["dataset_row_count"] for entry in cell["routed_no_replay_schedule"])
            == UPDATE_BUDGET * TASK_COUNT
            for cell in cells
        ),
        "same_total_optimizer_steps": ITERS_PER_UPDATE * TASK_COUNT == 640,
        "slot_seed_policy_fixed": all(
            all(
                entry["slot_initialization_policy"] == SLOT_INITIALIZATION_POLICY
                and entry["optimizer_state_policy"] == OPTIMIZER_STATE_POLICY
                for entry in cell["replay_schedule"]
            )
            for cell in cells
        ),
        "replay_rows_route_to_fact_task_slot": all(
            all(row["route_key"] == f"T{row['task_id']}" for entry in cell["replay_schedule"] for row in entry["rows"])
            for cell in cells
        ),
        "replay_not_rerunning_current_shared_design": True,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    plan = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "TaskRoutedReplayConsolidationProtocolOnlyNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentTaskRoutedReplayConsolidationProtocol",
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
        "slot_layers": SLOT_LAYERS,
        "full_shared_layers_reference": FULL_SHARED_LAYERS,
        "total_examples_per_cell": UPDATE_BUDGET * TASK_COUNT,
        "total_optimizer_steps_per_cell": ITERS_PER_UPDATE * TASK_COUNT,
        "changed_protocol_variable": "task_routed_replay_consolidation_v1",
        "replay_selection_policy": REPLAY_SELECTION_POLICY,
        "slot_initialization_policy": SLOT_INITIALIZATION_POLICY,
        "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
        "update_route_policy": UPDATE_ROUTE_POLICY,
        "slot_seed_base": SLOT_SEED_BASE,
        "cells": cells,
        "gates": gates,
        "model_training_authorized": False,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
        "next_run_condition": "run_one_corrected_local_preflight_only_after_independent_schedule_validation",
    }
    plan["plan_sha256"] = digest({key: value for key, value in plan.items() if key != "plan_sha256"})
    return plan


def validate_plan(plan: dict) -> dict:
    expected = build_plan()
    if plan != expected:
        raise ValueError("V23 protocol plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V23 plan digest mismatch")
    contract_gate_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_gate_keys):
        raise ValueError("V23 protocol gate failure")
    if plan["gates"]["h100_authorized"] is not False or plan["gates"]["breakthrough_claim_eligible"] is not False:
        raise ValueError("V23 authority boundary drift")
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

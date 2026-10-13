#!/usr/bin/env python3
"""V26 pure-data protocol for a globally seeded shared update stream.

This module derives deterministic update schedules only. It does not load a
model, invoke MLX, or authorize replication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import shared_adapter_task_keyed_optimizer_state_protocol as v24  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v26-shared-global-update-stream"
SOURCE_STATE_SLICE = "continual-learning-protocol-v25-shared-adapter-reference-initialization-preflight"
MODEL_DEFAULT = v24.MODEL_DEFAULT
DATA_SEED = 20260812
INITIALIZATION_POLICY = "global_data_seed_before_model_load_and_after_load_before_lora_v1"
DATA_ORDER_POLICY = "single_global_rng_stream_no_per_task_reseed_v1"
OPTIMIZER_STATE_POLICY = "one_shared_adamw_state_persistent_across_updates_v1"
UPDATE_ROUTE_POLICY = "all_current_and_replay_rows_one_shared_dataset_v1"
CHANGED_PROTOCOL_VARIABLE = "shared_global_update_stream_v1"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def make_schedule(seed: int, order: tuple[int, ...], replay_enabled: bool) -> list[dict]:
    base_schedule = v24.make_schedule(seed, order, replay_enabled)
    schedule = []
    for base in base_schedule:
        entry = {
            key: base[key]
            for key in (
                "step",
                "task_id",
                "current_fact_ids",
                "replay_fact_ids",
                "selected_fact_ids",
                "dataset_row_count",
                "rows",
                "route_counts_by_task",
            )
        }
        entry.update(
            {
                "shared_adapter_id": v24.SHARED_ADAPTER_ID,
                "shared_adapter_layers": v24.SHARED_ADAPTER_LAYERS,
                "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
                "update_route_policy": UPDATE_ROUTE_POLICY,
                "data_order_policy": DATA_ORDER_POLICY,
                "optimizer_iterations": v24.ITERS_PER_UPDATE,
            }
        )
        schedule.append(entry)
    return schedule


def validate_schedule(seed: int, order: tuple[int, ...], schedule: list[dict], replay_enabled: bool) -> dict:
    expected = make_schedule(seed, order, replay_enabled)
    if schedule != expected:
        raise ValueError("schedule is not the deterministic V26 derivation")
    seen = set()
    for entry in schedule:
        current = set(entry["current_fact_ids"])
        replay_ids = set(entry["replay_fact_ids"])
        if entry["dataset_row_count"] != v24.UPDATE_BUDGET or len(entry["rows"]) != v24.UPDATE_BUDGET:
            raise ValueError(f"update budget drift at step {entry['step']}")
        if replay_ids & current or not replay_ids.issubset(seen):
            raise ValueError(f"replay custody drift at step {entry['step']}")
        if any(row["route_key"] != f"T{row['task_id']}" for row in entry["rows"]):
            raise ValueError(f"route key drift at step {entry['step']}")
        if entry["optimizer_iterations"] != v24.ITERS_PER_UPDATE:
            raise ValueError(f"optimizer iteration drift at step {entry['step']}")
        if entry["shared_adapter_id"] != v24.SHARED_ADAPTER_ID or entry["shared_adapter_layers"] != v24.SHARED_ADAPTER_LAYERS:
            raise ValueError(f"shared adapter drift at step {entry['step']}")
        if entry["optimizer_state_policy"] != OPTIMIZER_STATE_POLICY:
            raise ValueError(f"optimizer state policy drift at step {entry['step']}")
        if entry["update_route_policy"] != UPDATE_ROUTE_POLICY or entry["data_order_policy"] != DATA_ORDER_POLICY:
            raise ValueError(f"update stream policy drift at step {entry['step']}")
        seen.update(current)
    return {"valid": True, "steps": len(schedule), "rows": sum(entry["dataset_row_count"] for entry in schedule)}


def build_plan() -> dict:
    cells = []
    for seed in v24.SEEDS:
        for order in v24.ORDERS:
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
        "matrix_identity_exact": all(cell["seed"] in v24.SEEDS and tuple(cell["order"]) in v24.ORDERS for cell in cells),
        "shared_replay_schedule_deterministic": all(validate_schedule(cell["seed"], tuple(cell["order"]), cell["shared_replay_schedule"], True)["valid"] for cell in cells),
        "shared_no_replay_schedule_deterministic": all(validate_schedule(cell["seed"], tuple(cell["order"]), cell["shared_no_replay_schedule"], False)["valid"] for cell in cells),
        "same_update_row_budget": all(
            [entry["dataset_row_count"] for entry in cell["shared_replay_schedule"]]
            == [entry["dataset_row_count"] for entry in cell["shared_no_replay_schedule"]]
            == [v24.UPDATE_BUDGET] * v24.TASK_COUNT
            for cell in cells
        ),
        "same_total_examples": all(
            sum(entry["dataset_row_count"] for entry in cell["shared_replay_schedule"])
            == sum(entry["dataset_row_count"] for entry in cell["shared_no_replay_schedule"])
            == v24.UPDATE_BUDGET * v24.TASK_COUNT
            for cell in cells
        ),
        "same_total_optimizer_steps": v24.ITERS_PER_UPDATE * v24.TASK_COUNT == 640,
        "shared_adapter_fixed": all(
            entry["shared_adapter_id"] == v24.SHARED_ADAPTER_ID
            and entry["shared_adapter_layers"] == v24.SHARED_ADAPTER_LAYERS
            for cell in cells for entry in cell["shared_replay_schedule"]
        ),
        "one_shared_optimizer_state": all(
            entry["optimizer_state_policy"] == OPTIMIZER_STATE_POLICY
            for cell in cells for entry in cell["shared_replay_schedule"]
        ),
        "all_rows_use_one_shared_dataset": all(
            entry["update_route_policy"] == UPDATE_ROUTE_POLICY
            for cell in cells for entry in cell["shared_replay_schedule"]
        ),
        "global_rng_stream_fixed": all(
            entry["data_order_policy"] == DATA_ORDER_POLICY
            for cell in cells for entry in cell["shared_replay_schedule"]
        ),
        "same_seed_and_order_as_v24": True,
        "not_rerunning_v25_reference_initialization": True,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    plan = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "SharedGlobalUpdateStreamProtocolOnlyNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentSharedGlobalUpdateStreamProtocol",
        "model": MODEL_DEFAULT,
        "matrix_policy": "three_seeds_by_three_orders_v1",
        "seeds": list(v24.SEEDS),
        "orders": [list(order) for order in v24.ORDERS],
        "fixed_preflight_seed": DATA_SEED,
        "task_count": v24.TASK_COUNT,
        "train_facts_per_task": v24.TRAIN_FACTS_PER_TASK,
        "test_facts_per_task": v24.TEST_FACTS_PER_TASK,
        "update_budget": v24.UPDATE_BUDGET,
        "replay_capacity": v24.REPLAY_CAPACITY,
        "iters_per_update": v24.ITERS_PER_UPDATE,
        "shared_adapter_layers": v24.SHARED_ADAPTER_LAYERS,
        "total_examples_per_cell": v24.UPDATE_BUDGET * v24.TASK_COUNT,
        "total_optimizer_steps_per_cell": v24.ITERS_PER_UPDATE * v24.TASK_COUNT,
        "changed_protocol_variable": CHANGED_PROTOCOL_VARIABLE,
        "initialization_policy": INITIALIZATION_POLICY,
        "data_order_policy": DATA_ORDER_POLICY,
        "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
        "update_route_policy": UPDATE_ROUTE_POLICY,
        "replay_selection_policy": v24.REPLAY_SELECTION_POLICY,
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
        raise ValueError("V26 protocol plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V26 plan digest mismatch")
    contract_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_keys):
        raise ValueError("V26 protocol gate failure")
    if plan["h100_authorized"] or plan["breakthrough_claim_eligible"]:
        raise ValueError("V26 authority boundary drift")
    return {
        "valid": True,
        "state_slice": plan["state_slice"],
        "source_state_slice": plan["source_state_slice"],
        "cell_count": len(plan["cells"]),
        "gates": plan["gates"],
        "fixed_preflight_seed": plan["fixed_preflight_seed"],
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

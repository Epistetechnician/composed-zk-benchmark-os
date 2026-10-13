#!/usr/bin/env python3
"""V27 pure-data protocol for fresh replication of V26."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import shared_adapter_task_keyed_optimizer_state_protocol as v24  # noqa: E402
from experiments.continual_learning import shared_global_update_stream_protocol as v26  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v27-shared-global-update-stream-replication"
SOURCE_STATE_SLICE = "continual-learning-protocol-v26-shared-global-update-stream-preflight"
MODEL_DEFAULT = v24.MODEL_DEFAULT
ANCHOR_SEED = v26.DATA_SEED
ANCHOR_ORDER = (0, 1, 2, 3)
SEEDS = v24.SEEDS
ORDERS = v24.ORDERS
REPLICATION_CELLS = tuple(
    (seed, order)
    for seed in SEEDS
    for order in ORDERS
    if (seed, order) != (ANCHOR_SEED, ANCHOR_ORDER)
)
CHANGED_PROTOCOL_VARIABLE = "v26_shared_global_update_stream_replication_v1"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def make_cell(seed: int, order: tuple[int, ...]) -> dict:
    if seed not in SEEDS or order not in ORDERS:
        raise ValueError("V27 replication matrix identity drift")
    replay_schedule = v26.make_schedule(seed, order, True)
    no_replay_schedule = v26.make_schedule(seed, order, False)
    return {
        "cell": f"seed-{seed}-order-{''.join(str(value) for value in order)}",
        "seed": seed,
        "order": list(order),
        "execution_kind": "fresh_replication",
        "shared_replay_schedule": replay_schedule,
        "shared_no_replay_schedule": no_replay_schedule,
        "shared_replay_schedule_sha256": digest(replay_schedule),
        "shared_no_replay_schedule_sha256": digest(no_replay_schedule),
    }


def build_plan() -> dict:
    cells = [make_cell(seed, order) for seed, order in REPLICATION_CELLS]
    anchor = {
        "cell": f"seed-{ANCHOR_SEED}-order-{''.join(str(value) for value in ANCHOR_ORDER)}",
        "seed": ANCHOR_SEED,
        "order": list(ANCHOR_ORDER),
        "execution_kind": "development_anchor_not_rerun",
    }
    gates = {
        "replication_cell_count_exact": len(cells) == 8,
        "anchor_identity_exact": (ANCHOR_SEED, ANCHOR_ORDER) not in REPLICATION_CELLS,
        "all_matrix_identities_exact": all(cell["seed"] in SEEDS and tuple(cell["order"]) in ORDERS for cell in cells),
        "no_duplicate_fresh_cells": len({(cell["seed"], tuple(cell["order"])) for cell in cells}) == 8,
        "fresh_cells_exclude_anchor": all((cell["seed"], tuple(cell["order"])) != (ANCHOR_SEED, ANCHOR_ORDER) for cell in cells),
        "same_seed_order_matrix_as_v26": set((cell["seed"], tuple(cell["order"])) for cell in cells) | {(ANCHOR_SEED, ANCHOR_ORDER)} == set((seed, order) for seed in SEEDS for order in ORDERS),
        "same_total_examples": all(
            sum(entry["dataset_row_count"] for entry in cell["shared_replay_schedule"])
            == sum(entry["dataset_row_count"] for entry in cell["shared_no_replay_schedule"])
            == 128
            for cell in cells
        ),
        "same_total_optimizer_steps": all(
            sum(entry["optimizer_iterations"] for entry in cell["shared_replay_schedule"])
            == sum(entry["optimizer_iterations"] for entry in cell["shared_no_replay_schedule"])
            == 640
            for cell in cells
        ),
        "same_update_row_budget": all(
            [entry["dataset_row_count"] for entry in cell["shared_replay_schedule"]]
            == [entry["dataset_row_count"] for entry in cell["shared_no_replay_schedule"]]
            == [32, 32, 32, 32]
            for cell in cells
        ),
        "not_rerunning_v26_anchor": True,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    plan = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "SharedGlobalUpdateStreamReplicationProtocolOnlyNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentSharedGlobalUpdateStreamReplicationProtocol",
        "model": MODEL_DEFAULT,
        "matrix_policy": "three_seeds_by_three_orders_with_preflight_anchor_excluded_v1",
        "seeds": list(SEEDS),
        "orders": [list(order) for order in ORDERS],
        "anchor": anchor,
        "replication_cells": cells,
        "replication_cell_count": len(cells),
        "task_count": v24.TASK_COUNT,
        "train_facts_per_task": v24.TRAIN_FACTS_PER_TASK,
        "test_facts_per_task": v24.TEST_FACTS_PER_TASK,
        "update_budget": v24.UPDATE_BUDGET,
        "replay_capacity": v24.REPLAY_CAPACITY,
        "iters_per_update": v24.ITERS_PER_UPDATE,
        "shared_adapter_layers": v24.SHARED_ADAPTER_LAYERS,
        "total_examples_per_cell": 128,
        "total_optimizer_steps_per_cell": 640,
        "changed_protocol_variable": CHANGED_PROTOCOL_VARIABLE,
        "source_protocol_variable": v26.CHANGED_PROTOCOL_VARIABLE,
        "initialization_policy": v26.INITIALIZATION_POLICY,
        "data_order_policy": v26.DATA_ORDER_POLICY,
        "optimizer_state_policy": v26.OPTIMIZER_STATE_POLICY,
        "update_route_policy": v26.UPDATE_ROUTE_POLICY,
        "replay_selection_policy": v24.REPLAY_SELECTION_POLICY,
        "gates": gates,
        "model_training_authorized": False,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
        "next_run_condition": "run_exactly_eight_fresh_cells_after_anchor_validation",
    }
    plan["plan_sha256"] = digest({key: value for key, value in plan.items() if key != "plan_sha256"})
    return plan


def validate_plan(plan: dict) -> dict:
    expected = build_plan()
    if plan != expected:
        raise ValueError("V27 protocol plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V27 plan digest mismatch")
    contract_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_keys):
        raise ValueError("V27 protocol gate failure")
    if plan["h100_authorized"] or plan["breakthrough_claim_eligible"]:
        raise ValueError("V27 authority boundary drift")
    return {
        "valid": True,
        "state_slice": plan["state_slice"],
        "source_state_slice": plan["source_state_slice"],
        "replication_cell_count": plan["replication_cell_count"],
        "anchor": plan["anchor"],
        "gates": plan["gates"],
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

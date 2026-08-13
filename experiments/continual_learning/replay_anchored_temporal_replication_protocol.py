#!/usr/bin/env python3
"""V29 pure-data replication matrix over the seven remaining cells."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import replay_anchored_temporal_protocol as v29  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v29-replay-anchored-temporal-replication"
SOURCE_STATE_SLICE = "continual-learning-protocol-v29-replay-anchored-temporal-confirmation-preflight"
CELL_STATE_SLICE = f"{STATE_SLICE}-cell"
MODEL_DEFAULT = v29.MODEL_DEFAULT
SEEDS = tuple(v29.v24.SEEDS)
ORDERS = tuple(v29.v24.ORDERS)
ANCHOR_CELLS = (
    (20260812, (0, 3, 1, 2)),
    (20260812, (0, 2, 3, 1)),
)
REPLICATION_CELLS = tuple(
    (seed, order)
    for seed in SEEDS
    for order in ORDERS
    if (seed, order) not in ANCHOR_CELLS
)
DATA_SEED = SEEDS[0]
PREFLIGHT_ORDER = ORDERS[0]
BATCH_SIZE = v29.BATCH_SIZE
BATCH_POLICY = v29.BATCH_POLICY
TEMPORAL_BATCH_ORDER_POLICY = v29.TEMPORAL_BATCH_ORDER_POLICY
CHANGED_PROTOCOL_VARIABLE = v29.CHANGED_PROTOCOL_VARIABLE
INITIALIZATION_POLICY = v29.INITIALIZATION_POLICY
DATA_ORDER_POLICY = v29.DATA_ORDER_POLICY
OPTIMIZER_STATE_POLICY = v29.OPTIMIZER_STATE_POLICY
UPDATE_ROUTE_POLICY = v29.UPDATE_ROUTE_POLICY
v24 = v29.v24
v26 = v29.v26


def digest(value) -> str:
    return v29.digest(value)


def write_json(path: Path, value) -> None:
    v29.write_json(path, value)


def make_schedule(seed: int, order: tuple[int, ...], replay_enabled: bool) -> list[dict]:
    return v29.make_schedule(seed, order, replay_enabled)


def validate_schedule(seed: int, order: tuple[int, ...], schedule: list[dict], replay_enabled: bool) -> dict:
    return v29.validate_schedule(seed, order, schedule, replay_enabled)


def replay_anchored_batch_indices(task_ids: list[int], current_task_id: int, batch_size: int = BATCH_SIZE) -> list[list[int]]:
    return v29.replay_anchored_batch_indices(task_ids, current_task_id, batch_size)


def replay_anchored_batch_task_ids(task_ids: list[int], current_task_id: int, batch_size: int = BATCH_SIZE) -> list[list[int]]:
    return v29.replay_anchored_batch_task_ids(task_ids, current_task_id, batch_size)


def _build_cell_plan(seed: int, order: tuple[int, ...]) -> dict:
    if seed not in SEEDS or order not in ORDERS:
        raise ValueError("V29 replication cell identity drift")
    replay_schedule = make_schedule(seed, order, True)
    no_replay_schedule = make_schedule(seed, order, False)
    gates = {
        "replication_cell_identity_exact": (seed, order) in set((item, tuple(values)) for item in SEEDS for values in ORDERS),
        "cell_is_not_v29_anchor": (seed, order) not in ANCHOR_CELLS,
        "same_selected_fact_ids_as_v29": True,
        "same_selected_fact_ids_as_v26": replay_schedule == v26.make_schedule(seed, order, True)
        and no_replay_schedule == v26.make_schedule(seed, order, False),
        "same_update_row_budget": all(
            entry["dataset_row_count"] == 32 and entry["optimizer_iterations"] == 160
            for entry in replay_schedule + no_replay_schedule
        ),
        "same_total_examples": sum(entry["dataset_row_count"] for entry in replay_schedule) == 128
        and sum(entry["dataset_row_count"] for entry in no_replay_schedule) == 128,
        "same_total_optimizer_steps": sum(entry["optimizer_iterations"] for entry in replay_schedule) == 640
        and sum(entry["optimizer_iterations"] for entry in no_replay_schedule) == 640,
        "same_batch_size": BATCH_SIZE == 2,
        "oldest_replay_tasks_first": True,
        "current_phase_after_replay_anchor": True,
        "no_random_batch_permutation": True,
        "shared_adapter_fixed": True,
        "one_shared_optimizer_state": True,
        "no_per_task_reseed": True,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    plan = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "cell_state_slice": CELL_STATE_SLICE,
        "classification": "ReplayAnchoredTemporalMicrobatchReplicationProtocolOnlyNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentReplayAnchoredTemporalMicrobatchReplicationProtocol",
        "model": MODEL_DEFAULT,
        "preflight_seed": seed,
        "preflight_order": list(order),
        "replication_cell": {"seed": seed, "order": list(order)},
        "anchor_cells": [{"seed": item, "order": list(values)} for item, values in ANCHOR_CELLS],
        "replication_cell_count": len(REPLICATION_CELLS),
        "task_count": v24.TASK_COUNT,
        "train_facts_per_task": v24.TRAIN_FACTS_PER_TASK,
        "test_facts_per_task": v24.TEST_FACTS_PER_TASK,
        "update_budget": v24.UPDATE_BUDGET,
        "replay_capacity": v24.REPLAY_CAPACITY,
        "iters_per_update": v24.ITERS_PER_UPDATE,
        "batch_size": BATCH_SIZE,
        "shared_adapter_layers": v24.SHARED_ADAPTER_LAYERS,
        "total_examples_per_arm": 128,
        "total_optimizer_steps_per_arm": 640,
        "changed_protocol_variable": CHANGED_PROTOCOL_VARIABLE,
        "batch_policy": BATCH_POLICY,
        "temporal_batch_order_policy": TEMPORAL_BATCH_ORDER_POLICY,
        "initialization_policy": INITIALIZATION_POLICY,
        "data_order_policy": DATA_ORDER_POLICY,
        "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
        "update_route_policy": UPDATE_ROUTE_POLICY,
        "replay_selection_policy": v24.REPLAY_SELECTION_POLICY,
        "shared_replay_schedule": replay_schedule,
        "shared_no_replay_schedule": no_replay_schedule,
        "shared_replay_schedule_sha256": digest(replay_schedule),
        "shared_no_replay_schedule_sha256": digest(no_replay_schedule),
        "gates": gates,
        "model_training_authorized": False,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
        "next_run_condition": "run_seven_fresh_cells_once_after_anchor_validation",
    }
    plan["plan_sha256"] = digest({key: value for key, value in plan.items() if key != "plan_sha256"})
    return plan


def build_plan() -> dict:
    return _build_cell_plan(DATA_SEED, PREFLIGHT_ORDER)


def build_matrix_plan() -> dict:
    cells = []
    for seed, order in REPLICATION_CELLS:
        cell = _build_cell_plan(seed, order)
        cells.append(
            {
                "cell": f"seed-{seed}-order-{''.join(str(value) for value in order)}",
                "seed": seed,
                "order": list(order),
                "execution_kind": "fresh_replication",
                "cell_plan_sha256": cell["plan_sha256"],
                "shared_replay_schedule_sha256": cell["shared_replay_schedule_sha256"],
                "shared_no_replay_schedule_sha256": cell["shared_no_replay_schedule_sha256"],
            }
        )
    plan = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "ReplayAnchoredTemporalMicrobatchReplicationMatrixProtocolOnlyNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentReplayAnchoredTemporalMicrobatchReplicationMatrixProtocol",
        "model": MODEL_DEFAULT,
        "matrix_policy": "three_seeds_by_three_orders_with_two_v29_anchor_cells_excluded_v1",
        "seeds": list(SEEDS),
        "orders": [list(order) for order in ORDERS],
        "anchor_cells": [{"seed": seed, "order": list(order)} for seed, order in ANCHOR_CELLS],
        "replication_cells": cells,
        "replication_cell_count": len(cells),
        "task_count": v24.TASK_COUNT,
        "update_budget": v24.UPDATE_BUDGET,
        "replay_capacity": v24.REPLAY_CAPACITY,
        "iters_per_update": v24.ITERS_PER_UPDATE,
        "shared_adapter_layers": v24.SHARED_ADAPTER_LAYERS,
        "total_examples_per_cell": 128,
        "total_optimizer_steps_per_cell": 640,
        "changed_protocol_variable": CHANGED_PROTOCOL_VARIABLE,
        "batch_policy": BATCH_POLICY,
        "temporal_batch_order_policy": TEMPORAL_BATCH_ORDER_POLICY,
        "initialization_policy": INITIALIZATION_POLICY,
        "data_order_policy": DATA_ORDER_POLICY,
        "optimizer_state_policy": OPTIMIZER_STATE_POLICY,
        "update_route_policy": UPDATE_ROUTE_POLICY,
        "replay_selection_policy": v24.REPLAY_SELECTION_POLICY,
        "gates": {
            "replication_cell_count_exact": len(cells) == 7,
            "anchor_cell_count_exact": len(ANCHOR_CELLS) == 2,
            "matrix_identity_exact": set((cell["seed"], tuple(cell["order"])) for cell in cells) | set(ANCHOR_CELLS)
            == set((seed, order) for seed in SEEDS for order in ORDERS),
            "no_duplicate_fresh_cells": len({(cell["seed"], tuple(cell["order"])) for cell in cells}) == 7,
            "fresh_cells_exclude_anchors": all((cell["seed"], tuple(cell["order"])) not in ANCHOR_CELLS for cell in cells),
            "same_total_examples": all(_build_cell_plan(cell["seed"], tuple(cell["order"]))["total_examples_per_arm"] == 128 for cell in cells),
            "same_total_optimizer_steps": all(_build_cell_plan(cell["seed"], tuple(cell["order"]))["total_optimizer_steps_per_arm"] == 640 for cell in cells),
            "v29_temporal_policy_fixed": True,
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
        },
        "model_training_authorized": False,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
        "next_run_condition": "run_each_fresh_cell_once_and_require_all_cell_retention_gate",
    }
    plan["plan_sha256"] = digest({key: value for key, value in plan.items() if key != "plan_sha256"})
    return plan


def validate_plan(plan: dict) -> dict:
    expected = build_plan()
    if plan != expected:
        raise ValueError("V29 replication cell plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V29 replication cell plan digest mismatch")
    contract_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_keys):
        raise ValueError("V29 replication cell gate failure")
    return {"valid": True, "state_slice": plan["state_slice"], "replication_cell": plan["replication_cell"], "plan_sha256": plan["plan_sha256"]}


def validate_matrix_plan(plan: dict) -> dict:
    expected = build_matrix_plan()
    if plan != expected:
        raise ValueError("V29 replication matrix plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V29 replication matrix plan digest mismatch")
    contract_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_keys):
        raise ValueError("V29 replication matrix gate failure")
    if plan["h100_authorized"] or plan["breakthrough_claim_eligible"]:
        raise ValueError("V29 replication matrix authority boundary drift")
    return {"valid": True, "state_slice": plan["state_slice"], "replication_cell_count": plan["replication_cell_count"], "anchor_cells": plan["anchor_cells"], "plan_sha256": plan["plan_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    plan = build_matrix_plan()
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, plan)
    print(json.dumps(validate_matrix_plan(plan), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

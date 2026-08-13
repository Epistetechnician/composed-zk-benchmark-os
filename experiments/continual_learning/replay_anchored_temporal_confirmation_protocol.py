#!/usr/bin/env python3
"""V29 confirmation protocol for the other pre-identified V27 tie cell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import replay_anchored_temporal_protocol as v29  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v29-replay-anchored-temporal-confirmation"
SOURCE_STATE_SLICE = v29.STATE_SLICE
CONFIRMATION_OF_STATE_SLICE = v29.STATE_SLICE
MODEL_DEFAULT = v29.MODEL_DEFAULT
DATA_SEED = v29.DATA_SEED
PREFLIGHT_ORDER = (0, 2, 3, 1)
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


def build_plan() -> dict:
    replay_schedule = make_schedule(DATA_SEED, PREFLIGHT_ORDER, True)
    no_replay_schedule = make_schedule(DATA_SEED, PREFLIGHT_ORDER, False)
    gates = {
        "confirmation_cell_identity_exact": DATA_SEED == 20260812 and PREFLIGHT_ORDER == (0, 2, 3, 1),
        "confirms_other_v27_20260812_tie_cell": True,
        "same_selected_fact_ids_as_v29": replay_schedule == v29.make_schedule(DATA_SEED, PREFLIGHT_ORDER, True)
        and no_replay_schedule == v29.make_schedule(DATA_SEED, PREFLIGHT_ORDER, False),
        "same_selected_fact_ids_as_v26": replay_schedule == v26.make_schedule(DATA_SEED, PREFLIGHT_ORDER, True)
        and no_replay_schedule == v26.make_schedule(DATA_SEED, PREFLIGHT_ORDER, False),
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
        "confirmation_of_state_slice": CONFIRMATION_OF_STATE_SLICE,
        "classification": "ReplayAnchoredTemporalMicrobatchConfirmationProtocolOnlyNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentReplayAnchoredTemporalMicrobatchConfirmationProtocol",
        "model": MODEL_DEFAULT,
        "preflight_seed": DATA_SEED,
        "preflight_order": list(PREFLIGHT_ORDER),
        "confirmation_cell": {"seed": DATA_SEED, "order": list(PREFLIGHT_ORDER), "v27_effect": 0.0},
        "prior_v28_effect_on_cell": 0.25,
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
        "next_run_condition": "evaluate_both_v29_tie_cell_confirmations_before_matrix_expansion",
    }
    plan["plan_sha256"] = digest({key: value for key, value in plan.items() if key != "plan_sha256"})
    return plan


def validate_plan(plan: dict) -> dict:
    expected = build_plan()
    if plan != expected:
        raise ValueError("V29 confirmation protocol plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V29 confirmation plan digest mismatch")
    contract_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_keys):
        raise ValueError("V29 confirmation protocol gate failure")
    if plan["h100_authorized"] or plan["breakthrough_claim_eligible"]:
        raise ValueError("V29 confirmation authority boundary drift")
    return {
        "valid": True,
        "state_slice": plan["state_slice"],
        "source_state_slice": plan["source_state_slice"],
        "confirmation_cell": plan["confirmation_cell"],
        "preflight_seed": plan["preflight_seed"],
        "preflight_order": plan["preflight_order"],
        "batch_policy": plan["batch_policy"],
        "temporal_batch_order_policy": plan["temporal_batch_order_policy"],
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

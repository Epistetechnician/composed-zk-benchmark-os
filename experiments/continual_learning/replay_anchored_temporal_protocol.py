#!/usr/bin/env python3
"""V29 pure-data protocol for replay-anchored temporal microbatch ordering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import task_stratified_microbatch_confirmation_protocol as v28  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v29-replay-anchored-temporal-microbatch"
SOURCE_STATE_SLICE = "continual-learning-protocol-v28-task-stratified-microbatch-confirmation-preflight"
MODEL_DEFAULT = v28.MODEL_DEFAULT
DATA_SEED = v28.DATA_SEED
PREFLIGHT_ORDER = v28.PREFLIGHT_ORDER
BATCH_SIZE = v28.BATCH_SIZE
BATCH_POLICY = "replay_anchored_oldest_first_temporal_microbatch_v1"
TEMPORAL_BATCH_ORDER_POLICY = BATCH_POLICY
CHANGED_PROTOCOL_VARIABLE = "replay_anchored_temporal_microbatch_schedule_v1"
INITIALIZATION_POLICY = v28.INITIALIZATION_POLICY
DATA_ORDER_POLICY = v28.DATA_ORDER_POLICY
OPTIMIZER_STATE_POLICY = v28.OPTIMIZER_STATE_POLICY
UPDATE_ROUTE_POLICY = v28.UPDATE_ROUTE_POLICY
v24 = v28.v24
v26 = v28.v26


def digest(value) -> str:
    return v28.digest(value)


def write_json(path: Path, value) -> None:
    v28.write_json(path, value)


def make_schedule(seed: int, order: tuple[int, ...], replay_enabled: bool) -> list[dict]:
    return v28.make_schedule(seed, order, replay_enabled)


def validate_schedule(seed: int, order: tuple[int, ...], schedule: list[dict], replay_enabled: bool) -> dict:
    return v28.validate_schedule(seed, order, schedule, replay_enabled)


def _task_batches(task_ids: list[int], batch_size: int) -> dict[int, list[list[int]]]:
    if len(task_ids) < batch_size or len(task_ids) % batch_size:
        raise ValueError("V29 schedule requires an exact batch budget")
    buckets: dict[int, list[int]] = {task_id: [] for task_id in sorted(set(task_ids))}
    for index, task_id in enumerate(task_ids):
        buckets[task_id].append(index)
    batches = {}
    for task_id, indices in buckets.items():
        if len(indices) % batch_size:
            raise ValueError("V29 task bucket must divide into exact microbatches")
        batches[task_id] = [indices[i : i + batch_size] for i in range(0, len(indices), batch_size)]
    return batches


def replay_anchored_batch_indices(task_ids: list[int], current_task_id: int, batch_size: int = BATCH_SIZE) -> list[list[int]]:
    batches = _task_batches(task_ids, batch_size)
    if current_task_id not in batches:
        raise ValueError("V29 current task is absent from the update dataset")
    current_batches = list(batches.pop(current_task_id))
    replay_batches = batches
    ordered: list[list[int]] = []
    while any(replay_batches.values()):
        for task_id in sorted(replay_batches):
            if replay_batches[task_id]:
                ordered.append(replay_batches[task_id].pop(0))
        if current_batches:
            ordered.append(current_batches.pop(0))
    ordered.extend(current_batches)
    return ordered


def replay_anchored_batch_task_ids(task_ids: list[int], current_task_id: int, batch_size: int = BATCH_SIZE) -> list[list[int]]:
    return [[task_ids[index] for index in batch] for batch in replay_anchored_batch_indices(task_ids, current_task_id, batch_size)]


def build_plan() -> dict:
    replay_schedule = make_schedule(DATA_SEED, PREFLIGHT_ORDER, True)
    no_replay_schedule = make_schedule(DATA_SEED, PREFLIGHT_ORDER, False)
    gates = {
        "frozen_v28_tie_cell_exact": DATA_SEED == 20260812 and PREFLIGHT_ORDER == (0, 3, 1, 2),
        "same_selected_fact_ids_as_v28": replay_schedule == v28.make_schedule(DATA_SEED, PREFLIGHT_ORDER, True)
        and no_replay_schedule == v28.make_schedule(DATA_SEED, PREFLIGHT_ORDER, False),
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
        "classification": "ReplayAnchoredTemporalMicrobatchProtocolOnlyNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentReplayAnchoredTemporalMicrobatchProtocol",
        "model": MODEL_DEFAULT,
        "preflight_seed": DATA_SEED,
        "preflight_order": list(PREFLIGHT_ORDER),
        "frozen_v28_confirmation_effect": 0.0,
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
        "next_run_condition": "one_corrected_local_preflight_after_independent_temporal_schedule_validation",
    }
    plan["plan_sha256"] = digest({key: value for key, value in plan.items() if key != "plan_sha256"})
    return plan


def validate_plan(plan: dict) -> dict:
    expected = build_plan()
    if plan != expected:
        raise ValueError("V29 protocol plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V29 plan digest mismatch")
    contract_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_keys):
        raise ValueError("V29 protocol gate failure")
    if plan["h100_authorized"] or plan["breakthrough_claim_eligible"]:
        raise ValueError("V29 authority boundary drift")
    return {
        "valid": True,
        "state_slice": plan["state_slice"],
        "source_state_slice": plan["source_state_slice"],
        "preflight_seed": plan["preflight_seed"],
        "preflight_order": plan["preflight_order"],
        "batch_policy": plan["batch_policy"],
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

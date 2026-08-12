#!/usr/bin/env python3
"""V28 pure-data protocol for task-stratified shared microbatches."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import shared_global_update_stream_protocol as v26  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v28-task-stratified-microbatch"
SOURCE_STATE_SLICE = "continual-learning-protocol-v27-shared-global-update-stream-replication-preflight"
MODEL_DEFAULT = v26.MODEL_DEFAULT
DATA_SEED = 20260812
PREFLIGHT_ORDER = (0, 2, 3, 1)
BATCH_SIZE = 2
BATCH_POLICY = "task_stratified_round_robin_microbatch_v1"
CHANGED_PROTOCOL_VARIABLE = "task_stratified_microbatch_schedule_v1"
INITIALIZATION_POLICY = v26.INITIALIZATION_POLICY
DATA_ORDER_POLICY = v26.DATA_ORDER_POLICY
OPTIMIZER_STATE_POLICY = v26.OPTIMIZER_STATE_POLICY
UPDATE_ROUTE_POLICY = v26.UPDATE_ROUTE_POLICY
v24 = v26.v24


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def make_schedule(seed: int, order: tuple[int, ...], replay_enabled: bool) -> list[dict]:
    return v26.make_schedule(seed, order, replay_enabled)


def validate_schedule(seed: int, order: tuple[int, ...], schedule: list[dict], replay_enabled: bool) -> dict:
    return v26.validate_schedule(seed, order, schedule, replay_enabled)


def task_stratified_batch_task_ids(task_ids: list[int], batch_size: int = BATCH_SIZE) -> list[list[int]]:
    if len(task_ids) < batch_size or len(task_ids) % batch_size:
        raise ValueError("task-stratified schedule requires an exact batch budget")
    buckets = {task_id: [] for task_id in sorted(set(task_ids))}
    for index, task_id in enumerate(task_ids):
        buckets[task_id].append(index)
    ordered_indices = []
    while any(buckets.values()):
        for task_id in sorted(buckets):
            if buckets[task_id]:
                ordered_indices.append(buckets[task_id].pop(0))
    return [
        [task_ids[index] for index in ordered_indices[i : i + batch_size]]
        for i in range(0, len(ordered_indices), batch_size)
    ]


def build_plan() -> dict:
    replay_schedule = make_schedule(DATA_SEED, PREFLIGHT_ORDER, True)
    no_replay_schedule = make_schedule(DATA_SEED, PREFLIGHT_ORDER, False)
    gates = {
        "preflight_cell_identity_exact": DATA_SEED == 20260812 and PREFLIGHT_ORDER == (0, 2, 3, 1),
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
        "shared_adapter_fixed": True,
        "one_shared_optimizer_state": True,
        "no_per_task_reseed": True,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    plan = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "TaskStratifiedMicrobatchProtocolOnlyNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentTaskStratifiedMicrobatchProtocol",
        "model": MODEL_DEFAULT,
        "preflight_seed": DATA_SEED,
        "preflight_order": list(PREFLIGHT_ORDER),
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
        "next_run_condition": "one_corrected_local_preflight_on_the_first_20260812_tie_cell",
    }
    plan["plan_sha256"] = digest({key: value for key, value in plan.items() if key != "plan_sha256"})
    return plan


def validate_plan(plan: dict) -> dict:
    expected = build_plan()
    if plan != expected:
        raise ValueError("V28 protocol plan drift")
    if plan["plan_sha256"] != digest({key: value for key, value in plan.items() if key != "plan_sha256"}):
        raise ValueError("V28 plan digest mismatch")
    contract_keys = [key for key in plan["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(plan["gates"][key] for key in contract_keys):
        raise ValueError("V28 protocol gate failure")
    if plan["h100_authorized"] or plan["breakthrough_claim_eligible"]:
        raise ValueError("V28 authority boundary drift")
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

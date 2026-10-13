#!/usr/bin/env python3
"""Independent validator for the V19 compact task-routed residual preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import validate_route_boundary_representation_preflight as v18


STATE_SLICE = "continual-learning-protocol-v19-task-routed-compact-residual"
SOURCE_STATE_SLICE = "continual-learning-protocol-v18-route-boundary-representation"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    config = json.loads((root / "config.json").read_text())
    result = json.loads((root / "result.json").read_text())
    original = (v18.STATE_SLICE, v18.SOURCE_STATE_SLICE)
    v18.STATE_SLICE = STATE_SLICE
    v18.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    try:
        inherited = v18.validate(root)
    finally:
        v18.STATE_SLICE, v18.SOURCE_STATE_SLICE = original
    if result["state_slice"] != STATE_SLICE or result["source_state_slice"] != SOURCE_STATE_SLICE:
        raise ValueError("V19 state boundary drift")
    if result["result_sha256"] != digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ValueError("result digest mismatch")
    expected_config = {
        "representation_redesign": "route_binding_at_answer_boundary_v1",
        "v19_representation_redesign": "task_routed_compact_residual_v1",
        "task_routing_policy": "task_token_to_compact_slot_v1",
        "compact_slot_count": 4,
        "compact_slot_num_layers": 2,
        "full_shared_num_layers_reference": 8,
        "parameter_budget_policy": "four_slots_times_two_layers_equals_one_shared_eight_layer_adapter_v1",
        "total_optimizer_steps_per_candidate": 640,
        "total_training_examples_per_candidate": 128,
    }
    for key, expected in expected_config.items():
        if config.get(key) != expected:
            raise ValueError(f"V19 config drift: {key}")
    audit = json.loads((root / "audit" / "task_routed_compact_residual.json").read_text())
    tasks = json.loads((root / "tasks.json").read_text())
    task_train_ids = {task["task_id"]: [fact["fact_id"] for fact in task["train_facts"]] for task in tasks}
    if len(audit) != 4 or {entry["route_key"] for entry in audit} != {f"T{task}" for task in range(4)}:
        raise ValueError("compact route audit drift")
    for entry in audit:
        task_id = entry["task_id"]
        if entry["train_fact_ids"] != task_train_ids[task_id] or entry["selected_fact_ids"] != task_train_ids[task_id]:
            raise ValueError(f"compact fact selection drift: task {task_id}")
        if entry["replay_fact_ids"] != [] or entry["replay_counts_by_task"] != {} or entry["dataset_row_count"] != 32:
            raise ValueError(f"compact replay boundary drift: task {task_id}")
        if entry["resumed_from"] is not None or entry["slot_num_layers"] != 2 or entry["target_task_accuracy_after_update"]["n"] != 8:
            raise ValueError(f"compact slot contract drift: task {task_id}")
        adapter = root / entry["adapter_relative_path"] / "adapters.safetensors"
        if not adapter.exists():
            raise ValueError(f"compact adapter missing: task {task_id}")
    candidate = result["task_routed_compact_residual"]
    for endpoint in ("acquisition", "retention_after_interference", "recovery_after_reacquisition"):
        metric = candidate[endpoint]
        if metric["n"] != 8 or not 0 <= metric["accuracy"] <= 1:
            raise ValueError(f"compact metric drift: {endpoint}")
    budget = result["parameter_budget"]
    if budget["full_shared_adapter_bytes"] <= 0 or budget["compact_slot_total_adapter_bytes"] <= 0:
        raise ValueError("parameter budget missing")
    expected_ratio = budget["compact_slot_total_adapter_bytes"] / budget["full_shared_adapter_bytes"]
    if abs(expected_ratio - budget["compact_to_full_bytes_ratio"]) > 1e-12 or budget["matched"] != (0.75 <= expected_ratio <= 1.25):
        raise ValueError("parameter budget ratio drift")
    if result["task_routed_audit_sha256"] != digest(audit):
        raise ValueError("compact audit digest mismatch")
    naive = result["results"]["naive_sequential_lora"]["retention_after_interference"]["accuracy"]
    gates = {
        "task_routed_solvability_floor": candidate["acquisition"]["accuracy"] >= config["solvability_guard_accuracy"],
        "task_routed_retention_above_naive": candidate["retention_after_interference"]["accuracy"] > naive,
        "parameter_budget_matched": budget["matched"],
    }
    if result["v19_candidate_gates"] != gates or result["v19_candidate_eligible"] != all(gates.values()):
        raise ValueError("V19 gate derivation drift")
    if result["breakthrough_claim_eligible"] is not False or result["h100_authorized"] is not False:
        raise ValueError("claim or hardware boundary drift")
    return {"valid": True, "inherited": inherited, "v19_candidate_gates": gates, "v19_candidate_eligible": result["v19_candidate_eligible"], "result_sha256": result["result_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root.resolve()), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

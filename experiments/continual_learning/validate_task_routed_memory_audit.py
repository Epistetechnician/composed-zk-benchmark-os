#!/usr/bin/env python3
"""Independent validator for the V16 task-routed memory audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


STATE_SLICE = "continual-learning-protocol-v16-task-routed-memory-audit"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    report = json.loads((root / "report.json").read_text())
    if report["state_slice"] != STATE_SLICE or report["breakthrough_claim_eligible"] is not False or report["h100_authorized"] is not False:
        raise ValueError("state, claim, or hardware boundary drift")
    if report["report_sha256"] != digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("report digest mismatch")
    if report["fixed_contract_match"] is not True or report["gates"]["fixed_contract_match"] is not True:
        raise ValueError("fixed contract gate drift")
    route = report["route_audit"]
    if route["route_count"] != 4 or route["unique_route_keys"] != 4 or route["route_resolution_passed"] is not True:
        raise ValueError("route audit drift")
    if any(not item["route_key_exact"] or not item["adapter_exists"] or item["resumed_from"] is not None for item in route["routes"]):
        raise ValueError("route resolution drift")
    fixed = report["matched_contract_keys"]
    if fixed != [
        "model", "seed", "order", "task_count", "train_facts_per_task", "test_facts_per_task", "task_rule", "mapping_policy", "split_policy", "solvability_control", "memory_mechanism", "route_policy", "replay_capacity", "update_budget", "current_examples_per_update", "replay_examples_per_update", "replay_policy", "optimizer", "learning_rate", "batch_size", "num_layers", "mask_prompt", "max_seq_length", "fine_tune_type", "audit_schema", "checkpoint_target_task_id", "checkpoint_assessment_context_mode", "solvability_guard_accuracy", "primary_metric", "prompt_contract", "iters", "source_context_removed_for", "assessment_effects_generated_before_prediction_lock", "objective_repair", "baseline_iters", "recovery_iters"
    ]:
        raise ValueError("matched contract key list drift")
    retention = report["retention_comparison"]
    if retention["naive_v14"] != {"correct": 2, "n": 8, "accuracy": 0.25} or retention["shared_replay_v14"] != {"correct": 2, "n": 8, "accuracy": 0.25} or retention["interleaved_replay_v15"] != {"correct": 0, "n": 8, "accuracy": 0.0} or retention["task_adapter_bank_v14"] != {"correct": 8, "n": 8, "accuracy": 1.0}:
        raise ValueError("retention comparison drift")
    if report["gates"] != {
        "bank_retention_above_shared_naive": True,
        "fixed_contract_match": True,
        "interleaved_replay_retention_above_naive": False,
        "route_resolution": True,
        "runtime_or_memory_bottleneck_demonstrated": False,
        "shared_replay_retention_above_naive": False,
    }:
        raise ValueError("gate result drift")
    for version, expected_peak_memory in (("v14", 0.765), ("v15", 0.764)):
        telemetry = report["telemetry"][version]
        storage = report["storage"][version]
        if telemetry["training_log_count"] != 14 or telemetry["peak_memory_gb_max"] != expected_peak_memory or telemetry["it_per_sec_sample_count"] <= 0:
            raise ValueError(f"telemetry drift: {version}")
        if storage["by_strategy"]["task_adapter_bank"]["adapter_file_count"] != 4 or storage["by_strategy"]["task_adapter_bank"]["adapter_bytes"] != 23509180:
            raise ValueError(f"adapter storage drift: {version}")
    return {"valid": True, "claim_ceiling": report["claim_ceiling"], "decision": report["decision"], "h100_authorized": report["h100_authorized"], "report_sha256": report["report_sha256"]}


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

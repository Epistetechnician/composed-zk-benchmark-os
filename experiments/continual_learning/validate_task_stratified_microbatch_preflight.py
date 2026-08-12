#!/usr/bin/env python3
"""Independent validator for the V28 corrected preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import task_stratified_microbatch_preflight as preflight  # noqa: E402
from experiments.continual_learning import task_stratified_microbatch_protocol as protocol  # noqa: E402


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    result = json.loads((root / "result.json").read_text())
    plan = protocol.build_plan()
    if result["state_slice"] != preflight.STATE_SLICE:
        raise ValueError("V28 preflight state slice drift")
    if result["config"]["seed"] != protocol.DATA_SEED or result["config"]["order"] != list(protocol.PREFLIGHT_ORDER):
        raise ValueError("V28 preflight identity drift")
    if result["config"]["total_examples_per_strategy"] != 128 or result["config"]["total_optimizer_steps_per_strategy"] != 640:
        raise ValueError("V28 budget drift")
    if result["batch_policy"] != protocol.BATCH_POLICY:
        raise ValueError("V28 batch policy drift")
    tasks = json.loads((root / "tasks.json").read_text())
    manifest = {
        "config": result["config"],
        "tasks": tasks,
        "byte_reference": result["byte_reference"],
        "results": result["results"],
        "batch_schedule_audit": result["batch_schedule_audit"],
    }
    if result["manifest_sha256"] != digest(manifest):
        raise ValueError("V28 manifest digest mismatch")
    without_digest = dict(result)
    without_digest.pop("result_sha256", None)
    if result["result_sha256"] != digest(without_digest):
        raise ValueError("V28 result digest mismatch")
    training_audits = [audit for audit in result["batch_schedule_audit"] if audit["dataset_example_count"] == 32]
    if len(training_audits) != 24:
        raise ValueError("V28 32-row iterator audit count drift")
    for audit in training_audits:
        if audit["batch_size"] != 2 or audit["batch_count"] != 16:
            raise ValueError("V28 microbatch budget drift")
        flattened = [task_id for batch in audit["batch_task_ids"] for task_id in batch]
        if len(flattened) != 32:
            raise ValueError("V28 microbatch row drift")
        if {str(task_id): flattened.count(task_id) for task_id in sorted(set(flattened))} != audit["task_counts"]:
            raise ValueError("V28 microbatch task-count drift")
        if audit["batch_policy"] != protocol.BATCH_POLICY:
            raise ValueError("V28 audit policy drift")
    for arm in ("shared_replay", "shared_no_replay"):
        metrics = result["results"][arm]
        if metrics["total_training_examples"] != 128 or metrics["total_optimizer_iterations"] != 640:
            raise ValueError(f"V28 {arm} budget drift")
        if not metrics["replay_exposure_verified"] or not metrics["optimizer_state_persistence_verified"]:
            raise ValueError(f"V28 {arm} custody drift")
        if not metrics["parameter_budget"]["matched"]:
            raise ValueError(f"V28 {arm} parameter budget drift")
        for update in metrics["updates"]:
            if update["dataset_row_count"] != 32 or update["optimizer_iterations"] != 160:
                raise ValueError(f"V28 {arm} update budget drift")
            if not update["replay_examples_present_in_training_datasets"]:
                raise ValueError(f"V28 {arm} replay exposure drift")
    if result["h100_authorized"] or result["breakthrough_claim_eligible"]:
        raise ValueError("V28 authority boundary drift")
    return {
        "valid": True,
        "state_slice": result["state_slice"],
        "batch_policy": result["batch_policy"],
        "32_row_iterator_audits": len(training_audits),
        "shared_replay_acquisition": result["results"]["shared_replay"]["target_task_acquisition"]["accuracy"],
        "shared_replay_retention": result["results"]["shared_replay"]["target_task_retention_after_interference"]["accuracy"],
        "shared_no_replay_acquisition": result["results"]["shared_no_replay"]["target_task_acquisition"]["accuracy"],
        "shared_no_replay_retention": result["results"]["shared_no_replay"]["target_task_retention_after_interference"]["accuracy"],
        "replay_retention_effect": result["results"]["shared_replay"]["target_task_retention_after_interference"]["accuracy"] - result["results"]["shared_no_replay"]["target_task_retention_after_interference"]["accuracy"],
        "h100_authorized": result["h100_authorized"],
        "breakthrough_claim_eligible": result["breakthrough_claim_eligible"],
    }


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

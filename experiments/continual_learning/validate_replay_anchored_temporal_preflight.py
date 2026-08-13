#!/usr/bin/env python3
"""Independent validator for the V29 replay-anchored temporal preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import replay_anchored_temporal_preflight as preflight
from experiments.continual_learning import replay_anchored_temporal_protocol as protocol
from experiments.continual_learning import validate_task_stratified_microbatch_preflight as base_validator


def validate(root: Path) -> dict:
    original_preflight = base_validator.preflight
    original_protocol = base_validator.protocol
    base_validator.preflight = preflight
    base_validator.protocol = protocol
    try:
        summary = base_validator.validate(root.resolve())
    finally:
        base_validator.preflight = original_preflight
        base_validator.protocol = original_protocol
    result = json.loads((root / "result.json").read_text())
    plan = protocol.build_plan()
    if result["source_state_slice"] != preflight.SOURCE_STATE_SLICE:
        raise ValueError("V29 source state slice drift")
    if result["batch_policy"] != protocol.BATCH_POLICY or result["temporal_batch_order_policy"] != protocol.TEMPORAL_BATCH_ORDER_POLICY:
        raise ValueError("V29 temporal policy drift")
    if result["config"]["protocol_plan_sha256"] != plan["plan_sha256"]:
        raise ValueError("V29 protocol plan drift")
    audits = [audit for audit in result["batch_schedule_audit"] if audit["dataset_example_count"] == 32]
    for audit in audits:
        flattened = [task_id for batch in audit["batch_task_ids"] for task_id in batch]
        expected = protocol.replay_anchored_batch_task_ids(flattened, audit["current_task_id"], audit["batch_size"])
        if audit["batch_task_ids"] != expected:
            raise ValueError("V29 temporal batch order drift")
        if audit["temporal_batch_order_policy"] != protocol.TEMPORAL_BATCH_ORDER_POLICY:
            raise ValueError("V29 temporal audit policy drift")
    replay = result["results"]["shared_replay"]
    no_replay = result["results"]["shared_no_replay"]
    replay_retention = replay["target_task_retention_after_interference"]["accuracy"]
    no_replay_retention = no_replay["target_task_retention_after_interference"]["accuracy"]
    summary.update(
        {
            "state_slice": result["state_slice"],
            "temporal_batch_order_policy": result["temporal_batch_order_policy"],
            "replay_retention_effect": replay_retention - no_replay_retention,
            "candidate_retention_gate": replay_retention > no_replay_retention,
            "candidate_acquisition_gate": replay["target_task_acquisition"]["accuracy"] >= 0.75,
        }
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

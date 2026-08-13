#!/usr/bin/env python3
"""Independent validator for the V28 second-cell confirmation preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import task_stratified_microbatch_confirmation_preflight as preflight
from experiments.continual_learning import task_stratified_microbatch_confirmation_protocol as protocol
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
        raise ValueError("V28 confirmation source state slice drift")
    if result["confirmation_of_state_slice"] != protocol.SOURCE_STATE_SLICE:
        raise ValueError("V28 confirmation ancestry drift")
    if result["confirmation_cell"] != plan["confirmation_cell"]:
        raise ValueError("V28 confirmation cell drift")
    if result["config"]["protocol_plan_sha256"] != plan["plan_sha256"]:
        raise ValueError("V28 confirmation protocol plan drift")
    replay = result["results"]["shared_replay"]
    no_replay = result["results"]["shared_no_replay"]
    replay_retention = replay["target_task_retention_after_interference"]["accuracy"]
    no_replay_retention = no_replay["target_task_retention_after_interference"]["accuracy"]
    summary.update(
        {
            "state_slice": result["state_slice"],
            "confirmation_cell": result["confirmation_cell"],
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

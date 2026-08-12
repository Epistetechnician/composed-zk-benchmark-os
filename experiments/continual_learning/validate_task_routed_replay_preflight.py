#!/usr/bin/env python3
"""Independent validator for one corrected V23 local preflight receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import task_routed_replay_preflight as preflight  # noqa: E402
from experiments.continual_learning import task_routed_replay_protocol as protocol  # noqa: E402


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate(root: Path) -> dict:
    result = json.loads((root / "result.json").read_text(encoding="utf8"))
    if result["state_slice"] != preflight.STATE_SLICE:
        raise ValueError("preflight state slice drift")
    config = result["config"]
    if config["seed"] != 20260812 or config["order"] != [0, 1, 2, 3]:
        raise ValueError("preflight matrix identity drift")
    if config["total_examples_per_strategy"] != 128 or config["total_optimizer_steps_per_strategy"] != 640:
        raise ValueError("preflight budget drift")
    tasks = json.loads((root / "tasks.json").read_text(encoding="utf8"))
    byte_reference = result["byte_reference"]
    manifest = {
        "config": config,
        "tasks": tasks,
        "byte_reference": byte_reference,
        "results": result["results"],
    }
    if result["manifest_sha256"] != digest(manifest):
        raise ValueError("preflight manifest digest mismatch")
    result_without_digest = dict(result)
    result_without_digest.pop("result_sha256", None)
    if result["result_sha256"] != digest(result_without_digest):
        raise ValueError("preflight result digest mismatch")
    replay = result["results"]["routed_replay"]
    no_replay = result["results"]["routed_no_replay"]
    if not replay["replay_exposure_verified"] or not replay["slot_state_persistence_verified"]:
        raise ValueError("replay custody gate failed")
    for candidate in (replay, no_replay):
        if candidate["total_training_examples"] != 128 or candidate["total_optimizer_iterations"] != 640:
            raise ValueError("candidate total budget drift")
        if not candidate["parameter_budget"]["matched"]:
            raise ValueError("adapter byte budget drift")
        for update in candidate["updates"]:
            if update["dataset_row_count"] != protocol.UPDATE_BUDGET:
                raise ValueError(f"dataset row budget drift at step {update['step']}")
            if update["optimizer_iterations"] != protocol.ITERS_PER_UPDATE:
                raise ValueError(f"optimizer budget drift at step {update['step']}")
            if not update["replay_examples_present_in_training_datasets"]:
                raise ValueError(f"replay dataset exposure drift at step {update['step']}")
            for slot in update["slot_updates"]:
                if slot["optimizer_state_step_after"] - slot["optimizer_state_step_before"] != slot["optimizer_iterations"]:
                    raise ValueError(f"optimizer receipt drift at step {update['step']}")
                if not Path(slot["adapter_relative_path"]).joinpath("adapters.safetensors").exists():
                    raise ValueError("missing adapter artifact")
                if not Path(slot["optimizer_state_relative_path"]).exists():
                    raise ValueError("missing optimizer-state artifact")
    gates = result["candidate_gates"]
    if gates["replay_retention_above_routed_no_replay"]:
        raise ValueError("validator is frozen for the observed preflight tie")
    if result["h100_authorized"] or result["breakthrough_claim_eligible"]:
        raise ValueError("authority boundary drift")
    return {
        "valid": True,
        "state_slice": result["state_slice"],
        "replay_exposure_verified": replay["replay_exposure_verified"],
        "optimizer_state_persistence_verified": replay["slot_state_persistence_verified"],
        "routed_replay_retention": replay["target_task_retention_after_interference"]["accuracy"],
        "routed_no_replay_retention": no_replay["target_task_retention_after_interference"]["accuracy"],
        "replay_effect": replay["target_task_retention_after_interference"]["accuracy"] - no_replay["target_task_retention_after_interference"]["accuracy"],
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

#!/usr/bin/env python3
"""Independent validator for one corrected V24 local preflight receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import shared_adapter_task_keyed_optimizer_state_preflight as preflight  # noqa: E402
from experiments.continual_learning import shared_adapter_task_keyed_optimizer_state_protocol as protocol  # noqa: E402


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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
    manifest = {
        "config": config,
        "tasks": tasks,
        "byte_reference": result["byte_reference"],
        "results": result["results"],
    }
    if result["manifest_sha256"] != digest(manifest):
        raise ValueError("preflight manifest digest mismatch")
    result_without_digest = dict(result)
    result_without_digest.pop("result_sha256", None)
    if result["result_sha256"] != digest(result_without_digest):
        raise ValueError("preflight result digest mismatch")
    replay = result["results"]["shared_replay"]
    no_replay = result["results"]["shared_no_replay"]
    for candidate in (replay, no_replay):
        if candidate["total_training_examples"] != 128 or candidate["total_optimizer_iterations"] != 640:
            raise ValueError("candidate total budget drift")
        if not candidate["parameter_budget"]["matched"]:
            raise ValueError("shared adapter byte budget drift")
        if not candidate["optimizer_state_persistence_verified"]:
            raise ValueError("optimizer-state custody drift")
        for update in candidate["updates"]:
            if update["dataset_row_count"] != protocol.UPDATE_BUDGET or update["optimizer_iterations"] != protocol.ITERS_PER_UPDATE:
                raise ValueError(f"update budget drift at step {update['step']}")
            if not update["replay_examples_present_in_training_datasets"]:
                raise ValueError(f"dataset exposure drift at step {update['step']}")
            if update["shared_adapter_id"] != protocol.SHARED_ADAPTER_ID or update["shared_adapter_layers"] != protocol.SHARED_ADAPTER_LAYERS:
                raise ValueError("shared adapter identity drift")
            for group in update["group_receipts"]:
                if group["optimizer_state_step_after"] - group["optimizer_state_step_before"] != group["optimizer_iterations"]:
                    raise ValueError("optimizer step receipt drift")
                if not Path(group["optimizer_state_relative_path"]).exists():
                    raise ValueError("missing optimizer state artifact")
                if not Path(group["dataset_relative_path"]).joinpath("train.jsonl").exists():
                    raise ValueError("missing training dataset")
    if not replay["replay_exposure_verified"]:
        raise ValueError("replay exposure gate failed")
    if result["candidate_gates"]["target_task_acquisition_floor"]:
        raise ValueError("validator is frozen for the observed acquisition failure")
    if result["h100_authorized"] or result["breakthrough_claim_eligible"]:
        raise ValueError("authority boundary drift")
    return {
        "valid": True,
        "state_slice": result["state_slice"],
        "replay_exposure_verified": replay["replay_exposure_verified"],
        "optimizer_state_persistence_verified": replay["optimizer_state_persistence_verified"],
        "shared_replay_acquisition": replay["target_task_acquisition"]["accuracy"],
        "shared_replay_retention": replay["target_task_retention_after_interference"]["accuracy"],
        "shared_no_replay_acquisition": no_replay["target_task_acquisition"]["accuracy"],
        "shared_no_replay_retention": no_replay["target_task_retention_after_interference"]["accuracy"],
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

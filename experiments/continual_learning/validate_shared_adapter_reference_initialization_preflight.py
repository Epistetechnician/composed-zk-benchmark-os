#!/usr/bin/env python3
"""Independent validator for one V25 corrected local preflight receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import shared_adapter_reference_initialization_preflight as preflight  # noqa: E402
from experiments.continual_learning import shared_adapter_reference_initialization_protocol as protocol  # noqa: E402


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    result = json.loads((root / "result.json").read_text())
    if result["state_slice"] != preflight.STATE_SLICE:
        raise ValueError("V25 preflight state slice drift")
    if result["adapter_initialization"]["seed"] != protocol.ADAPTER_INITIALIZATION_SEED:
        raise ValueError("V25 initialization seed drift")
    config = result["config"]
    if config["seed"] != 20260812 or config["order"] != [0, 1, 2, 3]:
        raise ValueError("V25 matrix identity drift")
    if config["total_examples_per_strategy"] != 128 or config["total_optimizer_steps_per_strategy"] != 640:
        raise ValueError("V25 budget drift")
    tasks = json.loads((root / "tasks.json").read_text())
    manifest = {"config": config, "tasks": tasks, "byte_reference": result["byte_reference"], "results": result["results"]}
    if result["manifest_sha256"] != digest(manifest):
        raise ValueError("V25 manifest digest mismatch")
    result_without_digest = dict(result)
    result_without_digest.pop("result_sha256", None)
    if result["result_sha256"] != digest(result_without_digest):
        raise ValueError("V25 result digest mismatch")
    replay = result["results"]["shared_replay"]
    no_replay = result["results"]["shared_no_replay"]
    for candidate in (replay, no_replay):
        if candidate["total_training_examples"] != 128 or candidate["total_optimizer_iterations"] != 640:
            raise ValueError("V25 candidate budget drift")
        if not candidate["parameter_budget"]["matched"] or not candidate["optimizer_state_persistence_verified"]:
            raise ValueError("V25 custody or byte gate failed")
        for update in candidate["updates"]:
            if update["dataset_row_count"] != 32 or update["optimizer_iterations"] != 160:
                raise ValueError(f"V25 update budget drift at step {update['step']}")
            if not update["replay_examples_present_in_training_datasets"]:
                raise ValueError(f"V25 replay exposure drift at step {update['step']}")
    if not replay["replay_exposure_verified"]:
        raise ValueError("V25 replay exposure gate failed")
    if result["h100_authorized"] or result["breakthrough_claim_eligible"]:
        raise ValueError("V25 authority boundary drift")
    return {
        "valid": True,
        "state_slice": result["state_slice"],
        "adapter_initialization_seed": protocol.ADAPTER_INITIALIZATION_SEED,
        "replay_exposure_verified": replay["replay_exposure_verified"],
        "optimizer_state_persistence_verified": replay["optimizer_state_persistence_verified"],
        "shared_replay_acquisition": replay["target_task_acquisition"]["accuracy"],
        "shared_replay_retention": replay["target_task_retention_after_interference"]["accuracy"],
        "shared_no_replay_acquisition": no_replay["target_task_acquisition"]["accuracy"],
        "shared_no_replay_retention": no_replay["target_task_retention_after_interference"]["accuracy"],
        "replay_retention_effect": replay["target_task_retention_after_interference"]["accuracy"] - no_replay["target_task_retention_after_interference"]["accuracy"],
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

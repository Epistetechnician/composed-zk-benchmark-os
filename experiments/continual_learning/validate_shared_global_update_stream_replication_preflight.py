#!/usr/bin/env python3
"""Independent validator for the V27 fresh replication matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import shared_global_update_stream_replication_preflight as preflight  # noqa: E402
from experiments.continual_learning import shared_global_update_stream_replication_protocol as protocol  # noqa: E402


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_cell_artifact(root: Path, summary: dict) -> None:
    seed = summary["replication_cell"]["seed"]
    order = tuple(summary["replication_cell"]["order"])
    cell_root = root / "cells" / f"seed-{seed}-order-{''.join(str(value) for value in order)}"
    cell_result = json.loads((cell_root / "result.json").read_text())
    if cell_result["state_slice"] != preflight.CELL_STATE_SLICE:
        raise ValueError(f"V27 cell state slice drift: {cell_root}")
    if cell_result["replication_cell"] != {"seed": seed, "order": list(order)}:
        raise ValueError(f"V27 cell identity drift: {cell_root}")
    cell_config = cell_result["config"]
    if cell_config["seed"] != seed or cell_config["order"] != list(order):
        raise ValueError(f"V27 cell config identity drift: {cell_root}")
    cell_tasks = json.loads((cell_root / "tasks.json").read_text())
    cell_manifest = {
        "config": cell_config,
        "tasks": cell_tasks,
        "byte_reference": cell_result["byte_reference"],
        "results": cell_result["results"],
    }
    if cell_result["manifest_sha256"] != digest(cell_manifest):
        raise ValueError(f"V27 cell manifest digest mismatch: {cell_root}")
    without_digest = dict(cell_result)
    without_digest.pop("result_sha256", None)
    if cell_result["result_sha256"] != digest(without_digest):
        raise ValueError(f"V27 cell result digest mismatch: {cell_root}")
    for arm in ("shared_replay", "shared_no_replay"):
        metrics = cell_result["results"][arm]
        if metrics["total_training_examples"] != 128 or metrics["total_optimizer_iterations"] != 640:
            raise ValueError(f"V27 cell budget drift: {cell_root} {arm}")
        if not metrics["replay_exposure_verified"] or not metrics["optimizer_state_persistence_verified"] or not metrics["parameter_budget"]["matched"]:
            raise ValueError(f"V27 cell custody drift: {cell_root} {arm}")
        for update in metrics["updates"]:
            if update["dataset_row_count"] != 32 or update["optimizer_iterations"] != 160:
                raise ValueError(f"V27 cell update budget drift: {cell_root} {arm}")
            if not update["replay_examples_present_in_training_datasets"]:
                raise ValueError(f"V27 cell replay exposure drift: {cell_root} {arm}")
    replay = cell_result["results"]["shared_replay"]
    no_replay = cell_result["results"]["shared_no_replay"]
    expected_summary = {
        "shared_replay_acquisition": replay["target_task_acquisition"]["accuracy"],
        "shared_replay_retention": replay["target_task_retention_after_interference"]["accuracy"],
        "shared_no_replay_acquisition": no_replay["target_task_acquisition"]["accuracy"],
        "shared_no_replay_retention": no_replay["target_task_retention_after_interference"]["accuracy"],
        "replay_retention_effect": replay["target_task_retention_after_interference"]["accuracy"] - no_replay["target_task_retention_after_interference"]["accuracy"],
        "result_sha256": cell_result["result_sha256"],
    }
    for key, value in expected_summary.items():
        if summary[key] != value:
            raise ValueError(f"V27 aggregate summary drift for {key}: {cell_root}")


def validate(root: Path) -> dict:
    result = json.loads((root / "result.json").read_text())
    plan = json.loads((root / "plan.json").read_text())
    if result["state_slice"] != preflight.STATE_SLICE:
        raise ValueError("V27 matrix state slice drift")
    if result["plan_sha256"] != plan["plan_sha256"] or plan["plan_sha256"] != protocol.build_plan()["plan_sha256"]:
        raise ValueError("V27 plan binding drift")
    manifest = json.loads((root / "manifest.json").read_text())
    if result["manifest_sha256"] != digest(manifest):
        raise ValueError("V27 manifest digest mismatch")
    result_without_digest = dict(result)
    result_without_digest.pop("result_sha256", None)
    if result["result_sha256"] != digest(result_without_digest):
        raise ValueError("V27 result digest mismatch")
    expected = set((seed, tuple(order)) for seed, order in protocol.REPLICATION_CELLS)
    observed = set()
    if len(result["cells"]) != 8:
        raise ValueError("V27 fresh cell count drift")
    for cell in result["cells"]:
        seed = cell["replication_cell"]["seed"]
        order = tuple(cell["replication_cell"]["order"])
        if (seed, order) not in expected or (seed, order) in observed:
            raise ValueError("V27 replication identity drift")
        observed.add((seed, order))
        if cell["total_examples"] != 128 or cell["total_optimizer_steps"] != 640:
            raise ValueError("V27 cell budget drift")
        if not cell["replay_exposure_verified"] or not cell["optimizer_state_persistence_verified"] or not cell["parameter_budget_matched"]:
            raise ValueError("V27 cell custody gate failure")
        validate_cell_artifact(root, cell)
    if observed != expected:
        raise ValueError("V27 matrix coverage drift")
    if result["gates"]["h100_authorized"] or result["gates"]["breakthrough_claim_eligible"]:
        raise ValueError("V27 authority boundary drift")
    return {
        "valid": True,
        "state_slice": result["state_slice"],
        "fresh_cell_count": len(result["cells"]),
        "all_cells_acquisition_floor": result["gates"]["all_cells_acquisition_floor"],
        "all_cells_replay_above_control": result["gates"]["all_cells_replay_above_control"],
        "effects": [cell["replay_retention_effect"] for cell in result["cells"]],
        "h100_authorized": result["gates"]["h100_authorized"],
        "breakthrough_claim_eligible": result["gates"]["breakthrough_claim_eligible"],
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

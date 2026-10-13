#!/usr/bin/env python3
"""V27 fresh replication matrix for the V26 shared update stream."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import shared_global_update_stream_preflight as v26_preflight  # noqa: E402
from experiments.continual_learning import shared_global_update_stream_replication_protocol as protocol  # noqa: E402
from experiments.continual_learning import validate_shared_global_update_stream_preflight as v26_validator  # noqa: E402
from experiments.continual_learning import validate_shared_global_update_stream_replication_protocol as protocol_validator  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v27-shared-global-update-stream-replication-preflight"
SOURCE_STATE_SLICE = protocol.STATE_SLICE
CELL_STATE_SLICE = f"{STATE_SLICE}-cell"


def digest(value) -> str:
    return protocol.digest(value)


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def validate_anchor(anchor: Path) -> dict:
    summary = v26_validator.validate(anchor.resolve())
    if summary["state_slice"] != "continual-learning-protocol-v26-shared-global-update-stream-preflight":
        raise ValueError("V26 anchor state slice drift")
    return summary


def run_cell(root: Path, model: Path, seed: int, order: tuple[int, ...]) -> dict:
    cell_name = f"seed-{seed}-order-{''.join(str(value) for value in order)}"
    output = root / "cells" / cell_name
    args = argparse.Namespace(
        output=output,
        model=model,
        seed=seed,
        order=",".join(str(value) for value in order),
        task_count=protocol.v24.TASK_COUNT,
        iters=protocol.v24.ITERS_PER_UPDATE,
    )
    original_data_seed = v26_preflight.protocol.DATA_SEED
    original_order = v26_preflight.FIXED_PREFLIGHT_ORDER
    original_state = v26_preflight.STATE_SLICE
    original_source = v26_preflight.SOURCE_STATE_SLICE
    try:
        v26_preflight.protocol.DATA_SEED = seed
        v26_preflight.FIXED_PREFLIGHT_ORDER = order
        v26_preflight.STATE_SLICE = CELL_STATE_SLICE
        v26_preflight.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
        result = v26_preflight.run(args)
    finally:
        v26_preflight.protocol.DATA_SEED = original_data_seed
        v26_preflight.FIXED_PREFLIGHT_ORDER = original_order
        v26_preflight.STATE_SLICE = original_state
        v26_preflight.SOURCE_STATE_SLICE = original_source

    config = result["config"]
    config.update(
        {
            "state_slice": CELL_STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "changed_protocol_variable": protocol.CHANGED_PROTOCOL_VARIABLE,
            "replication_cell": {"seed": seed, "order": list(order)},
        }
    )
    config["contract_sha256"] = digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(output / "config.json", config)
    result.update(
        {
            "state_slice": CELL_STATE_SLICE,
            "source_state_slice": SOURCE_STATE_SLICE,
            "classification": "FreshLocalSharedGlobalUpdateStreamReplicationCellNoBreakthroughClaim",
            "claim_ceiling": "LocalDevelopmentSharedGlobalUpdateStreamReplicationCell",
            "config": config,
            "replication_cell": {"seed": seed, "order": list(order)},
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
        }
    )
    tasks = json.loads((output / "tasks.json").read_text())
    result["manifest_sha256"] = digest(
        {"config": config, "tasks": tasks, "byte_reference": result["byte_reference"], "results": result["results"]}
    )
    result["result_sha256"] = digest({key: value for key, value in result.items() if key != "result_sha256"})
    write_json(output / "result.json", result)
    return result


def cell_summary(result: dict) -> dict:
    replay = result["results"]["shared_replay"]
    no_replay = result["results"]["shared_no_replay"]
    return {
        "replication_cell": result["replication_cell"],
        "shared_replay_acquisition": replay["target_task_acquisition"]["accuracy"],
        "shared_replay_retention": replay["target_task_retention_after_interference"]["accuracy"],
        "shared_no_replay_acquisition": no_replay["target_task_acquisition"]["accuracy"],
        "shared_no_replay_retention": no_replay["target_task_retention_after_interference"]["accuracy"],
        "replay_retention_effect": replay["target_task_retention_after_interference"]["accuracy"] - no_replay["target_task_retention_after_interference"]["accuracy"],
        "replay_exposure_verified": replay["replay_exposure_verified"],
        "optimizer_state_persistence_verified": replay["optimizer_state_persistence_verified"],
        "parameter_budget_matched": replay["parameter_budget"]["matched"],
        "total_examples": replay["total_training_examples"],
        "total_optimizer_steps": replay["total_optimizer_iterations"],
        "result_sha256": result["result_sha256"],
    }


def run(args: argparse.Namespace) -> dict:
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    plan = protocol.build_plan()
    protocol_validator.validate_plan(plan)
    anchor_summary = validate_anchor(args.anchor)
    model = args.model.resolve()
    output.mkdir(parents=True)
    write_json(output / "plan.json", plan)
    fresh_results = []
    for seed, order in protocol.REPLICATION_CELLS:
        fresh_results.append(run_cell(output, model, seed, order))
    summaries = [cell_summary(result) for result in fresh_results]
    gates = {
        "fresh_cell_count_exact": len(summaries) == protocol.REPLICATION_CELLS.__len__() == 8,
        "all_cells_acquisition_floor": all(summary["shared_replay_acquisition"] >= 0.75 for summary in summaries),
        "all_cells_replay_exposure_verified": all(summary["replay_exposure_verified"] for summary in summaries),
        "all_cells_optimizer_state_persistence_verified": all(summary["optimizer_state_persistence_verified"] for summary in summaries),
        "all_cells_parameter_budget_matched": all(summary["parameter_budget_matched"] for summary in summaries),
        "all_cells_exact_examples": all(summary["total_examples"] == 128 for summary in summaries),
        "all_cells_exact_optimizer_steps": all(summary["total_optimizer_steps"] == 640 for summary in summaries),
        "all_cells_replay_above_control": all(summary["replay_retention_effect"] > 0 for summary in summaries),
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    manifest = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "plan_sha256": plan["plan_sha256"],
        "anchor": {"path": str(args.anchor.resolve()), "validation": anchor_summary},
        "cells": summaries,
    }
    result = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "FreshLocalSharedGlobalUpdateStreamReplicationMatrixNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentSharedGlobalUpdateStreamReplicationMatrix",
        "plan_sha256": plan["plan_sha256"],
        "anchor": {"path": str(args.anchor.resolve()), "validation": anchor_summary},
        "cells": summaries,
        "gates": gates,
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    result["manifest_sha256"] = digest(manifest)
    result["result_sha256"] = digest(result)
    write_json(output / "manifest.json", manifest)
    write_json(output / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--anchor", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=protocol.MODEL_DEFAULT)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

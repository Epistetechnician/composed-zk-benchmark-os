#!/usr/bin/env python3
"""V29 fresh seven-cell replication matrix preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import replay_anchored_temporal_replication_protocol as protocol  # noqa: E402
from experiments.continual_learning import replay_anchored_temporal_preflight as v29_preflight  # noqa: E402
from experiments.continual_learning import validate_replay_anchored_temporal_confirmation_preflight as confirmation_validator  # noqa: E402
from experiments.continual_learning import validate_replay_anchored_temporal_preflight as anchor_validator  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v29-replay-anchored-temporal-replication-preflight"
SOURCE_STATE_SLICE = protocol.STATE_SLICE


def digest(value) -> str:
    return protocol.digest(value)


def write_json(path: Path, value) -> None:
    protocol.write_json(path, value)


def normalize_artifact_summary(root: Path, summary: dict) -> dict:
    result = json.loads((root / "result.json").read_text())
    replay = result["results"]["shared_replay"]
    no_replay = result["results"]["shared_no_replay"]
    return {
        **summary,
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
        "temporal_batch_order_policy": result["temporal_batch_order_policy"],
        "temporal_audit_count": len(result["batch_schedule_audit"]),
        "result_sha256": result["result_sha256"],
    }


def validate_anchors(anchor: Path, confirmation: Path) -> dict:
    anchor_summary = anchor_validator.validate(anchor.resolve())
    confirmation_summary = confirmation_validator.validate(confirmation.resolve())
    if anchor_summary["candidate_retention_gate"] is not True or confirmation_summary["candidate_retention_gate"] is not True:
        raise ValueError("V29 prerequisite confirmation gate failure")
    return {
        "anchor": normalize_artifact_summary(anchor.resolve(), anchor_summary),
        "confirmation": normalize_artifact_summary(confirmation.resolve(), confirmation_summary),
    }


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
    originals = {
        "protocol": v29_preflight.protocol,
        "seed": protocol.DATA_SEED,
        "order": protocol.PREFLIGHT_ORDER,
        "state": v29_preflight.STATE_SLICE,
        "source": v29_preflight.SOURCE_STATE_SLICE,
    }
    protocol.DATA_SEED = seed
    protocol.PREFLIGHT_ORDER = order
    v29_preflight.protocol = protocol
    v29_preflight.STATE_SLICE = f"{STATE_SLICE}-cell"
    v29_preflight.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    try:
        result = v29_preflight.run(args)
    finally:
        v29_preflight.protocol = originals["protocol"]
        protocol.DATA_SEED = originals["seed"]
        protocol.PREFLIGHT_ORDER = originals["order"]
        v29_preflight.STATE_SLICE = originals["state"]
        v29_preflight.SOURCE_STATE_SLICE = originals["source"]
    cell_plan = protocol._build_cell_plan(seed, order)
    config = result["config"]
    config.update(
        {
            "state_slice": f"{STATE_SLICE}-cell",
            "source_state_slice": SOURCE_STATE_SLICE,
            "replication_cell": {"seed": seed, "order": list(order)},
            "protocol_plan_sha256": cell_plan["plan_sha256"],
        }
    )
    config["contract_sha256"] = digest({key: value for key, value in config.items() if key != "contract_sha256"})
    write_json(output / "config.json", config)
    result.update(
        {
            "state_slice": f"{STATE_SLICE}-cell",
            "source_state_slice": SOURCE_STATE_SLICE,
            "classification": "FreshLocalReplayAnchoredTemporalReplicationCellNoBreakthroughClaim",
            "claim_ceiling": "LocalDevelopmentReplayAnchoredTemporalReplicationCell",
            "config": config,
            "replication_cell": {"seed": seed, "order": list(order)},
            "batch_policy": protocol.BATCH_POLICY,
            "temporal_batch_order_policy": protocol.TEMPORAL_BATCH_ORDER_POLICY,
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
        }
    )
    tasks = json.loads((output / "tasks.json").read_text())
    result["manifest_sha256"] = digest(
        {
            "config": config,
            "tasks": tasks,
            "byte_reference": result["byte_reference"],
            "results": result["results"],
            "batch_schedule_audit": result["batch_schedule_audit"],
        }
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
        "temporal_batch_order_policy": result["temporal_batch_order_policy"],
        "temporal_audit_count": len(result["batch_schedule_audit"]),
        "result_sha256": result["result_sha256"],
    }


def run(args: argparse.Namespace) -> dict:
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    plan = protocol.build_matrix_plan()
    protocol.validate_matrix_plan(plan)
    prerequisite = validate_anchors(args.anchor, args.confirmation)
    model = args.model.resolve()
    output.mkdir(parents=True)
    write_json(output / "plan.json", plan)
    fresh_results = [run_cell(output, model, seed, order) for seed, order in protocol.REPLICATION_CELLS]
    summaries = [cell_summary(result) for result in fresh_results]
    known = [prerequisite["anchor"], prerequisite["confirmation"]]
    all_summaries = known + summaries
    gates = {
        "fresh_cell_count_exact": len(summaries) == 7,
        "anchor_confirmation_count_exact": len(known) == 2,
        "all_nine_cell_acquisition_floor": all(summary["shared_replay_acquisition"] >= 0.75 for summary in all_summaries),
        "all_nine_cell_replay_exposure_verified": all(summary["replay_exposure_verified"] for summary in all_summaries),
        "all_nine_cell_optimizer_state_persistence_verified": all(summary["optimizer_state_persistence_verified"] for summary in all_summaries),
        "all_nine_cell_parameter_budget_matched": all(summary["parameter_budget_matched"] for summary in all_summaries),
        "all_nine_cell_exact_examples": all(summary["total_examples"] == 128 for summary in all_summaries),
        "all_nine_cell_exact_optimizer_steps": all(summary["total_optimizer_steps"] == 640 for summary in all_summaries),
        "all_nine_cell_temporal_policy_fixed": all(summary.get("temporal_batch_order_policy") == protocol.TEMPORAL_BATCH_ORDER_POLICY for summary in all_summaries),
        "all_nine_cell_replay_above_control": all(summary["replay_retention_effect"] > 0 for summary in all_summaries),
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    manifest = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "plan_sha256": plan["plan_sha256"],
        "prerequisite": prerequisite,
        "cells": summaries,
    }
    result = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "FreshLocalReplayAnchoredTemporalReplicationMatrixNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentReplayAnchoredTemporalReplicationMatrix",
        "plan_sha256": plan["plan_sha256"],
        "prerequisite": prerequisite,
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
    parser.add_argument("--confirmation", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=protocol.MODEL_DEFAULT)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

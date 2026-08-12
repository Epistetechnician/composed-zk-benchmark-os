#!/usr/bin/env python3
"""Independent validator for the V22 matrix and replay exposure."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import residue_only_codebook_benchmark as v11  # noqa: E402
from experiments.continual_learning import route_boundary_representation_preflight as route  # noqa: E402
from experiments.continual_learning import validate_task_routed_compact_residual_preflight as v19  # noqa: E402
from experiments.continual_learning.seed_independent_slot_replication_cell_preflight import (  # noqa: E402
    OPTIMIZER_STATE_POLICY,
    SLOT_INITIALIZATION_POLICY,
    SLOT_SEED_BASE,
    STATE_SLICE as CELL_STATE_SLICE,
)
from experiments.continual_learning.seed_independent_slot_replication_matrix_preflight import ORDERS, SEEDS, STATE_SLICE  # noqa: E402


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _row_key(row: dict[str, str]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"))


def validate_replay_exposure(root: Path, config: dict) -> dict:
    tasks = v11.base.make_tasks(config["seed"], config["task_count"])
    facts = {fact.fact_id: fact for task in tasks for fact in task.train_facts}
    audit = json.loads((root / "audit" / "replay_lora.json").read_text())
    if len(audit) != len(config["order"]):
        raise ValueError("replay audit update count drift")
    verified = []
    for entry in audit:
        train_path = root / "data" / "replay_lora" / f"step-{entry['step']}" / "train.jsonl"
        rows = [json.loads(line) for line in train_path.read_text().splitlines() if line]
        if len(rows) != entry["dataset_row_count"] or len(rows) != config["update_budget"]:
            raise ValueError(f"replay dataset row count drift at step {entry['step']}")
        row_counts = Counter(_row_key(row) for row in rows)
        expected_keys = {
            _row_key(route.route_bound_training_example(facts[fact_id]))
            for fact_id in entry["selected_fact_ids"]
        }
        actual_keys = set(row_counts)
        if actual_keys != expected_keys:
            raise ValueError(f"replay dataset fact selection drift at step {entry['step']}")
        for fact_id in entry["replay_fact_ids"]:
            if fact_id not in facts:
                raise ValueError(f"replay fact unknown at step {entry['step']}: {fact_id}")
            if row_counts[_row_key(route.route_bound_training_example(facts[fact_id]))] < 1:
                raise ValueError(f"replay fact absent from dataset at step {entry['step']}: {fact_id}")
        expected_counts = Counter(str(facts[fact_id].task_id) for fact_id in entry["replay_fact_ids"])
        if dict(sorted(expected_counts.items())) != entry["replay_counts_by_task"]:
            raise ValueError(f"replay per-task count drift at step {entry['step']}")
        verified.append(
            {
                "step": entry["step"],
                "replay_fact_ids": entry["replay_fact_ids"],
                "replay_counts_by_task": entry["replay_counts_by_task"],
                "dataset_row_count": len(rows),
                "selected_fact_ids_present": True,
            }
        )
    return {"valid": True, "updates": verified}


def validate(root: Path) -> dict:
    matrix = json.loads((root / "matrix.json").read_text())
    if matrix["state_slice"] != STATE_SLICE or matrix["h100_authorized"] is not False or matrix["breakthrough_claim_eligible"] is not False:
        raise ValueError("V22 matrix claim boundary drift")
    if matrix["matrix_sha256"] != digest({key: value for key, value in matrix.items() if key != "matrix_sha256"}):
        raise ValueError("matrix digest mismatch")
    if matrix["seeds"] != list(SEEDS) or matrix["orders"] != [list(order) for order in ORDERS] or len(matrix["cells"]) != 9:
        raise ValueError("matrix identity drift")
    seen = set()
    validated = []
    replay_reports = []
    for cell in matrix["cells"]:
        identity = (cell["seed"], tuple(cell["order"]))
        if identity in seen or cell["seed"] not in SEEDS or identity[1] not in ORDERS:
            raise ValueError("cell identity drift")
        seen.add(identity)
        cell_root = root / cell["relative_root"]
        config = json.loads((cell_root / "config.json").read_text())
        result = json.loads((cell_root / "result.json").read_text())
        if result["result_sha256"] != digest({key: value for key, value in result.items() if key != "result_sha256"}):
            raise ValueError(f"cell result digest mismatch: {cell['cell']}")
        original_state = v19.STATE_SLICE
        original_source = v19.SOURCE_STATE_SLICE
        v19.STATE_SLICE = CELL_STATE_SLICE
        v19.SOURCE_STATE_SLICE = "continual-learning-protocol-v21-seed-sensitivity-diagnosis"
        try:
            report = v19.validate(cell_root)
        finally:
            v19.STATE_SLICE = original_state
            v19.SOURCE_STATE_SLICE = original_source
        if result["v22_replication_cell"] != {"seed": cell["seed"], "order": cell["order"]}:
            raise ValueError(f"cell metadata drift: {cell['cell']}")
        if config["seed"] != cell["seed"] or list(config["order"]) != cell["order"]:
            raise ValueError(f"cell config identity drift: {cell['cell']}")
        fixed_controls = {
            "task_count": 4,
            "train_facts_per_task": 8,
            "test_facts_per_task": 8,
            "update_budget": 32,
            "optimizer": "adamw",
            "learning_rate": 0.0001,
            "batch_size": 2,
            "iters": 160,
            "compact_slot_num_layers": 2,
            "full_shared_num_layers_reference": 8,
        }
        if any(config.get(key) != value for key, value in fixed_controls.items()):
            raise ValueError(f"frozen control drift: {cell['cell']}")
        if config["slot_initialization_policy"] != SLOT_INITIALIZATION_POLICY or config["optimizer_state_policy"] != OPTIMIZER_STATE_POLICY or config["slot_seed_base"] != SLOT_SEED_BASE or config["candidate_slot_seed_depends_on_experiment_seed"] is not False:
            raise ValueError(f"slot state contract drift: {cell['cell']}")
        audit = json.loads((cell_root / "audit" / "task_routed_compact_residual.json").read_text())
        expected_slot_seeds = {str(task_id): SLOT_SEED_BASE + task_id for task_id in range(4)}
        actual_slot_seeds = {str(entry["task_id"]): entry["slot_seed"] for entry in audit}
        if actual_slot_seeds != expected_slot_seeds:
            raise ValueError(f"slot seed drift: {cell['cell']}")
        for entry in audit:
            if entry["slot_initialization_policy"] != SLOT_INITIALIZATION_POLICY or entry["optimizer_state_policy"] != OPTIMIZER_STATE_POLICY:
                raise ValueError(f"slot audit policy drift: {cell['cell']}")
        replay_reports.append(validate_replay_exposure(cell_root, config))
        candidate = result["task_routed_compact_residual"]
        expected = {
            "candidate_acquisition": candidate["acquisition"]["accuracy"],
            "candidate_retention": candidate["retention_after_interference"]["accuracy"],
            "candidate_recovery": candidate["recovery_after_reacquisition"]["accuracy"],
            "naive_acquisition": result["results"]["naive_sequential_lora"]["acquisition"]["accuracy"],
            "naive_retention": result["results"]["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
            "replay_retention": result["results"]["replay_lora"]["retention_after_interference"]["accuracy"],
            "result_sha256": result["result_sha256"],
        }
        if any(cell[key] != value for key, value in expected.items()):
            raise ValueError(f"cell summary drift: {cell['cell']}")
        validated.append(report)
    if len(seen) != 9:
        raise ValueError("matrix cell coverage drift")
    slot_seed_policy_valid = all(
        cell["slot_seed_by_task"] == {str(task_id): SLOT_SEED_BASE + task_id for task_id in range(4)}
        for cell in matrix["cells"]
    )
    adapter_identity_by_task = {
        str(task_id): {cell["slot_adapter_sha256_by_task"][str(task_id)] for cell in matrix["cells"]}
        for task_id in range(4)
    }
    adapter_identity_consistent = all(len(hashes) == 1 for hashes in adapter_identity_by_task.values())
    gates = {
        "cell_count_exact": len(matrix["cells"]) == 9,
        "candidate_solvability_all_cells": all(cell["candidate_acquisition"] >= 0.75 for cell in matrix["cells"]),
        "candidate_retention_above_naive_all_cells": all(cell["candidate_retention"] > cell["naive_retention"] for cell in matrix["cells"]),
        "parameter_budget_matched_all_cells": all(cell["candidate_gates"]["parameter_budget_matched"] for cell in matrix["cells"]),
        "replay_retention_above_naive_all_cells": all(cell["replay_retention"] > cell["naive_retention"] for cell in matrix["cells"]),
        "slot_seed_policy_valid_all_cells": slot_seed_policy_valid,
        "slot_adapter_identity_consistent_all_cells": adapter_identity_consistent,
    }
    if matrix["gates"] != gates or matrix["replication_eligible"] != all(
        gates[key]
        for key in (
            "cell_count_exact",
            "candidate_solvability_all_cells",
            "candidate_retention_above_naive_all_cells",
            "parameter_budget_matched_all_cells",
            "slot_seed_policy_valid_all_cells",
            "slot_adapter_identity_consistent_all_cells",
        )
    ):
        raise ValueError("matrix gate derivation drift")
    return {
        "valid": True,
        "cell_count": len(validated),
        "gates": gates,
        "replay_exposure_valid_all_cells": all(report["valid"] for report in replay_reports),
        "replication_eligible": matrix["replication_eligible"],
        "matrix_sha256": matrix["matrix_sha256"],
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

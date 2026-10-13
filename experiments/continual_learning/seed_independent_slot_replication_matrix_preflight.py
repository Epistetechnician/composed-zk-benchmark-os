#!/usr/bin/env python3
"""V22 three-seed by three-order seed-independent slot replication matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.seed_independent_slot_replication_cell_preflight import (
    MODEL_DEFAULT,
    run as run_cell,
)


STATE_SLICE = "continual-learning-protocol-v22-seed-independent-init-replication"
SEEDS = (20260811, 20260812, 20260813)
ORDERS = ((0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def run(args: argparse.Namespace) -> dict:
    model = args.model.resolve()
    if model != MODEL_DEFAULT.resolve() or args.iters != 160:
        raise ValueError("V22 matrix fixed contract drift")
    root = args.output.resolve()
    if root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {root}")
    root.mkdir(parents=True)
    cells = []
    for seed in SEEDS:
        for order in ORDERS:
            order_text = ",".join(str(value) for value in order)
            cell_name = f"seed-{seed}-order-{order_text.replace(',', '')}"
            cell_args = argparse.Namespace(
                output=root / "cells" / cell_name,
                model=model,
                seed=seed,
                order=order_text,
                task_count=4,
                iters=args.iters,
            )
            result = run_cell(cell_args)
            candidate = result["task_routed_compact_residual"]
            audit = json.loads((cell_args.output / "audit" / "task_routed_compact_residual.json").read_text())
            cells.append(
                {
                    "cell": cell_name,
                    "seed": seed,
                    "order": list(order),
                    "relative_root": str(Path("cells") / cell_name),
                    "result_sha256": result["result_sha256"],
                    "candidate_acquisition": candidate["acquisition"]["accuracy"],
                    "candidate_retention": candidate["retention_after_interference"]["accuracy"],
                    "candidate_recovery": candidate["recovery_after_reacquisition"]["accuracy"],
                    "naive_acquisition": result["results"]["naive_sequential_lora"]["acquisition"]["accuracy"],
                    "naive_retention": result["results"]["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
                    "replay_retention": result["results"]["replay_lora"]["retention_after_interference"]["accuracy"],
                    "candidate_gates": result["v19_candidate_gates"],
                    "slot_seed_by_task": {str(entry["task_id"]): entry["slot_seed"] for entry in audit},
                    "slot_adapter_sha256_by_task": {str(entry["task_id"]): entry["adapter_sha256"] for entry in audit},
                    "slot_adapter_bytes_by_task": {str(entry["task_id"]): entry["adapter_bytes"] for entry in audit},
                }
            )
    slot_seed_policy_valid = all(
        cell["slot_seed_by_task"] == {str(task_id): 22000000 + task_id for task_id in range(4)} for cell in cells
    )
    adapter_identity_by_task = {
        str(task_id): {cell["slot_adapter_sha256_by_task"][str(task_id)] for cell in cells}
        for task_id in range(4)
    }
    adapter_identity_consistent = all(len(hashes) == 1 for hashes in adapter_identity_by_task.values())
    gates = {
        "cell_count_exact": len(cells) == 9,
        "candidate_solvability_all_cells": all(cell["candidate_gates"]["task_routed_solvability_floor"] for cell in cells),
        "candidate_retention_above_naive_all_cells": all(cell["candidate_gates"]["task_routed_retention_above_naive"] for cell in cells),
        "parameter_budget_matched_all_cells": all(cell["candidate_gates"]["parameter_budget_matched"] for cell in cells),
        "replay_retention_above_naive_all_cells": all(cell["replay_retention"] > cell["naive_retention"] for cell in cells),
        "slot_seed_policy_valid_all_cells": slot_seed_policy_valid,
        "slot_adapter_identity_consistent_all_cells": adapter_identity_consistent,
    }
    result = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentSeedIndependentSlotStabilityReplication",
        "classification": "SeedIndependentSlotStabilityReplicationNoBreakthroughClaim",
        "model": str(model),
        "matrix_policy": "three_seeds_by_three_orders_v1",
        "seeds": list(SEEDS),
        "orders": [list(order) for order in ORDERS],
        "iters": args.iters,
        "slot_initialization_policy": "task_keyed_fixed_seed_v1",
        "optimizer_state_policy": "fresh_zero_state_task_keyed_seed_v1",
        "slot_seed_base": 22000000,
        "cells": cells,
        "adapter_identity_by_task": {task_id: sorted(hashes) for task_id, hashes in adapter_identity_by_task.items()},
        "gates": gates,
        "replication_eligible": all(
            gates[key]
            for key in (
                "cell_count_exact",
                "candidate_solvability_all_cells",
                "candidate_retention_above_naive_all_cells",
                "parameter_budget_matched_all_cells",
                "slot_seed_policy_valid_all_cells",
                "slot_adapter_identity_consistent_all_cells",
            )
        ),
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
    }
    result["matrix_sha256"] = digest({key: value for key, value in result.items() if key != "matrix_sha256"})
    write_json(root / "matrix.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--iters", type=int, default=160)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

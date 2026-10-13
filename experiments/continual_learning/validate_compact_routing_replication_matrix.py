#!/usr/bin/env python3
"""Independent validator for the V20 compact-routing replication matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import validate_task_routed_compact_residual_preflight as v19  # noqa: E402
from experiments.continual_learning.compact_routing_replication_matrix_preflight import ORDERS, SEEDS, STATE_SLICE  # noqa: E402


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    matrix = json.loads((root / "matrix.json").read_text())
    if matrix["state_slice"] != STATE_SLICE or matrix["breakthrough_claim_eligible"] is not False or matrix["h100_authorized"] is not False:
        raise ValueError("matrix claim boundary drift")
    if matrix["matrix_sha256"] != digest({key: value for key, value in matrix.items() if key != "matrix_sha256"}):
        raise ValueError("matrix digest mismatch")
    if matrix["seeds"] != list(SEEDS) or matrix["orders"] != [list(order) for order in ORDERS] or len(matrix["cells"]) != 9:
        raise ValueError("matrix identity drift")
    seen = set()
    validated = []
    for cell in matrix["cells"]:
        identity = (cell["seed"], tuple(cell["order"]))
        if identity in seen or cell["seed"] not in SEEDS or identity[1] not in ORDERS:
            raise ValueError("cell identity drift")
        seen.add(identity)
        cell_root = root / cell["relative_root"]
        original_state = v19.STATE_SLICE
        original_source = v19.SOURCE_STATE_SLICE
        v19.STATE_SLICE = "continual-learning-protocol-v20-compact-routing-replication-cell"
        v19.SOURCE_STATE_SLICE = "continual-learning-protocol-v19-task-routed-compact-residual"
        try:
            report = v19.validate(cell_root)
        finally:
            v19.STATE_SLICE = original_state
            v19.SOURCE_STATE_SLICE = original_source
        cell_result = json.loads((cell_root / "result.json").read_text())
        candidate = cell_result["task_routed_compact_residual"]
        if cell_result["v20_replication_cell"] != {"seed": cell["seed"], "order": cell["order"]}:
            raise ValueError("cell metadata drift")
        expected = {
            "candidate_acquisition": candidate["acquisition"]["accuracy"],
            "candidate_retention": candidate["retention_after_interference"]["accuracy"],
            "candidate_recovery": candidate["recovery_after_reacquisition"]["accuracy"],
            "naive_acquisition": cell_result["results"]["naive_sequential_lora"]["acquisition"]["accuracy"],
            "naive_retention": cell_result["results"]["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
            "replay_retention": cell_result["results"]["replay_lora"]["retention_after_interference"]["accuracy"],
            "result_sha256": cell_result["result_sha256"],
        }
        if any(cell[key] != value for key, value in expected.items()):
            raise ValueError(f"cell summary drift: {cell['cell']}")
        validated.append(report)
    if len(seen) != 9:
        raise ValueError("matrix cell coverage drift")
    gates = {
        "cell_count_exact": len(matrix["cells"]) == 9,
        "candidate_solvability_all_cells": all(cell["candidate_acquisition"] >= 0.75 for cell in matrix["cells"]),
        "candidate_retention_above_naive_all_cells": all(cell["candidate_retention"] > cell["naive_retention"] for cell in matrix["cells"]),
        "parameter_budget_matched_all_cells": all(cell["candidate_gates"]["parameter_budget_matched"] for cell in matrix["cells"]),
        "replay_retention_above_naive_all_cells": all(cell["replay_retention"] > cell["naive_retention"] for cell in matrix["cells"]),
    }
    if matrix["gates"] != gates or matrix["replication_eligible"] != all(gates[key] for key in ("cell_count_exact", "candidate_solvability_all_cells", "candidate_retention_above_naive_all_cells", "parameter_budget_matched_all_cells")):
        raise ValueError("matrix gate derivation drift")
    return {"valid": True, "cell_count": len(validated), "gates": gates, "replication_eligible": matrix["replication_eligible"], "matrix_sha256": matrix["matrix_sha256"]}


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

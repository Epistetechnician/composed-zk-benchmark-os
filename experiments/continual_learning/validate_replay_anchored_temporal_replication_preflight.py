#!/usr/bin/env python3
"""Independent validator for the V29 seven-cell replication result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import replay_anchored_temporal_replication_preflight as preflight  # noqa: E402
from experiments.continual_learning import replay_anchored_temporal_replication_protocol as protocol  # noqa: E402


def validate(root: Path) -> dict:
    result = json.loads((root / "result.json").read_text())
    plan = protocol.build_matrix_plan()
    if result["state_slice"] != preflight.STATE_SLICE or result["plan_sha256"] != plan["plan_sha256"]:
        raise ValueError("V29 replication result identity drift")
    manifest = json.loads((root / "manifest.json").read_text())
    if result["manifest_sha256"] != protocol.digest(manifest):
        raise ValueError("V29 replication manifest digest mismatch")
    if result["result_sha256"] != protocol.digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ValueError("V29 replication result digest mismatch")
    if len(result["cells"]) != 7:
        raise ValueError("V29 replication fresh cell count drift")
    for cell in result["cells"]:
        if cell["temporal_batch_order_policy"] != protocol.TEMPORAL_BATCH_ORDER_POLICY:
            raise ValueError("V29 replication temporal policy drift")
        if cell["temporal_audit_count"] != 24:
            raise ValueError("V29 replication temporal audit count drift")
        if cell["total_examples"] != 128 or cell["total_optimizer_steps"] != 640:
            raise ValueError("V29 replication budget drift")
    required_gates = [key for key in result["gates"] if key not in {"h100_authorized", "breakthrough_claim_eligible"}]
    if not all(result["gates"][key] for key in required_gates):
        raise ValueError("V29 replication gate failure")
    if result["h100_authorized"] or result["breakthrough_claim_eligible"]:
        raise ValueError("V29 replication authority boundary drift")
    return {
        "valid": True,
        "state_slice": result["state_slice"],
        "fresh_cell_count": len(result["cells"]),
        "all_nine_cell_replay_above_control": result["gates"]["all_nine_cell_replay_above_control"],
        "all_nine_cell_acquisition_floor": result["gates"]["all_nine_cell_acquisition_floor"],
        "h100_authorized": result["h100_authorized"],
        "breakthrough_claim_eligible": result["breakthrough_claim_eligible"],
        "result_sha256": result["result_sha256"],
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

#!/usr/bin/env python3
"""Independent validator for the V17 readout feasibility report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


STATE_SLICE = "continual-learning-protocol-v17-task-keyed-readout-feasibility"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    report = json.loads((root / "report.json").read_text())
    if report["state_slice"] != STATE_SLICE or report["breakthrough_claim_eligible"] is not False:
        raise ValueError("state or claim boundary drift")
    if report["report_sha256"] != digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("report digest mismatch")
    fixed = report["fixed_contract"]
    if fixed["seed"] != 20260810 or fixed["order"] != [0, 1, 2, 3] or fixed["task_count"] != 4 or fixed["update_budget"] != 32 or fixed["optimizer"] != "adamw" or fixed["iters"] != 160:
        raise ValueError("fixed contract drift")
    architecture = report["readout_architecture"]
    if architecture != {
        "type": "task_keyed_permutation_readout_v1",
        "slot_count": 4,
        "parameters_per_slot": 16,
        "total_discrete_table_entries": 64,
        "fit_source": "task_train_facts_only",
        "shared_adapter": "replay_lora/step-3",
    }:
        raise ValueError("readout architecture drift")
    slots = report["slots"]
    if len(slots) != 4 or {slot["route_key"] for slot in slots} != {"T0", "T1", "T2", "T3"}:
        raise ValueError("readout route drift")
    for slot in slots:
        if len(slot["permutation"]) != 4 or set(slot["permutation"]) != {"A", "B", "C", "D"} or slot["candidate_count"] != 24:
            raise ValueError("readout table drift")
        for key in ("train_accuracy", "heldout_accuracy", "raw_train_accuracy", "raw_heldout_accuracy"):
            metric = slot[key]
            if metric["n"] != 8 or not 0 <= metric["accuracy"] <= 1:
                raise ValueError(f"readout metric drift: {key}")
    target = report["target_task"]
    if target["task_id"] != 0 or target["naive_reference"]["n"] != 8 or target["shared_replay_reference"]["n"] != 8:
        raise ValueError("target reference drift")
    gates = report["gates"]
    if report["candidate_eligible"] != all(gates.values()):
        raise ValueError("candidate derivation drift")
    return {"valid": True, "claim_ceiling": report["claim_ceiling"], "gates": gates, "candidate_eligible": report["candidate_eligible"], "report_sha256": report["report_sha256"]}


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

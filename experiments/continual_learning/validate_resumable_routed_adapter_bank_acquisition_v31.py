#!/usr/bin/env python3
"""Independent validator for the V31 resumable acquisition control plane."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.resumable_routed_adapter_bank_acquisition_v31 import (
    CLAIM_CEILING,
    PROTOCOL,
    SOURCE_PROTOCOL,
    SOURCE_STATE_SLICE,
    STATE_SLICE,
    validate_task_receipt,
)


def validate(root: Path) -> dict:
    root = root.resolve()
    config = json.loads((root / "config.json").read_text(encoding="utf8"))
    source_manifest = json.loads((root / "source_manifest.json").read_text(encoding="utf8"))
    guard = json.loads((root / "resource_guard.json").read_text(encoding="utf8"))
    run_receipt = json.loads((root / "run_receipt.json").read_text(encoding="utf8"))
    if config["state_slice"] != STATE_SLICE or config["protocol"] != PROTOCOL:
        raise ValueError("V31 state or protocol drift")
    if config["source_state_slice"] != SOURCE_STATE_SLICE or config["source_protocol"] != SOURCE_PROTOCOL:
        raise ValueError("source state drift")
    if config["claim_ceiling"] != CLAIM_CEILING or config["production_claim_eligible"] is not False:
        raise ValueError("claim boundary drift")
    if config["contract_sha256"] != base.digest({key: value for key, value in config.items() if key != "contract_sha256"}):
        raise ValueError("V31 contract digest mismatch")
    if source_manifest["manifest_sha256"] != base.digest(
        {key: value for key, value in source_manifest.items() if key != "manifest_sha256"}
    ):
        raise ValueError("source manifest digest mismatch")
    if config["source_manifest_sha256"] != source_manifest["manifest_sha256"]:
        raise ValueError("source manifest binding drift")
    if run_receipt["receipt_sha256"] != base.digest(
        {key: value for key, value in run_receipt.items() if key != "receipt_sha256"}
    ):
        raise ValueError("run receipt digest mismatch")
    if run_receipt["eligible"] is not False:
        raise ValueError("resumable control plane cannot emit eligible=true")
    if run_receipt["status"] not in {"incomplete", "ready_for_assessment"}:
        raise ValueError("unknown V31 run status")
    events = {}
    for path in sorted((root / "task_receipts").glob("task-*.json")):
        receipt = json.loads(path.read_text(encoding="utf8"))
        validate_task_receipt(receipt)
        task_id = str(receipt["task_id"])
        status = receipt["status"]
        if path.stem != f"task-{task_id}.{status}":
            raise ValueError(f"task receipt filename drift: {path.name}")
        events.setdefault(task_id, {})[status] = receipt
    if set(events) != {str(task_id) for task_id in range(4)}:
        raise ValueError("task receipt cardinality drift")
    latest = {}
    for task_id, by_status in events.items():
        if "complete" in by_status:
            latest[task_id] = by_status["complete"]
        elif "failed" in by_status:
            latest[task_id] = by_status["failed"]
        elif "running" in by_status:
            latest[task_id] = by_status["running"]
        else:
            latest[task_id] = by_status["pending"]
    statuses = {task_id: record["status"] for task_id, record in latest.items()}
    if statuses != run_receipt["task_statuses"]:
        raise ValueError("run/task status mismatch")
    if run_receipt["status"] == "ready_for_assessment" and any(status != "complete" for status in statuses.values()):
        raise ValueError("assessment-ready run has incomplete task")
    if run_receipt["status"] == "incomplete" and run_receipt["failure_reason"] is None:
        raise ValueError("incomplete run requires a failure reason")
    return {
        "valid": True,
        "claim_ceiling": CLAIM_CEILING,
        "status": run_receipt["status"],
        "eligible": False,
        "task_statuses": statuses,
        "source_manifest_sha256": source_manifest["manifest_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

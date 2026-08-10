#!/usr/bin/env python3
"""Independent structural validator for model continual-learning pilots."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


STRATEGIES = ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    config = json.loads((root / "config.json").read_text())
    tasks = json.loads((root / "tasks.json").read_text())
    result = json.loads((root / "result.json").read_text())
    if result["state_slice"] != "continual-learning-model-adapter-v2":
        raise ValueError("state slice mismatch")
    if result["breakthrough_claim_eligible"] is not False:
        raise ValueError("pilot cannot claim breakthrough eligibility")
    if config["source_context_removed_for"] != ["acquisition", "retention_after_interference", "recovery_after_reacquisition"]:
        raise ValueError("source-context boundary drift")
    if config["assessment_effects_generated_before_prediction_lock"] is not False:
        raise ValueError("prediction-lock boundary drift")
    task_ids = [task["task_id"] for task in tasks]
    if task_ids != list(range(config["task_count"])):
        raise ValueError("task ids are not contiguous")
    fact_ids = [fact["fact_id"] for task in tasks for fact in task["facts"]]
    if len(fact_ids) != len(set(fact_ids)):
        raise ValueError("fact identifiers are not disjoint")
    expected_manifest = digest({"config": config, "tasks": tasks})
    if result["manifest_sha256"] != expected_manifest:
        raise ValueError("manifest digest mismatch")
    if set(result["results"]) != set(STRATEGIES):
        raise ValueError("strategy panel drift")
    expected_n = config["facts_per_task"]
    for strategy in STRATEGIES:
        metrics = result["results"][strategy]
        for endpoint in ("acquisition", "retention_after_interference", "recovery_after_reacquisition"):
            if metrics[endpoint]["n"] != expected_n:
                raise ValueError(f"denominator mismatch: {strategy}/{endpoint}")
            if not 0 <= metrics[endpoint]["accuracy"] <= 1:
                raise ValueError(f"accuracy outside range: {strategy}/{endpoint}")
    return {"valid": True, "claim_ceiling": result["claim_ceiling"], "manifest_sha256": result["manifest_sha256"]}


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

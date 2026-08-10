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
    if result["state_slice"] != "continual-learning-model-adapter-v4-signed-replay-path":
        raise ValueError("state slice mismatch")
    if result["breakthrough_claim_eligible"] is not False:
        raise ValueError("pilot cannot claim breakthrough eligibility")
    if config["source_context_removed_for"] != ["acquisition", "retention_after_interference", "recovery_after_reacquisition"]:
        raise ValueError("source-context boundary drift")
    if config["assessment_effects_generated_before_prediction_lock"] is not False:
        raise ValueError("prediction-lock boundary drift")
    prompt_contract = config.get("prompt_contract", {})
    if prompt_contract.get("training_prompt_equals_assessment_prompt") is not True:
        raise ValueError("training/assessment prompt parity is not locked")
    if prompt_contract.get("answer_suffix") != "\nAnswer:":
        raise ValueError("answer suffix drift")
    if config.get("replay_policy") != "stratified_hash_replay_v1":
        raise ValueError("replay policy drift")
    if config.get("replay_examples_per_update") != 8 or config.get("current_examples_per_update") != 8:
        raise ValueError("update budget split drift")
    unsigned_config = {key: value for key, value in config.items() if key != "contract_sha256"}
    if config.get("contract_sha256") != digest(unsigned_config):
        raise ValueError("contract digest mismatch")
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
    for path in root.glob("data/*/step-*/train.jsonl"):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if not row["prompt"].endswith("\nAnswer:"):
                raise ValueError(f"training prompt parity failure: {path}")
    expected_n = config["facts_per_task"]
    for strategy in STRATEGIES:
        metrics = result["results"][strategy]
        for endpoint in ("acquisition", "retention_after_interference", "recovery_after_reacquisition"):
            if metrics[endpoint]["n"] != expected_n:
                raise ValueError(f"denominator mismatch: {strategy}/{endpoint}")
            if not 0 <= metrics[endpoint]["accuracy"] <= 1:
                raise ValueError(f"accuracy outside range: {strategy}/{endpoint}")
    no_update = result["results"]["no_update"]
    retrieval = result["results"]["retrieval"]
    naive = result["results"]["naive_sequential_lora"]
    replay = result["results"]["replay_lora"]
    gates = {
        "retrieval_above_no_update": retrieval["acquisition"]["accuracy"] > no_update["acquisition"]["accuracy"],
        "trainable_acquisition_above_no_update": max(
            naive["acquisition"]["accuracy"], replay["acquisition"]["accuracy"]
        ) > no_update["acquisition"]["accuracy"],
        "replay_retention_above_naive": replay["retention_after_interference"]["accuracy"] > naive["retention_after_interference"]["accuracy"],
    }
    return {
        "valid": True,
        "claim_ceiling": result["claim_ceiling"],
        "manifest_sha256": result["manifest_sha256"],
        "candidate_gates": gates,
        "candidate_eligible": all(gates.values()),
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

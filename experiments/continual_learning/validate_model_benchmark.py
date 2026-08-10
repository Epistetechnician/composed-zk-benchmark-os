#!/usr/bin/env python3
"""Independent structural validator for model continual-learning pilots."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


STRATEGIES = ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora")
AUDIT_STRATEGIES = ("naive_sequential_lora", "replay_lora")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    config = json.loads((root / "config.json").read_text())
    tasks = json.loads((root / "tasks.json").read_text())
    result = json.loads((root / "result.json").read_text())
    if result["state_slice"] != "continual-learning-model-adapter-v6-balanced-full-memory-replay":
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
    if config.get("replay_policy") != "balanced_full_memory_v1":
        raise ValueError("replay policy drift")
    if config.get("replay_examples_per_update") != 24 or config.get("current_examples_per_update") != 8:
        raise ValueError("update budget split drift")
    fixed_config = {
        "seed": 20260810,
        "order": [0, 1, 2, 3],
        "task_count": 4,
        "facts_per_task": 8,
        "replay_capacity": 24,
        "update_budget": 32,
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "mask_prompt": True,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "audit_schema": "replay_exposure_audit_v1",
        "checkpoint_target_task_id": 0,
        "checkpoint_assessment_variant": "direct",
        "checkpoint_assessment_context_mode": "none",
        "iters": 40,
    }
    for key, expected in fixed_config.items():
        if config.get(key) != expected:
            raise ValueError(f"fixed training contract drift: {key}")
    unsigned_config = {key: value for key, value in config.items() if key != "contract_sha256"}
    if config.get("contract_sha256") != digest(unsigned_config):
        raise ValueError("contract digest mismatch")
    task_ids = [task["task_id"] for task in tasks]
    if task_ids != list(range(config["task_count"])):
        raise ValueError("task ids are not contiguous")
    fact_ids = [fact["fact_id"] for task in tasks for fact in task["facts"]]
    if len(fact_ids) != len(set(fact_ids)):
        raise ValueError("fact identifiers are not disjoint")
    audits = {}
    for strategy in AUDIT_STRATEGIES:
        audit_path = root / "audit" / f"{strategy}.json"
        if not audit_path.exists():
            raise ValueError(f"missing replay exposure audit: {strategy}")
        audits[strategy] = json.loads(audit_path.read_text())
        if len(audits[strategy]) != len(config["order"]):
            raise ValueError(f"update count mismatch: {strategy}")
    if result.get("audit_sha256") != {strategy: digest(audits[strategy]) for strategy in AUDIT_STRATEGIES}:
        raise ValueError("audit digest mismatch")
    expected_manifest = digest({"config": config, "tasks": tasks, "audits": audits})
    if result["manifest_sha256"] != expected_manifest:
        raise ValueError("manifest digest mismatch")
    if set(result["results"]) != set(STRATEGIES):
        raise ValueError("strategy panel drift")
    for path in root.glob("data/*/step-*/train.jsonl"):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if not row["prompt"].endswith("\nAnswer:"):
                raise ValueError(f"training prompt parity failure: {path}")
    task_fact_lists = {
        task["task_id"]: [fact["fact_id"] for fact in task["facts"]]
        for task in tasks
    }
    task_facts = {task_id: set(fact_ids) for task_id, fact_ids in task_fact_lists.items()}
    fact_to_task = {
        fact_id: task_id
        for task_id, fact_ids in task_fact_lists.items()
        for fact_id in fact_ids
    }
    all_fact_ids = sorted(fact_to_task)
    for strategy in AUDIT_STRATEGIES:
        for update in audits[strategy]:
            step = update["step"]
            task_id = update["task_id"]
            current_ids = update["current_fact_ids"]
            replay_ids = update["replay_fact_ids"]
            selected_ids = update["selected_fact_ids"]
            if current_ids != task_fact_lists[task_id]:
                raise ValueError(f"current fact audit mismatch: {strategy}/step-{step}")
            if set(replay_ids) & set(current_ids):
                raise ValueError(f"replay/current overlap: {strategy}/step-{step}")
            if selected_ids != current_ids + replay_ids:
                raise ValueError(f"selected fact audit mismatch: {strategy}/step-{step}")
            expected_counts = dict(sorted(
                (str(task), count)
                for task, count in Counter(fact_to_task[fact_id] for fact_id in replay_ids).items()
            ))
            if update["replay_counts_by_task"] != expected_counts:
                raise ValueError(f"replay count audit mismatch: {strategy}/step-{step}")
            if strategy == "replay_lora":
                expected_full_replay = {
                    str(prior_task): config["facts_per_task"]
                    for prior_task in range(task_id)
                }
                if update["replay_counts_by_task"] != expected_full_replay:
                    raise ValueError(f"full replay policy mismatch: {strategy}/step-{step}")
            dataset_path = root / "data" / strategy / f"step-{step}" / "train.jsonl"
            rows = [json.loads(line) for line in dataset_path.read_text().splitlines()]
            if len(rows) != config["update_budget"] or update["dataset_row_count"] != len(rows):
                raise ValueError(f"dataset budget audit mismatch: {strategy}/step-{step}")
            row_ids = []
            for row in rows:
                matches = [fact_id for fact_id in all_fact_ids if f"identifier {fact_id}" in row["prompt"]]
                if len(matches) != 1:
                    raise ValueError(f"dataset fact identity missing: {strategy}/step-{step}")
                row_ids.append(matches[0])
            if set(row_ids) != set(selected_ids):
                raise ValueError(f"dataset membership mismatch: {strategy}/step-{step}")
            if not set(replay_ids).issubset(row_ids):
                raise ValueError(f"replay examples absent from dataset: {strategy}/step-{step}")
            checkpoint = update["target_task_accuracy_after_update"]
            if checkpoint["n"] != config["facts_per_task"] or not 0 <= checkpoint["accuracy"] <= 1:
                raise ValueError(f"checkpoint accuracy audit mismatch: {strategy}/step-{step}")
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

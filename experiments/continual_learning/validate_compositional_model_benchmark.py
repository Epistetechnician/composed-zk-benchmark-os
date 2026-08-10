#!/usr/bin/env python3
"""Independent validator for the held-out compositional V7 pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


STATE_SLICE = "continual-learning-model-adapter-v7-heldout-compositional-task"
LABELS = ("A", "B", "C", "D")
SYMBOLS = ("zero", "one", "two", "three")
ANSWER_SUFFIX = "\nAnswer:"
STRATEGIES = ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora")
AUDIT_STRATEGIES = ("naive_sequential_lora", "replay_lora")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def expected_prompt(fact):
    return (
        "Answer with exactly one letter: A, B, C, or D.\n"
        f"Task token: {fact['task_token']}.\n"
        f"Compose {SYMBOLS[fact['left']]} + {SYMBOLS[fact['right']]}.\n"
        "Apply the task's modular-four rule and return only the option letter."
        f"{ANSWER_SUFFIX}"
    )


def validate(root: Path, expected_seed: int = 20260810, expected_order: list[int] | None = None) -> dict:
    if expected_order is None:
        expected_order = [0, 1, 2, 3]
    config = json.loads((root / "config.json").read_text())
    tasks = json.loads((root / "tasks.json").read_text())
    result = json.loads((root / "result.json").read_text())
    if result["state_slice"] != STATE_SLICE:
        raise ValueError("state slice mismatch")
    if result["breakthrough_claim_eligible"] is not False:
        raise ValueError("pilot cannot claim breakthrough eligibility")
    fixed = {
        "seed": expected_seed,
        "order": expected_order,
        "task_count": 4,
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_permutation_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "replay_capacity": 24,
        "update_budget": 32,
        "current_examples_per_update": 8,
        "replay_examples_per_update": 24,
        "replay_policy": "balanced_full_memory_v1",
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "mask_prompt": True,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "audit_schema": "replay_exposure_audit_v1",
        "checkpoint_target_task_id": 0,
        "checkpoint_assessment_context_mode": "none",
        "iters": 40,
    }
    for key, expected in fixed.items():
        if config.get(key) != expected:
            raise ValueError(f"fixed contract drift: {key}")
    prompt_contract = config.get("prompt_contract", {})
    if prompt_contract != {"training_prompt_equals_assessment_prompt": True, "answer_suffix": ANSWER_SUFFIX}:
        raise ValueError("prompt contract drift")
    if config["source_context_removed_for"] != ["acquisition", "retention_after_interference", "recovery_after_reacquisition"]:
        raise ValueError("source-context boundary drift")
    if config["assessment_effects_generated_before_prediction_lock"] is not False:
        raise ValueError("prediction-lock boundary drift")
    unsigned = {key: value for key, value in config.items() if key != "contract_sha256"}
    if config.get("contract_sha256") != digest(unsigned):
        raise ValueError("contract digest mismatch")
    if [task["task_id"] for task in tasks] != list(range(config["task_count"])):
        raise ValueError("task ids are not contiguous")
    train_by_id = {}
    test_by_id = {}
    all_train_facts = []
    for task in tasks:
        if task["mapping"] == sorted(task["mapping"]) or set(task["mapping"]) != set(LABELS):
            raise ValueError("task mapping is not a label permutation")
        if len(task["train_facts"]) != 8 or len(task["test_facts"]) != 8:
            raise ValueError("train/test split size drift")
        train_ids = {fact["fact_id"] for fact in task["train_facts"]}
        test_ids = {fact["fact_id"] for fact in task["test_facts"]}
        if train_ids & test_ids:
            raise ValueError("train/test fact overlap")
        for fact in task["train_facts"] + task["test_facts"]:
            if fact["split"] not in ("train", "test") or fact["label"] != task["mapping"][fact["residue"]]:
                raise ValueError("compositional label rule drift")
            if fact["residue"] != (fact["left"] + fact["right"]) % 4:
                raise ValueError("residue rule drift")
        train_by_id.update({fact["fact_id"]: fact for fact in task["train_facts"]})
        test_by_id.update({fact["fact_id"]: fact for fact in task["test_facts"]})
        all_train_facts.extend(task["train_facts"])
    if set(train_by_id) & set(test_by_id):
        raise ValueError("global train/test fact overlap")
    audits = {}
    for strategy in AUDIT_STRATEGIES:
        path = root / "audit" / f"{strategy}.json"
        if not path.exists():
            raise ValueError(f"missing audit: {strategy}")
        audits[strategy] = json.loads(path.read_text())
        if len(audits[strategy]) != len(config["order"]):
            raise ValueError(f"audit update count mismatch: {strategy}")
    if result.get("audit_sha256") != {strategy: digest(audits[strategy]) for strategy in AUDIT_STRATEGIES}:
        raise ValueError("audit digest mismatch")
    tasks_json = tasks
    if result["manifest_sha256"] != digest({"config": config, "tasks": tasks_json, "audits": audits}):
        raise ValueError("manifest digest mismatch")
    if set(result["results"]) != set(STRATEGIES):
        raise ValueError("strategy panel drift")
    prompt_to_fact = {expected_prompt(fact): fact for fact in all_train_facts}
    for path in root.glob("data/*/step-*/train.jsonl"):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if not row["prompt"].endswith(ANSWER_SUFFIX):
                raise ValueError(f"training prompt parity failure: {path}")
            fact = prompt_to_fact.get(row["prompt"])
            if fact is None or row["completion"] != f" {fact['label']}":
                raise ValueError(f"training fact membership failure: {path}")
    for strategy in AUDIT_STRATEGIES:
        for update in audits[strategy]:
            step = update["step"]
            task_id = update["task_id"]
            current_ids = [fact["fact_id"] for fact in tasks[task_id]["train_facts"]]
            replay_ids = update["replay_fact_ids"]
            if update["current_fact_ids"] != current_ids or update["selected_fact_ids"] != current_ids + replay_ids:
                raise ValueError(f"audit fact identity mismatch: {strategy}/step-{step}")
            expected_counts = dict(sorted(
                (str(task), count)
                for task, count in Counter(train_by_id[fact_id]["task_id"] for fact_id in replay_ids).items()
            ))
            expected_full = {str(task): 8 for task in config["order"][:step]}
            if update["replay_counts_by_task"] != expected_counts:
                raise ValueError(f"replay count mismatch: {strategy}/step-{step}")
            if strategy == "replay_lora" and expected_counts != expected_full:
                raise ValueError(f"full replay mismatch: {strategy}/step-{step}")
            rows = [json.loads(line) for line in (root / "data" / strategy / f"step-{step}" / "train.jsonl").read_text().splitlines()]
            if len(rows) != 32 or update["dataset_row_count"] != 32:
                raise ValueError(f"dataset budget mismatch: {strategy}/step-{step}")
            row_ids = [prompt_to_fact[row["prompt"]]["fact_id"] for row in rows]
            if set(row_ids) != set(update["selected_fact_ids"]):
                raise ValueError(f"dataset membership mismatch: {strategy}/step-{step}")
            checkpoint = update["target_task_accuracy_after_update"]
            if checkpoint["n"] != 8 or not 0 <= checkpoint["accuracy"] <= 1:
                raise ValueError(f"checkpoint metric mismatch: {strategy}/step-{step}")
    for strategy in STRATEGIES:
        for endpoint in ("acquisition", "retention_after_interference", "recovery_after_reacquisition"):
            metric = result["results"][strategy][endpoint]
            if metric["n"] != 8 or not 0 <= metric["accuracy"] <= 1:
                raise ValueError(f"metric denominator/range mismatch: {strategy}/{endpoint}")
    no_update = result["results"]["no_update"]
    retrieval = result["results"]["retrieval"]
    naive = result["results"]["naive_sequential_lora"]
    replay = result["results"]["replay_lora"]
    gates = {
        "retrieval_above_no_update": retrieval["acquisition"]["accuracy"] > no_update["acquisition"]["accuracy"],
        "trainable_acquisition_above_no_update": max(
            naive["acquisition"]["accuracy"], replay["acquisition"]["accuracy"]
        ) > no_update["acquisition"]["accuracy"],
        "replay_heldout_retention_above_naive": replay["retention_after_interference"]["accuracy"] > naive["retention_after_interference"]["accuracy"],
    }
    return {"valid": True, "claim_ceiling": result["claim_ceiling"], "manifest_sha256": result["manifest_sha256"], "candidate_gates": gates, "candidate_eligible": all(gates.values())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--expected-seed", type=int, default=20260810)
    parser.add_argument("--expected-order", default="0,1,2,3")
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root.resolve(), args.expected_seed, [int(value) for value in args.expected_order.split(",")]), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

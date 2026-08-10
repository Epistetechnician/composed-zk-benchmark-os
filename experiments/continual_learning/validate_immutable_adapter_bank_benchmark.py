#!/usr/bin/env python3
"""Independent validator for the V9 immutable adapter-bank pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.validate_compositional_model_benchmark import (
    ANSWER_SUFFIX,
    LABELS,
    SYMBOLS,
    expected_prompt,
)


STATE_SLICE = "continual-learning-model-adapter-v9-immutable-task-adapter-bank"
STRATEGIES = ("no_update", "context_only", "retrieval", "naive_sequential_lora", "replay_lora", "task_adapter_bank")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    config = json.loads((root / "config.json").read_text())
    tasks = json.loads((root / "tasks.json").read_text())
    result = json.loads((root / "result.json").read_text())
    if result["state_slice"] != STATE_SLICE or result["breakthrough_claim_eligible"] is not False:
        raise ValueError("state or claim boundary drift")
    fixed = {
        "seed": 20260810,
        "order": [0, 1, 2, 3],
        "task_count": 4,
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "memory_mechanism": "immutable_task_keyed_adapter_bank_v1",
        "route_policy": "task_token_exact_v1",
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
        "audit_schema": "immutable_adapter_bank_audit_v1",
        "checkpoint_target_task_id": 0,
        "checkpoint_assessment_context_mode": "none",
        "iters": 40,
    }
    for key, expected in fixed.items():
        if config.get(key) != expected:
            raise ValueError(f"fixed contract drift: {key}")
    if config.get("prompt_contract") != {"training_prompt_equals_assessment_prompt": True, "answer_suffix": ANSWER_SUFFIX}:
        raise ValueError("prompt contract drift")
    if config["contract_sha256"] != digest({key: value for key, value in config.items() if key != "contract_sha256"}):
        raise ValueError("contract digest mismatch")
    train_facts = {}
    task_train_ids = {}
    all_train = []
    for task in tasks:
        mapping = [LABELS[(residue + task["task_id"]) % 4] for residue in range(4)]
        if task["mapping"] != mapping:
            raise ValueError("task mapping drift")
        train_ids = [fact["fact_id"] for fact in task["train_facts"]]
        test_ids = [fact["fact_id"] for fact in task["test_facts"]]
        if len(train_ids) != 8 or len(test_ids) != 8 or set(train_ids) & set(test_ids):
            raise ValueError("held-out split drift")
        if {fact["residue"] for fact in task["train_facts"]} != set(range(4)) or {fact["residue"] for fact in task["test_facts"]} != set(range(4)):
            raise ValueError("residue coverage drift")
        for fact in task["train_facts"] + task["test_facts"]:
            if fact["label"] != mapping[fact["residue"]] or fact["residue"] != (fact["left"] + fact["right"]) % 4:
                raise ValueError("compositional label drift")
        task_train_ids[task["task_id"]] = train_ids
        for fact in task["train_facts"]:
            train_facts[fact["fact_id"]] = fact
            all_train.append(fact)
    audit_payloads = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in ("naive_sequential_lora", "replay_lora")
    }
    audit_payloads["task_adapter_bank"] = json.loads((root / "audit" / "task_adapter_bank.json").read_text())
    if result["manifest_sha256"] != digest({"config": config, "tasks": tasks, "audits": audit_payloads}):
        raise ValueError("manifest digest mismatch")
    if set(result["results"]) != set(STRATEGIES):
        raise ValueError("strategy panel drift")
    prompt_to_fact = {expected_prompt(fact): fact for fact in all_train}
    for path in root.glob("data/*/step-*/train.jsonl"):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            fact = prompt_to_fact.get(row["prompt"])
            if fact is None or row["completion"] != f" {fact['label']}" or not row["prompt"].endswith(ANSWER_SUFFIX):
                raise ValueError(f"dataset membership failure: {path}")
    audits = {}
    for strategy in ("naive_sequential_lora", "replay_lora"):
        audits[strategy] = json.loads((root / "audit" / f"{strategy}.json").read_text())
        if len(audits[strategy]) != 4:
            raise ValueError(f"shared audit length drift: {strategy}")
        for update in audits[strategy]:
            expected_current = task_train_ids[update["task_id"]]
            replay_ids = update["replay_fact_ids"]
            if update["current_fact_ids"] != expected_current or update["selected_fact_ids"] != expected_current + replay_ids:
                raise ValueError(f"shared audit fact drift: {strategy}/step-{update['step']}")
            counts = dict(sorted((str(task), count) for task, count in Counter(train_facts[fact_id]["task_id"] for fact_id in replay_ids).items()))
            expected_counts = {str(task): 8 for task in config["order"][:update["step"]]} if strategy == "replay_lora" else {}
            if counts != expected_counts or update["replay_counts_by_task"] != counts or update["dataset_row_count"] != 32:
                raise ValueError(f"shared replay audit drift: {strategy}/step-{update['step']}")
    bank_audit = json.loads((root / "audit" / "task_adapter_bank.json").read_text())
    if len(bank_audit) != 4 or {entry["route_key"] for entry in bank_audit} != {f"T{task}" for task in range(4)}:
        raise ValueError("adapter-bank route drift")
    seen_paths = set()
    for entry in bank_audit:
        task_id = entry["task_id"]
        if entry["train_fact_ids"] != task_train_ids[task_id] or entry["dataset_row_count"] != 32 or entry["resumed_from"] is not None:
            raise ValueError(f"adapter-bank audit drift: task {task_id}")
        if entry["adapter_relative_path"] in seen_paths or not (root / entry["adapter_relative_path"] / "adapters.safetensors").exists():
            raise ValueError("adapter-bank immutability/path drift")
        seen_paths.add(entry["adapter_relative_path"])
    audits["task_adapter_bank"] = bank_audit
    expected_audits = {strategy: digest(audit) for strategy, audit in audits.items()}
    if result["audit_sha256"] != expected_audits:
        raise ValueError("audit digest mismatch")
    for strategy in STRATEGIES:
        for endpoint in ("acquisition", "retention_after_interference", "recovery_after_reacquisition"):
            metric = result["results"][strategy][endpoint]
            if metric["n"] != 8 or not 0 <= metric["accuracy"] <= 1:
                raise ValueError(f"metric range drift: {strategy}/{endpoint}")
    no_update = result["results"]["no_update"]
    retrieval = result["results"]["retrieval"]
    bank = result["results"]["task_adapter_bank"]
    naive = result["results"]["naive_sequential_lora"]
    gates = {
        "retrieval_above_no_update": retrieval["acquisition"]["accuracy"] > no_update["acquisition"]["accuracy"],
        "bank_acquisition_above_no_update": bank["acquisition"]["accuracy"] > no_update["acquisition"]["accuracy"],
        "bank_retention_above_naive": bank["retention_after_interference"]["accuracy"] > naive["retention_after_interference"]["accuracy"],
    }
    return {"valid": True, "claim_ceiling": result["claim_ceiling"], "manifest_sha256": result["manifest_sha256"], "candidate_gates": gates, "candidate_eligible": all(gates.values())}


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

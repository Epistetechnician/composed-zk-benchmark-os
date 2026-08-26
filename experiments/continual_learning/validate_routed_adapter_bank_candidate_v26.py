#!/usr/bin/env python3
"""Independent validator for V26 routed-adapter-bank candidate artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_model_benchmark import ANSWER_SUFFIX


STATE_SLICE = "continual-learning-candidate-task-routed-adapter-bank-v26"
MODEL_DEFAULT = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def expected_prompt(fact: dict) -> str:
    return (
        "Answer with exactly one letter: A, B, C, or D.\n"
        f"Task token: {fact['task_token']}.\n"
        f"Derived residue: {fact['residue']}.\n"
        "Use the task's residue-to-option codebook and return only the option letter.\n"
        f"Task route binding: {fact['task_token']}.{ANSWER_SUFFIX}"
    )


def validate(root: Path) -> dict:
    config = json.loads((root / "config.json").read_text())
    tasks = json.loads((root / "tasks.json").read_text())
    result = json.loads((root / "result.json").read_text())
    if result["state_slice"] != STATE_SLICE or result["breakthrough_claim_eligible"] is not False:
        raise ValueError("state or claim boundary drift")
    if result["production_claim_eligible"] is not False:
        raise ValueError("production claim boundary drift")
    if result["result_sha256"] != digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ValueError("result digest mismatch")
    fixed = {
        "model": MODEL_DEFAULT,
        "task_count": 4,
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "memory_mechanism": "append_only_task_routed_adapter_bank_v1",
        "task_update_redesign": "fresh_adapter_per_task_from_frozen_base_v1",
        "route_policy": "task_token_exact_v1",
        "update_budget": 32,
        "current_examples_per_update": 8,
        "replay_examples_per_update": 24,
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "mask_prompt": True,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "audit_schema": "residue_only_solvability_audit_v1",
        "checkpoint_target_task_id": 0,
        "checkpoint_assessment_context_mode": "none",
        "iters": 160,
    }
    for key, expected in fixed.items():
        if config.get(key) != expected:
            raise ValueError(f"fixed contract drift: {key}")
    if config.get("prompt_contract") != {
        "training_prompt_equals_assessment_prompt": True,
        "answer_suffix": ANSWER_SUFFIX,
        "derived_residue_visible": True,
        "raw_pair_present": False,
        "route_binding_at_answer_boundary": True,
        "route_binding_policy": "task_route_suffix_v1",
    }:
        raise ValueError("prompt contract drift")
    if config["contract_sha256"] != digest({key: value for key, value in config.items() if key != "contract_sha256"}):
        raise ValueError("contract digest mismatch")
    if result["config"] != config or result["tasks"] != tasks or len(tasks) != 4:
        raise ValueError("embedded manifest drift")

    task_train_ids = {}
    train_by_prompt = {}
    for task in tasks:
        mapping = ["A", "B", "C", "D"]
        mapping = [mapping[(residue + task["task_id"]) % 4] for residue in range(4)]
        if task["mapping"] != mapping:
            raise ValueError("task mapping drift")
        train = task["train_facts"]
        test = task["test_facts"]
        if len(train) != 8 or len(test) != 8:
            raise ValueError("fact count drift")
        train_ids = [fact["fact_id"] for fact in train]
        test_ids = [fact["fact_id"] for fact in test]
        if set(train_ids) & set(test_ids) or {fact["residue"] for fact in train} != set(range(4)) or {fact["residue"] for fact in test} != set(range(4)):
            raise ValueError("held-out split drift")
        task_train_ids[task["task_id"]] = train_ids
        for fact in train:
            if fact["label"] != mapping[fact["residue"]] or fact["residue"] != (fact["left"] + fact["right"]) % 4:
                raise ValueError("fact rule drift")
            train_by_prompt[expected_prompt(fact)] = fact

    audits = {
        strategy: json.loads((root / "audit" / f"{strategy}.json").read_text())
        for strategy in ("naive_sequential_lora", "replay_lora", "task_adapter_bank")
    }
    if result["manifest_sha256"] != digest({"config": config, "tasks": tasks, "audits": audits}):
        raise ValueError("manifest digest mismatch")
    dataset_paths = sorted((root / "data").glob("*/step-*/train.jsonl")) + sorted((root / "data" / "task_adapter_bank").glob("task-*/train.jsonl"))
    if len(dataset_paths) != 12:
        raise ValueError("dataset panel drift")
    for path in dataset_paths:
        rows = path.read_text().splitlines()
        if len(rows) != 32:
            raise ValueError(f"dataset row count drift: {path}")
        for line in rows:
            row = json.loads(line)
            fact = train_by_prompt.get(row["prompt"])
            if fact is None or row["completion"] != f" {fact['label']}" or not row["prompt"].endswith(ANSWER_SUFFIX):
                raise ValueError(f"dataset prompt membership drift: {path}")
            if "Compose " in row["prompt"] or f"Task route binding: {fact['task_token']}." not in row["prompt"]:
                raise ValueError(f"route prompt leakage: {path}")

    bank_audit = audits["task_adapter_bank"]
    if len(bank_audit) != 4 or {entry["route_key"] for entry in bank_audit} != {"T0", "T1", "T2", "T3"}:
        raise ValueError("route registry drift")
    seen = set()
    for entry in bank_audit:
        if entry["train_fact_ids"] != task_train_ids[entry["task_id"]] or entry["dataset_row_count"] != 32 or entry["resumed_from"] is not None:
            raise ValueError(f"fresh adapter audit drift: task {entry['task_id']}")
        if entry["adapter_relative_path"] in seen or not (root / entry["adapter_relative_path"] / "adapters.safetensors").is_file():
            raise ValueError("adapter path reuse or missing artifact")
        seen.add(entry["adapter_relative_path"])

    metrics = result["results"]
    for strategy in metrics:
        for endpoint in ("acquisition", "retention_after_interference", "recovery_after_reacquisition"):
            value = metrics[strategy][endpoint]
            if value["n"] != 8 or not 0 <= value["accuracy"] <= 1:
                raise ValueError(f"metric range drift: {strategy}/{endpoint}")
    gates = {
        "retrieval_above_no_update": metrics["retrieval"]["acquisition"]["accuracy"] > metrics["no_update"]["acquisition"]["accuracy"],
        "bank_acquisition_above_no_update": metrics["task_adapter_bank"]["acquisition"]["accuracy"] > metrics["no_update"]["acquisition"]["accuracy"],
        "bank_retention_above_naive": metrics["task_adapter_bank"]["retention_after_interference"]["accuracy"] > metrics["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
        "bank_heldout_solubility_floor": metrics["task_adapter_bank"]["retention_after_interference"]["accuracy"] >= 0.75,
    }
    if result["candidate_gates"] != gates or result["candidate_eligible"] != all(gates.values()):
        raise ValueError("candidate gate drift")
    return {
        "valid": True,
        "candidate_eligible": result["candidate_eligible"],
        "candidate_gates": gates,
        "manifest_sha256": result["manifest_sha256"],
        "claim_ceiling": result["claim_ceiling"],
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

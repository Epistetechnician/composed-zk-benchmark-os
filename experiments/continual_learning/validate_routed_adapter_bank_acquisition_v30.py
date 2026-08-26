#!/usr/bin/env python3
"""Independent structural and metric validator for the V30 parity repair."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import routed_adapter_bank_acquisition_v29 as v29
from experiments.continual_learning.routed_adapter_bank_acquisition_v30 import (
    CLAIM_CEILING,
    MODEL_DEFAULT,
    PROTOCOL,
    STATE_SLICE,
    raw_text_training_example,
)


def validate(root: Path) -> dict:
    config = json.loads((root / "config.json").read_text())
    tasks = json.loads((root / "tasks.json").read_text())
    result = json.loads((root / "result.json").read_text())
    audit = json.loads((root / "audit" / "task_adapter_bank.json").read_text())
    if result["state_slice"] != STATE_SLICE or result["protocol"] != PROTOCOL:
        raise ValueError("state or protocol drift")
    if result["claim_ceiling"] != CLAIM_CEILING or result["production_claim_eligible"] is not False:
        raise ValueError("claim boundary drift")
    for key in ("network_access", "retention_executed", "interference_executed", "provider_executed"):
        if result[key] is not False:
            raise ValueError(f"execution boundary drift: {key}")
    if result["result_sha256"] != base.digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ValueError("result digest mismatch")
    if config["state_slice"] != STATE_SLICE or config["protocol"] != PROTOCOL:
        raise ValueError("config state drift")
    if config["model"] != str(MODEL_DEFAULT) or config["seed"] != 20260861 or config["order"] != [0, 1, 2, 3]:
        raise ValueError("fixed V30 config drift")
    if config["dataset_format"] != "raw_text_prompt_plus_completion_v1":
        raise ValueError("dataset parity repair drift")
    if config["prompt_contract"]["dataset_chat_template_wrapping"] is not False:
        raise ValueError("chat-template wrapping was not disabled")
    if config["contract_sha256"] != base.digest({key: value for key, value in config.items() if key != "contract_sha256"}):
        raise ValueError("contract digest mismatch")
    if result["config"] != config or result["tasks"] != tasks or len(tasks) != 4 or len(audit) != 4:
        raise ValueError("embedded manifest drift")

    train_by_prompt = {}
    task_train_ids = {}
    for task in tasks:
        train = task["train_facts"]
        test = task["test_facts"]
        if len(train) != 8 or len(test) != 8:
            raise ValueError("fact count drift")
        train_ids = [fact["fact_id"] for fact in train]
        test_ids = [fact["fact_id"] for fact in test]
        if set(train_ids) & set(test_ids):
            raise ValueError("train/test leakage")
        task_train_ids[task["task_id"]] = train_ids
        for fact in train:
            row = raw_text_training_example(type("Fact", (), fact)())
            train_by_prompt[row["text"]] = fact

    dataset_paths = sorted((root / "data" / "task_adapter_bank").glob("task-*/train.jsonl"))
    if len(dataset_paths) != 4:
        raise ValueError("dataset panel drift")
    for path in dataset_paths:
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if len(rows) != 32 or any(set(row) != {"text"} for row in rows):
            raise ValueError(f"raw-text dataset shape drift: {path}")
        if any(row["text"] not in train_by_prompt for row in rows):
            raise ValueError(f"raw-text dataset membership drift: {path}")

    for entry in audit:
        task_id = entry["task_id"]
        adapter = root / entry["adapter_relative_path"] / "adapters.safetensors"
        if entry["train_fact_ids"] != task_train_ids[task_id] or entry["dataset_row_count"] != 32:
            raise ValueError(f"audit drift: task {task_id}")
        if entry["resumed_from"] is not None or not adapter.is_file():
            raise ValueError(f"adapter artifact drift: task {task_id}")

    for item in result["task_results"]:
        for key in ("no_update_train", "adapter_train", "adapter_test"):
            metric = item[key]
            if metric["n"] != 8 or len(metric["rows"]) != 8 or not 0 <= metric["accuracy"] <= 1:
                raise ValueError(f"metric shape drift: task {item['task_id']}/{key}")
    gates = v29.eligibility_gates(result["task_results"])
    if gates != result["eligibility_gates"] or result["eligible"] != all(gates.values()):
        raise ValueError("eligibility gate drift")
    if result["audit_sha256"] != base.digest(audit):
        raise ValueError("audit digest mismatch")
    if result["manifest_sha256"] != base.digest({"config": config, "tasks": tasks, "audit": audit}):
        raise ValueError("manifest digest mismatch")
    return {"valid": True, "eligible": result["eligible"], "eligibility_gates": gates, "manifest_sha256": result["manifest_sha256"], "claim_ceiling": CLAIM_CEILING}


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

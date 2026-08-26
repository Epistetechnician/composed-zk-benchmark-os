#!/usr/bin/env python3
"""Independent validator for one V34 Qwen2.5 raw-text case."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_model_benchmark import ANSWER_SUFFIX


STATE_SLICE = "continual-learning-qwen25-raw-text-acquisition-v34"
PROTOCOL = "v34-qwen25-raw-text-acquisition-eligibility-v1"
MODEL = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
ORDER = [0, 1, 2, 3]
SEEDS = [20260856, 20260857, 20260858]
TARGET_FLOOR = 0.75


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def expected_prompt(fact: dict) -> str:
    return (
        "Answer with exactly one letter: A, B, C, or D.\n"
        f"Task token: {fact['task_token']}.\n"
        f"Derived residue: {fact['residue']}.\n"
        "Use the task's residue-to-option codebook and return only the option letter.\n"
        f"Task route binding: {fact['task_token']}.{ANSWER_SUFFIX}"
    )


def _metric_shape(metric: dict) -> None:
    if metric["n"] != 8 or len(metric["rows"]) != 8 or not 0 <= metric["accuracy"] <= 1:
        raise ValueError("metric shape drift")


def validate(root: Path, model: Path, expected_seed: int) -> dict:
    root = root.resolve()
    model = model.resolve()
    if expected_seed not in SEEDS:
        raise ValueError("seed is outside the V34 fixed set")
    config = json.loads((root / "config.json").read_text(encoding="utf8"))
    tasks = json.loads((root / "tasks.json").read_text(encoding="utf8"))
    result = json.loads((root / "result.json").read_text(encoding="utf8"))
    if config["state_slice"] != STATE_SLICE or config["protocol"] != PROTOCOL:
        raise ValueError("state or protocol drift")
    if result["state_slice"] != STATE_SLICE or result["protocol"] != PROTOCOL:
        raise ValueError("result state drift")
    if result["config"] != config or result["tasks"] != tasks:
        raise ValueError("result manifest identity drift")
    if config["model"] != str(model) or config["seed"] != expected_seed or config["order"] != ORDER:
        raise ValueError("model, seed, or order binding drift")
    if config["dataset_format"] != "raw_text_prompt_plus_completion_v1" or config["mask_prompt"] is not False:
        raise ValueError("raw-text serialization contract drift")
    if config["contract_sha256"] != digest({key: value for key, value in config.items() if key != "contract_sha256"}):
        raise ValueError("contract digest mismatch")
    if result["result_sha256"] != digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ValueError("result digest mismatch")
    for key in ("network_access", "retention_executed", "interference_executed", "provider_executed", "production_claim_eligible"):
        if result[key] is not False:
            raise ValueError(f"execution boundary drift: {key}")
    if len(tasks) != 4:
        raise ValueError("task cardinality drift")
    task_train_ids = {}
    for task in tasks:
        if len(task["train_facts"]) != 8 or len(task["test_facts"]) != 8:
            raise ValueError("fact count drift")
        train_ids = [fact["fact_id"] for fact in task["train_facts"]]
        test_ids = [fact["fact_id"] for fact in task["test_facts"]]
        if set(train_ids) & set(test_ids):
            raise ValueError("train/test leakage")
        task_train_ids[task["task_id"]] = train_ids
    datasets = sorted((root / "data" / "task_adapter_bank").glob("task-*/train.jsonl"))
    if len(datasets) != 4:
        raise ValueError("dataset cardinality drift")
    task_by_id = {task["task_id"]: task for task in tasks}
    for path in datasets:
        task_id = int(path.parent.name.split("-")[-1])
        if task_id not in task_by_id:
            raise ValueError(f"dataset task binding drift: {path}")
        task = task_by_id[task_id]
        expected_rows = [
            {"text": expected_prompt(fact) + f" {fact['label']}"}
            for fact in task["train_facts"]
        ]
        expected_rows = (expected_rows * ((32 + len(expected_rows) - 1) // len(expected_rows)))[:32]
        rows = [json.loads(line) for line in path.read_text(encoding="utf8").splitlines()]
        if len(rows) != 32 or any(set(row) != {"text"} for row in rows):
            raise ValueError(f"raw-text dataset shape drift: {path}")
        if rows != expected_rows:
            raise ValueError(f"raw-text prompt/completion binding drift: {path}")
    audit = json.loads((root / "audit" / "task_adapter_bank.json").read_text(encoding="utf8"))
    if len(audit) != 4:
        raise ValueError("audit cardinality drift")
    for entry in audit:
        adapter = root / entry["adapter_relative_path"] / "adapters.safetensors"
        if entry["train_fact_ids"] != task_train_ids[entry["task_id"]] or entry["dataset_row_count"] != 32 or entry["resumed_from"] is not None:
            raise ValueError(f"audit drift for task {entry['task_id']}")
        if entry.get("dataset_format") != "raw_text_prompt_plus_completion_v1" or not adapter.is_file():
            raise ValueError(f"raw-text adapter audit drift for task {entry['task_id']}")
    if result["audit_sha256"] != digest(audit):
        raise ValueError("audit digest mismatch")
    if result["manifest_sha256"] != digest({"config": config, "tasks": tasks, "audit": audit}):
        raise ValueError("manifest digest mismatch")
    if len(result["task_results"]) != 4:
        raise ValueError("task result cardinality drift")
    for item in result["task_results"]:
        for key in ("no_update_train", "adapter_train", "adapter_test"):
            _metric_shape(item[key])
    target = next(item for item in result["task_results"] if item["task_id"] == 0)
    gates = {
        "all_task_train_above_no_update": all(item["adapter_train"]["accuracy"] > item["no_update_train"]["accuracy"] for item in result["task_results"]),
        "target_train_floor": target["adapter_train"]["accuracy"] >= TARGET_FLOOR,
        "target_heldout_floor": target["adapter_test"]["accuracy"] >= TARGET_FLOOR,
        "target_not_constant_output": len({row["observed"] for row in target["adapter_train"]["rows"]}) > 1,
    }
    if result["eligibility_gates"] != gates or result["eligible"] != all(gates.values()):
        raise ValueError("eligibility gate drift")
    return {"valid": True, "eligible": result["eligible"], "eligibility_gates": gates, "result_sha256": result["result_sha256"], "claim_ceiling": result["claim_ceiling"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--expected-seed", type=int, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root, args.model, args.expected_seed), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

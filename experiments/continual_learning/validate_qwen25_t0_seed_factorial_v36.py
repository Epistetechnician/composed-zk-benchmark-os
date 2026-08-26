#!/usr/bin/env python3
"""Independent validator for one V36 target-only diagnosis case."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_model_benchmark import ANSWER_SUFFIX


STATE_SLICE = "continual-learning-qwen25-t0-seed-factorial-diagnosis-v36"
PROTOCOL = "v36-qwen25-t0-task-vs-optimizer-seed-factorial-v1"
MODEL = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
SEEDS = (20260856, 20260857, 20260858)
FAILING_TASK_SEED = 20260857
FIXED_OPTIMIZER_SEED = 20260857


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


def validate(root: Path, arm: str, task_seed: int, optimizer_seed: int, model: Path) -> dict:
    root = root.resolve()
    model = model.resolve()
    if arm not in ("optimizer_seed_arm", "task_seed_arm"):
        raise ValueError("arm drift")
    if task_seed not in SEEDS or optimizer_seed not in SEEDS:
        raise ValueError("seed drift")
    if arm == "optimizer_seed_arm" and task_seed != FAILING_TASK_SEED:
        raise ValueError("optimizer arm task seed drift")
    if arm == "task_seed_arm" and optimizer_seed != FIXED_OPTIMIZER_SEED:
        raise ValueError("task arm optimizer seed drift")
    config = json.loads((root / "config.json").read_text(encoding="utf8"))
    tasks = json.loads((root / "tasks.json").read_text(encoding="utf8"))
    result = json.loads((root / "result.json").read_text(encoding="utf8"))
    if config["state_slice"] != STATE_SLICE or config["protocol"] != PROTOCOL:
        raise ValueError("state/protocol drift")
    if config["model"] != str(model) or config["arm"] != arm or config["task_seed"] != task_seed or config["optimizer_seed"] != optimizer_seed:
        raise ValueError("seed/model binding drift")
    if config["dataset_format"] != "raw_text_prompt_plus_completion_v1" or config["completion_masking"] is not False:
        raise ValueError("raw-text contract drift")
    if config["contract_sha256"] != digest({key: value for key, value in config.items() if key != "contract_sha256"}):
        raise ValueError("contract digest mismatch")
    if result["config"] != config or result["tasks"] != tasks:
        raise ValueError("result identity drift")
    if result["result_sha256"] != digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ValueError("result digest mismatch")
    for key in ("network_access", "retention_executed", "interference_executed", "provider_executed", "production_claim_eligible"):
        if result[key] is not False:
            raise ValueError(f"execution boundary drift: {key}")
    if len(tasks) != 4:
        raise ValueError("task cardinality drift")
    target = next(task for task in tasks if task["task_id"] == 0)
    if len(target["train_facts"]) != 8 or len(target["test_facts"]) != 8:
        raise ValueError("target fact count drift")
    dataset = root / "data" / "target-task-0" / "train.jsonl"
    rows = [json.loads(line) for line in dataset.read_text(encoding="utf8").splitlines()]
    expected = [{"text": expected_prompt(fact) + f" {fact['label']}"} for fact in target["train_facts"]]
    expected = (expected * ((32 + len(expected) - 1) // len(expected)))[:32]
    if rows != expected:
        raise ValueError("target raw-text dataset drift")
    audit = json.loads((root / "audit.json").read_text(encoding="utf8"))
    adapter = root / audit["adapter_relative_path"] / "adapters.safetensors"
    if audit["arm"] != arm or audit["task_seed"] != task_seed or audit["optimizer_seed"] != optimizer_seed:
        raise ValueError("audit seed drift")
    if audit["train_fact_ids"] != [fact["fact_id"] for fact in target["train_facts"]] or audit["dataset_row_count"] != 32:
        raise ValueError("audit dataset drift")
    if not adapter.is_file() or audit["resumed_from"] is not None:
        raise ValueError("adapter artifact drift")
    if result["audit_sha256"] != digest(audit) or result["manifest_sha256"] != digest({"config": config, "tasks": tasks, "audit": audit}):
        raise ValueError("artifact digest mismatch")
    for metric in (result["no_update_train"], result["adapter_train"], result["adapter_test"]):
        _metric_shape(metric)
    gates = {
        "train_above_no_update": result["adapter_train"]["accuracy"] > result["no_update_train"]["accuracy"],
        "heldout_floor": result["adapter_test"]["accuracy"] >= 0.75,
        "not_constant_output": len({row["observed"] for row in result["adapter_train"]["rows"]}) > 1,
    }
    if result["diagnostic_gates"] != gates or result["eligible"] != all(gates.values()):
        raise ValueError("diagnostic gate drift")
    return {"valid": True, "eligible": result["eligible"], "diagnostic_gates": gates, "result_sha256": result["result_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--task-seed", type=int, required=True)
    parser.add_argument("--optimizer-seed", type=int, required=True)
    parser.add_argument("--model", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root, args.arm, args.task_seed, args.optimizer_seed, args.model), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

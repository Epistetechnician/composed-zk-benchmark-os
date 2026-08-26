#!/usr/bin/env python3
"""V30 acquisition-only repair with raw-text train/evaluation parity.

State slice: continual-learning-model-acquisition-eligibility-v30.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import routed_adapter_bank_acquisition_v29 as v29
from experiments.continual_learning.routed_adapter_bank_candidate_v26 import route_bound_prompt_for


STATE_SLICE = "continual-learning-model-acquisition-eligibility-v30"
CLAIM_CEILING = "LocalDevelopmentModelAcquisitionEligibilityPreflight"
PROTOCOL = "v30-qwen36-raw-text-parity-repair-v1"
MODEL_DEFAULT = v29.MODEL_DEFAULT
SEED = v29.SEED
ORDER = v29.ORDER
ITERS = v29.ITERS
UPDATE_BUDGET = v29.UPDATE_BUDGET
TARGET_TASK_ID = v29.TARGET_TASK_ID
TARGET_FLOOR = v29.TARGET_FLOOR


def raw_text_training_example(fact) -> dict[str, str]:
    return {"text": route_bound_prompt_for(fact) + f" {fact.label}"}


def raw_text_training_command(model: Path, dataset: Path, adapter_path: Path, seed: int, iters: int) -> list[str]:
    return [
        arg
        for arg in base.training_command(model, dataset, adapter_path, seed, iters, None)
        if arg != "--mask-prompt"
    ]


def _train_adapter_bank(root: Path, model: Path, tasks, order: tuple[int, ...], seed: int, iters: int, update_budget: int):
    data_root = root / "data" / "task_adapter_bank"
    adapter_root = root / "adapters" / "task_adapter_bank"
    audit_root = root / "audit"
    data_root.mkdir(parents=True, exist_ok=False)
    adapter_root.mkdir(parents=True, exist_ok=False)
    audit_root.mkdir(parents=True, exist_ok=True)
    task_by_id = {task.task_id: task for task in tasks}
    adapters = {}
    audit = []
    for step, task_id in enumerate(order):
        task = task_by_id[task_id]
        rows = [raw_text_training_example(fact) for fact in task.train_facts]
        rows = (rows * ((update_budget + len(rows) - 1) // len(rows)))[:update_budget]
        dataset = data_root / f"task-{task_id}"
        base.write_dataset(dataset, rows)
        adapter_path = adapter_root / f"task-{task_id}"
        command = raw_text_training_command(model, dataset, adapter_path, seed + task_id, iters)
        env = os.environ.copy()
        env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
        (adapter_root / f"task-{task_id}.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf8"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"adapter-bank training failed for task {task_id}: {completed.returncode}")
        adapters[task_id] = adapter_path
        audit.append(
            {
                "step": step,
                "task_id": task_id,
                "route_key": task.task_token,
                "adapter_relative_path": str(adapter_path.relative_to(root)),
                "resumed_from": None,
                "train_fact_ids": [fact.fact_id for fact in task.train_facts],
                "dataset_row_count": len(rows),
                "target_task_id": TARGET_TASK_ID,
            }
        )
    base.write_json(audit_root / "task_adapter_bank.json", audit)
    return adapters, audit


def run(args: argparse.Namespace) -> dict:
    root = args.output.resolve()
    model = args.model.resolve()
    order = tuple(int(value) for value in args.order.split(","))
    if root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {root}")
    if model != MODEL_DEFAULT.resolve() or args.seed != SEED or args.task_count != 4:
        raise ValueError("V30 fixed model/task contract drift")
    if args.iters != ITERS or args.update_budget != UPDATE_BUDGET or order != ORDER:
        raise ValueError("V30 fixed budget/order contract drift")
    if not model.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model}")

    root.mkdir(parents=True)
    tasks = base.make_tasks(args.seed, args.task_count)
    tasks_json = [
        {
            "task_id": task.task_id,
            "task_token": task.task_token,
            "mapping": list(task.mapping),
            "train_facts": [asdict(fact) for fact in task.train_facts],
            "test_facts": [asdict(fact) for fact in task.test_facts],
        }
        for task in tasks
    ]
    config = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "model": str(model),
        "seed": args.seed,
        "order": list(order),
        "task_count": args.task_count,
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "memory_mechanism": "append_only_task_routed_adapter_bank_v1",
        "route_policy": "task_token_exact_v1",
        "dataset_format": "raw_text_prompt_plus_completion_v1",
        "update_budget": UPDATE_BUDGET,
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "iters": ITERS,
        "assessment": "exact_train_and_heldout_acquisition_only_v1",
        "target_task_id": TARGET_TASK_ID,
        "target_floor": TARGET_FLOOR,
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "prompt_contract": {
            "training_prefix_equals_assessment_prefix": True,
            "dataset_chat_template_wrapping": False,
            "derived_residue_visible": True,
            "raw_pair_present": False,
            "route_binding_at_answer_boundary": True,
        },
    }
    config["contract_sha256"] = base.digest(config)
    base.write_json(root / "tasks.json", tasks_json)
    base.write_json(root / "config.json", config)
    adapters, audit = _train_adapter_bank(root, model, tasks, order, args.seed, args.iters, args.update_budget)

    task_by_id = {task.task_id: task for task in tasks}
    task_results = []
    for task_id in range(args.task_count):
        task = task_by_id[task_id]
        no_update_train = v29._isolated_metric(model, root / "tasks.json", task_id, None, "train")
        adapter_train = v29._isolated_metric(model, root / "tasks.json", task_id, adapters[task_id], "train")
        adapter_test = v29._isolated_metric(model, root / "tasks.json", task_id, adapters[task_id], "test")
        for metric in (no_update_train, adapter_train, adapter_test):
            metric["constant_output"] = len({row["observed"] for row in metric["rows"]}) == 1
        task_results.append(
            {
                "task_id": task_id,
                "route_key": task.task_token,
                "no_update_train": no_update_train,
                "adapter_train": adapter_train,
                "adapter_test": adapter_test,
            }
        )
    gates = v29.eligibility_gates(task_results)
    result = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "classification": "Qwen36RawTextParityRepairAcquisitionPreflightNoRetentionClaim",
        "config": config,
        "tasks": tasks_json,
        "task_results": task_results,
        "eligibility_gates": gates,
        "eligible": all(gates.values()),
        "network_access": False,
        "training": True,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "audit_sha256": base.digest(audit),
        "manifest_sha256": base.digest({"config": config, "tasks": tasks_json, "audit": audit}),
    }
    result["result_sha256"] = base.digest(result)
    base.write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--order", default=",".join(str(value) for value in ORDER))
    parser.add_argument("--task-count", type=int, default=4)
    parser.add_argument("--iters", type=int, default=ITERS)
    parser.add_argument("--update-budget", type=int, default=UPDATE_BUDGET)
    result = run(parser.parse_args())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

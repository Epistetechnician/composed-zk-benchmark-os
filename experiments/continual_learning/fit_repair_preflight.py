#!/usr/bin/env python3
"""V13 fit-only optimization repair preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_calibration_benchmark import make_tasks  # noqa: E402
from experiments.continual_learning.compositional_model_benchmark import (  # noqa: E402
    ANSWER_SUFFIX,
    ChoiceModel,
    training_command,
    write_dataset,
)
from experiments.continual_learning.residue_only_codebook_benchmark import (  # noqa: E402
    residue_only_accuracy,
    residue_only_prompt_for,
    residue_only_training_example,
)
from experiments.continual_learning.training_fit_audit import parse_training_receipt  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v13-training-objective-repair"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf8")


def run_control(root: Path, model: Path, facts: tuple, strategy: str, adapter_relative: str, seed: int, iters: int) -> dict:
    rows = [residue_only_training_example(fact) for fact in facts]
    rows = (rows * ((32 + len(rows) - 1) // len(rows)))[:32]
    dataset = root / "data" / strategy
    write_dataset(dataset, rows)
    adapter_path = root / adapter_relative
    command = training_command(model, dataset, adapter_path, seed, iters, None)
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    log_path = root / f"{adapter_relative}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
    if completed.returncode != 0:
        raise RuntimeError(f"fit-repair training failed for {strategy}: {completed.returncode}")
    fitted = ChoiceModel(model, adapter_path)
    metric = residue_only_accuracy(fitted, facts)
    return {
        "strategy": strategy,
        "adapter_relative_path": adapter_relative,
        "dataset_relative_path": str(dataset.relative_to(root)),
        "dataset_row_count": len(rows),
        "train_accuracy": {"correct": metric["correct"], "n": metric["n"], "accuracy": metric["accuracy"]},
        "receipt": parse_training_receipt(log_path),
    }


def run(args: argparse.Namespace) -> dict:
    root = args.output.resolve()
    if root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {root}")
    root.mkdir(parents=True)
    model = args.model.resolve()
    if not model.is_dir():
        raise RuntimeError(f"model path does not exist: {model}")
    tasks = make_tasks(args.seed, 4)
    target = tasks[0].train_facts
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
    write_json(root / "tasks.json", tasks_json)
    config = {
        "state_slice": STATE_SLICE,
        "source_state_slice": "continual-learning-protocol-v12-training-fit-audit",
        "model": str(model),
        "seed": args.seed,
        "order": [0, 1, 2, 3],
        "task_count": 4,
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "solvability_control": "residue_only_v1",
        "fit_repair": "iterations_only_v1",
        "baseline_iters": 40,
        "iters": args.iters,
        "update_budget": 32,
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "mask_prompt": True,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "audit_schema": "fit_repair_preflight_audit_v1",
        "fit_floor_threshold": 0.75,
        "prompt_contract": {
            "training_prompt_equals_assessment_prompt": True,
            "answer_suffix": ANSWER_SUFFIX,
            "derived_residue_visible": True,
            "raw_pair_present": False,
        },
    }
    config["contract_sha256"] = digest(config)
    write_json(root / "config.json", config)
    controls = [
        run_control(root, model, target, "naive_fit", "adapters/naive_fit", args.seed, args.iters),
        run_control(root, model, target, "task_adapter_bank_fit", "adapters/task_adapter_bank_fit", args.seed, args.iters),
    ]
    base_model = ChoiceModel(model)
    token_supervision = {
        "candidate_token_lengths": {label: len(ids) for label, ids in base_model.candidate_ids.items()},
        "single_token_labels": all(len(ids) == 1 for ids in base_model.candidate_ids.values()),
    }
    parity_failures = []
    rows_checked = 0
    expected_prompts = {residue_only_prompt_for(fact): fact for fact in target}
    for control in controls:
        for line_number, line in enumerate((root / control["dataset_relative_path"] / "train.jsonl").read_text().splitlines(), start=1):
            rows_checked += 1
            row = json.loads(line)
            fact = expected_prompts.get(row["prompt"])
            if fact is None or row["completion"] != f" {fact.label}":
                parity_failures.append({"strategy": control["strategy"], "line": line_number})
    gates = {
        "prompt_completion_parity": not parity_failures and rows_checked == 64,
        "single_token_label_supervision": token_supervision["single_token_labels"],
        "naive_fit_floor": controls[0]["train_accuracy"]["accuracy"] >= config["fit_floor_threshold"],
        "bank_fit_floor": controls[1]["train_accuracy"]["accuracy"] >= config["fit_floor_threshold"],
        "training_receipts_complete": all(control["receipt"]["final_weights_saved"] for control in controls),
    }
    result = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentTrainingObjectiveRepairPilot",
        "classification": "TrainingObjectiveRepairPilotNoBreakthroughClaim",
        "config": config,
        "tasks": tasks_json,
        "controls": controls,
        "dataset_parity": {
            "rows_checked": rows_checked,
            "expected_rows": 64,
            "parity_failures": parity_failures,
            "exact_prompt_completion_parity": gates["prompt_completion_parity"],
        },
        "token_supervision": token_supervision,
        "gates": gates,
        "fit_floor_passed": all(gates.values()),
        "retention_comparison_run": False,
        "breakthrough_claim_eligible": False,
    }
    result["manifest_sha256"] = digest({"config": config, "tasks": tasks_json, "controls": controls})
    result["result_sha256"] = digest(result)
    write_json(root / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--iters", type=int, default=160)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

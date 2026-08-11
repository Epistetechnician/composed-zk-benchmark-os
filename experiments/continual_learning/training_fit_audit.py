#!/usr/bin/env python3
"""V12 read-only audit of V11 training fit and supervision boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.compositional_calibration_benchmark import make_tasks  # noqa: E402
from experiments.continual_learning.compositional_model_benchmark import ChoiceModel  # noqa: E402
from experiments.continual_learning.residue_only_codebook_benchmark import residue_only_accuracy, residue_only_prompt_for  # noqa: E402


STATE_SLICE = "continual-learning-protocol-v12-training-fit-audit"
SOURCE_STATE_SLICE = "continual-learning-protocol-v11-residue-only-codebook"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")
TRAIN_RE = re.compile(r"Iter\s+(\d+): Train loss ([0-9.]+).*?Peak mem ([0-9.]+) GB")
VAL_RE = re.compile(r"Iter\s+(\d+): Val loss ([0-9.]+)")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def summarize(metric: dict) -> dict:
    return {"correct": metric["correct"], "n": metric["n"], "accuracy": metric["accuracy"]}


def parse_training_receipt(path: Path) -> dict:
    text = path.read_text(encoding="utf8")
    train = [(int(step), float(loss), float(memory)) for step, loss, memory in TRAIN_RE.findall(text)]
    validation = [(int(step), float(loss)) for step, loss in VAL_RE.findall(text)]
    if not train or not validation or "Saved final weights" not in text:
        raise ValueError(f"incomplete training receipt: {path}")
    step, train_loss, peak_memory = train[-1]
    val_step, val_loss = validation[-1]
    return {
        "log_relative_path": str(path),
        "final_train_step": step,
        "final_train_loss": train_loss,
        "final_val_step": val_step,
        "final_val_loss": val_loss,
        "peak_memory_gb": max(memory for _, _, memory in train),
        "final_weights_saved": True,
        "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def audit_dataset_parity(root: Path, facts: tuple) -> dict:
    fact_by_prompt = {residue_only_prompt_for(fact): fact for fact in facts if fact.split == "train"}
    paths = sorted((root / "data").glob("*/step-*/train.jsonl"))
    paths.extend(sorted((root / "data" / "task_adapter_bank").glob("task-*/train.jsonl")))
    failures = []
    rows_checked = 0
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf8").splitlines(), start=1):
            rows_checked += 1
            row = json.loads(line)
            fact = fact_by_prompt.get(row.get("prompt"))
            if fact is None or row.get("completion") != f" {fact.label}" or not row["prompt"].endswith("\nAnswer:"):
                failures.append({"path": str(path), "line": line_number})
    return {
        "dataset_count": len(paths),
        "rows_checked": rows_checked,
        "expected_dataset_count": 12,
        "expected_rows": 384,
        "parity_failures": failures,
        "exact_prompt_completion_parity": not failures and len(paths) == 12 and rows_checked == 384,
    }


def adapter_fit_audit(root: Path, model_path: Path, tasks: tuple) -> dict:
    task_by_id = {task.task_id: task for task in tasks}
    entries = []
    receipts = []
    for strategy in ("naive_sequential_lora", "replay_lora"):
        for step, task_id in enumerate((0, 1, 2, 3)):
            adapter_relative = f"adapters/{strategy}/step-{step}"
            adapter_path = root / adapter_relative
            model = ChoiceModel(model_path, adapter_path)
            target_fit = residue_only_accuracy(model, task_by_id[0].train_facts)
            current_fit = residue_only_accuracy(model, task_by_id[task_id].train_facts)
            entries.append(
                {
                    "strategy": strategy,
                    "step": step,
                    "task_id": task_id,
                    "adapter_relative_path": adapter_relative,
                    "target_task_train_accuracy": summarize(target_fit),
                    "current_task_train_accuracy": summarize(current_fit),
                }
            )
            receipts.append(parse_training_receipt(root / "adapters" / strategy / f"step-{step}.log"))
    bank_entries = []
    for task_id in range(4):
        adapter_relative = f"adapters/task_adapter_bank/task-{task_id}"
        adapter_path = root / adapter_relative
        model = ChoiceModel(model_path, adapter_path)
        task_fit = residue_only_accuracy(model, task_by_id[task_id].train_facts)
        target_fit = residue_only_accuracy(model, task_by_id[0].train_facts)
        bank_entries.append(
            {
                "strategy": "task_adapter_bank",
                "step": task_id,
                "task_id": task_id,
                "adapter_relative_path": adapter_relative,
                "target_task_train_accuracy": summarize(target_fit),
                "current_task_train_accuracy": summarize(task_fit),
            }
        )
        receipts.append(parse_training_receipt(root / "adapters" / "task_adapter_bank" / f"task-{task_id}.log"))
    entries.extend(bank_entries)
    target_naive = next(
        entry["target_task_train_accuracy"]["accuracy"]
        for entry in entries
        if entry["strategy"] == "naive_sequential_lora" and entry["step"] == 3
    )
    target_bank = next(
        entry["target_task_train_accuracy"]["accuracy"]
        for entry in entries
        if entry["strategy"] == "task_adapter_bank" and entry["task_id"] == 0
    )
    return {
        "entries": entries,
        "entry_count": len(entries),
        "expected_entry_count": 12,
        "naive_final_target_train_accuracy": target_naive,
        "bank_task0_train_accuracy": target_bank,
        "fit_floor_threshold": 0.75,
        "naive_final_fit_floor": target_naive >= 0.75,
        "bank_task0_fit_floor": target_bank >= 0.75,
        "training_receipts": receipts,
    }


def run(args: argparse.Namespace) -> dict:
    source_root = args.source.resolve()
    report_root = args.output.resolve()
    if report_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {report_root}")
    source_result = json.loads((source_root / "result.json").read_text(encoding="utf8"))
    config = json.loads((source_root / "config.json").read_text(encoding="utf8"))
    if source_result["state_slice"] != SOURCE_STATE_SLICE:
        raise ValueError("unexpected source state slice")
    if config["contract_sha256"] != source_result["config"]["contract_sha256"]:
        raise ValueError("source config mismatch")
    model_path = Path(config["model"])
    tasks = make_tasks(config["seed"], config["task_count"])
    all_facts = tuple(fact for task in tasks for fact in task.train_facts + task.test_facts)
    parity = audit_dataset_parity(source_root, all_facts)
    token_model = ChoiceModel(model_path)
    token_supervision = {
        "labels": ["A", "B", "C", "D"],
        "candidate_token_lengths": {label: len(ids) for label, ids in token_model.candidate_ids.items()},
        "single_token_labels": all(len(ids) == 1 for ids in token_model.candidate_ids.values()),
    }
    fit = adapter_fit_audit(source_root, model_path, tasks)
    gates = {
        "prompt_completion_parity": parity["exact_prompt_completion_parity"],
        "single_token_label_supervision": token_supervision["single_token_labels"],
        "naive_final_fit_floor": fit["naive_final_fit_floor"],
        "bank_task0_fit_floor": fit["bank_task0_fit_floor"],
        "training_receipts_complete": all(receipt["final_weights_saved"] for receipt in fit["training_receipts"]),
    }
    report = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "source_root": str(source_root),
        "source_manifest_sha256": source_result["manifest_sha256"],
        "source_contract_sha256": config["contract_sha256"],
        "classification": "TrainingFitAuditNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentTrainingFitAudit",
        "dataset_parity": parity,
        "token_supervision": token_supervision,
        "adapter_fit": fit,
        "gates": gates,
        "fit_floor_passed": all(gates.values()),
        "breakthrough_claim_eligible": False,
    }
    report["report_sha256"] = digest(report)
    report_root.mkdir(parents=True)
    (report_root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

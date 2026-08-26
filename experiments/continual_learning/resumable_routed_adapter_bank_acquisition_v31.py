#!/usr/bin/env python3
"""V31 resumable control plane for the V30 raw-text acquisition repair.

State slice: continual-learning-model-acquisition-eligibility-v31-resumable.

This module separates task-artifact recovery from assessment.  A V30 output
directory is read-only input; every V31 output directory is new and immutable.
No incomplete task bank can emit an eligible result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import routed_adapter_bank_acquisition_v29 as v29
from experiments.continual_learning.routed_adapter_bank_acquisition_v30 import (
    CLAIM_CEILING,
    MODEL_DEFAULT,
    ORDER,
    PROTOCOL as SOURCE_PROTOCOL,
    SEED,
    TARGET_FLOOR,
    raw_text_training_command,
)


STATE_SLICE = "continual-learning-model-acquisition-eligibility-v31-resumable"
PROTOCOL = "v31-v30-raw-text-resume-control-v1"
SOURCE_STATE_SLICE = "continual-learning-model-acquisition-eligibility-v30"
MAX_PEAK_MEMORY_GB = 26.0
MAX_TASK_ELAPSED_S = 1800.0
PEAK_MEMORY_PATTERN = re.compile(r"Peak mem ([0-9]+(?:\.[0-9]+)?) GB")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf8"))


def write_immutable_json(path: Path, value) -> None:
    if path.exists():
        raise RuntimeError(f"refusing overwrite of immutable artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    base.write_json(path, value)


def task_artifact_path(source_root: Path, task_id: int) -> Path:
    return source_root / "adapters" / "task_adapter_bank" / f"task-{task_id}" / "adapters.safetensors"


def task_log_path(source_root: Path, task_id: int) -> Path:
    return source_root / "adapters" / "task_adapter_bank" / f"task-{task_id}.log"


def _expected_tasks(seed: int, task_count: int) -> list[dict]:
    return [
        {
            "task_id": task.task_id,
            "task_token": task.task_token,
            "mapping": list(task.mapping),
            "train_facts": [asdict(fact) for fact in task.train_facts],
            "test_facts": [asdict(fact) for fact in task.test_facts],
        }
        for task in base.make_tasks(seed, task_count)
    ]


def _source_config(config: dict) -> dict:
    return {key: value for key, value in config.items() if key != "contract_sha256"}


def _validate_source_contract(source_root: Path, model: Path) -> tuple[dict, list[dict], list[dict]]:
    config = read_json(source_root / "config.json")
    tasks = read_json(source_root / "tasks.json")
    audit = read_json(source_root / "audit" / "task_adapter_bank.json")
    if config["state_slice"] != SOURCE_STATE_SLICE or config["protocol"] != SOURCE_PROTOCOL:
        raise ValueError("resume source is not the V30 raw-text contract")
    if config["model"] != str(model) or config["seed"] != SEED or config["order"] != list(ORDER):
        raise ValueError("resume source model or fixed-order binding drift")
    if config["dataset_format"] != "raw_text_prompt_plus_completion_v1":
        raise ValueError("resume source dataset format drift")
    if config["contract_sha256"] != base.digest(_source_config(config)):
        raise ValueError("resume source contract digest mismatch")
    expected = _expected_tasks(SEED, 4)
    if tasks != expected:
        raise ValueError("resume source task manifest drift")
    if len(audit) != 4 or {entry["task_id"] for entry in audit} != set(range(4)):
        raise ValueError("resume source audit cardinality drift")
    return config, tasks, sorted(audit, key=lambda entry: entry["task_id"])


def _validate_task_dataset(source_root: Path, task: dict) -> str:
    path = source_root / "data" / "task_adapter_bank" / f"task-{task['task_id']}" / "train.jsonl"
    if not path.is_file():
        raise ValueError(f"missing task dataset: {path}")
    rows = [json.loads(line) for line in path.read_text(encoding="utf8").splitlines()]
    if len(rows) != 32 or any(set(row) != {"text"} for row in rows):
        raise ValueError(f"task dataset shape drift: {path}")
    return sha256_file(path)


def _observed_peak_memory(source_root: Path) -> float | None:
    values = []
    for path in sorted((source_root / "adapters" / "task_adapter_bank").glob("task-*.log")):
        values.extend(float(match.group(1)) for match in PEAK_MEMORY_PATTERN.finditer(path.read_text(encoding="utf8")))
    return max(values) if values else None


def inspect_resume_source(source_root: Path, model: Path) -> dict:
    """Validate a frozen V30 source and classify each task without mutation."""

    source_root = source_root.resolve()
    config, tasks, audit = _validate_source_contract(source_root, model.resolve())
    audit_by_id = {entry["task_id"]: entry for entry in audit}
    task_records = []
    for task in tasks:
        task_id = task["task_id"]
        dataset_digest = _validate_task_dataset(source_root, task)
        adapter = task_artifact_path(source_root, task_id)
        log = task_log_path(source_root, task_id)
        entry = audit_by_id[task_id]
        if entry["train_fact_ids"] != [fact["fact_id"] for fact in task["train_facts"]] or entry["dataset_row_count"] != 32:
            raise ValueError(f"resume source audit drift for task {task_id}")
        adapter_config = adapter.parent / "adapter_config.json"
        if adapter.is_file() and not adapter_config.is_file():
            raise ValueError(f"adapter config missing for task {task_id}")
        if adapter.is_file():
            task_records.append(
                {
                    "task_id": task_id,
                    "status": "complete",
                    "adapter_relative_path": str(adapter.relative_to(source_root)),
                    "adapter_path": str(adapter),
                    "adapter_sha256": sha256_file(adapter),
                    "training_log_sha256": sha256_file(log) if log.is_file() else None,
                    "dataset_sha256": dataset_digest,
                    "source": "v30",
                }
            )
        else:
            task_records.append(
                {
                    "task_id": task_id,
                    "status": "pending",
                    "adapter_relative_path": str(adapter.relative_to(source_root)),
                    "adapter_path": str(adapter),
                    "adapter_sha256": None,
                    "training_log_sha256": sha256_file(log) if log.is_file() else None,
                    "dataset_sha256": dataset_digest,
                    "source": "v30",
                }
            )
    manifest = {
        "source_state_slice": SOURCE_STATE_SLICE,
        "source_protocol": SOURCE_PROTOCOL,
        "source_root": str(source_root),
        "config_sha256": base.digest(config),
        "tasks_sha256": base.digest(tasks),
        "audit_sha256": base.digest(audit),
        "task_records": task_records,
    }
    manifest["manifest_sha256"] = base.digest(manifest)
    return {
        "config": config,
        "tasks": tasks,
        "audit": audit,
        "manifest": manifest,
        "task_records": task_records,
        "completed_task_ids": [record["task_id"] for record in task_records if record["status"] == "complete"],
        "missing_task_ids": [record["task_id"] for record in task_records if record["status"] != "complete"],
        "observed_peak_memory_gb": _observed_peak_memory(source_root),
    }


def validate_task_receipt(receipt: dict) -> None:
    if receipt["status"] not in {"pending", "running", "complete", "failed", "unknown"}:
        raise ValueError("unknown task receipt status")
    if receipt["status"] == "complete":
        adapter = Path(receipt["adapter_path"])
        if not adapter.is_file() or not receipt.get("adapter_sha256"):
            raise ValueError("completed task receipt requires an adapter artifact")
        if sha256_file(adapter) != receipt["adapter_sha256"]:
            raise ValueError("completed task adapter digest mismatch")
    if receipt["status"] == "failed" and not receipt.get("failure_reason"):
        raise ValueError("failed task receipt requires a failure reason")


def evaluate_resource_guard(
    *,
    observed_peak_memory_gb: float | None,
    projected_peak_memory_gb: float | None,
    projected_task_elapsed_s: float | None,
    max_peak_memory_gb: float = MAX_PEAK_MEMORY_GB,
    max_task_elapsed_s: float = MAX_TASK_ELAPSED_S,
    operator_override: bool = False,
) -> dict:
    reasons = []
    projected_peak = projected_peak_memory_gb if projected_peak_memory_gb is not None else observed_peak_memory_gb
    if projected_peak is None:
        reasons.append("missing_peak_memory_projection")
    elif projected_peak > max_peak_memory_gb:
        reasons.append("peak_memory_budget_exceeded")
    if projected_task_elapsed_s is None:
        reasons.append("missing_task_elapsed_projection")
    elif projected_task_elapsed_s > max_task_elapsed_s:
        reasons.append("task_elapsed_budget_exceeded")
    return {
        "allowed": bool(operator_override or not reasons),
        "operator_override": operator_override,
        "observed_peak_memory_gb": observed_peak_memory_gb,
        "projected_peak_memory_gb": projected_peak,
        "projected_task_elapsed_s": projected_task_elapsed_s,
        "max_peak_memory_gb": max_peak_memory_gb,
        "max_task_elapsed_s": max_task_elapsed_s,
        "reasons": reasons,
    }


def eligible_from_state(task_records: list[dict], assessment_complete: bool) -> bool:
    return bool(assessment_complete and task_records and all(record["status"] == "complete" for record in task_records))


def prepare_output_root(root: Path) -> Path:
    root = root.resolve()
    if root.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {root}")
    root.mkdir(parents=True)
    return root


def _write_task_event(root: Path, record: dict) -> None:
    validate_task_receipt(record)
    write_immutable_json(root / "task_receipts" / f"task-{record['task_id']}.{record['status']}.json", record)


def _run_missing_task(root: Path, source: dict, task_id: int, model: Path, seed: int, iters: int) -> dict:
    task_dataset = Path(source["manifest"]["source_root"]) / "data" / "task_adapter_bank" / f"task-{task_id}"
    adapter_path = root / "adapters" / "task_adapter_bank" / f"task-{task_id}"
    log_path = root / "adapters" / "task_adapter_bank" / f"task-{task_id}.log"
    running = {
        "task_id": task_id,
        "status": "running",
        "adapter_path": str(adapter_path),
        "adapter_sha256": None,
        "dataset_sha256": sha256_file(task_dataset / "train.jsonl"),
        "training_log_sha256": None,
        "source": "v31-resume",
    }
    _write_task_event(root, running)
    started = time.perf_counter()
    command = raw_text_training_command(model, task_dataset, adapter_path, seed + task_id, iters)
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    guard = read_json(root / "resource_guard.json")
    timeout_s = int(guard["max_task_elapsed_s"])
    try:
        completed = subprocess.run(command, env=env, text=True, capture_output=True, check=False, timeout=timeout_s)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf8")
        if completed.returncode != 0:
            raise RuntimeError(f"training_exit_{completed.returncode}")
        adapter = adapter_path / "adapters.safetensors"
        if not adapter.is_file():
            raise RuntimeError("training_completed_without_adapter")
        record = {
            "task_id": task_id,
            "status": "complete",
            "adapter_path": str(adapter),
            "adapter_sha256": sha256_file(adapter),
            "dataset_sha256": sha256_file(task_dataset / "train.jsonl"),
            "training_log_sha256": sha256_file(log_path),
            "elapsed_s": round(time.perf_counter() - started, 3),
            "source": "v31-resume",
        }
    except subprocess.TimeoutExpired as exc:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text((exc.stdout or "") + "\n" + (exc.stderr or ""), encoding="utf8")
        record = {
            "task_id": task_id,
            "status": "failed",
            "adapter_path": str(adapter_path / "adapters.safetensors"),
            "adapter_sha256": None,
            "dataset_sha256": sha256_file(task_dataset / "train.jsonl"),
            "training_log_sha256": sha256_file(log_path),
            "elapsed_s": round(time.perf_counter() - started, 3),
            "failure_reason": "task_timeout",
            "source": "v31-resume",
        }
    except Exception as exc:
        record = {
            "task_id": task_id,
            "status": "failed",
            "adapter_path": str(adapter_path / "adapters.safetensors"),
            "adapter_sha256": None,
            "dataset_sha256": sha256_file(task_dataset / "train.jsonl"),
            "training_log_sha256": sha256_file(log_path) if log_path.is_file() else None,
            "elapsed_s": round(time.perf_counter() - started, 3),
            "failure_reason": str(exc),
            "source": "v31-resume",
        }
    _write_task_event(root, record)
    return record


def run(args: argparse.Namespace) -> dict:
    model = args.model.resolve()
    source = inspect_resume_source(args.resume_source, model)
    guard = evaluate_resource_guard(
        observed_peak_memory_gb=source["observed_peak_memory_gb"],
        projected_peak_memory_gb=args.projected_peak_memory_gb,
        projected_task_elapsed_s=args.projected_task_elapsed_s,
        operator_override=args.allow_resource_override,
    )
    root = prepare_output_root(args.output)
    write_immutable_json(root / "source_manifest.json", source["manifest"])
    write_immutable_json(root / "tasks.json", source["tasks"])
    config = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "source_state_slice": SOURCE_STATE_SLICE,
        "source_protocol": SOURCE_PROTOCOL,
        "source_manifest_sha256": source["manifest"]["manifest_sha256"],
        "model": str(model),
        "seed": SEED,
        "order": list(ORDER),
        "target_floor": TARGET_FLOOR,
        "claim_ceiling": CLAIM_CEILING,
        "network_access": False,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
    }
    config["contract_sha256"] = base.digest(config)
    write_immutable_json(root / "config.json", config)
    write_immutable_json(root / "resource_guard.json", guard)

    records = []
    for record in source["task_records"]:
        if record["status"] == "complete":
            _write_task_event(root, record)
            records.append(record)
        else:
            pending = dict(record)
            pending["status"] = "pending"
            _write_task_event(root, pending)
            records.append(pending)
    if source["missing_task_ids"] and args.execute_missing:
        if not guard["allowed"]:
            run_status = "incomplete"
            failure_reason = "resource_guard_rejected"
        else:
            for task_id in source["missing_task_ids"]:
                record = _run_missing_task(root, source, task_id, model, SEED, v29.ITERS)
                records = [item for item in records if item["task_id"] != task_id] + [record]
                if record["status"] != "complete":
                    break
            run_status = "ready_for_assessment" if all(item["status"] == "complete" for item in records) else "incomplete"
            failure_reason = None if run_status == "ready_for_assessment" else "task_resume_incomplete"
    elif source["missing_task_ids"]:
        run_status = "incomplete"
        failure_reason = "missing_tasks_not_executed"
    else:
        run_status = "ready_for_assessment"
        failure_reason = None
    run_receipt = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "status": run_status,
        "task_ids": sorted(item["task_id"] for item in records),
        "task_statuses": {str(item["task_id"]): item["status"] for item in sorted(records, key=lambda item: item["task_id"])},
        "resource_guard_allowed": guard["allowed"],
        "failure_reason": failure_reason,
        "eligible": False,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
    }
    run_receipt["receipt_sha256"] = base.digest(run_receipt)
    write_immutable_json(root / "run_receipt.json", run_receipt)
    return run_receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--execute-missing", action="store_true")
    parser.add_argument("--projected-peak-memory-gb", type=float)
    parser.add_argument("--projected-task-elapsed-s", type=float)
    parser.add_argument("--allow-resource-override", action="store_true")
    args = parser.parse_args()
    try:
        receipt = run(args)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 1 if receipt["status"] == "incomplete" else 0
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

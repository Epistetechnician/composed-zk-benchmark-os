from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import routed_adapter_bank_acquisition_v30 as v30
from experiments.continual_learning import resumable_routed_adapter_bank_acquisition_v31 as v31
from experiments.continual_learning.resumable_routed_adapter_bank_acquisition_v31 import (
    CLAIM_CEILING,
    MODEL_DEFAULT,
    PROTOCOL,
    SEED,
    STATE_SLICE,
    _expected_tasks,
    eligible_from_state,
    evaluate_resource_guard,
    inspect_resume_source,
    prepare_output_root,
    run,
    validate_task_receipt,
)
from experiments.continual_learning.validate_resumable_routed_adapter_bank_acquisition_v31 import validate


def _source_config() -> dict:
    config = {
        "state_slice": v30.STATE_SLICE,
        "protocol": v30.PROTOCOL,
        "model": str(MODEL_DEFAULT),
        "seed": SEED,
        "order": [0, 1, 2, 3],
        "task_count": 4,
        "train_facts_per_task": 8,
        "test_facts_per_task": 8,
        "task_rule": "mod4_sum_then_task_shift_v2",
        "mapping_policy": "task_id_shift_v1",
        "split_policy": "two_train_two_test_per_residue_v1",
        "memory_mechanism": "append_only_task_routed_adapter_bank_v1",
        "route_policy": "task_token_exact_v1",
        "dataset_format": "raw_text_prompt_plus_completion_v1",
        "update_budget": 32,
        "optimizer": "adamw",
        "learning_rate": 0.0001,
        "batch_size": 2,
        "num_layers": 8,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "iters": 160,
        "assessment": "exact_train_and_heldout_acquisition_only_v1",
        "target_task_id": 0,
        "target_floor": 0.75,
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
    return config


def _write_source(tmp_path: Path, complete_tasks: tuple[int, ...] = (0, 1, 2)) -> Path:
    root = tmp_path / "source"
    tasks = _expected_tasks(SEED, 4)
    (root / "audit").mkdir(parents=True)
    for task in tasks:
        task_id = task["task_id"]
        data_root = root / "data" / "task_adapter_bank" / f"task-{task_id}"
        data_root.mkdir(parents=True)
        rows = [
            v30.raw_text_training_example(type("Fact", (), fact)())
            for fact in task["train_facts"]
        ]
        rows = (rows * 4)[:32]
        for filename in ("train.jsonl", "valid.jsonl", "test.jsonl"):
            (data_root / filename).write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf8"
            )
        adapter_root = root / "adapters" / "task_adapter_bank" / f"task-{task_id}"
        if task_id in complete_tasks:
            adapter_root.mkdir(parents=True)
            (adapter_root / "adapters.safetensors").write_bytes(f"adapter-{task_id}".encode())
            (adapter_root / "adapter_config.json").write_text("{}\n", encoding="utf8")
        log_root = root / "adapters" / "task_adapter_bank"
        log_root.mkdir(parents=True, exist_ok=True)
        (log_root / f"task-{task_id}.log").write_text("Peak mem 25.551 GB\n", encoding="utf8")
    audit = [
        {
            "step": task_id,
            "task_id": task_id,
            "route_key": task["task_token"],
            "adapter_relative_path": f"adapters/task_adapter_bank/task-{task_id}",
            "resumed_from": None,
            "train_fact_ids": [fact["fact_id"] for fact in task["train_facts"]],
            "dataset_row_count": 32,
            "target_task_id": 0,
        }
        for task_id, task in enumerate(tasks)
    ]
    (root / "config.json").write_text(json.dumps(_source_config(), sort_keys=True), encoding="utf8")
    (root / "tasks.json").write_text(json.dumps(tasks, sort_keys=True), encoding="utf8")
    (root / "audit" / "task_adapter_bank.json").write_text(json.dumps(audit, sort_keys=True), encoding="utf8")
    return root


def test_completed_task_receipt_requires_adapter_file(tmp_path):
    receipt = {"task_id": 3, "status": "complete", "adapter_path": str(tmp_path / "missing.safetensors")}
    with pytest.raises(ValueError, match="requires an adapter"):
        validate_task_receipt(receipt)


def test_partial_source_validates_and_identifies_missing_t3(tmp_path):
    source = _write_source(tmp_path)
    inspected = inspect_resume_source(source, MODEL_DEFAULT)
    assert inspected["completed_task_ids"] == [0, 1, 2]
    assert inspected["missing_task_ids"] == [3]
    assert inspected["observed_peak_memory_gb"] == 25.551


def test_failed_task_cannot_make_state_eligible():
    records = [{"task_id": 0, "status": "failed"}, {"task_id": 1, "status": "complete"}]
    assert eligible_from_state(records, True) is False


def test_output_root_is_immutable(tmp_path):
    root = prepare_output_root(tmp_path / "output")
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        prepare_output_root(root)


def test_resource_guard_rejects_over_budget_projection():
    guard = evaluate_resource_guard(
        observed_peak_memory_gb=25.551,
        projected_peak_memory_gb=26.5,
        projected_task_elapsed_s=300,
    )
    assert guard["allowed"] is False
    assert "peak_memory_budget_exceeded" in guard["reasons"]


def test_incomplete_run_is_independently_validated_and_not_eligible(tmp_path):
    source = _write_source(tmp_path)
    output = tmp_path / "v31"
    receipt = run(
        Namespace(
            resume_source=source,
            output=output,
            model=MODEL_DEFAULT,
            execute_missing=False,
            projected_peak_memory_gb=25.8,
            projected_task_elapsed_s=300.0,
            allow_resource_override=False,
        )
    )
    assert receipt["state_slice"] == STATE_SLICE
    assert receipt["protocol"] == PROTOCOL
    assert receipt["status"] == "incomplete"
    assert receipt["eligible"] is False
    report = validate(output)
    assert report["valid"] is True
    assert report["eligible"] is False
    assert report["claim_ceiling"] == CLAIM_CEILING


def test_incomplete_cli_run_returns_nonzero(tmp_path, monkeypatch):
    source = _write_source(tmp_path)
    output = tmp_path / "v31-cli"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "resumable_routed_adapter_bank_acquisition_v31.py",
            "--resume-source",
            str(source),
            "--output",
            str(output),
            "--projected-peak-memory-gb",
            "25.8",
            "--projected-task-elapsed-s",
            "300",
        ],
    )
    assert v31.main() == 1

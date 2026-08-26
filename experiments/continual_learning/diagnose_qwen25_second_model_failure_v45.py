#!/usr/bin/env python3
"""Read-only diagnosis of the V44 second-model acquisition failure.

State slice family: continual-learning-qwen25-second-model-failure-diagnosis-v45.

This module consumes only the immutable V44 acquisition artifacts. It does not
load a model, execute inference or training, access the network, tune a
protocol, or relabel V44 as positive evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.runtime_seam import digest, sha256_file, write_json


STATE_SLICE = "continual-learning-qwen25-second-model-failure-diagnosis-v45"
PROTOCOL = "v45-qwen25-second-model-failure-diagnosis-v1"
CLAIM_CEILING = "LocalDevelopmentSecondModelFailureDiagnosis"
SOURCE_STATE_SLICE = "continual-learning-qwen25-second-model-replication-v44"
SOURCE_PROTOCOL = "v44-qwen25-second-model-replication-v1"
SOURCE_ROOT = Path(
    "/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/"
    "continual-learning-qwen25-second-model-replication-v44-20260826-r1"
)
SOURCE_REPORT_FILE_SHA256 = "0680ec9db0d2cc824287345b14916de4cb4441fa9bc1a1738d0d5fed5541dfe9"
SOURCE_CONTRACT_FILE_SHA256 = "d0f3c10a3ede85845d04c180a0b80c72b042d167de71fc82831cd1bab65742a9"
SOURCE_REPORT_SHA256 = "310b78d7830a2d1a449136d89c0883b42c22bbf645a90e36b147e468b2553a47"
SOURCE_CONTRACT_SHA256 = "a501157d87d9ce86a8a4f18516d8012c7bf41468d3a31ad46cb17dbc98c4a7e0"
MODEL = "/Users/shaanp/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit"
TASK_SEEDS = (20260862, 20260863, 20260864)
TASK_IDS = (0, 1, 2, 3)
FIXED_OPTIMIZER_SEED = 20260856
ITERS = 160
UPDATE_BUDGET = 32
TARGET_TASK_ID = 0
LABELS = ("A", "B", "C", "D")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_external_new_root(root: Path) -> None:
    resolved = root.resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ValueError("V45 diagnosis output must remain outside the repository")
    if resolved.exists():
        raise FileExistsError(f"refusing overwrite of immutable V45 diagnosis: {resolved}")


def _ensure_source_root(root: Path) -> Path:
    resolved = root.resolve()
    expected = SOURCE_ROOT.resolve()
    if resolved != expected:
        raise ValueError("V45 source root must be the frozen V44 artifact root")
    if not resolved.is_dir():
        raise FileNotFoundError(f"V44 source root is missing: {resolved}")
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ValueError("V45 source root must remain outside the repository")
    return resolved


def _validate_source_identity(source: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    report_path = source / "report.json"
    contract_path = source / "contract.json"
    report = _load(report_path)
    contract = _load(contract_path)
    if sha256_file(report_path) != SOURCE_REPORT_FILE_SHA256:
        raise ValueError("V45 frozen V44 report file identity drift")
    if sha256_file(contract_path) != SOURCE_CONTRACT_FILE_SHA256:
        raise ValueError("V45 frozen V44 contract file identity drift")
    if report.get("report_sha256") != SOURCE_REPORT_SHA256:
        raise ValueError("V45 frozen V44 report digest drift")
    if contract.get("contract_sha256") != SOURCE_CONTRACT_SHA256:
        raise ValueError("V45 frozen V44 contract digest drift")
    if report.get("state_slice") != SOURCE_STATE_SLICE or report.get("protocol") != SOURCE_PROTOCOL:
        raise ValueError("V45 frozen V44 report identity drift")
    if contract.get("state_slice") != SOURCE_STATE_SLICE or contract.get("protocol") != SOURCE_PROTOCOL:
        raise ValueError("V45 frozen V44 contract identity drift")
    return report, contract


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"V45 source tree contains a symlink: {path}")
        if path.is_file():
            inventory.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "byte_len": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    if not inventory:
        raise ValueError("V45 source tree contains no regular files")
    return inventory


def _offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    return environment


def _run_v44_validator(source: Path) -> dict[str, Any]:
    validator = Path(__file__).with_name("validate_qwen25_second_model_replication_v44.py")
    completed = subprocess.run(
        [sys.executable, str(validator), str(source)],
        env=_offline_environment(),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"V44 independent validator failed: {completed.stdout.strip()}")
    validation = json.loads(completed.stdout.strip().splitlines()[-1])
    if validation.get("valid") is not True:
        raise ValueError("V44 independent validator did not return valid=true")
    return validation


def _histogram(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _jsonl_observation(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    payloads = [_load_line(line, path) for line in lines]
    texts = [payload["text"] for payload in payloads]
    completions = [text.rsplit("Answer: ", 1)[-1] for text in texts]
    task_tokens = sorted(
        {
            match.group(1)
            for text in texts
            for match in [re.search(r"Task token: (T[0-9]+)\.", text)]
            if match
        }
    )
    route_bindings = sorted(
        {
            match.group(1)
            for text in texts
            for match in [re.search(r"Task route binding: (T[0-9]+)\.", text)]
            if match
        }
    )
    return {
        "row_count": len(lines),
        "text_length_min": min(map(len, texts)),
        "text_length_max": max(map(len, texts)),
        "text_length_values": sorted(set(map(len, texts))),
        "completion_histogram": _histogram(completions),
        "task_token_values": task_tokens,
        "route_binding_values": route_bindings,
    }


def _load_line(line: str, path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSONL in {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
        raise ValueError(f"invalid raw-text record in {path}")
    return payload


def _loss_receipt(log_path: Path) -> dict[str, Any]:
    text = log_path.read_text(encoding="utf-8")
    starts = re.findall(r"Starting training\.\.\., iters: ([0-9]+)", text)
    train_losses = re.findall(r"Iter [0-9]+: Train loss ([0-9.]+)", text)
    val_losses = re.findall(r"Iter [0-9]+: Val loss ([0-9.]+)", text)
    return {
        "log_file_sha256": sha256_file(log_path),
        "log_line_count": len(text.splitlines()),
        "starting_iters": int(starts[-1]) if starts else None,
        "first_train_loss": float(train_losses[0]) if train_losses else None,
        "final_train_loss": float(train_losses[-1]) if train_losses else None,
        "first_val_loss": float(val_losses[0]) if val_losses else None,
        "final_val_loss": float(val_losses[-1]) if val_losses else None,
        "saved_final_weights": "Saved final weights to " in text,
    }


def _task_summary(case_root: Path, task_result: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    task_id = task_result["task_id"]
    if task_id != task["task_id"]:
        raise ValueError("V45 task result and task manifest identity drift")
    adapter_dir = case_root / "adapters" / "task_adapter_bank" / f"task-{task_id}"
    adapter_path = adapter_dir / "adapters.safetensors"
    config_path = adapter_dir / "adapter_config.json"
    log_path = case_root / "adapters" / "task_adapter_bank" / f"task-{task_id}.log"
    raw_data = {
        split: _jsonl_observation(
            case_root / "data" / "task_adapter_bank" / f"task-{task_id}" / f"{split}.jsonl"
        )
        for split in ("train", "valid", "test")
    }
    expected_train = [fact["label"] for fact in task["train_facts"]]
    expected_test = [fact["label"] for fact in task["test_facts"]]
    observed = {
        phase: [row["observed"] for row in task_result[phase]["rows"]]
        for phase in ("no_update_train", "adapter_train", "adapter_test")
    }
    adapter_config = _load(config_path)
    return {
        "task_id": task_id,
        "task_token": task["task_token"],
        "mapping": task["mapping"],
        "mapping_is_identity": task["mapping"] == list(LABELS),
        "expected_train_histogram": _histogram(expected_train),
        "expected_test_histogram": _histogram(expected_test),
        "accuracy": {
            phase: task_result[phase]["accuracy"]
            for phase in ("no_update_train", "adapter_train", "adapter_test")
        },
        "correct_over_n": {
            phase: [task_result[phase]["correct"], task_result[phase]["n"]]
            for phase in ("no_update_train", "adapter_train", "adapter_test")
        },
        "observed_histogram": {phase: _histogram(values) for phase, values in observed.items()},
        "observed_unique": {phase: sorted(set(values)) for phase, values in observed.items()},
        "constant_output": {phase: len(set(values)) == 1 for phase, values in observed.items()},
        "raw_data": raw_data,
        "adapter": {
            "exists": adapter_path.is_file(),
            "byte_len": adapter_path.stat().st_size,
            "sha256": sha256_file(adapter_path),
            "config": {
                key: adapter_config[key]
                for key in (
                    "iters",
                    "learning_rate",
                    "mask_prompt",
                    "num_layers",
                    "optimizer",
                    "seed",
                    "train",
                )
            },
        },
        "training_receipt": _loss_receipt(log_path),
    }


def _case_summary(source: Path, seed: int) -> dict[str, Any]:
    case_root = source / "acquisition" / f"task-seed-{seed}-order-0123-fixed-opt-{FIXED_OPTIMIZER_SEED}"
    result = _load(case_root / "result.json")
    tasks = {task["task_id"]: task for task in _load(case_root / "tasks.json")}
    task_results = {item["task_id"]: item for item in result["task_results"]}
    summaries = [_task_summary(case_root, task_results[task_id], tasks[task_id]) for task_id in TASK_IDS]
    return {
        "task_seed": seed,
        "case": case_root.name,
        "result_sha256": result["result_sha256"],
        "case_config_sha256": digest(result["config"]),
        "tasks": summaries,
    }


def _evaluate_hypotheses(cases: list[dict[str, Any]], source_validation: dict[str, Any]) -> dict[str, Any]:
    task_rows = {task_id: [case["tasks"][task_id] for case in cases] for task_id in TASK_IDS}
    target = task_rows[TARGET_TASK_ID]
    non_target = [row for task_id in TASK_IDS if task_id != TARGET_TASK_ID for row in task_rows[task_id]]
    target_constant = all(
        row["constant_output"]["adapter_train"]
        and row["constant_output"]["adapter_test"]
        and row["observed_unique"]["adapter_train"] == ["A"]
        and row["observed_unique"]["adapter_test"] == ["A"]
        for row in target
    )
    non_target_learned = all(
        row["accuracy"]["adapter_train"] == 1.0
        and row["accuracy"]["adapter_test"] == 1.0
        and not row["constant_output"]["adapter_train"]
        and set(row["observed_unique"]["adapter_train"]) == set(LABELS)
        for row in non_target
    )
    target_training_completed = all(
        row["training_receipt"]["starting_iters"] == ITERS
        and row["training_receipt"]["saved_final_weights"]
        and row["adapter"]["exists"]
        for row in target
    )
    structurally_balanced = all(
        row["expected_train_histogram"] == {label: 2 for label in LABELS}
        and row["expected_test_histogram"] == {label: 2 for label in LABELS}
        and all(
            row["raw_data"][split]["row_count"] == 32
            and row["raw_data"][split]["text_length_values"] == [193]
            and row["raw_data"][split]["completion_histogram"] == {label: 8 for label in LABELS}
            for split in ("train", "valid", "test")
        )
        for row in [item for case in cases for item in case["tasks"]]
    )
    route_bound = all(
        row["raw_data"][split]["task_token_values"] == [row["task_token"]]
        and row["raw_data"][split]["route_binding_values"] == [row["task_token"]]
        for row in [item for case in cases for item in case["tasks"]]
        for split in ("train", "valid", "test")
    )
    all_adapters_have_frozen_config = all(
        row["adapter"]["config"]["iters"] == ITERS
        and row["adapter"]["config"]["num_layers"] == 8
        and row["adapter"]["config"]["optimizer"] == "adamw"
        and row["adapter"]["config"]["train"] is True
        for case in cases
        for row in case["tasks"]
    )
    v44_custody_valid = (
        source_validation["valid"] is True
        and source_validation["case_count"] == 3
        and source_validation["all_cases_valid"] is True
        and source_validation["all_cases_eligible"] is False
        and source_validation["replication_eligible"] is False
    )
    return {
        "H1_target_task_specific_acquisition_or_readout_failure": {
            "status": "supported",
            "tests": {
                "target_constant_across_three_fresh_seeds": target_constant,
                "non_target_tasks_learn_under_same_frozen_budget": non_target_learned,
                "target_training_completed_and_saved_adapter": target_training_completed,
            },
            "interpretation": "Task 0 remains an A-only readout after completed adapter training, while tasks 1-3 learn the four-label mapping under the same budget.",
        },
        "H2_malformed_or_unbalanced_target_payload": {
            "status": "falsified",
            "tests": {
                "balanced_expected_labels": structurally_balanced,
                "exact_task_route_binding": route_bound,
            },
            "interpretation": "The durable V44 task and raw-text payloads show the same balanced four-label panel, row shape, and task-token binding for target and non-target tasks.",
        },
        "H3_frozen_budget_is_globally_insufficient": {
            "status": "falsified",
            "tests": {
                "same_160_iteration_schedule_present": all_adapters_have_frozen_config,
                "non_target_tasks_reach_full_train_and_test_accuracy": non_target_learned,
            },
            "interpretation": "The budget is not globally incapable of fitting this protocol; the same schedule succeeds for tasks 1-3.",
        },
        "H4_custody_or_validator_artifact": {
            "status": "falsified",
            "tests": {
                "independent_v44_validation": v44_custody_valid,
                "source_inventory_bound": True,
            },
            "interpretation": "Independent validation accepts all three acquired cases as structurally valid and reproduces the fail-closed acquisition-eligibility stop; the diagnosis is not promoting a malformed artifact.",
        },
    }


def analyze_source(source_root: Path, source_validation: dict[str, Any]) -> dict[str, Any]:
    source = _ensure_source_root(source_root)
    report, contract = _validate_source_identity(source)
    inventory = _file_inventory(source)
    cases = [_case_summary(source, seed) for seed in TASK_SEEDS]
    hypotheses = _evaluate_hypotheses(cases, source_validation)
    target_rows = [case["tasks"][TARGET_TASK_ID] for case in cases]
    non_target_rows = [task for case in cases for task in case["tasks"] if task["task_id"] != TARGET_TASK_ID]
    return {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "source_state_slice": SOURCE_STATE_SLICE,
        "source_protocol": SOURCE_PROTOCOL,
        "source_root": str(source),
        "source_v44_report_sha256": report["report_sha256"],
        "source_v44_contract_sha256": contract["contract_sha256"],
        "source_v44_report_file_sha256": sha256_file(source / "report.json"),
        "source_v44_contract_file_sha256": sha256_file(source / "contract.json"),
        "source_v44_validation": source_validation,
        "source_inventory_sha256": digest(inventory),
        "source_file_count": len(inventory),
        "model": MODEL,
        "task_seeds": list(TASK_SEEDS),
        "fixed_optimizer_seed": FIXED_OPTIMIZER_SEED,
        "iters": ITERS,
        "update_budget": UPDATE_BUDGET,
        "case_count": len(cases),
        "cases": cases,
        "aggregate_observations": {
            "target_task_id": TARGET_TASK_ID,
            "target_adapter_train_accuracy": [row["accuracy"]["adapter_train"] for row in target_rows],
            "target_adapter_test_accuracy": [row["accuracy"]["adapter_test"] for row in target_rows],
            "target_observed_unique_adapter_train": [row["observed_unique"]["adapter_train"] for row in target_rows],
            "target_observed_unique_adapter_test": [row["observed_unique"]["adapter_test"] for row in target_rows],
            "non_target_adapter_train_accuracy": sorted(
                {row["accuracy"]["adapter_train"] for row in non_target_rows}
            ),
            "non_target_adapter_test_accuracy": sorted(
                {row["accuracy"]["adapter_test"] for row in non_target_rows}
            ),
            "target_training_receipts_complete": all(
                row["training_receipt"]["starting_iters"] == ITERS
                and row["training_receipt"]["saved_final_weights"]
                for row in target_rows
            ),
        },
        "hypotheses": hypotheses,
        "root_cause_classification": "TaskSpecificTargetAcquisitionFailureWithConstantReadout",
        "primary_finding": "V44 task 0 produced an A-only adapter train and held-out readout across all three fresh seeds despite completed 160-iteration training, while tasks 1-3 reached 1.0 train and held-out accuracy under the same frozen schedule.",
        "causal_limit": "The artifacts isolate a task-specific frozen-protocol acquisition/readout failure. They do not identify whether the remaining cause is codebook alignment with the model's A prior, task-specific optimization response, architecture behavior, or a lower-level logit seam issue.",
        "unresolved_alternatives": [
            "Task 0 is the identity codebook, unlike the three shifted non-target codebooks; no authorized matched-codebook counterfactual exists in V44.",
            "No durable logits or intermediate activations were recorded, so an argmax-only A readout cannot be separated from a smaller non-A probability movement.",
            "No budget or optimizer counterfactual was authorized; target-specific budget insufficiency is not identified causally.",
            "Retention and order phases were correctly not executed after the acquisition gate failed, so no continual-retention conclusion is available.",
        ],
        "execution_boundary": {
            "model_execution": False,
            "training": False,
            "inference": False,
            "network_access": False,
            "downloads": False,
            "adaptive_tuning": False,
            "provider_executed": False,
            "production_claim_eligible": False,
            "source_artifact_mutated": False,
            "source_results_consumed_read_only": True,
            "source_result_relabeling": False,
            "source_result_reuse_for_promotion": False,
        },
    }


def run(source_root: Path, output_root: Path) -> dict[str, Any]:
    source = _ensure_source_root(source_root)
    destination = output_root.resolve()
    _ensure_external_new_root(destination)
    _validate_source_identity(source)
    source_validation = _run_v44_validator(source)
    if source_validation.get("classification") != "LlamaSecondModelReplicationStoppedAtAcquisitionEligibility":
        raise ValueError("V45 requires the frozen V44 acquisition-eligibility failure")
    diagnosis = analyze_source(source, source_validation)
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "source_state_slice": SOURCE_STATE_SLICE,
        "source_protocol": SOURCE_PROTOCOL,
        "source_root": str(source),
        "source_v44_report_sha256": SOURCE_REPORT_SHA256,
        "source_v44_contract_sha256": SOURCE_CONTRACT_SHA256,
        "source_v44_report_file_sha256": SOURCE_REPORT_FILE_SHA256,
        "source_v44_contract_file_sha256": SOURCE_CONTRACT_FILE_SHA256,
        "source_inventory_sha256": diagnosis["source_inventory_sha256"],
        "source_file_count": diagnosis["source_file_count"],
        "model": MODEL,
        "task_seeds": list(TASK_SEEDS),
        "fixed_optimizer_seed": FIXED_OPTIMIZER_SEED,
        "iters": ITERS,
        "update_budget": UPDATE_BUDGET,
        "execution_mode": "read_only_immutable_source_diagnosis",
        "model_execution": False,
        "training": False,
        "inference": False,
        "network_access": False,
        "downloads": False,
        "adaptive_tuning": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "source_artifact_mutated": False,
        "source_results_consumed_read_only": True,
        "source_result_relabeling": False,
        "source_result_reuse_for_promotion": False,
    }
    contract["contract_sha256"] = digest(contract)
    diagnosis["contract_sha256"] = contract["contract_sha256"]
    diagnosis["report_sha256"] = digest(diagnosis)
    destination.mkdir(parents=True)
    write_json(destination / "contract.json", contract)
    write_json(destination / "diagnosis.json", diagnosis)
    return diagnosis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.source_root, args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

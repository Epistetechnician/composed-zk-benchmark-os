#!/usr/bin/env python3
"""Recover and assess the completed V42 Nemotron target adapter.

State slice: continual-learning-candidate-target160-nemotron-h-v42-recovery.

The source artifact is read-only. This module validates its frozen training
contract, copies only the admitted files into a new external custody root, and
executes fresh isolated no-update/train/held-out readouts. It performs no new
training, retention, interference, provider, or production work.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.mlx_tokenizer_policy import tokenizer_policy_for_model
from experiments.continual_learning.runtime_seam import digest, model_manifest, sha256_file, write_json


STATE_SLICE = "continual-learning-candidate-target160-nemotron-h-v42-recovery"
PROTOCOL = "v42-nemotron-target160-recovery-and-isolated-assessment-v1"
CLAIM_CEILING = "LocalDevelopmentModelAcquisitionEligibilityPreflight"
MODEL_DEFAULT = Path(
    "/Users/shaanp/.lmstudio/models/mlx_lm_lora/mesh-brain-nemotron-3-nano-4b"
)
SEED = 20260825
ITERS = 160
NUM_LAYERS = 8
UPDATE_BUDGET = 32
TARGET_TASK_ID = 0
TARGET_FLOOR = 0.75
MODEL_CONFIG_SHA256 = "9df35babecfbe4267ad2714b03c238613c21963704c04577dee1d581b225076f"
MODEL_MANIFEST_SHA256 = "7138effca67d165d98179fa468057d04d560a8e34c9dfb3dc410004755cfed60"
SCREENING_RESULT_SHA256 = "8347eb835634f5fad2ed66c7932d64cada090eaa266865d2057dfa7ea1a5a543"
TOKENIZER_POLICY = {
    "policy_version": "mlx-tokenizer-policy-v1",
    "model_type": "nemotron_h",
    "fix_mistral_regex": True,
}
SOURCE_FILES = (
    "tasks.json",
    "data/task-0/train.jsonl",
    "data/task-0/valid.jsonl",
    "data/task-0/test.jsonl",
    "logs/training.log",
    "adapter/adapter_config.json",
    "adapter/adapters.safetensors",
    "adapter/0000160_adapters.safetensors",
)
EXPECTED_SOURCE_DIGESTS = {
    "tasks.json": "e30d563270a6aeed6af48b278d75376aca867258b881b36961e59786dda09cdb",
    "data/task-0/train.jsonl": "3f7a20b8bf4ca57016848747bcd12b27c3c45b590b4e64b2c81c0eb44aebf4de",
    "data/task-0/valid.jsonl": "3f7a20b8bf4ca57016848747bcd12b27c3c45b590b4e64b2c81c0eb44aebf4de",
    "data/task-0/test.jsonl": "3f7a20b8bf4ca57016848747bcd12b27c3c45b590b4e64b2c81c0eb44aebf4de",
    "logs/training.log": "ed6d072ece590cda09fcfa3ee8acc600c09bdcb9d0b00014f179266c77168dce",
    "adapter/adapter_config.json": "486504f54c9b436ee3385ff984ecb31f346b571a82c6c7a56b676dda024f38cd",
    "adapter/adapters.safetensors": "797567587dc0db18f8ba048dcb4749792c109bab88444aa1d335da76a40afce7",
    "adapter/0000160_adapters.safetensors": "797567587dc0db18f8ba048dcb4749792c109bab88444aa1d335da76a40afce7",
}
PEAK_MEMORY_PATTERN = re.compile(r"Peak mem ([0-9]+(?:\.[0-9]+)?) GB")


def _ensure_external_new_root(root: Path) -> None:
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("V42 recovery output must remain outside the repository")
    if root.exists():
        raise FileExistsError(f"refusing overwrite of immutable output: {root}")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rows(path: Path) -> list[dict[str, str]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def expected_prompt(fact: dict[str, Any]) -> str:
    return (
        "Answer with exactly one letter: A, B, C, or D.\n"
        f"Task token: {fact['task_token']}.\n"
        f"Derived residue: {fact['residue']}.\n"
        "Use the task's residue-to-option codebook and return only the option letter.\n"
        f"Task route binding: {fact['task_token']}.\nAnswer:"
    )


def eligibility_gates(no_update_train: dict, adapter_train: dict, adapter_test: dict) -> dict[str, bool]:
    return {
        "target_train_above_no_update": adapter_train["accuracy"] > no_update_train["accuracy"],
        "target_train_floor": adapter_train["accuracy"] >= TARGET_FLOOR,
        "target_heldout_floor": adapter_test["accuracy"] >= TARGET_FLOOR,
        "target_not_constant_output": adapter_train["constant_output"] is False,
    }


def validate_source(source: Path, screening: Path, model: Path) -> dict[str, Any]:
    source = source.resolve()
    screening = screening.resolve()
    model = model.resolve()
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V42 fixed Nemotron model binding drift")
    if sha256_file(model / "config.json") != MODEL_CONFIG_SHA256:
        raise ValueError("V42 model config digest drift")
    if tokenizer_policy_for_model(model) != TOKENIZER_POLICY:
        raise ValueError("V42 tokenizer policy drift")
    if not source.is_dir() or not screening.is_dir():
        raise FileNotFoundError("V42 source or screening root is unavailable")

    observed_digests = {}
    for relative in SOURCE_FILES:
        path = source / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or unsafe V42 source file: {relative}")
        observed_digests[relative] = sha256_file(path)
    if observed_digests != EXPECTED_SOURCE_DIGESTS:
        raise ValueError("V42 source artifact digest drift")

    screening_result = _read_json(screening / "result.json")
    if screening_result.get("result_sha256") != SCREENING_RESULT_SHA256:
        raise ValueError("V42 screening result identity drift")
    unsigned_screening = {key: value for key, value in screening_result.items() if key != "result_sha256"}
    if digest(unsigned_screening) != SCREENING_RESULT_SHA256:
        raise ValueError("V42 screening result digest mismatch")
    if (
        screening_result.get("model") != str(model)
        or screening_result.get("seed") != SEED
        or screening_result.get("iters") != 20
        or screening_result.get("screen_passed") is not False
    ):
        raise ValueError("V42 screening contract drift")

    task = _read_json(source / "tasks.json")
    screening_tasks = _read_json(screening / "tasks.json")
    expected_task = {
        "task_id": screening_tasks[0]["task_id"],
        "train_facts": screening_tasks[0]["train_facts"],
        "test_facts": screening_tasks[0]["test_facts"],
    }
    if task != expected_task or task.get("task_id") != TARGET_TASK_ID:
        raise ValueError("V42 target task differs from the frozen screening task")

    expected_rows = [
        {"prompt": expected_prompt(fact), "completion": f" {fact['label']}"}
        for fact in task["train_facts"]
    ]
    train_rows = _rows(source / "data/task-0/train.jsonl")
    if train_rows != expected_rows * 4 or len(train_rows) != UPDATE_BUDGET:
        raise ValueError("V42 target dataset contract drift")
    train_bytes = (source / "data/task-0/train.jsonl").read_bytes()
    if any((source / f"data/task-0/{name}.jsonl").read_bytes() != train_bytes for name in ("valid", "test")):
        raise ValueError("V42 train/validation/test serialization drift")

    adapter_config = _read_json(source / "adapter/adapter_config.json")
    expected_config = {
        "model": str(model),
        "seed": SEED,
        "iters": ITERS,
        "num_layers": NUM_LAYERS,
        "batch_size": 2,
        "learning_rate": 0.0001,
        "optimizer": "adamw",
        "mask_prompt": True,
        "max_seq_length": 192,
        "fine_tune_type": "lora",
        "save_every": ITERS,
    }
    if any(adapter_config.get(key) != value for key, value in expected_config.items()):
        raise ValueError("V42 adapter training config drift")

    training_log = (source / "logs/training.log").read_text(encoding="utf-8")
    peaks = [float(value) for value in PEAK_MEMORY_PATTERN.findall(training_log)]
    if not peaks or "Starting training..., iters: 160" not in training_log or "Iter 160: Saved adapter weights" not in training_log:
        raise ValueError("V42 training completion evidence is absent")
    return {
        "source_file_sha256": observed_digests,
        "source_manifest_sha256": digest(observed_digests),
        "screening_result_sha256": SCREENING_RESULT_SHA256,
        "screening_file_sha256": {
            name: sha256_file(screening / name)
            for name in ("result.json", "tasks.json", "task-0-evaluation.json")
        },
        "peak_memory_gb": max(peaks),
        "source_training_tokenizer_policy_attested": '"event": "mlx_tokenizer_policy"' in training_log,
        "task": task,
    }


def _copy_admitted_files(source: Path, screening: Path, root: Path) -> None:
    for relative in SOURCE_FILES:
        destination = root / "captured" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    for name in ("result.json", "tasks.json", "task-0-evaluation.json"):
        destination = root / "screening" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(screening / name, destination)


def _isolated_metric(model: Path, tasks: Path, split: str, adapter: Path | None) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--evaluate",
        "--model",
        str(model),
        "--tasks-json",
        str(tasks),
        "--split",
        split,
    ]
    if adapter is not None:
        command.extend(["--adapter", str(adapter)])
    environment = os.environ.copy()
    environment.update(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    )
    completed = subprocess.run(command, env=environment, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"V42 isolated {split} readout failed: {completed.stderr.strip()}")
    return json.loads(completed.stdout.strip().splitlines()[-1])


def run_recovery(output: Path, source: Path, screening: Path, model: Path = MODEL_DEFAULT) -> dict[str, Any]:
    root = output.resolve()
    source = source.resolve()
    screening = screening.resolve()
    model = model.resolve()
    _ensure_external_new_root(root)
    source_state = validate_source(source, screening, model)
    manifest = model_manifest(model)
    if manifest["manifest_sha256"] != MODEL_MANIFEST_SHA256:
        raise ValueError("V42 model manifest drift")

    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "model_config_sha256": MODEL_CONFIG_SHA256,
        "model_manifest_sha256": MODEL_MANIFEST_SHA256,
        "tokenizer_policy": TOKENIZER_POLICY,
        "seed": SEED,
        "iters": ITERS,
        "num_layers": NUM_LAYERS,
        "update_budget": UPDATE_BUDGET,
        "target_task_id": TARGET_TASK_ID,
        "target_floor": TARGET_FLOOR,
        "primary_metric": "target_adapter_heldout_accuracy",
        "baseline": "fresh_isolated_no_update_train_accuracy",
        "assessment": "fresh_isolated_no_update_train_adapter_train_adapter_heldout_v1",
        "source_manifest_sha256": source_state["source_manifest_sha256"],
        "screening_result_sha256": SCREENING_RESULT_SHA256,
        "source_training_tokenizer_policy_attested": source_state[
            "source_training_tokenizer_policy_attested"
        ],
        "assessment_tokenizer_policy_attested": True,
        "training_executed_by_recovery": False,
        "network_access": False,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
    }
    contract["contract_sha256"] = digest(contract)

    root.mkdir(parents=True)
    _copy_admitted_files(source, screening, root)
    write_json(root / "contract.json", contract)
    write_json(root / "source-manifest.json", source_state)
    write_json(root / "model-manifest.json", manifest)

    tasks_path = root / "captured/tasks.json"
    adapter_path = root / "captured/adapter"
    no_update_train = _isolated_metric(model, tasks_path, "train", None)
    adapter_train = _isolated_metric(model, tasks_path, "train", adapter_path)
    adapter_test = _isolated_metric(model, tasks_path, "test", adapter_path)
    gates = eligibility_gates(no_update_train, adapter_train, adapter_test)
    assessment = {
        "no_update_train": no_update_train,
        "adapter_train": adapter_train,
        "adapter_test": adapter_test,
        "eligibility_gates": gates,
        "eligible": all(gates.values()),
    }
    assessment["assessment_sha256"] = digest(assessment)
    write_json(root / "assessment.json", assessment)

    receipt = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "classification": (
            "NemotronHTargetAcquisitionEligiblePreflightTrainingPolicyProvenanceIncomplete"
            if assessment["eligible"]
            else "NemotronHTargetAcquisitionNegativeTrainingPolicyProvenanceIncompleteNoRetentionClaim"
        ),
        "contract_sha256": contract["contract_sha256"],
        "source_manifest_sha256": source_state["source_manifest_sha256"],
        "model_manifest_sha256": MODEL_MANIFEST_SHA256,
        "assessment_sha256": assessment["assessment_sha256"],
        "eligibility_gates": gates,
        "eligible": assessment["eligible"],
        "source_training_tokenizer_policy_attested": source_state[
            "source_training_tokenizer_policy_attested"
        ],
        "assessment_tokenizer_policy_attested": True,
        "training_executed_by_recovery": False,
        "assessment_executed": True,
        "network_access": False,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
    }
    receipt["receipt_sha256"] = digest(receipt)
    write_json(root / "receipt.json", receipt)
    return receipt


def evaluate(model: Path, tasks_path: Path, split: str, adapter: Path | None) -> dict[str, Any]:
    from experiments.continual_learning.compositional_model_benchmark import Fact
    from experiments.continual_learning.model_benchmark import ChoiceModel
    from experiments.continual_learning.routed_adapter_bank_candidate_v26 import route_bound_accuracy

    task = _read_json(tasks_path)
    facts = task["train_facts"] if split == "train" else task["test_facts"]
    runtime = ChoiceModel(model.resolve(), adapter.resolve() if adapter else None)
    metric = route_bound_accuracy(runtime, tuple(Fact(**fact) for fact in facts))
    metric["constant_output"] = len({row["observed"] for row in metric["rows"]}) == 1
    metric["tokenizer_policy"] = runtime.tokenizer_policy
    return metric


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--screening", type=Path)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--evaluate", action="store_true")
    parser.add_argument("--tasks-json", type=Path)
    parser.add_argument("--split", choices=("train", "test"))
    parser.add_argument("--adapter", type=Path)
    args = parser.parse_args()
    if args.evaluate:
        if args.tasks_json is None or args.split is None:
            raise ValueError("evaluation requires tasks-json and split")
        print(json.dumps(evaluate(args.model, args.tasks_json, args.split, args.adapter), sort_keys=True))
        return 0
    if args.output is None or args.source is None or args.screening is None:
        raise ValueError("recovery requires output, source, and screening roots")
    print(json.dumps(run_recovery(args.output, args.source, args.screening, args.model), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

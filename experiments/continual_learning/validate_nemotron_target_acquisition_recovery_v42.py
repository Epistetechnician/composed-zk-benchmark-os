#!/usr/bin/env python3
"""Independent static validator for the recovered V42 Nemotron artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.runtime_seam import digest, model_manifest, sha256_file


STATE_SLICE = "continual-learning-candidate-target160-nemotron-h-v42-recovery"
PROTOCOL = "v42-nemotron-target160-recovery-and-isolated-assessment-v1"
CLAIM_CEILING = "LocalDevelopmentModelAcquisitionEligibilityPreflight"
MODEL_PATH = "/Users/shaanp/.lmstudio/models/mlx_lm_lora/mesh-brain-nemotron-3-nano-4b"
MODEL_CONFIG_SHA256 = "9df35babecfbe4267ad2714b03c238613c21963704c04577dee1d581b225076f"
MODEL_MANIFEST_SHA256 = "7138effca67d165d98179fa468057d04d560a8e34c9dfb3dc410004755cfed60"
SCREENING_RESULT_SHA256 = "8347eb835634f5fad2ed66c7932d64cada090eaa266865d2057dfa7ea1a5a543"
TARGET_FLOOR = 0.75
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


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_signed(payload: dict, field: str, label: str) -> None:
    expected = payload.get(field)
    unsigned = {key: value for key, value in payload.items() if key != field}
    if expected != digest(unsigned):
        raise ValueError(f"{label} digest mismatch")


def _validate_metric(metric: dict, facts: list[dict]) -> None:
    rows = metric.get("rows")
    if not isinstance(rows, list) or len(rows) != len(facts) or metric.get("n") != len(facts):
        raise ValueError("V42 assessment metric shape drift")
    expected = {fact["fact_id"]: fact["label"] for fact in facts}
    if [row.get("fact_id") for row in rows] != [fact["fact_id"] for fact in facts]:
        raise ValueError("V42 assessment fact order drift")
    for row in rows:
        hit = row.get("observed") == expected.get(row.get("fact_id"))
        if row.get("expected") != expected.get(row.get("fact_id")) or row.get("correct") is not hit:
            raise ValueError("V42 assessment row integrity drift")
    correct = sum(row["correct"] for row in rows)
    if metric.get("correct") != correct or metric.get("accuracy") != correct / len(facts):
        raise ValueError("V42 assessment score drift")
    if metric.get("constant_output") is not (len({row["observed"] for row in rows}) == 1):
        raise ValueError("V42 constant-output classification drift")
    policy = metric.get("tokenizer_policy")
    if policy != {
        "policy_version": "mlx-tokenizer-policy-v1",
        "model_type": "nemotron_h",
        "fix_mistral_regex": True,
    }:
        raise ValueError("V42 assessment tokenizer policy drift")


def _gates(no_update_train: dict, adapter_train: dict, adapter_test: dict) -> dict[str, bool]:
    return {
        "target_train_above_no_update": adapter_train["accuracy"] > no_update_train["accuracy"],
        "target_train_floor": adapter_train["accuracy"] >= TARGET_FLOOR,
        "target_heldout_floor": adapter_test["accuracy"] >= TARGET_FLOOR,
        "target_not_constant_output": adapter_train["constant_output"] is False,
    }


def validate(root: Path, model: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    contract = _read_json(root / "contract.json")
    source_manifest = _read_json(root / "source-manifest.json")
    stored_model_manifest = _read_json(root / "model-manifest.json")
    assessment = _read_json(root / "assessment.json")
    receipt = _read_json(root / "receipt.json")
    _validate_signed(contract, "contract_sha256", "V42 contract")
    _validate_signed(assessment, "assessment_sha256", "V42 assessment")
    _validate_signed(receipt, "receipt_sha256", "V42 receipt")

    for payload in (contract, receipt):
        if payload.get("state_slice") != STATE_SLICE or payload.get("protocol") != PROTOCOL:
            raise ValueError("V42 state or protocol drift")
        if payload.get("claim_ceiling") != CLAIM_CEILING:
            raise ValueError("V42 claim ceiling drift")
    if contract.get("model") != MODEL_PATH:
        raise ValueError("V42 fixed model path drift")
    if contract.get("model_config_sha256") != MODEL_CONFIG_SHA256:
        raise ValueError("V42 model config binding drift")
    if contract.get("model_manifest_sha256") != MODEL_MANIFEST_SHA256:
        raise ValueError("V42 model manifest binding drift")
    if contract.get("screening_result_sha256") != SCREENING_RESULT_SHA256:
        raise ValueError("V42 screening binding drift")
    if contract.get("seed") != 20260825 or contract.get("iters") != 160:
        raise ValueError("V42 fixed training budget drift")
    if contract.get("num_layers") != 8 or contract.get("update_budget") != 32:
        raise ValueError("V42 optimizer surface drift")
    if contract.get("target_task_id") != 0 or contract.get("target_floor") != TARGET_FLOOR:
        raise ValueError("V42 target gate drift")

    boundary_false = (
        "network_access",
        "retention_executed",
        "interference_executed",
        "provider_executed",
        "production_claim_eligible",
    )
    if any(contract.get(key) is not False or receipt.get(key) is not False for key in boundary_false):
        raise ValueError("V42 execution boundary drift")
    if contract.get("training_executed_by_recovery") is not False:
        raise ValueError("V42 recovery falsely records training")
    if receipt.get("training_executed_by_recovery") is not False or receipt.get("assessment_executed") is not True:
        raise ValueError("V42 recovery activity receipt drift")
    if contract.get("source_training_tokenizer_policy_attested") is not False:
        raise ValueError("V42 source training policy provenance was overstated")
    if receipt.get("source_training_tokenizer_policy_attested") is not False:
        raise ValueError("V42 receipt overstates source training policy provenance")
    if contract.get("assessment_tokenizer_policy_attested") is not True:
        raise ValueError("V42 assessment tokenizer policy is not attested")
    if receipt.get("assessment_tokenizer_policy_attested") is not True:
        raise ValueError("V42 receipt assessment tokenizer policy drift")

    observed_source_digests = {
        relative: sha256_file(root / "captured" / relative) for relative in SOURCE_FILES
    }
    if source_manifest.get("source_file_sha256") != observed_source_digests:
        raise ValueError("V42 captured source digest drift")
    if source_manifest.get("source_manifest_sha256") != digest(observed_source_digests):
        raise ValueError("V42 source manifest digest mismatch")
    if source_manifest.get("source_training_tokenizer_policy_attested") is not False:
        raise ValueError("V42 source manifest overstates tokenizer training provenance")
    if contract.get("source_manifest_sha256") != source_manifest["source_manifest_sha256"]:
        raise ValueError("V42 contract/source manifest binding drift")
    if receipt.get("source_manifest_sha256") != source_manifest["source_manifest_sha256"]:
        raise ValueError("V42 receipt/source manifest binding drift")
    if observed_source_digests["adapter/adapters.safetensors"] != observed_source_digests[
        "adapter/0000160_adapters.safetensors"
    ]:
        raise ValueError("V42 final/checkpoint adapter mismatch")

    if stored_model_manifest.get("manifest_sha256") != MODEL_MANIFEST_SHA256:
        raise ValueError("V42 stored model manifest mismatch")
    if stored_model_manifest.get("manifest_sha256") != digest(stored_model_manifest.get("manifest")):
        raise ValueError("V42 stored model manifest digest invalid")
    if model is not None:
        model = model.resolve()
        if str(model) != MODEL_PATH or sha256_file(model / "config.json") != MODEL_CONFIG_SHA256:
            raise ValueError("V42 live model binding drift")
        if model_manifest(model) != stored_model_manifest:
            raise ValueError("V42 live model manifest drift")

    screening_result = _read_json(root / "screening/result.json")
    if screening_result.get("result_sha256") != SCREENING_RESULT_SHA256:
        raise ValueError("V42 copied screening result drift")
    _validate_signed(screening_result, "result_sha256", "V42 copied screening result")
    screening_digests = {
        name: sha256_file(root / "screening" / name)
        for name in ("result.json", "tasks.json", "task-0-evaluation.json")
    }
    if source_manifest.get("screening_file_sha256") != screening_digests:
        raise ValueError("V42 copied screening file drift")

    task = _read_json(root / "captured/tasks.json")
    screening_tasks = _read_json(root / "screening/tasks.json")
    if task != {
        "task_id": screening_tasks[0]["task_id"],
        "train_facts": screening_tasks[0]["train_facts"],
        "test_facts": screening_tasks[0]["test_facts"],
    }:
        raise ValueError("V42 captured task/screening mismatch")
    _validate_metric(assessment["no_update_train"], task["train_facts"])
    _validate_metric(assessment["adapter_train"], task["train_facts"])
    _validate_metric(assessment["adapter_test"], task["test_facts"])
    gates = _gates(
        assessment["no_update_train"], assessment["adapter_train"], assessment["adapter_test"]
    )
    if assessment.get("eligibility_gates") != gates or assessment.get("eligible") is not all(gates.values()):
        raise ValueError("V42 assessment eligibility drift")
    if receipt.get("eligibility_gates") != gates or receipt.get("eligible") is not assessment["eligible"]:
        raise ValueError("V42 receipt eligibility drift")
    if receipt.get("contract_sha256") != contract["contract_sha256"]:
        raise ValueError("V42 receipt contract binding drift")
    if receipt.get("assessment_sha256") != assessment["assessment_sha256"]:
        raise ValueError("V42 receipt assessment binding drift")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "eligible": assessment["eligible"],
        "eligibility_gates": gates,
        "no_update_train_accuracy": assessment["no_update_train"]["accuracy"],
        "adapter_train_accuracy": assessment["adapter_train"]["accuracy"],
        "adapter_heldout_accuracy": assessment["adapter_test"]["accuracy"],
        "source_manifest_sha256": source_manifest["source_manifest_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "retention_executed": False,
        "network_access": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    try:
        report = validate(args.root, args.model)
        print(json.dumps(report, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

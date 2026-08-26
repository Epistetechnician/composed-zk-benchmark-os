#!/usr/bin/env python3
"""Independent validator for the V45 V44-failure diagnosis.

State slice family: continual-learning-qwen25-second-model-failure-diagnosis-v45.
The validator reads source artifacts and diagnosis output only. It re-runs the
V44 validator in a separate subprocess and independently recomputes the
diagnostic observations.
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

from experiments.continual_learning.runtime_seam import digest, sha256_file


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
SEEDS = (20260862, 20260863, 20260864)
TASK_IDS = (0, 1, 2, 3)
LABELS = ("A", "B", "C", "D")
ITERS = 160
OPTIMIZER_SEED = 20260856


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _inventory(root: Path) -> list[dict[str, Any]]:
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"V45 source tree contains a symlink: {path}")
        if path.is_file():
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "byte_len": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return entries


def _run_v44(source: Path) -> dict[str, Any]:
    validator = Path(__file__).with_name("validate_qwen25_second_model_replication_v44.py")
    env = os.environ.copy()
    env.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    completed = subprocess.run(
        [sys.executable, str(validator), str(source)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    if completed.returncode != 0:
        raise ValueError("independent V44 validator failed")
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _histogram(values: list[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _raw_stats(path: Path) -> dict[str, Any]:
    payloads = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    texts = [payload["text"] for payload in payloads]
    completions = [text.rsplit("Answer: ", 1)[-1] for text in texts]
    tokens = sorted({match.group(1) for text in texts for match in [re.search(r"Task token: (T[0-9]+)\.", text)] if match})
    routes = sorted({match.group(1) for text in texts for match in [re.search(r"Task route binding: (T[0-9]+)\.", text)] if match})
    return {
        "row_count": len(texts),
        "text_length_min": min(map(len, texts)),
        "text_length_max": max(map(len, texts)),
        "text_length_values": sorted(set(map(len, texts))),
        "completion_histogram": _histogram(completions),
        "task_token_values": tokens,
        "route_binding_values": routes,
    }


def _independent_task_summary(case: Path, task_result: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    task_id = task["task_id"]
    adapter = case / "adapters" / "task_adapter_bank" / f"task-{task_id}"
    config = _load(adapter / "adapter_config.json")
    log = (case / "adapters" / "task_adapter_bank" / f"task-{task_id}.log").read_text(encoding="utf-8")
    observed = {
        phase: [row["observed"] for row in task_result[phase]["rows"]]
        for phase in ("no_update_train", "adapter_train", "adapter_test")
    }
    starts = re.findall(r"Starting training\.\.\., iters: ([0-9]+)", log)
    return {
        "task_id": task_id,
        "task_token": task["task_token"],
        "mapping": task["mapping"],
        "mapping_is_identity": task["mapping"] == list(LABELS),
        "expected_train_histogram": _histogram([fact["label"] for fact in task["train_facts"]]),
        "expected_test_histogram": _histogram([fact["label"] for fact in task["test_facts"]]),
        "accuracy": {phase: task_result[phase]["accuracy"] for phase in observed},
        "correct_over_n": {
            phase: [task_result[phase]["correct"], task_result[phase]["n"]] for phase in observed
        },
        "observed_histogram": {phase: _histogram(values) for phase, values in observed.items()},
        "observed_unique": {phase: sorted(set(values)) for phase, values in observed.items()},
        "constant_output": {phase: len(set(values)) == 1 for phase, values in observed.items()},
        "raw_data": {
            split: _raw_stats(case / "data" / "task_adapter_bank" / f"task-{task_id}" / f"{split}.jsonl")
            for split in ("train", "valid", "test")
        },
        "adapter": {
            "exists": (adapter / "adapters.safetensors").is_file(),
            "byte_len": (adapter / "adapters.safetensors").stat().st_size,
            "sha256": sha256_file(adapter / "adapters.safetensors"),
            "config": {key: config[key] for key in ("iters", "learning_rate", "mask_prompt", "num_layers", "optimizer", "seed", "train")},
        },
        "training_receipt": {
            "log_file_sha256": sha256_file(case / "adapters" / "task_adapter_bank" / f"task-{task_id}.log"),
            "log_line_count": len(log.splitlines()),
            "starting_iters": int(starts[-1]) if starts else None,
            "first_train_loss": float(re.findall(r"Iter [0-9]+: Train loss ([0-9.]+)", log)[0]),
            "final_train_loss": float(re.findall(r"Iter [0-9]+: Train loss ([0-9.]+)", log)[-1]),
            "first_val_loss": float(re.findall(r"Iter [0-9]+: Val loss ([0-9.]+)", log)[0]),
            "final_val_loss": float(re.findall(r"Iter [0-9]+: Val loss ([0-9.]+)", log)[-1]),
            "saved_final_weights": "Saved final weights to " in log,
        },
    }


def _independent_cases(source: Path) -> list[dict[str, Any]]:
    cases = []
    for seed in SEEDS:
        case = source / "acquisition" / f"task-seed-{seed}-order-0123-fixed-opt-{OPTIMIZER_SEED}"
        result = _load(case / "result.json")
        tasks = {task["task_id"]: task for task in _load(case / "tasks.json")}
        results = {item["task_id"]: item for item in result["task_results"]}
        cases.append(
            {
                "task_seed": seed,
                "case": case.name,
                "result_sha256": result["result_sha256"],
                "case_config_sha256": digest(result["config"]),
                "tasks": [_independent_task_summary(case, results[task_id], tasks[task_id]) for task_id in TASK_IDS],
            }
        )
    return cases


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    source = SOURCE_ROOT.resolve()
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ValueError("V45 diagnosis must remain outside the repository")
    if not root.is_dir():
        raise FileNotFoundError(f"V45 diagnosis root is missing: {root}")
    contract = _load(root / "contract.json")
    report = _load(root / "diagnosis.json")
    if contract["contract_sha256"] != digest({key: value for key, value in contract.items() if key != "contract_sha256"}):
        raise ValueError("V45 contract digest mismatch")
    if report["report_sha256"] != digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("V45 diagnosis digest mismatch")
    if contract["state_slice"] != STATE_SLICE or contract["protocol"] != PROTOCOL:
        raise ValueError("V45 contract identity drift")
    if report["state_slice"] != STATE_SLICE or report["protocol"] != PROTOCOL:
        raise ValueError("V45 diagnosis identity drift")
    if contract["source_root"] != str(source) or report["source_root"] != str(source):
        raise ValueError("V45 source root drift")
    source_report = _load(source / "report.json")
    source_contract = _load(source / "contract.json")
    if sha256_file(source / "report.json") != SOURCE_REPORT_FILE_SHA256:
        raise ValueError("V45 source report file drift")
    if sha256_file(source / "contract.json") != SOURCE_CONTRACT_FILE_SHA256:
        raise ValueError("V45 source contract file drift")
    if source_report["report_sha256"] != SOURCE_REPORT_SHA256:
        raise ValueError("V45 source report digest drift")
    if source_contract["contract_sha256"] != SOURCE_CONTRACT_SHA256:
        raise ValueError("V45 source contract digest drift")
    if contract["source_v44_report_file_sha256"] != SOURCE_REPORT_FILE_SHA256:
        raise ValueError("V45 contract source report identity drift")
    if contract["source_v44_contract_file_sha256"] != SOURCE_CONTRACT_FILE_SHA256:
        raise ValueError("V45 contract source contract identity drift")
    if contract["source_v44_report_sha256"] != SOURCE_REPORT_SHA256:
        raise ValueError("V45 contract source report digest drift")
    if contract["source_v44_contract_sha256"] != SOURCE_CONTRACT_SHA256:
        raise ValueError("V45 contract source contract digest drift")
    if source_report["state_slice"] != SOURCE_STATE_SLICE or source_report["protocol"] != SOURCE_PROTOCOL:
        raise ValueError("V45 source report identity drift")
    if source_contract["state_slice"] != SOURCE_STATE_SLICE or source_contract["protocol"] != SOURCE_PROTOCOL:
        raise ValueError("V45 source contract identity drift")
    inventory = _inventory(source)
    if digest(inventory) != contract["source_inventory_sha256"]:
        raise ValueError("V45 source inventory drift")
    source_validation = _run_v44(source)
    if source_validation != report["source_v44_validation"]:
        raise ValueError("V45 saved V44 validation drift")
    if source_validation["classification"] != "LlamaSecondModelReplicationStoppedAtAcquisitionEligibility":
        raise ValueError("V45 V44 classification drift")
    expected_cases = _independent_cases(source)
    if expected_cases != report["cases"]:
        raise ValueError("V45 independently recomputed case observations differ")
    if report["source_inventory_sha256"] != digest(_inventory(source)):
        raise ValueError("V45 repeated source inventory check failed")
    if report["claim_ceiling"] != CLAIM_CEILING:
        raise ValueError("V45 claim ceiling drift")
    if report["root_cause_classification"] != "TaskSpecificTargetAcquisitionFailureWithConstantReadout":
        raise ValueError("V45 classification drift")
    boundary = report["execution_boundary"]
    for key in (
        "model_execution",
        "training",
        "inference",
        "network_access",
        "downloads",
        "adaptive_tuning",
        "provider_executed",
        "production_claim_eligible",
        "source_artifact_mutated",
        "source_result_relabeling",
        "source_result_reuse_for_promotion",
    ):
        if boundary[key] is not False:
            raise ValueError(f"V45 execution boundary drift: {key}")
    if boundary["source_results_consumed_read_only"] is not True:
        raise ValueError("V45 source-consumption boundary drift")
    for key in (
        "model_execution",
        "training",
        "inference",
        "network_access",
        "downloads",
        "adaptive_tuning",
        "provider_executed",
        "production_claim_eligible",
        "source_artifact_mutated",
        "source_result_relabeling",
        "source_result_reuse_for_promotion",
    ):
        if contract[key] is not False:
            raise ValueError(f"V45 contract execution boundary drift: {key}")
    if contract["source_results_consumed_read_only"] is not True:
        raise ValueError("V45 contract source-consumption boundary drift")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "source_state_slice": SOURCE_STATE_SLICE,
        "case_count": len(expected_cases),
        "source_v44_valid": source_validation["valid"],
        "source_v44_all_cases_valid": source_validation["all_cases_valid"],
        "source_v44_all_cases_eligible": source_validation["all_cases_eligible"],
        "diagnostic_classification": report["root_cause_classification"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

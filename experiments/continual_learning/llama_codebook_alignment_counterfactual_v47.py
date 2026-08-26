#!/usr/bin/env python3
"""V47 paired Llama codebook-alignment counterfactual execution.

State slice: continual-learning-llama-codebook-alignment-counterfactual-execution-v47.

The only scientific change between paired arms is the target task's codebook
shift. Each arm trains a fresh adapter from the cached Llama base in a
separate subprocess and writes immutable artifacts outside the repository.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from statistics import median
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import qwen25_fixed_optimizer_acquisition_v37 as fixed_optimizer
from experiments.continual_learning import qwen25_raw_text_acquisition_v34 as acquisition
from experiments.continual_learning import validate_qwen25_fixed_optimizer_acquisition_v37 as arm_validator
from experiments.continual_learning import validate_runtime_receipt as runtime_validator
from experiments.continual_learning.runtime_seam import digest, sha256_file, write_json


STATE_SLICE = "continual-learning-llama-codebook-alignment-counterfactual-execution-v47"
PROTOCOL = "v47-llama-codebook-alignment-counterfactual-execution-v1"
ARM_STATE_SLICE = "continual-learning-llama-codebook-alignment-counterfactual-arm-v47"
ARM_PROTOCOL = "v47-llama-codebook-alignment-counterfactual-arm-v1"
CLAIM_CEILING = "LocalDevelopmentCodebookAlignmentCounterfactualDiagnosis"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit")
TASK_SEEDS = (20260865, 20260866, 20260867)
TARGET_SHIFTS = (0, 1)
FIXED_OPTIMIZER_SEED = 20260856
ORDER = (0, 1, 2, 3)
ITERS = 160
UPDATE_BUDGET = 32
TARGET_FLOOR = 0.75
DIAGNOSTIC_DELTA_FLOOR = 0.25
RUNTIME_ROOT = Path(
    "/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/"
    "continual-learning-llama-runtime-v44-20260826-r1"
)


def _ensure_external_new_root(root: Path, label: str = "V47 artifacts") -> Path:
    resolved = root.resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ValueError(f"{label} must remain outside the repository")
    if resolved.exists():
        raise FileExistsError(f"refusing overwrite of immutable {label}: {resolved}")
    return resolved


@contextmanager
def _patched(module: Any, values: dict[str, Any]) -> Iterator[None]:
    originals = {key: getattr(module, key) for key in values}
    for key, value in values.items():
        setattr(module, key, value)
    try:
        yield
    finally:
        for key, value in originals.items():
            setattr(module, key, value)


def _counterfactual_tasks(seed: int, task_count: int, target_shift: int):
    if target_shift not in TARGET_SHIFTS:
        raise ValueError("target shift is outside the preregistered set")
    tasks = tuple(_ORIGINAL_MAKE_TASKS(seed, task_count))
    target = tasks[0]
    mapping = tuple(base.LABELS[(residue + target_shift) % 4] for residue in range(4))
    if target_shift == 0:
        return tasks
    def relabel(fact):
        return replace(fact, label=mapping[fact.residue])
    target = replace(
        target,
        mapping=mapping,
        train_facts=tuple(relabel(fact) for fact in target.train_facts),
        test_facts=tuple(relabel(fact) for fact in target.test_facts),
    )
    return (target, *tasks[1:])


_ORIGINAL_MAKE_TASKS = base.make_tasks


def _underlying_fact_digest(tasks: list[dict[str, Any]]) -> str:
    rows = []
    for task in tasks:
        for split_name in ("train_facts", "test_facts"):
            for fact in task[split_name]:
                rows.append(
                    {
                        "task_id": fact["task_id"],
                        "task_token": fact["task_token"],
                        "fact_id": fact["fact_id"],
                        "left": fact["left"],
                        "right": fact["right"],
                        "residue": fact["residue"],
                        "split": split_name,
                    }
                )
    return digest(sorted(rows, key=lambda row: (row["task_id"], row["split"], row["fact_id"])))


def _arm_name(task_seed: int, target_shift: int) -> str:
    label = "identity-target" if target_shift == 0 else "matched-shift-target"
    return f"task-seed-{task_seed}-{label}-shift-{target_shift}-fixed-opt-{FIXED_OPTIMIZER_SEED}"


def _target_accuracy(result: dict[str, Any]) -> float:
    target = next(item for item in result["task_results"] if item["task_id"] == 0)
    return target["adapter_test"]["accuracy"]


def run_arm(output: Path, model: Path, task_seed: int, target_shift: int) -> dict[str, Any]:
    output = _ensure_external_new_root(output, "V47 arm artifacts")
    model = model.resolve()
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V47 fixed Llama model is unavailable or drifted")
    if task_seed not in TASK_SEEDS:
        raise ValueError("V47 task seed is outside the preregistered set")
    if target_shift not in TARGET_SHIFTS:
        raise ValueError("V47 target shift is outside the preregistered set")

    def make_tasks(seed: int, task_count: int):
        return _counterfactual_tasks(seed, task_count, target_shift)

    with _patched(
        acquisition,
        {
            "MODEL_DEFAULT": model,
            "SEEDS": (task_seed,),
            "STATE_SLICE": ARM_STATE_SLICE,
            "PROTOCOL": ARM_PROTOCOL,
            "CLAIM_CEILING": CLAIM_CEILING,
            "_train_adapter_bank": fixed_optimizer._train_fixed_optimizer_bank,
        },
    ), _patched(base, {"make_tasks": make_tasks}):
        result = acquisition.run_case(output, model, task_seed)

    tasks = result["tasks"]
    paired_digest = _underlying_fact_digest(tasks)
    config = dict(result["config"])
    config.pop("seed", None)
    config.update(
        {
            "state_slice": ARM_STATE_SLICE,
            "protocol": ARM_PROTOCOL,
            "model": str(model),
            "task_seed": task_seed,
            "target_shift": target_shift,
            "arm": "identity-target" if target_shift == 0 else "matched-shift-target",
            "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
            "order": list(ORDER),
            "iters": ITERS,
            "update_budget": UPDATE_BUDGET,
            "target_floor": TARGET_FLOOR,
            "paired_underlying_fact_digest": paired_digest,
            "source_state_slice": "continual-learning-llama-codebook-alignment-counterfactual-v46",
            "diagnostic_only": True,
            "network_access": False,
            "retention_executed": False,
            "interference_executed": False,
            "provider_executed": False,
            "production_claim_eligible": False,
        }
    )
    config["contract_sha256"] = digest({key: value for key, value in config.items() if key != "contract_sha256"})
    result.update(
        {
            "state_slice": ARM_STATE_SLICE,
            "protocol": ARM_PROTOCOL,
            "claim_ceiling": CLAIM_CEILING,
            "classification": "LlamaCodebookAlignmentCounterfactualArm",
            "config": config,
            "model": str(model),
            "task_seed": task_seed,
            "target_shift": target_shift,
            "arm": config["arm"],
            "paired_underlying_fact_digest": paired_digest,
            "diagnostic_only": True,
            "network_access": False,
            "retention_executed": False,
            "interference_executed": False,
            "provider_executed": False,
            "production_claim_eligible": False,
            "target_heldout_accuracy": _target_accuracy(result),
        }
    )
    audit = json.loads((output / "audit" / "task_adapter_bank.json").read_text(encoding="utf-8"))
    result["audit_sha256"] = digest(audit)
    result["manifest_sha256"] = digest({"config": config, "tasks": tasks, "audit": audit})
    result["result_sha256"] = digest({key: value for key, value in result.items() if key != "result_sha256"})
    (output / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _offline_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    )
    return environment


def _run_arm_validator(arm_root: Path, model: Path, task_seed: int, target_shift: int) -> dict[str, Any]:
    with _patched(
        arm_validator,
        {
            "MODEL": str(model),
            "TASK_SEEDS": [task_seed],
            "STATE_SLICE": ARM_STATE_SLICE,
            "PROTOCOL": ARM_PROTOCOL,
            "FIXED_OPTIMIZER_SEED": FIXED_OPTIMIZER_SEED,
            "ORDER": list(ORDER),
        },
    ):
        validation = arm_validator.validate(arm_root, model, task_seed)
    config = json.loads((arm_root / "config.json").read_text(encoding="utf-8"))
    result = json.loads((arm_root / "result.json").read_text(encoding="utf-8"))
    if config["target_shift"] != target_shift or result["target_shift"] != target_shift:
        raise ValueError("V47 target shift binding drift")
    if config["arm"] != ("identity-target" if target_shift == 0 else "matched-shift-target"):
        raise ValueError("V47 arm binding drift")
    tasks = json.loads((arm_root / "tasks.json").read_text(encoding="utf-8"))
    if config["paired_underlying_fact_digest"] != _underlying_fact_digest(tasks):
        raise ValueError("V47 paired fact digest drift")
    expected_mapping = [base.LABELS[(residue + (target_shift if task_id == 0 else task_id)) % 4] for residue in range(4)]
    target = next(task for task in tasks if task["task_id"] == 0)
    if target["mapping"] != expected_mapping:
        raise ValueError("V47 target mapping drift")
    if result["target_heldout_accuracy"] != _target_accuracy(result):
        raise ValueError("V47 target accuracy binding drift")
    return validation


def _run_subprocess_validator(arm_root: Path, model: Path, task_seed: int, target_shift: int) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).with_name("validate_llama_codebook_alignment_counterfactual_v47.py")),
        "--arm-root",
        str(arm_root),
        "--model",
        str(model),
        "--task-seed",
        str(task_seed),
        "--target-shift",
        str(target_shift),
    ]
    completed = subprocess.run(command, env=_offline_environment(), text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise ValueError(f"V47 arm validator failed: {completed.stdout.strip()} {completed.stderr.strip()}")
    return json.loads(completed.stdout.strip().splitlines()[-1])


def run_campaign(artifact_root: Path, model: Path = MODEL_DEFAULT, runtime_root: Path = RUNTIME_ROOT) -> dict[str, Any]:
    artifact_root = _ensure_external_new_root(artifact_root, "V47 campaign artifacts")
    model = model.resolve()
    runtime_root = runtime_root.resolve()
    if model != MODEL_DEFAULT.resolve() or not model.is_dir():
        raise ValueError("V47 fixed Llama model is unavailable or drifted")
    runtime_validation = runtime_validator.validate(runtime_root, model)
    if runtime_validation.get("valid") is not True or runtime_validation.get("training") is not False:
        raise ValueError("V47 runtime preflight is not valid inference-only evidence")

    artifact_root.mkdir(parents=True)
    contract = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "task_seeds": list(TASK_SEEDS),
        "target_shifts": list(TARGET_SHIFTS),
        "optimizer_seed_base": FIXED_OPTIMIZER_SEED,
        "order": list(ORDER),
        "iters": ITERS,
        "update_budget": UPDATE_BUDGET,
        "expected_arm_count": len(TASK_SEEDS) * len(TARGET_SHIFTS),
        "primary_metric": "matched_shift target heldout accuracy minus identity target heldout accuracy",
        "diagnostic_delta_floor": DIAGNOSTIC_DELTA_FLOOR,
        "runtime_preflight_root": str(runtime_root),
        "runtime_preflight_manifest_sha256": runtime_validation["manifest_sha256"],
        "runtime_preflight_receipt_file_sha256": sha256_file(runtime_root / "receipt.json"),
        "training": True,
        "prediction_locking": True,
        "network_access": False,
        "adaptive_tuning": False,
        "retention_executed": False,
        "order_retention_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "v44_mutated": False,
        "v44_result_reused_for_promotion": False,
    }
    contract["contract_sha256"] = digest(contract)
    write_json(artifact_root / "contract.json", contract)
    (artifact_root / "validation").mkdir(parents=True, exist_ok=True)

    arms = []
    for task_seed in TASK_SEEDS:
        for target_shift in TARGET_SHIFTS:
            name = _arm_name(task_seed, target_shift)
            arm_root = artifact_root / "arms" / name
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--arm-output",
                str(arm_root),
                "--model",
                str(model),
                "--task-seed",
                str(task_seed),
                "--target-shift",
                str(target_shift),
            ]
            completed = subprocess.run(command, env=_offline_environment(), text=True, capture_output=True, check=False)
            (artifact_root / f"{name}.runner.log").write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
            if completed.returncode != 0:
                arms.append({"task_seed": task_seed, "target_shift": target_shift, "arm": name, "valid": False, "status": "runner_failed"})
                break
            try:
                validation = _run_subprocess_validator(arm_root, model, task_seed, target_shift)
            except Exception as exc:
                arms.append({"task_seed": task_seed, "target_shift": target_shift, "arm": name, "valid": False, "status": "validator_failed", "reason": str(exc)})
                break
            write_json(artifact_root / "validation" / f"{name}.json", validation)
            result = json.loads((arm_root / "result.json").read_text(encoding="utf-8"))
            arms.append(
                {
                    "task_seed": task_seed,
                    "target_shift": target_shift,
                    "arm": name,
                    "status": "validated",
                    "valid": validation["valid"],
                    "eligible": validation["eligible"],
                    "target_heldout_accuracy": result["target_heldout_accuracy"],
                    "paired_underlying_fact_digest": result["paired_underlying_fact_digest"],
                    "result_sha256": result["result_sha256"],
                }
            )
        if arms and not arms[-1]["valid"]:
            break

    pairs = []
    for task_seed in TASK_SEEDS:
        identity = next((row for row in arms if row["task_seed"] == task_seed and row["target_shift"] == 0), None)
        shifted = next((row for row in arms if row["task_seed"] == task_seed and row["target_shift"] == 1), None)
        if identity is None or shifted is None or not identity["valid"] or not shifted["valid"]:
            continue
        if identity["paired_underlying_fact_digest"] != shifted["paired_underlying_fact_digest"]:
            raise ValueError("V47 paired underlying fact digest mismatch")
        pairs.append(
            {
                "task_seed": task_seed,
                "identity_target_accuracy": identity["target_heldout_accuracy"],
                "matched_shift_target_accuracy": shifted["target_heldout_accuracy"],
                "delta": round(shifted["target_heldout_accuracy"] - identity["target_heldout_accuracy"], 6),
                "paired_underlying_fact_digest": identity["paired_underlying_fact_digest"],
            }
        )
    deltas = [pair["delta"] for pair in pairs]
    all_valid = len(arms) == contract["expected_arm_count"] and all(row["valid"] for row in arms)
    if all_valid and len(deltas) == len(TASK_SEEDS) and all(delta >= 0 for delta in deltas) and median(deltas) >= DIAGNOSTIC_DELTA_FLOOR:
        classification = "CodebookAlignmentSupported"
    elif all_valid and len(deltas) == len(TASK_SEEDS) and all(delta <= 0 for delta in deltas):
        classification = "CodebookAlignmentNotSupported"
    else:
        classification = "CodebookAlignmentInconclusive"
    report = {
        "state_slice": STATE_SLICE,
        "protocol": PROTOCOL,
        "claim_ceiling": CLAIM_CEILING,
        "model": str(model),
        "arms": arms,
        "expected_arm_count": contract["expected_arm_count"],
        "pairs": pairs,
        "deltas": deltas,
        "all_arms_valid": all_valid,
        "diagnostic_completed": all_valid and len(pairs) == len(TASK_SEEDS),
        "classification": classification,
        "retention_executed": False,
        "order_retention_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "network_access": False,
    }
    report["report_sha256"] = digest(report)
    write_json(artifact_root / "report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--arm-output", type=Path)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--task-seed", type=int)
    parser.add_argument("--target-shift", type=int)
    parser.add_argument("--runtime-root", type=Path, default=RUNTIME_ROOT)
    args = parser.parse_args()
    if args.arm_output is not None:
        if args.task_seed is None or args.target_shift is None:
            raise ValueError("V47 arm mode requires task-seed and target-shift")
        result = run_arm(args.arm_output, args.model, args.task_seed, args.target_shift)
        print(json.dumps(result, sort_keys=True))
        return 0
    if args.artifact_root is None:
        raise ValueError("V47 campaign mode requires artifact-root")
    result = run_campaign(args.artifact_root, args.model, args.runtime_root)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["diagnostic_completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

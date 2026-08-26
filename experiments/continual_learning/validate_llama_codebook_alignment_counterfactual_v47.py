#!/usr/bin/env python3
"""Independent V47 arm and campaign validator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning import validate_qwen25_fixed_optimizer_acquisition_v37 as arm_validator
from experiments.continual_learning import validate_runtime_receipt as runtime_validator
from experiments.continual_learning.llama_codebook_alignment_counterfactual_v47 import (
    ARM_PROTOCOL,
    ARM_STATE_SLICE,
    CLAIM_CEILING,
    DIAGNOSTIC_DELTA_FLOOR,
    FIXED_OPTIMIZER_SEED,
    MODEL_DEFAULT,
    ORDER,
    PROTOCOL,
    RUNTIME_ROOT,
    STATE_SLICE,
    TARGET_SHIFTS,
    TASK_SEEDS,
    _target_accuracy,
    _underlying_fact_digest,
)
from experiments.continual_learning.runtime_seam import digest, sha256_file


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _patched(module, values):
    originals = {key: getattr(module, key) for key in values}
    for key, value in values.items():
        setattr(module, key, value)
    return originals


def _restore(module, originals):
    for key, value in originals.items():
        setattr(module, key, value)


def validate_arm(root: Path, model: Path, task_seed: int, target_shift: int) -> dict:
    root = root.resolve()
    model = model.resolve()
    if model != MODEL_DEFAULT.resolve():
        raise ValueError("V47 fixed model drift")
    if task_seed not in TASK_SEEDS or target_shift not in TARGET_SHIFTS:
        raise ValueError("V47 arm identity drift")
    config = _load(root / "config.json")
    result = _load(root / "result.json")
    originals = _patched(
        arm_validator,
        {
            "MODEL": str(model),
            "TASK_SEEDS": [task_seed],
            "STATE_SLICE": ARM_STATE_SLICE,
            "PROTOCOL": ARM_PROTOCOL,
            "FIXED_OPTIMIZER_SEED": FIXED_OPTIMIZER_SEED,
            "ORDER": list(ORDER),
        },
    )
    try:
        delegated = arm_validator.validate(root, model, task_seed)
    finally:
        _restore(arm_validator, originals)
    if config["target_shift"] != target_shift or result["target_shift"] != target_shift:
        raise ValueError("V47 target shift drift")
    expected_arm = "identity-target" if target_shift == 0 else "matched-shift-target"
    if config["arm"] != expected_arm or result["arm"] != expected_arm:
        raise ValueError("V47 arm label drift")
    tasks = _load(root / "tasks.json")
    if config["paired_underlying_fact_digest"] != _underlying_fact_digest(tasks):
        raise ValueError("V47 paired fact digest drift")
    for task_id in range(4):
        task = next(item for item in tasks if item["task_id"] == task_id)
        shift = target_shift if task_id == 0 else task_id
        expected = [base.LABELS[(residue + shift) % 4] for residue in range(4)]
        if task["mapping"] != expected:
            raise ValueError("V47 mapping drift")
    if result["config"] != config:
        raise ValueError("V47 result/config identity drift")
    if result["target_heldout_accuracy"] != _target_accuracy(result):
        raise ValueError("V47 target accuracy drift")
    if result["result_sha256"] != digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ValueError("V47 result digest drift")
    return {"valid": True, "eligible": delegated["eligible"], "target_heldout_accuracy": result["target_heldout_accuracy"], "result_sha256": result["result_sha256"]}


def validate(root: Path, model: Path, runtime_root: Path) -> dict:
    root = root.resolve()
    model = model.resolve()
    runtime_root = runtime_root.resolve()
    contract = _load(root / "contract.json")
    report = _load(root / "report.json")
    if contract["state_slice"] != STATE_SLICE or contract["protocol"] != PROTOCOL:
        raise ValueError("V47 contract identity drift")
    if contract["model"] != str(model) or contract["task_seeds"] != list(TASK_SEEDS):
        raise ValueError("V47 contract model/seed drift")
    if contract["target_shifts"] != list(TARGET_SHIFTS) or contract["order"] != list(ORDER):
        raise ValueError("V47 contract arm/order drift")
    if contract["runtime_preflight_root"] != str(runtime_root):
        raise ValueError("V47 runtime root drift")
    runtime = runtime_validator.validate(runtime_root, model)
    if runtime.get("valid") is not True or runtime.get("training") is not False:
        raise ValueError("V47 runtime receipt invalid")
    if contract["runtime_preflight_manifest_sha256"] != runtime["manifest_sha256"]:
        raise ValueError("V47 runtime manifest drift")
    if contract["runtime_preflight_receipt_file_sha256"] != sha256_file(runtime_root / "receipt.json"):
        raise ValueError("V47 runtime receipt drift")
    if contract["contract_sha256"] != digest({key: value for key, value in contract.items() if key != "contract_sha256"}):
        raise ValueError("V47 contract digest drift")
    if report["state_slice"] != STATE_SLICE or report["protocol"] != PROTOCOL:
        raise ValueError("V47 report identity drift")
    if report["report_sha256"] != digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("V47 report digest drift")
    if report["expected_arm_count"] != len(TASK_SEEDS) * len(TARGET_SHIFTS):
        raise ValueError("V47 arm count drift")
    arms = report["arms"]
    if len(arms) != report["expected_arm_count"]:
        raise ValueError("V47 report arm cardinality drift")
    validated = []
    for row in arms:
        arm_root = root / "arms" / row["arm"]
        arm_validation = validate_arm(arm_root, model, row["task_seed"], row["target_shift"])
        saved = _load(root / "validation" / f"{row['arm']}.json")
        if saved != arm_validation:
            raise ValueError("V47 saved arm validation drift")
        if row["valid"] is not True or row["result_sha256"] != arm_validation["result_sha256"]:
            raise ValueError("V47 aggregate arm binding drift")
        result = _load(arm_root / "result.json")
        if row["target_heldout_accuracy"] != result["target_heldout_accuracy"]:
            raise ValueError("V47 aggregate target metric drift")
        validated.append(row)
    pairs = report["pairs"]
    if len(pairs) != len(TASK_SEEDS):
        raise ValueError("V47 pair cardinality drift")
    recomputed_pairs = []
    for task_seed in TASK_SEEDS:
        identity = next(row for row in validated if row["task_seed"] == task_seed and row["target_shift"] == 0)
        shifted = next(row for row in validated if row["task_seed"] == task_seed and row["target_shift"] == 1)
        if identity["paired_underlying_fact_digest"] != shifted["paired_underlying_fact_digest"]:
            raise ValueError("V47 pair digest mismatch")
        recomputed_pairs.append(
            {
                "task_seed": task_seed,
                "identity_target_accuracy": identity["target_heldout_accuracy"],
                "matched_shift_target_accuracy": shifted["target_heldout_accuracy"],
                "delta": round(shifted["target_heldout_accuracy"] - identity["target_heldout_accuracy"], 6),
                "paired_underlying_fact_digest": identity["paired_underlying_fact_digest"],
            }
        )
    if pairs != recomputed_pairs or report["deltas"] != [row["delta"] for row in recomputed_pairs]:
        raise ValueError("V47 paired metric drift")
    deltas = [row["delta"] for row in recomputed_pairs]
    all_valid = all(row["valid"] for row in validated)
    expected_classification = (
        "CodebookAlignmentSupported"
        if all_valid and all(delta >= 0 for delta in deltas) and median(deltas) >= DIAGNOSTIC_DELTA_FLOOR
        else "CodebookAlignmentNotSupported"
        if all_valid and all(delta <= 0 for delta in deltas)
        else "CodebookAlignmentInconclusive"
    )
    if report["classification"] != expected_classification:
        raise ValueError("V47 classification drift")
    if report["diagnostic_completed"] is not True or report["all_arms_valid"] is not True:
        raise ValueError("V47 campaign is not complete and valid")
    return {"valid": True, "classification": report["classification"], "deltas": deltas, "claim_ceiling": CLAIM_CEILING}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path)
    parser.add_argument("--arm-root", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, default=RUNTIME_ROOT)
    parser.add_argument("--task-seed", type=int)
    parser.add_argument("--target-shift", type=int)
    args = parser.parse_args()
    try:
        if args.arm_root is not None:
            if args.task_seed is None or args.target_shift is None:
                raise ValueError("arm validation requires task-seed and target-shift")
            result = validate_arm(args.arm_root, args.model, args.task_seed, args.target_shift)
        elif args.root is not None:
            result = validate(args.root, args.model, args.runtime_root)
        else:
            raise ValueError("validation requires root or arm-root")
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


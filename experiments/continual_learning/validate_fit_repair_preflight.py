#!/usr/bin/env python3
"""Independent validator for the V13 fit-repair preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


STATE_SLICE = "continual-learning-protocol-v13-training-objective-repair"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    config = json.loads((root / "config.json").read_text())
    result = json.loads((root / "result.json").read_text())
    if result["state_slice"] != STATE_SLICE or result["breakthrough_claim_eligible"] is not False:
        raise ValueError("state or claim boundary drift")
    if result["retention_comparison_run"] is not False:
        raise ValueError("retention comparison was not prohibited")
    fixed = {
        "source_state_slice": "continual-learning-protocol-v12-training-fit-audit",
        "seed": 20260810,
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
        "iters": 160,
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
    }
    for key, expected in fixed.items():
        if config.get(key) != expected:
            raise ValueError(f"fixed contract drift: {key}")
    if config.get("prompt_contract") != {
        "training_prompt_equals_assessment_prompt": True,
        "answer_suffix": "\nAnswer:",
        "derived_residue_visible": True,
        "raw_pair_present": False,
    }:
        raise ValueError("prompt contract drift")
    if config["contract_sha256"] != digest({key: value for key, value in config.items() if key != "contract_sha256"}):
        raise ValueError("contract digest mismatch")
    if result["result_sha256"] != digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ValueError("result digest mismatch")
    if result["dataset_parity"] != {
        "rows_checked": 64,
        "expected_rows": 64,
        "parity_failures": [],
        "exact_prompt_completion_parity": True,
    }:
        raise ValueError("dataset parity drift")
    if result["token_supervision"] != {
        "candidate_token_lengths": {"A": 1, "B": 1, "C": 1, "D": 1},
        "single_token_labels": True,
    }:
        raise ValueError("token supervision drift")
    if len(result["controls"]) != 2 or {control["strategy"] for control in result["controls"]} != {"naive_fit", "task_adapter_bank_fit"}:
        raise ValueError("fit control panel drift")
    for control in result["controls"]:
        if control["dataset_row_count"] != 32 or control["train_accuracy"]["n"] != 8 or not control["receipt"]["final_weights_saved"]:
            raise ValueError(f"fit control receipt drift: {control['strategy']}")
        if control["receipt"]["final_train_step"] != 160 or control["receipt"]["final_val_step"] != 160:
            raise ValueError(f"fit control iteration drift: {control['strategy']}")
    gates = result["gates"]
    if gates["prompt_completion_parity"] is not True or gates["single_token_label_supervision"] is not True or gates["training_receipts_complete"] is not True:
        raise ValueError("structural fit gate failure")
    if result["fit_floor_passed"] != (gates["naive_fit_floor"] and gates["bank_fit_floor"]):
        raise ValueError("fit floor derivation drift")
    return {
        "valid": True,
        "claim_ceiling": result["claim_ceiling"],
        "fit_floor_passed": result["fit_floor_passed"],
        "gates": gates,
        "manifest_sha256": result["manifest_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root.resolve()), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

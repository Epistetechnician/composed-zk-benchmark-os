#!/usr/bin/env python3
"""Independent validator for the V12 read-only training-fit audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


STATE_SLICE = "continual-learning-protocol-v12-training-fit-audit"
SOURCE_STATE_SLICE = "continual-learning-protocol-v11-residue-only-codebook"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(root: Path) -> dict:
    report = json.loads((root / "report.json").read_text(encoding="utf8"))
    if report["state_slice"] != STATE_SLICE or report["source_state_slice"] != SOURCE_STATE_SLICE:
        raise ValueError("state slice drift")
    if report["breakthrough_claim_eligible"] is not False:
        raise ValueError("claim boundary drift")
    if report["report_sha256"] != digest({key: value for key, value in report.items() if key != "report_sha256"}):
        raise ValueError("report digest mismatch")
    parity = report["dataset_parity"]
    if parity["dataset_count"] != 12 or parity["rows_checked"] != 384 or parity["parity_failures"]:
        raise ValueError("dataset parity audit failure")
    if parity["exact_prompt_completion_parity"] is not True:
        raise ValueError("prompt parity gate failure")
    tokens = report["token_supervision"]
    if tokens["candidate_token_lengths"] != {"A": 1, "B": 1, "C": 1, "D": 1} or tokens["single_token_labels"] is not True:
        raise ValueError("completion token supervision failure")
    fit = report["adapter_fit"]
    if fit["entry_count"] != 12 or fit["expected_entry_count"] != 12:
        raise ValueError("adapter fit entry count drift")
    if len(fit["training_receipts"]) != 12 or not all(receipt["final_weights_saved"] for receipt in fit["training_receipts"]):
        raise ValueError("training receipt failure")
    if fit["naive_final_target_train_accuracy"] != 0.5 or fit["bank_task0_train_accuracy"] != 0.25:
        raise ValueError("fit result drift")
    expected_gates = {
        "prompt_completion_parity": True,
        "single_token_label_supervision": True,
        "naive_final_fit_floor": False,
        "bank_task0_fit_floor": False,
        "training_receipts_complete": True,
    }
    if report["gates"] != expected_gates or report["fit_floor_passed"] is not False:
        raise ValueError("fit gate drift")
    return {
        "valid": True,
        "claim_ceiling": report["claim_ceiling"],
        "source_manifest_sha256": report["source_manifest_sha256"],
        "fit_floor_passed": report["fit_floor_passed"],
        "gates": report["gates"],
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

#!/usr/bin/env python3
"""Run and independently validate the preregistered V27 campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.validate_runtime_receipt import validate as validate_runtime


STATE_SLICE = "continual-learning-replication-task-routed-adapter-bank-v27"
MODEL_DEFAULT = Path("/Users/shaanp/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit")
CASES = (
    (20260850, "0,3,2,1"),
    (20260851, "0,2,3,1"),
    (20260852, "0,1,3,2"),
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: argparse.Namespace) -> dict:
    artifact_root = args.artifact_root.resolve()
    model = args.model.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable campaign root: {artifact_root}")
    if not model.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model}")
    runtime_root = args.runtime_receipt.resolve()
    runtime_validation = validate_runtime(runtime_root, model)
    if not runtime_validation["valid"] or runtime_validation["training"] is not False:
        raise RuntimeError("runtime preflight did not validate as offline inference-only")
    artifact_root.mkdir(parents=True)
    records = []
    runner = Path(__file__).with_name("routed_adapter_bank_replication_v27.py")
    validator = Path(__file__).with_name("validate_routed_adapter_bank_replication_v27.py")
    runtime_manifest_sha256 = runtime_validation["manifest_sha256"]
    runtime_receipt_sha256 = sha256_file(runtime_root / "receipt.json")
    for seed, order in CASES:
        case_root = artifact_root / f"seed-{seed}-order-{order.replace(',', '')}"
        command = [
            sys.executable,
            str(runner),
            "--output",
            str(case_root),
            "--model",
            str(model),
            "--seed",
            str(seed),
            "--order",
            order,
            "--iters",
            "160",
            "--runtime-manifest-sha256",
            runtime_manifest_sha256,
            "--runtime-receipt-sha256",
            runtime_receipt_sha256,
        ]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        (case_root.parent / f"{case_root.name}.runner.log").write_text(
            completed.stdout + "\n" + completed.stderr, encoding="utf8"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"V27 runner failed for {seed}/{order}: {completed.returncode}")
        completed_validation = subprocess.run(
            [sys.executable, str(validator), str(case_root)],
            text=True,
            capture_output=True,
            check=False,
        )
        (case_root.parent / f"{case_root.name}.validator.log").write_text(
            completed_validation.stdout + "\n" + completed_validation.stderr, encoding="utf8"
        )
        if completed_validation.returncode != 0:
            raise RuntimeError(f"V27 validation failed for {seed}/{order}: {completed_validation.returncode}")
        validation = json.loads(completed_validation.stdout)
        records.append(
            {
                "seed": seed,
                "order": order,
                "artifact": str(case_root),
                "validation": validation,
                "result_sha256": json.loads((case_root / "result.json").read_text())["result_sha256"],
            }
        )
        if not validation["valid"]:
            raise RuntimeError(f"V27 validation failed for {seed}/{order}")

    report = {
        "state_slice": STATE_SLICE,
        "model": str(model),
        "runtime_preflight_manifest_sha256": runtime_manifest_sha256,
        "runtime_preflight_receipt_sha256": runtime_receipt_sha256,
        "cases": records,
        "case_count": len(records),
        "all_valid": all(record["validation"]["valid"] for record in records),
        "all_candidate_gates": all(record["validation"]["candidate_eligible"] for record in records),
        "replication_eligible": all(record["validation"]["candidate_eligible"] for record in records),
        "claim_ceiling": "LocalDevelopmentTaskRoutedAdapterBankReplication",
        "production_claim_eligible": False,
        "network_access": False,
    }
    report_path = args.report.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--runtime-receipt", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    args = parser.parse_args()
    report = run(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["replication_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

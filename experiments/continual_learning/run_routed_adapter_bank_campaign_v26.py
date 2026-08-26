#!/usr/bin/env python3
"""Run the preregistered V26 fresh-case campaign with independent validation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.validate_routed_adapter_bank_candidate_v26 import validate


STATE_SLICE = "continual-learning-candidate-task-routed-adapter-bank-v26"
CASES = (
    (20260840, "0,1,2,3"),
    (20260841, "0,1,3,2"),
    (20260842, "0,2,1,3"),
)


def run(args: argparse.Namespace) -> dict:
    artifact_root = args.artifact_root.resolve()
    if artifact_root.exists():
        raise RuntimeError(f"refusing overwrite of immutable campaign root: {artifact_root}")
    artifact_root.mkdir(parents=True)
    records = []
    runner = Path(__file__).with_name("routed_adapter_bank_candidate_v26.py")
    validator = Path(__file__).with_name("validate_routed_adapter_bank_candidate_v26.py")
    for seed, order in CASES:
        case_root = artifact_root / f"seed-{seed}-order-{order.replace(',', '')}"
        command = [
            sys.executable,
            str(runner),
            "--output",
            str(case_root),
            "--model",
            str(args.model.resolve()),
            "--seed",
            str(seed),
            "--order",
            order,
            "--iters",
            "160",
        ]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        (case_root.parent / f"{case_root.name}.runner.log").write_text(
            completed.stdout + "\n" + completed.stderr,
            encoding="utf8",
        )
        if completed.returncode != 0:
            raise RuntimeError(f"V26 runner failed for {seed}/{order}: {completed.returncode}")
        validation = validate(case_root)
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
            raise RuntimeError(f"V26 validation failed for {seed}/{order}")

    report = {
        "state_slice": STATE_SLICE,
        "cases": records,
        "case_count": len(records),
        "all_valid": all(record["validation"]["valid"] for record in records),
        "all_candidate_gates": all(record["validation"]["candidate_eligible"] for record in records),
        "candidate_eligible": all(record["validation"]["candidate_eligible"] for record in records),
        "claim_ceiling": "LocalDevelopmentTaskRoutedAdapterBankCandidate",
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
    parser.add_argument("--model", type=Path, default=Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"))
    args = parser.parse_args()
    report = run(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["candidate_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

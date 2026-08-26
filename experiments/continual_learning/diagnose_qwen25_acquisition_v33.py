#!/usr/bin/env python3
"""V33 read-only diagnosis of the V32 non-target acquisition blocker.

State slice: continual-learning-diagnosis-qwen25-acquisition-v33.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.validate_qwen25_acquisition_eligibility_v32 import validate as validate_case


STATE_SLICE = "continual-learning-diagnosis-qwen25-acquisition-v33"
SOURCE_STATE_SLICE = "continual-learning-qwen25-acquisition-eligibility-v32"
CLAIM_CEILING = "LocalDevelopmentQwen25AcquisitionFailureDiagnosis"
MODEL = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")
SEEDS = (20260853, 20260854, 20260855)


def classify_task(task_result: dict) -> str:
    no_update = task_result["no_update_train"]["accuracy"]
    adapter = task_result["adapter_train"]["accuracy"]
    constant = task_result["adapter_train"]["constant_output"]
    if adapter <= no_update:
        return "NonTargetAcquisitionTieOrRegression"
    if constant:
        return "PartialAcquisitionConstantOutput"
    return "AcquiredNonConstant"


def _task_summary(task_result: dict) -> dict:
    observed = [row["observed"] for row in task_result["adapter_train"]["rows"]]
    return {
        "task_id": task_result["task_id"],
        "route_key": task_result["route_key"],
        "no_update_train_accuracy": task_result["no_update_train"]["accuracy"],
        "adapter_train_accuracy": task_result["adapter_train"]["accuracy"],
        "adapter_heldout_accuracy": task_result["adapter_test"]["accuracy"],
        "train_delta_vs_no_update": round(
            task_result["adapter_train"]["accuracy"] - task_result["no_update_train"]["accuracy"], 6
        ),
        "train_heldout_delta": round(
            task_result["adapter_train"]["accuracy"] - task_result["adapter_test"]["accuracy"], 6
        ),
        "constant_output": len(set(observed)) == 1,
        "observed_histogram": dict(sorted(Counter(observed).items())),
        "classification": classify_task(task_result),
    }


def run(artifact_root: Path, output: Path) -> dict:
    source = artifact_root.resolve()
    destination = output.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    if destination == repo_root or repo_root in destination.parents:
        raise ValueError("diagnostic output must remain outside the repository")
    if destination.exists():
        raise FileExistsError(f"refusing overwrite of immutable diagnostic: {destination}")
    source_report = json.loads((source / "campaign_report.json").read_text(encoding="utf8"))
    if source_report["state_slice"] != SOURCE_STATE_SLICE or source_report["campaign_eligible"] is not False:
        raise ValueError("V32 source campaign boundary drift")

    cases = []
    for seed in SEEDS:
        case_root = source / f"seed-{seed}-order-0123"
        validation = validate_case(case_root, MODEL, seed)
        result = json.loads((case_root / "result.json").read_text(encoding="utf8"))
        summaries = [_task_summary(item) for item in result["task_results"]]
        cases.append(
            {
                "seed": seed,
                "case": case_root.name,
                "case_result_sha256": result["result_sha256"],
                "case_valid": validation["valid"],
                "case_eligible": validation["eligible"],
                "target_task": next(item for item in summaries if item["task_id"] == 0),
                "tasks": summaries,
            }
        )

    failures = [
        {"seed": case["seed"], "task_id": task["task_id"], "classification": task["classification"]}
        for case in cases
        for task in case["tasks"]
        if task["classification"] != "AcquiredNonConstant"
    ]
    target_tasks = [case["target_task"] for case in cases]
    report = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "source_campaign_report_sha256": source_report["report_sha256"],
        "model": str(MODEL),
        "network_access": False,
        "training": False,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "cases": cases,
        "all_cases_valid": all(case["case_valid"] for case in cases),
        "target_acquisition_robust": all(
            task["adapter_train_accuracy"] > task["no_update_train_accuracy"]
            and task["adapter_heldout_accuracy"] >= 0.75
            and not task["constant_output"]
            for task in target_tasks
        ),
        "non_target_acquisition_stability": not any(item["task_id"] != 0 for item in failures),
        "non_target_failures": failures,
        "diagnostic_classification": "NonTargetAcquisitionInstabilityNotTargetFailure"
        if failures and all(item["task_id"] != 0 for item in failures)
        else "MixedOrTargetAcquisitionFailure",
        "next_hypothesis": "The next intervention must improve per-task acquisition stability across non-target routes; target T0 acquisition is already robust.",
    }
    report["report_sha256"] = base.digest(report)
    destination.mkdir(parents=True)
    (destination / "diagnosis.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.artifact_root, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

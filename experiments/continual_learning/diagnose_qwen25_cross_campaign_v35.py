#!/usr/bin/env python3
"""V35 read-only comparison of V32 and V34 Qwen2.5 campaigns.

State slice: continual-learning-cross-campaign-diagnosis-v35.

This diagnosis consumes only independently validated external receipts. It
does not execute a model, training, retention, provider, or production work.
The V32 and V34 seeds are disjoint, so the comparison diagnoses consistency;
it does not establish a causal effect for raw-text serialization.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import factorized_solvability_benchmark as base
from experiments.continual_learning.validate_qwen25_acquisition_campaign_v32 import validate as validate_v32
from experiments.continual_learning.validate_qwen25_raw_text_campaign_v34 import validate as validate_v34


STATE_SLICE = "continual-learning-cross-campaign-diagnosis-v35"
CLAIM_CEILING = "LocalDevelopmentQwen25CrossCampaignAcquisitionDiagnosis"
MODEL = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
V32_STATE_SLICE = "continual-learning-qwen25-acquisition-eligibility-v32"
V34_STATE_SLICE = "continual-learning-qwen25-raw-text-acquisition-v34"
V32_SEEDS = (20260853, 20260854, 20260855)
V34_SEEDS = (20260856, 20260857, 20260858)


def _stable(task: dict) -> bool:
    return (
        task["adapter_train"]["accuracy"] > task["no_update_train"]["accuracy"]
        and task["adapter_test"]["accuracy"] >= 0.75
        and len({row["observed"] for row in task["adapter_train"]["rows"]}) > 1
    )


def _load_campaign(root: Path, version: str) -> dict:
    validator = validate_v32 if version == "v32" else validate_v34
    validation = validator(root)
    report = json.loads((root / "campaign_report.json").read_text(encoding="utf8"))
    cases = []
    for row in report["cases"]:
        case_root = root / f"seed-{row['seed']}-order-0123"
        result = json.loads((case_root / "result.json").read_text(encoding="utf8"))
        task_stability = {str(task["task_id"]): _stable(task) for task in result["task_results"]}
        cases.append(
            {
                "seed": row["seed"],
                "result_sha256": result["result_sha256"],
                "eligible": result["eligible"],
                "task_stability": task_stability,
                "target_failure": not task_stability["0"],
            }
        )
    return {
        "version": version,
        "state_slice": report["state_slice"],
        "protocol": report["protocol"],
        "campaign_report_sha256": report["report_sha256"],
        "campaign_eligible": report["campaign_eligible"],
        "case_count": len(cases),
        "all_cases_valid": validation["valid"] and report["all_cases_valid"],
        "cases": cases,
    }


def _stability_summary(campaign: dict) -> dict:
    non_target = [
        stable
        for case in campaign["cases"]
        for task_id, stable in case["task_stability"].items()
        if task_id != "0"
    ]
    target = [case["task_stability"]["0"] for case in campaign["cases"]]
    return {
        "non_target_stable_cases": sum(non_target),
        "non_target_case_count": len(non_target),
        "non_target_stability_rate": sum(non_target) / len(non_target),
        "target_stable_cases": sum(target),
        "target_case_count": len(target),
        "target_stability_rate": sum(target) / len(target),
        "eligible_case_count": sum(case["eligible"] for case in campaign["cases"]),
    }


def run(v32_root: Path, v34_root: Path, output: Path) -> dict:
    destination = output.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    if destination == repo_root or repo_root in destination.parents:
        raise ValueError("diagnostic output must remain outside the repository")
    if destination.exists():
        raise FileExistsError(f"refusing overwrite of immutable diagnosis: {destination}")

    v32 = _load_campaign(v32_root.resolve(), "v32")
    v34 = _load_campaign(v34_root.resolve(), "v34")
    if v32["state_slice"] != V32_STATE_SLICE or v34["state_slice"] != V34_STATE_SLICE:
        raise ValueError("source state slice drift")
    if v32["case_count"] != len(V32_SEEDS) or v34["case_count"] != len(V34_SEEDS):
        raise ValueError("source case cardinality drift")

    v32_summary = _stability_summary(v32)
    v34_summary = _stability_summary(v34)
    report = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model": MODEL,
        "source_campaigns": [v32, v34],
        "v32_summary": v32_summary,
        "v34_summary": v34_summary,
        "primary_metric": "non_target_nonconstant_acquisition_stability_rate",
        "primary_metric_direction": "higher",
        "comparison": {
            "non_target_stability_rate_delta_v34_minus_v32": round(
                v34_summary["non_target_stability_rate"] - v32_summary["non_target_stability_rate"], 6
            ),
            "target_stability_rate_delta_v34_minus_v32": round(
                v34_summary["target_stability_rate"] - v32_summary["target_stability_rate"], 6
            ),
            "campaign_eligibility_delta_v34_minus_v32": v34_summary["eligible_case_count"] - v32_summary["eligible_case_count"],
        },
        "diagnostic_classification": "NonTargetStabilityImprovedTargetSeedSensitivityRemains",
        "causal_status": "DisjointSeedComparisonNotCausalProof",
        "network_access": False,
        "training": False,
        "retention_executed": False,
        "interference_executed": False,
        "provider_executed": False,
        "production_claim_eligible": False,
        "next_hypothesis": "Raw-text serialization remains a candidate for non-target stability, but target T0 requires a separately preregistered controlled initialization or optimizer-seed diagnosis before retention consideration.",
    }
    report["report_sha256"] = base.digest(report)
    destination.mkdir(parents=True)
    (destination / "diagnosis.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v32-root", type=Path, required=True)
    parser.add_argument("--v34-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.v32_root, args.v34_root, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

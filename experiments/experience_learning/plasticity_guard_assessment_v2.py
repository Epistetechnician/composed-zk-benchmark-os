"""Powered plasticity-guard assessment on custodied real experience streams.

State slice: ``oaklab-experience-learning-benchmark-v2``.

This is a new sealed protocol after the underpowered V1 result. Four fit
cohorts and four tune cohorts are consumed before thirty-two disjoint
assessment cohorts. The cohort size is reduced to 128 so the required sample
count is available in the custodied sensor panel without concatenating source
splits. No assessment outcome can change the learner hyperparameters.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Sequence

from .acquire_real_data_v1 import validate_manifest
from .custody import load_custodied_jsonl
from .learners import PlasticityGuardLearner, SGDLearner
from .statistics import estimate, paired_test
from .types import Experience


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"
PLAN = {
    "version": "plasticity-guard-real-powered-cohort-v2",
    "cohort_size": 128,
    "fit_cohort_indices": [0, 1, 2, 3],
    "tune_cohort_indices": [4, 5, 6, 7],
    "assessment_cohort_indices": list(range(8, 40)),
    "arms": ["fixed_sgd_b1", "plasticity_guard"],
    "alpha": 0.05,
    "target_standardized_effect": 0.5,
    "target_paired_sd": 1.0,
    "target_power": 0.80,
    "primary_endpoint": "assessment_cohort_mean_prediction_loss",
    "resource_gate": ["updates", "active_synaptic_ops", "state_bytes"],
    "frozen_hyperparameters": {
        "fixed_sgd_b1": {"learning_rate": 0.00001},
        "plasticity_guard": {
            "learning_rate": 0.00001,
            "guard_floor": 0.2,
            "recovery": 0.02,
            "surprise_threshold": 1.0,
        },
    },
}


def _digest(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


PLAN_DIGEST = _digest(PLAN)


def paired_normal_power(n: int, standardized_effect: float, alpha: float = 0.05) -> float:
    """Return the sealed two-sided normal-approximation paired-test power."""
    if n < 2 or standardized_effect < 0 or not math.isfinite(standardized_effect):
        raise ValueError("power inputs are invalid")
    if alpha != 0.05:
        raise ValueError("this sealed plan supports alpha=0.05 only")
    critical = 1.959963984540054
    noncentral = standardized_effect * math.sqrt(n)
    cdf = lambda value: 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))
    return cdf(-critical - noncentral) + 1.0 - cdf(critical - noncentral)


def _learner(name: str, dimensions: int):
    if name == "fixed_sgd_b1":
        return SGDLearner(dimensions, learning_rate=PLAN["frozen_hyperparameters"][name]["learning_rate"], batch_size=1)
    if name == "plasticity_guard":
        return PlasticityGuardLearner(dimensions, **PLAN["frozen_hyperparameters"][name])
    raise ValueError(f"unknown assessment arm: {name}")


def _cohort_metrics(experiences: Sequence[Experience], dimensions: int, arm: str) -> list[dict]:
    learner = _learner(arm, dimensions)
    cohort_size = PLAN["cohort_size"]
    records = []
    for cohort_index in range(len(experiences) // cohort_size):
        start_updates = learner.updates
        start_ops = learner.active_synaptic_ops
        losses = []
        state_bytes = 0
        for item in experiences[cohort_index * cohort_size:(cohort_index + 1) * cohort_size]:
            stats = learner.observe(item)
            losses.append(stats.loss)
            state_bytes = stats.state_bytes
        records.append({
            "cohort_index": cohort_index,
            "mean_loss": sum(losses) / len(losses),
            "updates": learner.updates - start_updates,
            "active_synaptic_ops": learner.active_synaptic_ops - start_ops,
            "state_bytes": state_bytes,
        })
    return records


def assess(experiences: Sequence[Experience], dataset: str) -> dict:
    required_cohorts = max(PLAN["assessment_cohort_indices"]) + 1
    required = required_cohorts * PLAN["cohort_size"]
    if len(experiences) < required:
        raise ValueError(f"{dataset} requires at least {required} experiences for the sealed powered plan")
    if any(item.step != index for index, item in enumerate(experiences[:required])):
        raise ValueError("powered assessment requires contiguous source order")
    dimensions = len(experiences[0].features)
    by_arm = {arm: _cohort_metrics(experiences[:required], dimensions, arm) for arm in PLAN["arms"]}
    assessment_ids = PLAN["assessment_cohort_indices"]
    fixed = [by_arm["fixed_sgd_b1"][index]["mean_loss"] for index in assessment_ids]
    guarded = [by_arm["plasticity_guard"][index]["mean_loss"] for index in assessment_ids]
    paired = paired_test(guarded, fixed)
    resource_summary = {}
    for metric in PLAN["resource_gate"]:
        fixed_values = [by_arm["fixed_sgd_b1"][index][metric] for index in assessment_ids]
        guarded_values = [by_arm["plasticity_guard"][index][metric] for index in assessment_ids]
        resource_summary[metric] = {
            "fixed": estimate(fixed_values).as_dict(),
            "guarded": estimate(guarded_values).as_dict(),
            "non_inferior": sum(guarded_values) / len(guarded_values) <= sum(fixed_values) / len(fixed_values),
        }
    fixed_estimate = estimate(fixed).as_dict()
    guarded_estimate = estimate(guarded).as_dict()
    lower_loss = guarded_estimate["mean"] < fixed_estimate["mean"]
    resource_gate = all(item["non_inferior"] for item in resource_summary.values())
    planned_power = paired_normal_power(len(assessment_ids), PLAN["target_standardized_effect"], PLAN["alpha"])
    power_target_met = planned_power >= PLAN["target_power"]
    candidate = lower_loss and paired["p_value"] <= PLAN["alpha"] and resource_gate and power_target_met
    return {
        "schema_version": "oaklab.experience-learning.plasticity-guard-assessment.v2",
        "state_slice": STATE_SLICE,
        "dataset": dataset,
        "plan": PLAN,
        "plan_digest": PLAN_DIGEST,
        "split_contract": {
            "fit_cohorts": PLAN["fit_cohort_indices"],
            "tune_cohorts": PLAN["tune_cohort_indices"],
            "assessment_cohorts": assessment_ids,
            "hyperparameters_locked_before_assessment": True,
        },
        "primary_endpoint": PLAN["primary_endpoint"],
        "assessment_cohort_count": len(assessment_ids),
        "fixed_sgd_b1": {"estimate": fixed_estimate},
        "plasticity_guard": {"estimate": guarded_estimate},
        "paired_test": paired,
        "resource_summary": resource_summary,
        "power": {
            "planned_n": len(assessment_ids),
            "target_standardized_effect": PLAN["target_standardized_effect"],
            "target_paired_sd": PLAN["target_paired_sd"],
            "target_power": PLAN["target_power"],
            "normal_approximation_power": planned_power,
            "target_met": power_target_met,
        },
        "strict_gate": {
            "lower_loss": lower_loss,
            "paired_p_le_alpha": paired["p_value"] <= PLAN["alpha"],
            "resource_non_inferiority": resource_gate,
            "power_target_met": power_target_met,
            "status": "candidate" if candidate else "no_candidate",
        },
    }


def run_custody_assessment(root: Path, dataset: str) -> dict:
    custody_status = validate_manifest(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    record = next((item for item in manifest["datasets"] if item["name"] == dataset), None)
    if record is None:
        raise ValueError(f"dataset is not in custody manifest: {dataset}")
    experiences, _ = load_custodied_jsonl(str(root / record["derived_file"]), record["kind"], record["derived_sha256"])
    result = assess(experiences, dataset)
    result["custody"] = {
        "manifest_sha256": custody_status["manifest_sha256"],
        "derived_sha256": record["derived_sha256"],
        "rows": len(experiences),
    }
    result["result_digest"] = _digest({key: value for key, value in result.items() if key != "result_digest"})
    return result

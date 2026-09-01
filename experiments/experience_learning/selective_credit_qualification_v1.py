"""Bounded qualification for the predictive-utility credit theory.

State slice: ``oaklab-experience-learning-selective-credit-v1``.

This is synthetic development evidence only.  It freezes the mechanism and
hyperparameters, compares against batch-one SGD on fresh deterministic stream
seeds, and keeps the existing noise-floor/oracle controls.  It does not open a
real-data or hardware claim.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Sequence

from .benchmark import _canonical_for_digest
from .controls import evaluate_control
from .learners import SGDLearner
from .metrics import MetricAccumulator
from .selective_credit_v1 import STATE_SLICE, PredictiveUtilityCreditLearner
from .statistics import estimate, paired_test
from .streams import STREAMS


SCHEMA_VERSION = "oaklab.experience-learning.selective-credit-qualification.v1"
PLAN = {
    "state_slice": STATE_SLICE,
    "schema_version": SCHEMA_VERSION,
    "stream_names": [
        "sparse_noisy", "nonstationary", "drifting", "noisy_mnist_like",
        "event_camera_like", "long_horizon",
    ],
    "seed_offsets": [0, 1, 2, 3, 4],
    "steps": 256,
    "split_rule": "fit=first-third;tune=second-third;assessment=final-third",
    "reference": "sgd_b1",
    "candidate": "predictive_utility_credit",
    "hyperparameters": {
        "sgd_b1": {"learning_rate": 0.03},
        "predictive_utility_credit": {
            "learning_rate": 0.03,
            "utility_decay": 0.9,
            "variance_decay": 0.9,
            "confidence_k": 0.5,
            "min_gate": 0.05,
            "warmup": 4,
        },
    },
    "controls": ["noise_floor", "oracle_feature_sgd_b1"],
    "primary_endpoint": "assessment_mean_prediction_loss",
    "secondary_endpoints": [
        "adaptation_lag", "updates", "active_synaptic_ops", "state_bytes",
        "gated_coordinates", "paired_p_value",
    ],
    "gate": {
        "alpha": 0.05,
        "minimum_stream_families": 2,
        "requires_strict_loss_reduction": True,
        "requires_noninferior_updates": True,
        "requires_noninferior_active_synaptic_ops": True,
        "requires_noninferior_state_bytes": True,
    },
    "anti_leakage": [
        "one Experience enters each observe call",
        "no replay buffer and no gradient accumulation",
        "only one previous parameter delta is retained",
        "no future labels or offline reshuffling",
        "no adaptive tuning on assessment",
    ],
    "claim_ceiling": "LocalDevelopmentOakLabSelectiveCreditSyntheticQualification",
}


def plan_digest() -> str:
    encoded = json.dumps(PLAN, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


PLAN_DIGEST = plan_digest()


def _stream_experiences(stream_name: str, seed_offset: int, steps: int):
    stream = STREAMS[stream_name](seed=7 + seed_offset, steps=steps)
    return stream, list(stream)


def _run_algorithm(stream_name: str, seed_offset: int, algorithm: str, steps: int) -> dict:
    stream, experiences = _stream_experiences(stream_name, seed_offset, steps)
    if not experiences:
        raise ValueError("stream produced no experiences")
    dimensions = len(experiences[0].features)
    fit_end = max(1, len(experiences) // 3)
    tune_end = max(fit_end + 1, 2 * len(experiences) // 3)
    if algorithm == "sgd_b1":
        learner = SGDLearner(dimensions, learning_rate=PLAN["hyperparameters"]["sgd_b1"]["learning_rate"], batch_size=1)
    elif algorithm == "predictive_utility_credit":
        learner = PredictiveUtilityCreditLearner(dimensions, **PLAN["hyperparameters"]["predictive_utility_credit"])
    else:
        raise ValueError(f"unknown qualification algorithm: {algorithm}")
    accumulators = {split: MetricAccumulator.create() for split in ("fit", "tune", "assessment")}
    for index, item in enumerate(experiences):
        split = "fit" if index < fit_end else "tune" if index < tune_end else "assessment"
        accumulators[split].add(learner.observe(item), item.target)
    learner.flush()
    change_points = [
        index for index in range(1, len(experiences))
        if experiences[index].task_id != experiences[index - 1].task_id
    ]
    summaries = {split: accumulator.summary(change_points) for split, accumulator in accumulators.items()}
    assessment = summaries["assessment"]
    record = {
        "status": "executed",
        "seed_offset": seed_offset,
        "summaries": summaries,
        "assessment_metrics": {
            "mean_loss": assessment["mean_prediction_loss"],
            "adaptation_lag": assessment["adaptation_lag"],
            "updates": assessment["updates"],
            "active_synaptic_ops": assessment["active_synaptic_ops"],
            "state_bytes": assessment["state_bytes"],
        },
        "accounting": {
            "presented_experiences": len(experiences),
            "learner_observe_calls": len(experiences),
            "max_experience_items_per_observe": 1,
            "batch_size": learner.batch_size,
            "strict_batch_one": learner.batch_size == 1 and not learner.allows_replay,
            "explicit_replay": False,
            "hidden_gradient_accumulation": False,
        },
        "final_state_digest": learner.digest(),
    }
    if isinstance(learner, PredictiveUtilityCreditLearner):
        record["gated_coordinates"] = learner.gated_coordinates
    return record


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _stream_gate(records: dict, paired: dict) -> dict:
    reference = records[PLAN["reference"]]["estimate"]
    candidate = records[PLAN["candidate"]]["estimate"]
    reference_resource = records[PLAN["reference"]]["resource_estimate"]
    candidate_resource = records[PLAN["candidate"]]["resource_estimate"]
    return {
        "lower_loss": candidate["mean"] < reference["mean"],
        "paired_significant": paired["p_value"] <= PLAN["gate"]["alpha"],
        "noninferior_updates": candidate_resource["updates"]["mean"] <= reference_resource["updates"]["mean"],
        "noninferior_active_synaptic_ops": candidate_resource["active_synaptic_ops"]["mean"] <= reference_resource["active_synaptic_ops"]["mean"],
        "noninferior_state_bytes": candidate_resource["state_bytes"]["mean"] <= reference_resource["state_bytes"]["mean"],
    }


def run_qualification(stream_names: Sequence[str] | None = None, steps: int | None = None) -> dict:
    names = list(stream_names or PLAN["stream_names"])
    run_steps = int(steps or PLAN["steps"])
    if run_steps < 12:
        raise ValueError("qualification requires at least 12 steps")
    streams = {}
    qualifying_streams = []
    for stream_name in names:
        per_algorithm = {PLAN["reference"]: [], PLAN["candidate"]: []}
        for seed_offset in PLAN["seed_offsets"]:
            for algorithm in per_algorithm:
                per_algorithm[algorithm].append(_run_algorithm(stream_name, seed_offset, algorithm, run_steps))
        reference_losses = [item["assessment_metrics"]["mean_loss"] for item in per_algorithm[PLAN["reference"]]]
        candidate_losses = [item["assessment_metrics"]["mean_loss"] for item in per_algorithm[PLAN["candidate"]]]
        records = {}
        for algorithm, values in per_algorithm.items():
            records[algorithm] = {
                "per_seed": values,
                "estimate": estimate([item["assessment_metrics"]["mean_loss"] for item in values]).as_dict(),
                "resource_estimate": {
                    metric: estimate([item["assessment_metrics"][metric] for item in values]).as_dict()
                    for metric in ("updates", "active_synaptic_ops", "state_bytes")
                },
            }
        paired = paired_test(candidate_losses, reference_losses)
        gate = _stream_gate(records, paired)
        if all(gate.values()):
            qualifying_streams.append(stream_name)
        controls = {
            control: [evaluate_control(stream_name, run_steps, seed_offset, control, PLAN["hyperparameters"])
                      for seed_offset in PLAN["seed_offsets"]]
            for control in PLAN["controls"]
        }
        streams[stream_name] = {
            "dimensions": len(_stream_experiences(stream_name, 0, run_steps)[1][0].features),
            "algorithms": records,
            "paired_test_candidate_minus_reference": paired,
            "gate": gate,
            "controls": controls,
        }
    status = "candidate" if len(qualifying_streams) >= PLAN["gate"]["minimum_stream_families"] else "no_candidate"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "plan": PLAN,
        "plan_digest": PLAN_DIGEST,
        "execution": {
            "stream_names": names,
            "steps": run_steps,
            "seed_offsets": PLAN["seed_offsets"],
            "synthetic_only": True,
            "hardware_energy": "not_run",
            "astral": "isolated_not_run",
        },
        "streams": streams,
        "qualifying_streams": qualifying_streams,
        "status": status,
        "claim_ceiling": PLAN["claim_ceiling"],
    }
    canonical = _canonical_for_digest(payload)
    payload["result_digest"] = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return payload


def write_result(result: dict, path: Path) -> None:
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

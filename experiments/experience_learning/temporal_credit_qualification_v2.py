"""Fresh qualification for scalar temporal-utility credit V2.

State slice: ``oaklab-experience-learning-selective-credit-v2``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Sequence

from .benchmark import _canonical_for_digest
from .controls import evaluate_control
from .learners import SGDLearner
from .metrics import MetricAccumulator
from .statistics import estimate, paired_test
from .streams import STREAMS
from .temporal_credit_v2 import STATE_SLICE, TemporalUtilityGateLearner


SCHEMA_VERSION = "oaklab.experience-learning.selective-credit-qualification.v2"
PLAN = {
    "state_slice": STATE_SLICE,
    "schema_version": SCHEMA_VERSION,
    "stream_names": [
        "sparse_noisy", "nonstationary", "drifting", "noisy_mnist_like",
        "event_camera_like", "long_horizon",
    ],
    "seed_offsets": [10, 11, 12, 13, 14],
    "steps": 256,
    "split_rule": "fit=first-third;tune=second-third;assessment=final-third",
    "reference": "sgd_b1",
    "candidate": "temporal_utility_gate",
    "hyperparameters": {
        "sgd_b1": {"learning_rate": 0.03},
        "temporal_utility_gate": {
            "learning_rate": 0.03,
            "utility_decay": 0.8,
            "variance_decay": 0.9,
            "confidence_k": 0.75,
            "min_gate": 0.1,
            "warmup": 8,
        },
    },
    "controls": ["noise_floor", "oracle_feature_sgd_b1"],
    "primary_endpoint": "assessment_mean_prediction_loss",
    "secondary_endpoints": [
        "adaptation_lag", "updates", "active_synaptic_ops", "state_bytes",
        "gated_updates", "paired_p_value",
    ],
    "gate": {
        "alpha": 0.05,
        "minimum_stream_families": 2,
        "requires_strict_loss_reduction": True,
        "requires_noninferior_updates": True,
        "requires_noninferior_active_synaptic_ops": True,
        "requires_noninferior_state_bytes": True,
    },
    "estimand": "expected one-step sequential loss change under the fixed online stream; not a causal counterfactual",
    "anti_leakage": [
        "one Experience enters each observe call",
        "no replay buffer and no gradient accumulation",
        "only scalar previous loss and scalar utility moments are retained",
        "no future labels or offline reshuffling",
        "assessment configuration is locked after fit and tune",
    ],
    "prediction_lock": "learner hyperparameters and split boundaries are sealed before assessment",
    "claim_ceiling": "LocalDevelopmentOakLabSelectiveCreditTemporalUtilityQualification",
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
    elif algorithm == "temporal_utility_gate":
        learner = TemporalUtilityGateLearner(dimensions, **PLAN["hyperparameters"]["temporal_utility_gate"])
    else:
        raise ValueError(f"unknown qualification algorithm: {algorithm}")
    accumulators = {split: MetricAccumulator.create() for split in ("fit", "tune", "assessment")}
    snapshots = {}
    for index, item in enumerate(experiences):
        split = "fit" if index < fit_end else "tune" if index < tune_end else "assessment"
        accumulators[split].add(learner.observe(item), item.target)
        if index + 1 == fit_end:
            snapshots["fit"] = learner.digest()
        elif index + 1 == tune_end:
            snapshots["tune"] = learner.digest()
    learner.flush()
    snapshots["assessment"] = learner.digest()
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
        "prediction_lock_snapshots": snapshots,
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
    if isinstance(learner, TemporalUtilityGateLearner):
        record["gated_updates"] = learner.gated_updates
    return record


def run_qualification(stream_names: Sequence[str] | None = None, steps: int | None = None) -> dict:
    names = list(stream_names or PLAN["stream_names"])
    run_steps = int(steps or PLAN["steps"])
    if run_steps < 24:
        raise ValueError("qualification requires at least 24 steps")
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
        reference = records[PLAN["reference"]]
        candidate = records[PLAN["candidate"]]
        gate = {
            "lower_loss": candidate["estimate"]["mean"] < reference["estimate"]["mean"],
            "paired_significant": paired["p_value"] <= PLAN["gate"]["alpha"],
            "noninferior_updates": candidate["resource_estimate"]["updates"]["mean"] <= reference["resource_estimate"]["updates"]["mean"],
            "noninferior_active_synaptic_ops": candidate["resource_estimate"]["active_synaptic_ops"]["mean"] <= reference["resource_estimate"]["active_synaptic_ops"]["mean"],
            "noninferior_state_bytes": candidate["resource_estimate"]["state_bytes"]["mean"] <= reference["resource_estimate"]["state_bytes"]["mean"],
        }
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
            "real_stream_execution": "sealed_pending_review",
            "astral": "isolated_not_run",
        },
        "streams": streams,
        "qualifying_streams": qualifying_streams,
        "status": status,
        "claim_ceiling": PLAN["claim_ceiling"],
    }
    payload["result_digest"] = hashlib.sha256(json.dumps(_canonical_for_digest(payload), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return payload


def write_result(result: dict, path: Path) -> None:
    path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")

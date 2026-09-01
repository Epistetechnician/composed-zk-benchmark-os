"""Run every applicable baseline on custodied real panels.

State slice: ``oaklab-experience-learning-benchmark-v2``.

The runner preserves source order, never reshuffles or accumulates hidden
minibatches, and reports fit, tune, and assessment separately. Assessment
statistics are paired by fixed 128-row source-order cohorts. TIDBD is marked
not-applicable when a panel has no declared temporal-difference semantics;
silently treating a supervised label as a TD reward would invalidate the
comparison.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Sequence

from .acquire_real_data_v1 import validate_manifest
from .benchmark import ALGORITHM_IDS, make_learner
from .controls import RunningMeanLearner, _project
from .custody import load_custodied_jsonl
from .metrics import MetricAccumulator
from .statistics import estimate, paired_test, pareto_frontier
from .types import Experience


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"
SCHEMA_VERSION = "oaklab.experience-learning.real-result.v1"
COHORT_SIZE = 128
FIT_COHORTS = 4
TUNE_COHORTS = 4
ASSESSMENT_COHORTS = 32
REQUIRED_ROWS = (FIT_COHORTS + TUNE_COHORTS + ASSESSMENT_COHORTS) * COHORT_SIZE
CONTROL_NAMES = ("noise_floor", "fit_only_topk_feature_sgd_b1", "oracle_feature_sgd_b1")

# Raw real panels intentionally retain published units. These rates are a
# separately sealed real-panel configuration; the synthetic V2 rates would
# overflow on household-power voltage and sub-metering scales.
REAL_HYPERPARAMETERS = {
    "sgd_b1": {"learning_rate": 0.00001}, "sgd_b32": {"learning_rate": 0.00001},
    "sgd_b128": {"learning_rate": 0.00001}, "adam_b1": {"learning_rate": 0.0001},
    "adam_b32": {"learning_rate": 0.0001}, "adam_b128": {"learning_rate": 0.0001},
    "idbd": {"meta_step": 0.001, "initial_step": 0.00001},
    "networkidbd": {"hidden_size": 8, "meta_step": 0.0002, "initial_step": 0.0005},
    "tidbd": {"gamma": 0.9, "meta_step": 0.001, "initial_step": 0.00001, "trace_decay": 0.8},
    "replay_sgd": {"capacity": 64, "replay_ratio": 1, "learning_rate": 0.00001},
    "ewc_sgd": {"learning_rate": 0.000001, "ewc_lambda": 2.0},
    "plasticity_guard": {"learning_rate": 0.00001, "guard_floor": 0.2,
                         "recovery": 0.02, "surprise_threshold": 1.0},
    "event_driven": {"learning_rate": 0.00001, "threshold": 0.5},
}


def _digest(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _change_points(experiences: Sequence[Experience]) -> list[int]:
    return [i for i in range(1, len(experiences)) if experiences[i].task_id != experiences[i - 1].task_id]


def _split_ranges(length: int) -> dict[str, tuple[int, int]]:
    fit_end = FIT_COHORTS * COHORT_SIZE
    tune_end = (FIT_COHORTS + TUNE_COHORTS) * COHORT_SIZE
    if length < tune_end + ASSESSMENT_COHORTS * COHORT_SIZE:
        raise ValueError(f"real panel requires at least {REQUIRED_ROWS} rows")
    return {"fit": (0, fit_end), "tune": (fit_end, tune_end), "assessment": (tune_end, length)}


def _run_learner(experiences: Sequence[Experience], algorithm: str, hyperparameters: dict) -> dict:
    if algorithm == "tidbd":
        if not any(item.next_features is not None for item in experiences):
            return {"status": "not_applicable", "reason": "panel has no next_features and no TD target"}
        if not any(item.reward != 0.0 for item in experiences):
            return {"status": "not_applicable", "reason": "panel has next_features but no declared nonzero TD reward"}
    dimensions = len(experiences[0].features)
    learner = make_learner(algorithm, dimensions, hyperparameters.get(algorithm))
    ranges = _split_ranges(len(experiences))
    accumulators = {split: MetricAccumulator.create() for split in ranges}
    change_points = _change_points(experiences)
    previous_task = experiences[0].task_id
    for index, item in enumerate(experiences):
        if algorithm == "ewc_sgd" and item.task_id != previous_task:
            learner.mark_task_boundary()  # type: ignore[attr-defined]
        previous_task = item.task_id
        split = next(name for name, (start, end) in ranges.items() if start <= index < end)
        try:
            stats = learner.observe(item)
            if not math.isfinite(float(stats.loss)) or not math.isfinite(float(stats.prediction)):
                raise FloatingPointError("non-finite learner output")
        except (OverflowError, FloatingPointError, ValueError) as error:
            return {"status": "diverged", "step": index, "reason": str(error)}
        accumulators[split].add(stats, item.target)
    learner.flush()
    assessment = accumulators["assessment"]
    summaries = {split: accumulator.summary(change_points) for split, accumulator in accumulators.items()}
    # Assessment paired tests use losses only; resource metrics are reported at
    # split level and never disguised as per-cohort deltas.
    return {
        "status": "executed",
        "summaries": summaries,
        "assessment_cohorts": [{"cohort_index": FIT_COHORTS + TUNE_COHORTS + i,
                                 "mean_loss": sum(assessment.losses[i * COHORT_SIZE:(i + 1) * COHORT_SIZE]) / COHORT_SIZE}
                                for i in range(len(assessment.losses) // COHORT_SIZE)],
        "accounting": {
            "presented_experiences": len(experiences),
            "learner_observe_calls": len(experiences),
            "max_experience_items_per_observe": 1,
            "batch_size": getattr(learner, "batch_size", 1),
            "strict_batch_one": getattr(learner, "batch_size", 1) == 1 and not getattr(learner, "allows_replay", False),
            "explicit_replay": bool(getattr(learner, "allows_replay", False)),
            "hidden_gradient_accumulation": False,
            "event_driven": bool(getattr(learner, "event_driven", False)),
        },
        "final_state_digest": learner.digest(),
    }


def _fit_only_topk_indices(experiences: Sequence[Experience], k: int = 16) -> tuple[int, ...]:
    fit = experiences[:FIT_COHORTS * COHORT_SIZE]
    dimensions = len(fit[0].features)
    means_x = [sum(item.features[i] for item in fit) / len(fit) for i in range(dimensions)]
    mean_y = sum(item.target for item in fit) / len(fit)
    scores = []
    for i in range(dimensions):
        score = sum((item.features[i] - means_x[i]) * (item.target - mean_y) for item in fit)
        scores.append((abs(score), i))
    return tuple(i for _, i in sorted(scores, key=lambda value: (-value[0], value[1]))[:min(k, dimensions)])


def _run_control(experiences: Sequence[Experience], control: str, hyperparameters: dict) -> dict:
    ranges = _split_ranges(len(experiences))
    if control == "oracle_feature_sgd_b1":
        return {"status": "not_available", "reason": "real source manifest declares no causal oracle feature indices"}
    if control == "noise_floor":
        learner = RunningMeanLearner()
        projected = experiences
        selection = None
    elif control == "fit_only_topk_feature_sgd_b1":
        selection = _fit_only_topk_indices(experiences)
        projected = tuple(_project(item, selection) for item in experiences)
        learner = make_learner("sgd_b1", len(selection), hyperparameters["sgd_b1"])
    else:
        raise ValueError(f"unknown control: {control}")
    accumulators = {split: MetricAccumulator.create() for split in ranges}
    for index, item in enumerate(projected):
        split = next(name for name, (start, end) in ranges.items() if start <= index < end)
        accumulators[split].add(learner.observe(item), item.target)
    learner.flush()
    return {"status": "executed", "selection": list(selection) if selection is not None else None,
            "summaries": {split: accumulator.summary() for split, accumulator in accumulators.items()}}


def run_dataset(experiences: Sequence[Experience], dataset: str,
                hyperparameters: dict[str, dict] | None = None) -> dict:
    """Run all baseline IDs and controls over one ordered real panel."""
    if not experiences:
        raise ValueError("real panel must not be empty")
    _split_ranges(len(experiences))
    params = hyperparameters or REAL_HYPERPARAMETERS
    results = {algorithm: _run_learner(experiences, algorithm, params) for algorithm in ALGORITHM_IDS}
    controls = {control: _run_control(experiences, control, params) for control in CONTROL_NAMES}
    baseline = results["sgd_b1"]
    assessment_count = (len(experiences) - (FIT_COHORTS + TUNE_COHORTS) * COHORT_SIZE) // COHORT_SIZE
    publish_records = {}
    for algorithm, result in results.items():
        if result["status"] != "executed":
            continue
        candidate_losses = [item["mean_loss"] for item in result["assessment_cohorts"]]
        reference_losses = [item["mean_loss"] for item in baseline["assessment_cohorts"]]
        paired = paired_test(candidate_losses, reference_losses) if algorithm != "sgd_b1" else None
        summary = result["summaries"]["assessment"]
        publish_records[algorithm] = {
            "mean_loss": summary["mean_prediction_loss"],
            "adaptation_lag": summary["adaptation_lag"],
            "updates": summary["updates"],
            "active_synaptic_ops": summary["active_synaptic_ops"],
            "state_bytes": summary["state_bytes"],
            "replay_storage_bytes": summary["replay_storage_bytes"],
            "paired_p_value": None if paired is None else paired["p_value"],
        }
        result["paired_vs_sgd_b1"] = paired
    split_ranges = _split_ranges(len(experiences))
    payload = {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "dataset": dataset,
        "protocol": "ordered real panel; fit/tune/assessment locked before assessment; 128-row paired cohorts",
        "split_ranges": {name: list(value) for name, value in split_ranges.items()},
        "cohort_size": COHORT_SIZE,
        "assessment_cohort_count": assessment_count,
        "algorithm_names": list(ALGORITHM_IDS),
        "control_names": list(CONTROL_NAMES),
        "frozen_hyperparameters": {"version": "oaklab.experience-learning.real-config.v1",
                                    "digest": _digest(REAL_HYPERPARAMETERS if hyperparameters is None else hyperparameters)},
        "algorithms": results,
        "controls": controls,
        "pareto_frontier": pareto_frontier(publish_records),
        "publish_records": publish_records,
        "real_data_status": "custodied_ordered_panel",
        "energy_status": "hardware_receipt_required",
    }
    payload["result_digest"] = _digest(payload)
    return payload


def run_custody(root: Path, datasets: Iterable[str] | None = None) -> dict:
    custody_status = validate_manifest(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    wanted = set(datasets or (record["name"] for record in manifest["datasets"]))
    outputs = {}
    for record in manifest["datasets"]:
        if record["name"] not in wanted:
            continue
        experiences, _ = load_custodied_jsonl(str(root / record["derived_file"]), record["kind"], record["derived_sha256"])
        result = run_dataset(experiences, record["name"])
        result["custody"] = {"manifest_sha256": custody_status["manifest_sha256"],
                             "derived_sha256": record["derived_sha256"], "rows": len(experiences),
                             "feature_dim": len(experiences[0].features)}
        result["result_digest"] = _digest({key: value for key, value in result.items() if key != "result_digest"})
        outputs[record["name"]] = result
    if set(outputs) != wanted:
        raise ValueError(f"requested datasets missing from custody: {sorted(wanted - set(outputs))}")
    aggregate = {"schema_version": "oaklab.experience-learning.real-matrix.v1",
                 "state_slice": STATE_SLICE, "protocol": "all-baseline real-panel matrix",
                 "custody": {"manifest_sha256": custody_status["manifest_sha256"], "datasets": sorted(outputs)},
                 "datasets": outputs}
    aggregate["result_digest"] = _digest(aggregate)
    return aggregate

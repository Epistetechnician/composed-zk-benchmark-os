"""Fresh-custody real-panel sensitivity campaign.

State slice: ``oaklab-experience-learning-real-sensitivity-v1``.

The protocol is intentionally separate from the fixed-configuration real
matrix. A mechanical review receipt is required before any assessment pass.
The fresh cohort root is read-only; this module writes only to a new external
artifact root.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from .acquire_real_data_v1 import validate_manifest
from .benchmark import make_learner
from .controls import RunningMeanLearner, _project
from .custody import load_custodied_jsonl
from .frozen import DEFAULT_FROZEN
from .learners import EWCLearner
from .metrics import MetricAccumulator
from .real_benchmark_v1 import REAL_HYPERPARAMETERS
from .statistics import estimate, paired_test


STATE_SLICE = "oaklab-experience-learning-real-sensitivity-v1"
SCHEMA_VERSION = "oaklab.experience-learning.real-sensitivity.v1"
PROTOCOL_SCHEMA_VERSION = "oaklab.experience-learning.real-sensitivity-protocol.v1"
REVIEW_SCHEMA_VERSION = "oaklab.experience-learning.real-sensitivity-review.v1"
SURVIVING_ALGORITHMS = (
    "sgd_b1", "sgd_b32", "sgd_b128", "adam_b1", "adam_b32", "adam_b128",
    "idbd", "networkidbd", "tidbd", "replay_sgd", "ewc_sgd", "event_driven",
)
DATASET_NAMES = ("noisy_mnist", "sensor", "long_horizon", "event_camera")
FIT_ROWS = 256
TUNE_ROWS = 256
COHORT_SIZE = 128
REQUIRED_ROWS = 2048


def _grid(*values: dict) -> tuple[dict, ...]:
    return tuple(dict(value) for value in values)


# Wider real-scale grids are declared before the fresh cohort is opened for
# assessment. Three candidates retain bounded runtime while expanding both
# sides of the prior fixed configuration.
REAL_SENSITIVITY_GRID = {
    "sgd_b1": _grid({"learning_rate": 1e-6}, {"learning_rate": 1e-5}, {"learning_rate": 1e-4}),
    "sgd_b32": _grid({"learning_rate": 1e-6}, {"learning_rate": 1e-5}, {"learning_rate": 1e-4}),
    "sgd_b128": _grid({"learning_rate": 1e-6}, {"learning_rate": 1e-5}, {"learning_rate": 1e-4}),
    "adam_b1": _grid({"learning_rate": 1e-5}, {"learning_rate": 1e-4}, {"learning_rate": 1e-3}),
    "adam_b32": _grid({"learning_rate": 1e-5}, {"learning_rate": 1e-4}, {"learning_rate": 1e-3}),
    "adam_b128": _grid({"learning_rate": 1e-5}, {"learning_rate": 1e-4}, {"learning_rate": 1e-3}),
    "idbd": _grid(
        {"meta_step": 3e-4, "initial_step": 1e-6},
        {"meta_step": 1e-3, "initial_step": 1e-5},
        {"meta_step": 3e-3, "initial_step": 1e-4},
    ),
    "networkidbd": _grid(
        {"hidden_size": 8, "meta_step": 1e-4, "initial_step": 1e-4},
        {"hidden_size": 8, "meta_step": 2e-4, "initial_step": 5e-4},
        {"hidden_size": 8, "meta_step": 4e-4, "initial_step": 1e-3},
    ),
    "tidbd": _grid(
        {"gamma": 0.9, "meta_step": 3e-4, "initial_step": 1e-6, "trace_decay": 0.8},
        {"gamma": 0.9, "meta_step": 1e-3, "initial_step": 1e-5, "trace_decay": 0.8},
        {"gamma": 0.9, "meta_step": 3e-3, "initial_step": 1e-4, "trace_decay": 0.8},
    ),
    "replay_sgd": _grid(
        {"capacity": 16, "replay_ratio": 1, "learning_rate": 1e-5},
        {"capacity": 64, "replay_ratio": 1, "learning_rate": 1e-5},
        {"capacity": 256, "replay_ratio": 1, "learning_rate": 1e-5},
    ),
    "ewc_sgd": _grid(
        {"learning_rate": 1e-6, "ewc_lambda": 0.5},
        {"learning_rate": 1e-6, "ewc_lambda": 2.0},
        {"learning_rate": 1e-6, "ewc_lambda": 8.0},
    ),
    "event_driven": _grid(
        {"learning_rate": 1e-5, "threshold": 0.25},
        {"learning_rate": 1e-5, "threshold": 0.5},
        {"learning_rate": 1e-5, "threshold": 0.75},
    ),
}


def _canonical(value):
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()
                if key != "result_digest"}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    return value


def _digest(value: Mapping) -> str:
    return hashlib.sha256(json.dumps(_canonical(dict(value)), sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _grid_digest(algorithms: Sequence[str]) -> str:
    return _digest({"algorithms": list(algorithms),
                    "grid": {name: [dict(item) for item in REAL_SENSITIVITY_GRID[name]]
                             for name in algorithms}})


def _split_ranges(length: int) -> dict[str, tuple[int, int]]:
    if length < REQUIRED_ROWS:
        raise ValueError(f"fresh real panel requires at least {REQUIRED_ROWS} rows")
    return {"fit": (0, FIT_ROWS), "tune": (FIT_ROWS, FIT_ROWS + TUNE_ROWS),
            "assessment": (FIT_ROWS + TUNE_ROWS, length)}


def _metric_record(summary: dict) -> dict:
    return {"mean_loss": float(summary["mean_prediction_loss"]),
            "adaptation_lag": float(summary["adaptation_lag"]),
            "updates": float(summary["updates"]),
            "active_synaptic_ops": float(summary["active_synaptic_ops"]),
            "state_bytes": float(summary["state_bytes"]),
            "event_count": float(summary["event_count"]),
            "replay_storage_bytes": float(summary["replay_storage_bytes"])}


def _aggregate(records: Sequence[dict], keys: Sequence[str]) -> dict:
    return {key: {"seed_values": [float(record[key]) for record in records],
                  "estimate": estimate([float(record[key]) for record in records]).as_dict()}
            for key in keys}


def _run(experiences: Sequence, algorithm: str, params: dict, phase: str) -> dict:
    if algorithm == "tidbd":
        if not any(item.next_features is not None for item in experiences):
            return {"status": "not_applicable", "reason": "panel has no next_features"}
        if not any(item.reward != 0.0 for item in experiences):
            return {"status": "not_applicable", "reason": "panel has no nonzero TD reward"}
    ranges = _split_ranges(len(experiences))
    learner = make_learner(algorithm, len(experiences[0].features), params)
    end = ranges["tune"][1] if phase == "tune" else len(experiences)
    accumulator = MetricAccumulator.create()
    cohorts: list[dict] = []
    previous_task = experiences[0].task_id
    try:
        for index, item in enumerate(experiences[:end]):
            if algorithm == "ewc_sgd" and item.task_id != previous_task:
                learner.mark_task_boundary()  # type: ignore[attr-defined]
            previous_task = item.task_id
            stats = learner.observe(item)
            if not math.isfinite(float(stats.loss)) or not math.isfinite(float(stats.prediction)):
                raise FloatingPointError("non-finite learner output")
            if (phase == "tune" and index >= ranges["tune"][0]) or (phase == "assessment" and index >= ranges["assessment"][0]):
                accumulator.add(stats, item.target)
        learner.flush()
    except (OverflowError, FloatingPointError, ValueError) as error:
        return {"status": "diverged", "reason": str(error)}
    if phase == "assessment":
        losses = accumulator.losses
        for start in range(0, len(losses) - COHORT_SIZE + 1, COHORT_SIZE):
            cohorts.append({"cohort_index": start // COHORT_SIZE,
                            "mean_loss": sum(losses[start:start + COHORT_SIZE]) / COHORT_SIZE})
    return {"status": "executed", "metrics": _metric_record(accumulator.summary()),
            "assessment_cohorts": cohorts,
            "accounting": {"presented_experiences": end,
                            "learner_observe_calls": end,
                            "max_experience_items_per_observe": 1,
                            "batch_size": getattr(learner, "batch_size", 1),
                            "strict_batch_one": getattr(learner, "batch_size", 1) == 1 and not getattr(learner, "allows_replay", False),
                            "explicit_replay": bool(getattr(learner, "allows_replay", False)),
                            "hidden_gradient_accumulation": False,
                            "event_driven": bool(getattr(learner, "event_driven", False))},
            "final_state_digest": learner.digest()}


def _topk_indices(experiences: Sequence, k: int = 16) -> tuple[int, ...]:
    fit = experiences[:FIT_ROWS]
    dimensions = len(fit[0].features)
    means_x = [sum(item.features[i] for item in fit) / len(fit) for i in range(dimensions)]
    mean_y = sum(item.target for item in fit) / len(fit)
    scores = []
    for i in range(dimensions):
        score = sum((item.features[i] - means_x[i]) * (item.target - mean_y) for item in fit)
        scores.append((abs(score), i))
    return tuple(i for _, i in sorted(scores, key=lambda value: (-value[0], value[1]))[:min(k, dimensions)])


def _controls(experiences: Sequence) -> dict:
    ranges = _split_ranges(len(experiences))
    output = {}
    for name in ("noise_floor", "fit_only_topk_feature_sgd_b1"):
        indices = None if name == "noise_floor" else _topk_indices(experiences)
        projected = experiences if indices is None else tuple(_project(item, indices) for item in experiences)
        learner = RunningMeanLearner() if indices is None else make_learner("sgd_b1", len(indices), REAL_HYPERPARAMETERS["sgd_b1"])
        acc = {key: MetricAccumulator.create() for key in ranges}
        for index, item in enumerate(projected):
            split = "fit" if index < FIT_ROWS else "tune" if index < FIT_ROWS + TUNE_ROWS else "assessment"
            acc[split].add(learner.observe(item), item.target)
        learner.flush()
        output[name] = {"status": "executed", "selection": None if indices is None else list(indices),
                        **_aggregate([_metric_record(acc["assessment"].summary())],
                                    ("mean_loss", "updates", "active_synaptic_ops", "state_bytes"))}
    output["oracle_feature_sgd_b1"] = {"status": "not_available",
        "reason": "fresh real-data manifest declares no causal oracle feature indices"}
    return output


def protocol_manifest(source_root: Path, algorithms: Sequence[str] = SURVIVING_ALGORITHMS) -> dict:
    custody = validate_manifest(source_root)
    requested = tuple(algorithms)
    if set(requested) - set(SURVIVING_ALGORITHMS):
        raise ValueError("protocol includes a closed or unknown algorithm")
    return {"schema_version": PROTOCOL_SCHEMA_VERSION, "state_slice": STATE_SLICE,
            "source_root": str(source_root), "source_manifest_sha256": custody["manifest_sha256"],
            "datasets": list(DATASET_NAMES), "algorithms": list(requested),
            "fit_rows": FIT_ROWS, "tune_rows": TUNE_ROWS, "cohort_size": COHORT_SIZE,
            "minimum_rows": REQUIRED_ROWS, "grid": {name: [dict(item) for item in REAL_SENSITIVITY_GRID[name]]
                                                       for name in requested},
            "grid_digest": _grid_digest(requested),
            "multiplicity": "Benjamini-Hochberg within each dataset over selected-arm paired p-values",
            "selection": "minimum tune mean prediction loss; assessment excluded",
            "assessment_authorization": "independent review receipt required before assessment",
            "closed_arms": ["plasticity_guard", "selective_credit_v1", "selective_credit_v2"]}


def write_protocol(source_root: Path, output_root: Path) -> dict:
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty output root: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = protocol_manifest(source_root)
    manifest["protocol_digest"] = _digest(manifest)
    (output_root / "protocol_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def review_protocol(protocol_path: Path) -> dict:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("schema_version") != PROTOCOL_SCHEMA_VERSION or protocol.get("state_slice") != STATE_SLICE:
        raise ValueError("protocol schema/state mismatch")
    if protocol.get("protocol_digest") != _digest({key: value for key, value in protocol.items() if key != "protocol_digest"}):
        raise ValueError("protocol digest mismatch")
    source_root = Path(protocol["source_root"])
    custody = validate_manifest(source_root)
    if custody["manifest_sha256"] != protocol["source_manifest_sha256"]:
        raise ValueError("source custody changed after protocol freeze")
    if tuple(protocol["algorithms"]) != SURVIVING_ALGORITHMS:
        raise ValueError("review requires the complete surviving algorithm set")
    receipt = {"schema_version": REVIEW_SCHEMA_VERSION, "state_slice": STATE_SLICE,
               "protocol_digest": protocol["protocol_digest"],
               "source_manifest_sha256": protocol["source_manifest_sha256"],
               "decision": "accepted_for_execution", "assessment_authorization": True,
               "review_scope": "custody, grid, split, closed arms, multiplicity, and review ordering only"}
    receipt["review_digest"] = _digest(receipt)
    return receipt


def _load_datasets(source_root: Path) -> tuple[dict, dict]:
    custody = validate_manifest(source_root)
    manifest = json.loads((source_root / "manifest.json").read_text(encoding="utf-8"))
    datasets = {}
    records = {record["name"]: record for record in manifest["datasets"]}
    for name in DATASET_NAMES:
        record = records.get(name)
        if record is None:
            raise ValueError(f"fresh custody missing dataset: {name}")
        rows, _ = load_custodied_jsonl(str(source_root / record["derived_file"]), record["kind"], record["derived_sha256"])
        _split_ranges(len(rows))
        datasets[name] = rows
    return datasets, custody


def _bh_adjust(pairs: Sequence[tuple[str, float]]) -> dict[str, float]:
    ordered = sorted(pairs, key=lambda pair: (pair[1], pair[0]))
    count = len(ordered)
    adjusted = {}
    running = 1.0
    for rank, (name, value) in reversed(list(enumerate(ordered, start=1))):
        running = min(running, float(value) * count / rank)
        adjusted[name] = min(1.0, running)
    return adjusted


def _strict_gate(dataset_records: Mapping[str, dict]) -> dict:
    wins: dict[str, list[str]] = {name: [] for name in SURVIVING_ALGORITHMS if name != "sgd_b1"}
    for dataset, result in dataset_records.items():
        baseline = result.get("algorithms", {}).get("sgd_b1", {}).get("assessment")
        if not baseline:
            continue
        ref = {key: baseline[key]["estimate"]["mean"] for key in baseline}
        for algorithm, arm in result.get("algorithms", {}).items():
            if algorithm == "sgd_b1" or arm.get("status") != "executed":
                continue
            candidate = {key: arm["assessment"][key]["estimate"]["mean"] for key in arm["assessment"]}
            paired = arm.get("paired_vs_frozen_sgd_b1", {})
            lower_quality = candidate["mean_loss"] < ref["mean_loss"] and candidate["adaptation_lag"] <= ref["adaptation_lag"]
            lower_resources = all(candidate[key] <= ref[key] for key in ("updates", "active_synaptic_ops", "state_bytes", "replay_storage_bytes"))
            strict_resource = any(candidate[key] < ref[key] for key in ("updates", "active_synaptic_ops", "state_bytes", "replay_storage_bytes"))
            if lower_quality and lower_resources and strict_resource and paired.get("adjusted_p_value", 1.0) <= 0.05:
                wins.setdefault(algorithm, []).append(dataset)
    qualifying = {algorithm: sorted(set(datasets)) for algorithm, datasets in wins.items() if len(set(datasets)) >= 2}
    return {"status": "candidate" if qualifying else "no_candidate", "reference": "frozen_real_sgd_b1",
            "alpha": 0.05, "multiplicity": "Benjamini-Hochberg within dataset",
            "qualifying_algorithms": qualifying,
            "requirement": "lower loss and adaptation, non-inferior resources, strict resource reduction, adjusted p <= alpha in >=2 datasets"}


def run_campaign(protocol_path: Path, review_path: Path, output_path: Path) -> dict:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if review.get("protocol_digest") != protocol.get("protocol_digest") or review.get("assessment_authorization") is not True:
        raise ValueError("assessment requires a matching independent review authorization")
    if review.get("review_digest") != _digest({key: value for key, value in review.items() if key != "review_digest"}):
        raise ValueError("review digest mismatch")
    datasets, custody = _load_datasets(Path(protocol["source_root"]))
    algorithms = tuple(protocol["algorithms"])
    dataset_records = {}
    for dataset, experiences in datasets.items():
        records = {}
        reference = _run(experiences, "sgd_b1", dict(REAL_HYPERPARAMETERS["sgd_b1"]), "assessment")
        for algorithm in algorithms:
            if algorithm == "tidbd" and (not any(item.next_features is not None for item in experiences) or not any(item.reward != 0.0 for item in experiences)):
                records[algorithm] = {"status": "not_applicable", "reason": "panel has no declared nonzero TD reward"}
                continue
            candidates = []
            for params in REAL_SENSITIVITY_GRID[algorithm]:
                tune = _run(experiences, algorithm, params, "tune")
                candidate = {"hyperparameters": dict(params), "status": tune["status"]}
                if tune["status"] == "executed":
                    candidate["tune_metrics"] = _aggregate([tune["metrics"]], ("mean_loss", "adaptation_lag", "updates", "active_synaptic_ops", "state_bytes"))
                    candidate["tune_mean_loss"] = candidate["tune_metrics"]["mean_loss"]["estimate"]["mean"]
                else:
                    candidate["reason"] = tune.get("reason", "candidate failed")
                candidates.append(candidate)
            valid = [(index, candidate) for index, candidate in enumerate(candidates) if candidate["status"] == "executed"]
            if not valid:
                records[algorithm] = {"status": "no_valid_candidate", "candidates": candidates,
                                      "selection": {"assessment_selection_used": False}}
                continue
            selected_index, selected = min(valid, key=lambda pair: (pair[1]["tune_mean_loss"], pair[0]))
            assessment = _run(experiences, algorithm, selected["hyperparameters"], "assessment")
            if assessment["status"] != "executed":
                records[algorithm] = {"status": "assessment_failed", "candidates": candidates,
                                      "selection": {"selected_index": selected_index,
                                                    "selected_hyperparameters": selected["hyperparameters"],
                                                    "assessment_selection_used": False},
                                      "reason": assessment.get("reason", "assessment failed")}
                continue
            record = {"status": "executed", "candidates": candidates,
                      "selection": {"selected_index": selected_index,
                                    "selected_hyperparameters": selected["hyperparameters"],
                                    "assessment_selection_used": False,
                                    "criterion": "minimum tune mean prediction loss; ties resolved by grid order"},
                      "assessment": _aggregate([assessment["metrics"]], tuple(assessment["metrics"])),
                      "assessment_cohorts": assessment["assessment_cohorts"],
                      "accounting": assessment["accounting"],
                      "paired_vs_frozen_sgd_b1": None}
            records[algorithm] = record
        if reference["status"] != "executed":
            raise ValueError(f"frozen real SGD reference failed on {dataset}")
        if records["sgd_b1"].get("status") == "executed":
            records["sgd_b1"]["selected_assessment"] = {
                "assessment": records["sgd_b1"]["assessment"],
                "assessment_cohorts": records["sgd_b1"]["assessment_cohorts"],
                "accounting": records["sgd_b1"]["accounting"],
            }
        records["sgd_b1"]["frozen_reference"] = True
        records["sgd_b1"]["assessment"] = _aggregate([reference["metrics"]], tuple(reference["metrics"]))
        records["sgd_b1"]["assessment_cohorts"] = reference["assessment_cohorts"]
        records["sgd_b1"]["accounting"] = reference["accounting"]
        baseline_cohorts = [item["mean_loss"] for item in reference["assessment_cohorts"]]
        p_values = []
        for algorithm, arm in records.items():
            if algorithm == "sgd_b1" or arm.get("status") != "executed":
                continue
            candidate_cohorts = [item["mean_loss"] for item in arm["assessment_cohorts"]]
            paired = paired_test(candidate_cohorts, baseline_cohorts)
            arm["paired_vs_frozen_sgd_b1"] = paired
            p_values.append((algorithm, paired["p_value"]))
        adjusted = _bh_adjust(p_values)
        for algorithm, value in adjusted.items():
            records[algorithm]["paired_vs_frozen_sgd_b1"]["adjusted_p_value"] = value
        dataset_records[dataset] = {"rows": len(experiences), "algorithms": records,
                                    "controls": _controls(experiences),
                                    "split_ranges": {"fit": [0, FIT_ROWS], "tune": [FIT_ROWS, FIT_ROWS + TUNE_ROWS],
                                                     "assessment": [FIT_ROWS + TUNE_ROWS, len(experiences)]},
                                    "assessment_cohort_count": len(reference["assessment_cohorts"])}
    gate = _strict_gate(dataset_records)
    payload = {"schema_version": SCHEMA_VERSION, "state_slice": STATE_SLICE,
               "protocol_digest": protocol["protocol_digest"], "review_digest": review["review_digest"],
               "source_manifest_sha256": custody["manifest_sha256"], "datasets": dataset_records,
               "dataset_names": list(DATASET_NAMES), "algorithm_names": list(algorithms),
               "grid_digest": protocol["grid_digest"], "multiplicity": protocol["multiplicity"],
               "protocol": "fresh real custody; review before assessment; fit/tune/assessment; BH-adjusted paired tests",
               "real_sensitivity_gate": gate,
               "publication_status": {"status": "no_candidate", "reasons": [
                   "privileged measured energy receipt is not present",
                   "strict publication requires measured energy and >=2 real stream families"],
                   "synthetic_guard_retune": False},
               "energy_status": "privileged_hardware_receipt_required"}
    payload["result_digest"] = _digest(payload)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return payload

"""Fresh-seed replication and preregistered sensitivity campaign.

State slice: ``oaklab-experience-learning-replication-sensitivity-v1``.

This campaign is deliberately separate from the closed plasticity-guard and
selective-credit families.  Each candidate is qualified on fit/tune data only;
one candidate is then locked per algorithm/stream and rerun from a fresh
learner state for assessment.  Assessment values never select a candidate.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Mapping, Sequence

from .benchmark import ALGORITHM_IDS, make_learner
from .controls import evaluate_control
from .frozen import DEFAULT_FROZEN
from .metrics import MetricAccumulator
from .statistics import estimate, paired_test, pareto_frontier, publish_gate
from .streams import STREAMS


STATE_SLICE = "oaklab-experience-learning-replication-sensitivity-v1"
SCHEMA_VERSION = "oaklab.experience-learning.replication-sensitivity.v1"
DEFAULT_SEED_OFFSETS = tuple(range(20, 30))
DEFAULT_STEPS = 256
STREAM_NAMES = (
    "sparse_noisy", "nonstationary", "drifting", "delayed_reward",
    "noisy_mnist_like", "event_camera_like", "long_horizon",
)

# The guard is terminally closed and cannot enter this grid.  This explicit
# tuple also prevents a future addition to benchmark.ALGORITHM_IDS from being
# silently treated as a surviving arm.
SURVIVING_ALGORITHMS = (
    "sgd_b1", "sgd_b32", "sgd_b128", "adam_b1", "adam_b32", "adam_b128",
    "idbd", "networkidbd", "tidbd", "replay_sgd", "ewc_sgd", "event_driven",
)


def _grid(*values: dict) -> tuple[dict, ...]:
    return tuple(dict(value) for value in values)


# These values are declared before campaign execution.  They are intentionally
# small, symmetric local perturbations around the frozen V2 configuration.
HYPERPARAMETER_GRID = {
    "sgd_b1": _grid({"learning_rate": 0.01}, {"learning_rate": 0.03}, {"learning_rate": 0.1}),
    "sgd_b32": _grid({"learning_rate": 0.01}, {"learning_rate": 0.03}, {"learning_rate": 0.1}),
    "sgd_b128": _grid({"learning_rate": 0.01}, {"learning_rate": 0.03}, {"learning_rate": 0.1}),
    "adam_b1": _grid({"learning_rate": 0.003}, {"learning_rate": 0.01}, {"learning_rate": 0.03}),
    "adam_b32": _grid({"learning_rate": 0.003}, {"learning_rate": 0.01}, {"learning_rate": 0.03}),
    "adam_b128": _grid({"learning_rate": 0.003}, {"learning_rate": 0.01}, {"learning_rate": 0.03}),
    "idbd": _grid(
        {"meta_step": 0.003, "initial_step": 0.03},
        {"meta_step": 0.01, "initial_step": 0.03},
        {"meta_step": 0.03, "initial_step": 0.03},
    ),
    "networkidbd": _grid(
        {"hidden_size": 8, "meta_step": 0.001, "initial_step": 0.01},
        {"hidden_size": 8, "meta_step": 0.002, "initial_step": 0.01},
        {"hidden_size": 8, "meta_step": 0.004, "initial_step": 0.01},
    ),
    "tidbd": _grid(
        {"gamma": 0.9, "meta_step": 0.003, "initial_step": 0.03, "trace_decay": 0.8},
        {"gamma": 0.9, "meta_step": 0.01, "initial_step": 0.03, "trace_decay": 0.8},
        {"gamma": 0.9, "meta_step": 0.03, "initial_step": 0.03, "trace_decay": 0.8},
    ),
    "replay_sgd": _grid(
        {"capacity": 32, "replay_ratio": 1, "learning_rate": 0.03},
        {"capacity": 64, "replay_ratio": 1, "learning_rate": 0.03},
        {"capacity": 128, "replay_ratio": 1, "learning_rate": 0.03},
    ),
    "ewc_sgd": _grid(
        {"learning_rate": 0.03, "ewc_lambda": 0.5},
        {"learning_rate": 0.03, "ewc_lambda": 2.0},
        {"learning_rate": 0.03, "ewc_lambda": 8.0},
    ),
    "event_driven": _grid(
        {"learning_rate": 0.03, "threshold": 0.25},
        {"learning_rate": 0.03, "threshold": 0.5},
        {"learning_rate": 0.03, "threshold": 0.75},
    ),
}


def _canonical(value):
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()
                if key not in {"result_digest", "wall_clock_latency_ns"}}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    if isinstance(value, tuple):
        return [_canonical(item) for item in value]
    return value


def _digest(payload: Mapping) -> str:
    encoded = json.dumps(_canonical(dict(payload)), sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def campaign_manifest() -> dict:
    """Return the complete pre-execution protocol manifest."""
    return {
        "state_slice": STATE_SLICE,
        "schema_version": SCHEMA_VERSION,
        "streams": list(STREAM_NAMES),
        "algorithms": list(SURVIVING_ALGORITHMS),
        "seed_offsets": list(DEFAULT_SEED_OFFSETS),
        "steps": DEFAULT_STEPS,
        "minimum_valid_seed_fraction": 1.0,
        "selection": "minimum mean tune prediction loss; assessment is not inspected",
        "assessment_lock": True,
        "grid": {name: [dict(item) for item in values] for name, values in HYPERPARAMETER_GRID.items()},
        "closed_arms": ["plasticity_guard", "selective_credit_v1", "selective_credit_v2"],
    }


def campaign_manifest_digest() -> str:
    return _digest(campaign_manifest())


def hyperparameter_grid_digest(algorithms: Sequence[str] = SURVIVING_ALGORITHMS) -> str:
    requested = tuple(algorithms)
    return _digest({"algorithms": list(requested),
                    "grid": {name: [dict(item) for item in HYPERPARAMETER_GRID[name]]
                             for name in requested}})


def _experiences(stream_name: str, seed_offset: int, steps: int):
    if stream_name not in STREAMS:
        raise ValueError(f"unknown stream: {stream_name}")
    kwargs = {"steps": steps} if stream_name != "delayed_reward" else {
        "episodes": max(1, steps // 8), "horizon": 8,
    }
    return list(STREAMS[stream_name](seed=7 + int(seed_offset), **kwargs))


def _metric_record(summary: dict) -> dict:
    return {
        "mean_loss": float(summary["mean_prediction_loss"]),
        "adaptation_lag": float(summary["adaptation_lag"]),
        "updates": float(summary["updates"]),
        "active_synaptic_ops": float(summary["active_synaptic_ops"]),
        "state_bytes": float(summary["state_bytes"]),
        "event_count": float(summary["event_count"]),
        "replay_storage_bytes": float(summary["replay_storage_bytes"]),
    }


def _aggregate(records: Sequence[dict], keys: Sequence[str] | None = None) -> dict:
    if not records:
        raise ValueError("cannot aggregate an empty record sequence")
    names = tuple(keys or ("mean_loss", "adaptation_lag", "updates", "active_synaptic_ops",
                           "state_bytes", "event_count", "replay_storage_bytes"))
    return {key: {"seed_values": [float(record[key]) for record in records],
                  "estimate": estimate([float(record[key]) for record in records]).as_dict()}
            for key in names}


def _split_ranges(length: int) -> dict[str, tuple[int, int]]:
    fit_end = max(1, length // 3)
    tune_end = max(fit_end + 1, 2 * length // 3)
    return {"fit": (0, fit_end), "tune": (fit_end, tune_end),
            "assessment": (tune_end, length)}


def _run_phase(experiences: Sequence, algorithm: str, params: dict, phase: str) -> dict:
    """Run one learner either through tune or through the locked assessment."""
    if algorithm == "tidbd" and not any(item.next_features is not None for item in experiences):
        return {"status": "not_applicable", "reason": "TIDBD requires next_features"}
    ranges = _split_ranges(len(experiences))
    dimensions = len(experiences[0].features)
    learner = make_learner(algorithm, dimensions, params)
    accumulator = MetricAccumulator.create()
    end = ranges["tune"][1] if phase == "tune" else len(experiences)
    previous_task = experiences[0].task_id
    try:
        for index, item in enumerate(experiences[:end]):
            if algorithm == "ewc_sgd" and item.task_id != previous_task:
                learner.mark_task_boundary()  # type: ignore[attr-defined]
            previous_task = item.task_id
            stats = learner.observe(item)
            if not math.isfinite(float(stats.loss)) or not math.isfinite(float(stats.prediction)):
                raise FloatingPointError("non-finite learner output")
            if phase == "tune":
                if index >= ranges["fit"][1]:
                    accumulator.add(stats, item.target)
            elif index >= ranges["assessment"][0]:
                accumulator.add(stats, item.target)
        learner.flush()
    except (OverflowError, FloatingPointError, ValueError) as error:
        return {"status": "diverged", "reason": str(error)}
    summary = accumulator.summary()
    return {"status": "executed", "metrics": _metric_record(summary),
            "accounting": {
                "presented_experiences": end,
                "learner_observe_calls": end,
                "max_experience_items_per_observe": 1,
                "batch_size": getattr(learner, "batch_size", 1),
                "strict_batch_one": getattr(learner, "batch_size", 1) == 1 and not getattr(learner, "allows_replay", False),
                "explicit_replay": bool(getattr(learner, "allows_replay", False)),
                "hidden_gradient_accumulation": False,
                "event_driven": bool(getattr(learner, "event_driven", False)),
            },
            "final_state_digest": learner.digest()}


def _candidate_tune(stream_name: str, algorithm: str, params: dict,
                    seeds: Sequence[int], steps: int) -> dict:
    records = []
    statuses = []
    for seed in seeds:
        result = _run_phase(_experiences(stream_name, seed, steps), algorithm, params, "tune")
        statuses.append(result["status"])
        if result["status"] == "executed":
            records.append(result["metrics"])
    output = {"hyperparameters": dict(params), "seed_statuses": statuses,
              "valid_seed_count": len(records), "required_seed_count": len(seeds)}
    if len(records) == len(seeds):
        output["status"] = "qualified"
        output["tune_metrics"] = _aggregate(records, ("mean_loss", "adaptation_lag", "updates",
                                                       "active_synaptic_ops", "state_bytes"))
        output["tune_mean_loss"] = output["tune_metrics"]["mean_loss"]["estimate"]["mean"]
    else:
        output["status"] = "rejected"
        output["tune_mean_loss"] = None
    return output


def _select(candidates: Sequence[dict]) -> tuple[int | None, str]:
    valid = [(index, candidate) for index, candidate in enumerate(candidates)
             if candidate["status"] == "qualified"]
    if not valid:
        return None, "no grid candidate achieved the required valid-seed fraction"
    # The index is the preregistered tie breaker after tune loss.
    index, _ = min(valid, key=lambda pair: (pair[1]["tune_mean_loss"], pair[0]))
    return index, "minimum mean tune prediction loss; ties resolved by grid order"


def _run_controls(stream_name: str, seeds: Sequence[int], steps: int) -> dict:
    controls = {"noise_floor": [], "oracle_feature_sgd_b1": []}
    reference_params = {"sgd_b1": dict(DEFAULT_FROZEN.algorithms["sgd_b1"])}
    for seed in seeds:
        for control in controls:
            result = evaluate_control(stream_name, steps, seed, control, reference_params)
            controls[control].append(result["assessment_metrics"])
    return {name: {"status": "executed", **_aggregate(records,
            ("mean_loss", "updates", "active_synaptic_ops", "state_bytes"))}
            for name, records in controls.items()}


def run_campaign(stream_names: Sequence[str] = STREAM_NAMES, steps: int = DEFAULT_STEPS,
                 seed_offsets: Sequence[int] = DEFAULT_SEED_OFFSETS,
                 algorithms: Sequence[str] = SURVIVING_ALGORITHMS,
                 include_controls: bool = True) -> dict:
    """Execute the fresh replication, tune lock, and assessment campaign."""
    seeds = tuple(int(seed) for seed in seed_offsets)
    names = tuple(stream_names)
    requested = tuple(algorithms)
    if steps < 3 or ("delayed_reward" in names and steps % 8):
        raise ValueError("steps must be >=3 and divisible by delayed-reward horizon 8")
    if len(seeds) < 2 or len(set(seeds)) != len(seeds):
        raise ValueError("seed_offsets must contain at least two distinct values")
    if set(requested) - set(SURVIVING_ALGORITHMS):
        raise ValueError("campaign accepts only surviving algorithms; plasticity guard is closed")
    if set(names) - set(STREAM_NAMES):
        raise ValueError("unknown stream in campaign")
    grid_digest = hyperparameter_grid_digest(requested)
    streams = {}
    publish_records = {}
    for stream_name in names:
        stream_algorithms = {}
        reference_by_seed = []
        reference_params = dict(DEFAULT_FROZEN.algorithms["sgd_b1"])
        for seed in seeds:
            result = _run_phase(_experiences(stream_name, seed, steps), "sgd_b1", reference_params, "assessment")
            if result["status"] == "executed":
                reference_by_seed.append(result["metrics"])
        for algorithm in requested:
            if algorithm == "tidbd" and stream_name != "delayed_reward":
                stream_algorithms[algorithm] = {"status": "not_applicable",
                    "reason": "TIDBD is a temporal-difference predictor and requires delayed_reward experiences"}
                continue
            candidates = [_candidate_tune(stream_name, algorithm, params, seeds, steps)
                          for params in HYPERPARAMETER_GRID[algorithm]]
            selected_index, reason = _select(candidates)
            if selected_index is None:
                stream_algorithms[algorithm] = {"status": "no_valid_candidate", "candidates": candidates,
                    "selection": {"assessment_selection_used": False, "reason": reason}}
                continue
            selected = candidates[selected_index]
            assessment_records = []
            assessment_statuses = []
            for seed in seeds:
                result = _run_phase(_experiences(stream_name, seed, steps), algorithm,
                                    selected["hyperparameters"], "assessment")
                assessment_statuses.append(result["status"])
                if result["status"] == "executed":
                    assessment_records.append(result["metrics"])
            if len(assessment_records) != len(seeds):
                stream_algorithms[algorithm] = {"status": "assessment_failed", "candidates": candidates,
                    "selection": {"selected_index": selected_index,
                                  "selected_hyperparameters": selected["hyperparameters"],
                                  "assessment_selection_used": False, "reason": reason},
                    "assessment_statuses": assessment_statuses}
                continue
            assessment = _aggregate(assessment_records)
            record = {"status": "executed", "candidates": candidates,
                      "selection": {"selected_index": selected_index,
                                    "selected_hyperparameters": selected["hyperparameters"],
                                    "assessment_selection_used": False,
                                    "criterion": reason,
                                    "grid_digest": grid_digest},
                      "assessment": assessment}
            if len(reference_by_seed) == len(assessment_records):
                record["paired_vs_frozen_sgd_b1"] = paired_test(
                    [item["mean_loss"] for item in assessment_records],
                    [item["mean_loss"] for item in reference_by_seed])
            stream_algorithms[algorithm] = record
        publish_records[stream_name] = {}
        for algorithm, record in stream_algorithms.items():
            if record.get("status") != "executed":
                continue
            assessment = record["assessment"]
            paired = record.get("paired_vs_frozen_sgd_b1")
            publish_records[stream_name][algorithm] = {
                "mean_loss": assessment["mean_loss"]["estimate"]["mean"],
                "updates": assessment["updates"]["estimate"]["mean"],
                "active_synaptic_ops": assessment["active_synaptic_ops"]["estimate"]["mean"],
                "state_bytes": assessment["state_bytes"]["estimate"]["mean"],
                "paired_p_value": None if paired is None else paired["p_value"],
            }
        stream_out = {"steps": steps, "seed_offsets": list(seeds),
                      "algorithms": stream_algorithms,
                      "pareto_frontier": pareto_frontier(publish_records[stream_name])}
        if include_controls:
            stream_out["controls"] = _run_controls(stream_name, seeds, steps)
        streams[stream_name] = stream_out
    synthetic_gate = publish_gate(publish_records, reference="sgd_b1")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "protocol": "fresh independent seeds; tune-only grid selection; locked assessment rerun; one experience per observe",
        "tuning_policy": "candidate selection uses tune loss only; assessment_selection_used is false",
        "confidence_interval": "normal approximation, 95 percent; paired tests are normal-approximation paired t",
        "steps": steps, "seed_offsets": list(seeds), "stream_names": list(names),
        "algorithm_names": list(requested),
        "hyperparameter_grid": {name: [dict(item) for item in HYPERPARAMETER_GRID[name] for _ in [0]]
                                for name in requested},
        "hyperparameter_grid_digest": grid_digest,
        "closed_arms": ["plasticity_guard", "selective_credit_v1", "selective_credit_v2"],
        "streams": streams,
        "synthetic_sensitivity_gate": synthetic_gate,
        "publication_status": {
            "status": "no_candidate",
            "reasons": [
                "this receipt is synthetic sensitivity evidence only",
                "real-panel sensitivity has not run in this slice",
                "privileged measured energy receipt is still required",
            ],
            "synthetic_gate_is_not_publication_authorization": True,
        },
        "real_data_status": "real_panel_sensitivity_not_run_in_this_slice",
        "energy_status": "privileged_hardware_receipt_required_and_campaign_bound",
    }
    payload["result_digest"] = _digest(payload)
    return payload


def write_result(result: Mapping, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    args = parser.parse_args()
    write_result(run_campaign(), args.output)

"""Frozen multi-seed experience-learning benchmark orchestration.

State slice: ``oaklab-experience-learning-benchmark-v2``.  This module only
aggregates the V1 executable learner records; it does not tune on assessment
data and it does not manufacture real-dataset or hardware-energy evidence.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence

from .benchmark import ALGORITHM_IDS, run_benchmark
from .controls import evaluate_control
from .frozen import DEFAULT_FROZEN, FrozenHyperparameters, STATE_SLICE
from .statistics import estimate, paired_test, pareto_frontier, publish_gate


SCHEMA_VERSION = "oaklab.experience-learning.result.v2"
DEFAULT_SEED_OFFSETS = (0, 1, 2, 3, 4)


def _canonical(value):
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()
                if key not in {"result_digest", "wall_clock_latency_ns"}}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def _digest(payload: dict) -> str:
    encoded = json.dumps(_canonical(payload), sort_keys=True,
                         separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _metric_record(result: dict) -> dict:
    summary = result["summaries"]["assessment"]
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
    metrics = {}
    keys = tuple(keys or ("mean_loss", "adaptation_lag", "updates", "active_synaptic_ops",
                          "state_bytes", "event_count", "replay_storage_bytes"))
    for key in keys:
        values = [float(record[key]) for record in records]
        metrics[key] = {"seed_values": values, "estimate": estimate(values).as_dict()}
    return metrics


def _control_aggregate(records: Sequence[dict]) -> dict:
    return _aggregate([record["assessment_metrics"] for record in records],
                      ("mean_loss", "updates", "active_synaptic_ops", "state_bytes"))


def run_multiseed(
    stream_names: Sequence[str] | None = None,
    steps: int = 256,
    seed_offsets: Sequence[int] = DEFAULT_SEED_OFFSETS,
    algorithms: Sequence[str] = ALGORITHM_IDS,
    frozen: FrozenHyperparameters = DEFAULT_FROZEN,
    include_controls: bool = True,
) -> dict:
    """Run sealed learners over independent seeds and return aggregate-only data."""
    if steps < 3:
        raise ValueError("steps must provide non-empty fit, tune, and assessment splits")
    seeds = tuple(int(seed) for seed in seed_offsets)
    if len(seeds) < 2 or len(set(seeds)) != len(seeds):
        raise ValueError("at least two distinct seed offsets are required")
    names = tuple(stream_names or ("sparse_noisy", "nonstationary", "drifting",
                                   "delayed_reward", "noisy_mnist_like",
                                   "event_camera_like", "long_horizon"))
    if "delayed_reward" in names and steps % 8:
        raise ValueError("steps must be divisible by delayed_reward horizon 8")
    requested = tuple(algorithms)
    unknown = sorted(set(requested) - set(ALGORITHM_IDS))
    if unknown:
        raise ValueError(f"unknown algorithms: {unknown}")
    if frozen.status != "sealed":
        raise ValueError("hyperparameter manifest must be sealed")
    missing = sorted(set(requested) - set(frozen.algorithms))
    if missing:
        raise ValueError(f"sealed hyperparameter manifest missing: {missing}")

    streams = {}
    publish_records = {}
    for stream_name in names:
        per_algorithm: dict[str, list[dict]] = {algorithm: [] for algorithm in requested}
        for seed in seeds:
            run = run_benchmark([stream_name], steps=steps, seed_offset=seed,
                                algorithms=requested,
                                hyperparameters=frozen.algorithms)
            for algorithm in requested:
                record = run["streams"][stream_name]["algorithms"][algorithm]
                if record["status"] == "executed":
                    per_algorithm[algorithm].append(_metric_record(record))
                elif record["status"] != "not_applicable":
                    raise ValueError(f"unexpected status for {stream_name}/{algorithm}")
        algorithms_out = {}
        for algorithm in requested:
            values = per_algorithm[algorithm]
            if not values:
                algorithms_out[algorithm] = {
                    "status": "not_applicable",
                    "reason": "underlying V1 learner is not applicable to this stream",
                }
                continue
            aggregate = _aggregate(values)
            aggregate["status"] = "executed"
            if "sgd_b1" in per_algorithm and len(per_algorithm["sgd_b1"]) == len(values):
                aggregate["paired_vs_sgd_b1"] = paired_test(
                    [item["mean_loss"] for item in values],
                    [item["mean_loss"] for item in per_algorithm["sgd_b1"]],
                )
            algorithms_out[algorithm] = aggregate
        publish_records[stream_name] = {
            algorithm: {
                "mean_loss": value["mean_loss"]["estimate"]["mean"],
                "updates": value["updates"]["estimate"]["mean"],
                "active_synaptic_ops": value["active_synaptic_ops"]["estimate"]["mean"],
                "state_bytes": value["state_bytes"]["estimate"]["mean"],
                "paired_p_value": value.get("paired_vs_sgd_b1", {}).get("p_value"),
            }
            for algorithm, value in algorithms_out.items()
            if value.get("status") == "executed"
        }
        stream_out = {
            "steps": steps,
            "n_experiences": steps,
            "algorithms": algorithms_out,
            "pareto_frontier": pareto_frontier(publish_records[stream_name]),
        }
        if include_controls:
            controls: dict[str, list[dict]] = {"noise_floor": [], "oracle_feature_sgd_b1": []}
            for seed in seeds:
                for control in controls:
                    controls[control].append(evaluate_control(
                        stream_name, steps, seed, control, frozen.algorithms))
            stream_out["controls"] = {
                control: {"status": "executed", **_control_aggregate(records)}
                for control, records in controls.items()
            }
        streams[stream_name] = stream_out

    payload = {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "protocol": "sealed fit/tune manifest; independent multi-seed assessment; aggregate-only statistics",
        "tuning_policy": "hyperparameters sealed before assessment seeds; no assessment tuning",
        "confidence_interval": "normal approximation, 95 percent; paired tests are normal-approximation paired t",
        "steps": steps,
        "seed_offsets": list(seeds),
        "stream_names": list(names),
        "algorithm_names": list(requested),
        "frozen_hyperparameters": frozen.canonical(),
        "frozen_hyperparameters_digest": frozen.digest,
        "streams": streams,
        "publish_gate": publish_gate(publish_records),
        "real_data_status": "custody_adapter_contract_only",
        "energy_status": "hardware_measurement_adapter_contract_only",
    }
    payload["result_digest"] = _digest(payload)
    return payload


def write_result(result: Mapping, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")

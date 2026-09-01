"""Independent validator for V2 aggregate-only benchmark results.

State slice: ``oaklab-experience-learning-benchmark-v2``.  This validator does
not execute learners and therefore cannot be mistaken for an independent
scientific replication of the underlying algorithms.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys

from .benchmark import ALGORITHM_IDS
from .frozen import CONFIG_VERSION, STATE_SLICE
from .benchmark_v2 import SCHEMA_VERSION


def _canonical(value):
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()
                if key not in {"result_digest", "wall_clock_latency_ns"}}
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def _digest(payload: dict) -> str:
    encoded = json.dumps(_canonical(payload), sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _check_estimate(findings: list[str], path: str, value: dict, expected_n: int) -> None:
    if not isinstance(value, dict):
        findings.append(f"{path}: estimate missing")
        return
    if value.get("n") != expected_n:
        findings.append(f"{path}: estimate n mismatch")
    for field in ("mean", "std"):
        if not _finite(value.get(field)) or value[field] < 0 and field == "std":
            findings.append(f"{path}: invalid {field}")
    low, high = value.get("ci95_low"), value.get("ci95_high")
    if expected_n > 1:
        if not (_finite(low) and _finite(high) and low <= high):
            findings.append(f"{path}: invalid confidence interval")
    elif low is not None or high is not None:
        findings.append(f"{path}: singleton confidence interval must be null")


def validate_result(result: dict) -> list[str]:
    findings: list[str] = []
    if not isinstance(result, dict):
        return ["result must be an object"]
    if result.get("schema_version") != SCHEMA_VERSION:
        findings.append("schema_version mismatch")
    if result.get("state_slice") != STATE_SLICE:
        findings.append("state_slice mismatch")
    try:
        if result.get("result_digest") != _digest(result):
            findings.append("result_digest mismatch")
    except (TypeError, ValueError):
        findings.append("result contains non-canonical or non-finite values")
    if result.get("tuning_policy") != "hyperparameters sealed before assessment seeds; no assessment tuning":
        findings.append("tuning policy mismatch")
    seeds = result.get("seed_offsets")
    if not isinstance(seeds, list) or len(seeds) < 2 or len(set(seeds)) != len(seeds):
        findings.append("seed offsets must contain at least two distinct values")
    expected_algorithms = result.get("algorithm_names")
    if not isinstance(expected_algorithms, list) or not set(expected_algorithms) <= set(ALGORITHM_IDS):
        findings.append("algorithm_names invalid")
    frozen = result.get("frozen_hyperparameters")
    if not isinstance(frozen, dict) or frozen.get("version") != CONFIG_VERSION or frozen.get("status") != "sealed":
        findings.append("frozen hyperparameter manifest is not sealed")
    else:
        algorithms = frozen.get("algorithms")
        if not isinstance(algorithms, dict) or not set(expected_algorithms or ()) <= set(algorithms):
            findings.append("frozen hyperparameter manifest differs from requested algorithms")
        encoded = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode()
        if result.get("frozen_hyperparameters_digest") != hashlib.sha256(encoded).hexdigest():
            findings.append("frozen hyperparameter digest mismatch")
    streams = result.get("streams")
    if not isinstance(streams, dict) or not streams:
        findings.append("streams missing")
        streams = {}
    n_seeds = len(seeds) if isinstance(seeds, list) else 0
    publish_records = {}
    for stream_name, stream in streams.items():
        if not isinstance(stream, dict):
            findings.append(f"{stream_name}: stream record missing")
            continue
        if stream.get("steps") != result.get("steps") or stream.get("n_experiences") != result.get("steps"):
            findings.append(f"{stream_name}: steps mismatch")
        algorithms = stream.get("algorithms", {})
        if set(algorithms) != set(expected_algorithms or ()):
            findings.append(f"{stream_name}: algorithm set mismatch")
        publish_records[stream_name] = {}
        for algorithm, record in algorithms.items():
            if record.get("status") == "not_applicable":
                if algorithm != "tidbd" or stream_name == "delayed_reward":
                    findings.append(f"{stream_name}/{algorithm}: invalid not_applicable")
                continue
            if record.get("status") != "executed":
                findings.append(f"{stream_name}/{algorithm}: status invalid")
                continue
            for metric in ("mean_loss", "adaptation_lag", "updates", "active_synaptic_ops",
                           "state_bytes", "event_count", "replay_storage_bytes"):
                metric_record = record.get(metric)
                if not isinstance(metric_record, dict) or not isinstance(metric_record.get("seed_values"), list):
                    findings.append(f"{stream_name}/{algorithm}/{metric}: seed values missing")
                    continue
                values = metric_record["seed_values"]
                if len(values) != n_seeds or not all(_finite(value) and value >= 0 for value in values):
                    findings.append(f"{stream_name}/{algorithm}/{metric}: invalid seed values")
                _check_estimate(findings, f"{stream_name}/{algorithm}/{metric}",
                                metric_record.get("estimate", {}), len(values))
            paired = record.get("paired_vs_sgd_b1")
            if algorithm != "sgd_b1" and paired is not None:
                if (paired.get("n") != n_seeds or not _finite(paired.get("p_value")) or
                        not _finite(paired.get("statistic")) or not isinstance(paired.get("degenerate"), bool)):
                    findings.append(f"{stream_name}/{algorithm}: invalid paired test")
            publish_records[stream_name][algorithm] = {
                "mean_loss": record["mean_loss"]["estimate"]["mean"],
                "updates": record["updates"]["estimate"]["mean"],
                "active_synaptic_ops": record["active_synaptic_ops"]["estimate"]["mean"],
                "state_bytes": record["state_bytes"]["estimate"]["mean"],
            }
        controls = stream.get("controls", {})
        for control in ("noise_floor", "oracle_feature_sgd_b1"):
            record = controls.get(control)
            if not isinstance(record, dict) or record.get("status") != "executed":
                findings.append(f"{stream_name}/{control}: control missing")
                continue
            for metric in ("mean_loss", "updates", "active_synaptic_ops", "state_bytes"):
                metric_record = record.get(metric, {})
                values = metric_record.get("seed_values", []) if isinstance(metric_record, dict) else []
                if len(values) != n_seeds or not all(_finite(value) and value >= 0 for value in values):
                    findings.append(f"{stream_name}/{control}/{metric}: invalid seed values")
                _check_estimate(findings, f"{stream_name}/{control}/{metric}",
                                metric_record.get("estimate", {}) if isinstance(metric_record, dict) else {}, len(values))
    gate = result.get("publish_gate")
    if (not isinstance(gate, dict) or gate.get("status") not in {"candidate", "no_candidate"} or
            gate.get("reference") != "sgd_b1" or gate.get("alpha") != 0.05):
        findings.append("publish gate missing")
    if result.get("real_data_status") != "custody_adapter_contract_only":
        findings.append("real-data status mismatch")
    if result.get("energy_status") != "hardware_measurement_adapter_contract_only":
        findings.append("energy status mismatch")
    return findings


def validate_file(path: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        return validate_result(json.load(handle))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m experiments.experience_learning.validate_v2 RESULT.json")
    errors = validate_file(sys.argv[1])
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("VALID")

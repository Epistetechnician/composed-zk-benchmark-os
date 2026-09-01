"""Independent aggregate-only validator for replication/sensitivity V1.

State slice: ``oaklab-experience-learning-replication-sensitivity-v1``.
The validator checks custody of the protocol, tune-only selection, seed
coverage, accounting, and finite aggregate statistics without executing a
learner or choosing a different hyperparameter.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys

from .replication_sensitivity_v1 import (
    HYPERPARAMETER_GRID, SCHEMA_VERSION, STATE_SLICE, STREAM_NAMES,
    SURVIVING_ALGORITHMS, _canonical, _digest, hyperparameter_grid_digest,
)


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _check_estimate(findings: list[str], path: str, record: dict, expected_n: int) -> None:
    if not isinstance(record, dict):
        findings.append(f"{path}: metric record missing")
        return
    values = record.get("seed_values")
    if not isinstance(values, list) or len(values) != expected_n or not all(_finite(v) and v >= 0 for v in values):
        findings.append(f"{path}: invalid seed values")
    estimate = record.get("estimate")
    if not isinstance(estimate, dict) or estimate.get("n") != expected_n:
        findings.append(f"{path}: estimate n mismatch")
        return
    if not _finite(estimate.get("mean")) or not _finite(estimate.get("std")) or estimate["std"] < 0:
        findings.append(f"{path}: invalid estimate")
    low, high = estimate.get("ci95_low"), estimate.get("ci95_high")
    if expected_n > 1 and not (_finite(low) and _finite(high) and low <= high):
        findings.append(f"{path}: invalid confidence interval")


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
    if result.get("tuning_policy") != "candidate selection uses tune loss only; assessment_selection_used is false":
        findings.append("tuning policy mismatch")
    seeds = result.get("seed_offsets")
    if not isinstance(seeds, list) or len(seeds) < 5 or len(set(seeds)) != len(seeds):
        findings.append("independent seed replication requires at least five distinct seeds")
    algorithms = result.get("algorithm_names")
    if not isinstance(algorithms, list) or not algorithms or set(algorithms) - set(SURVIVING_ALGORITHMS):
        findings.append("algorithm_names contain a closed or unknown arm")
    if "plasticity_guard" in (algorithms or []):
        findings.append("plasticity_guard must remain closed")
    grid = result.get("hyperparameter_grid")
    if not isinstance(grid, dict) or set(grid) != set(algorithms or ()):
        findings.append("hyperparameter grid does not match algorithm set")
    else:
        for algorithm in algorithms:
            expected = [dict(item) for item in HYPERPARAMETER_GRID[algorithm]]
            if grid.get(algorithm) != expected:
                findings.append(f"{algorithm}: declared grid differs from preregistered grid")
        expected_grid_digest = hyperparameter_grid_digest(algorithms)
        if result.get("hyperparameter_grid_digest") != expected_grid_digest:
            findings.append("hyperparameter_grid_digest mismatch")
    closed = result.get("closed_arms")
    if not isinstance(closed, list) or "plasticity_guard" not in closed:
        findings.append("closed arms are not recorded")
    streams = result.get("streams")
    if not isinstance(streams, dict) or not streams:
        findings.append("streams missing")
        streams = {}
    expected_n = len(seeds) if isinstance(seeds, list) else 0
    metric_names = ("mean_loss", "adaptation_lag", "updates", "active_synaptic_ops",
                    "state_bytes", "event_count", "replay_storage_bytes")
    for stream_name, stream in streams.items():
        if stream_name not in STREAM_NAMES:
            findings.append(f"{stream_name}: unknown stream")
            continue
        if not isinstance(stream, dict) or stream.get("seed_offsets") != seeds:
            findings.append(f"{stream_name}: seed offsets mismatch")
            continue
        records = stream.get("algorithms")
        if not isinstance(records, dict) or set(records) != set(algorithms or ()):
            findings.append(f"{stream_name}: algorithm set mismatch")
            continue
        for algorithm in algorithms:
            record = records[algorithm]
            if algorithm == "tidbd" and stream_name != "delayed_reward":
                if record.get("status") != "not_applicable":
                    findings.append(f"{stream_name}/{algorithm}: must be not_applicable")
                continue
            if record.get("status") not in {"executed", "no_valid_candidate", "assessment_failed"}:
                findings.append(f"{stream_name}/{algorithm}: invalid status")
                continue
            candidates = record.get("candidates")
            if not isinstance(candidates, list) or len(candidates) != len(HYPERPARAMETER_GRID[algorithm]):
                findings.append(f"{stream_name}/{algorithm}: candidate grid missing")
            for candidate in candidates or ():
                if candidate.get("required_seed_count") != expected_n:
                    findings.append(f"{stream_name}/{algorithm}: candidate seed count mismatch")
                if candidate.get("status") == "qualified":
                    tune = candidate.get("tune_metrics", {})
                    _check_estimate(findings, f"{stream_name}/{algorithm}/tune", tune.get("mean_loss"), expected_n)
                    if not _finite(candidate.get("tune_mean_loss")):
                        findings.append(f"{stream_name}/{algorithm}: invalid tune selection loss")
            selection = record.get("selection", {})
            if selection.get("assessment_selection_used") is not False:
                findings.append(f"{stream_name}/{algorithm}: assessment was used for selection")
            if record.get("status") == "executed":
                index = selection.get("selected_index")
                if not isinstance(index, int) or not 0 <= index < len(candidates):
                    findings.append(f"{stream_name}/{algorithm}: selected index invalid")
                assessment = record.get("assessment", {})
                for metric in metric_names:
                    _check_estimate(findings, f"{stream_name}/{algorithm}/{metric}",
                                    assessment.get(metric), expected_n)
                paired = record.get("paired_vs_frozen_sgd_b1")
                if paired is not None and (paired.get("n") != expected_n or
                        not _finite(paired.get("p_value"))):
                    findings.append(f"{stream_name}/{algorithm}: invalid paired test")
        controls = stream.get("controls")
        if not isinstance(controls, dict):
            findings.append(f"{stream_name}: controls missing")
        else:
            for name in ("noise_floor", "oracle_feature_sgd_b1"):
                control = controls.get(name)
                if not isinstance(control, dict) or control.get("status") != "executed":
                    findings.append(f"{stream_name}/{name}: control missing")
                    continue
                for metric in ("mean_loss", "updates", "active_synaptic_ops", "state_bytes"):
                    _check_estimate(findings, f"{stream_name}/{name}/{metric}",
                                    control.get(metric), expected_n)
    if result.get("real_data_status") != "real_panel_sensitivity_not_run_in_this_slice":
        findings.append("real-data status mismatch")
    if result.get("energy_status") != "privileged_hardware_receipt_required_and_campaign_bound":
        findings.append("energy status mismatch")
    publication = result.get("publication_status")
    if (not isinstance(publication, dict) or publication.get("status") != "no_candidate" or
            publication.get("synthetic_gate_is_not_publication_authorization") is not True):
        findings.append("publication status must remain no_candidate")
    return findings


def validate_file(path: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        return validate_result(json.load(handle))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m experiments.experience_learning.validate_replication_sensitivity_v1 RESULT.json")
    errors = validate_file(sys.argv[1])
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("VALID")

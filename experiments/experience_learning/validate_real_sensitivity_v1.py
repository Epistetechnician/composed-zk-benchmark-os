"""Independent validator for real sensitivity V1.

State slice: ``oaklab-experience-learning-real-sensitivity-v1``.  It validates
the frozen custody/review chain and aggregate-only result without selecting or
executing any learner.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from .real_sensitivity_v1 import (
    DATASET_NAMES, FIT_ROWS, PROTOCOL_SCHEMA_VERSION, REAL_SENSITIVITY_GRID,
    REQUIRED_ROWS, REVIEW_SCHEMA_VERSION, SCHEMA_VERSION, STATE_SLICE,
    SURVIVING_ALGORITHMS, TUNE_ROWS, _digest, _grid_digest,
)


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _metric(findings: list[str], path: str, record: dict, expected_n: int) -> None:
    if not isinstance(record, dict):
        findings.append(f"{path}: metric missing")
        return
    values = record.get("seed_values")
    if not isinstance(values, list) or len(values) != expected_n or not all(_finite(v) and v >= 0 for v in values):
        findings.append(f"{path}: invalid values")
    estimate = record.get("estimate")
    if not isinstance(estimate, dict) or estimate.get("n") != expected_n:
        findings.append(f"{path}: estimate n mismatch")
        return
    if not _finite(estimate.get("mean")) or not _finite(estimate.get("std")) or estimate["std"] < 0:
        findings.append(f"{path}: invalid estimate")
    if expected_n > 1 and not (_finite(estimate.get("ci95_low")) and _finite(estimate.get("ci95_high"))):
        findings.append(f"{path}: confidence interval missing")


def validate_protocol(protocol: dict, source_root: Path | None = None) -> list[str]:
    findings: list[str] = []
    if protocol.get("schema_version") != PROTOCOL_SCHEMA_VERSION or protocol.get("state_slice") != STATE_SLICE:
        findings.append("protocol schema/state mismatch")
    if protocol.get("protocol_digest") != _digest({key: value for key, value in protocol.items() if key != "protocol_digest"}):
        findings.append("protocol digest mismatch")
    if tuple(protocol.get("algorithms", ())) != SURVIVING_ALGORITHMS:
        findings.append("protocol algorithm set mismatch")
    if tuple(protocol.get("datasets", ())) != DATASET_NAMES:
        findings.append("protocol dataset set mismatch")
    if protocol.get("fit_rows") != FIT_ROWS or protocol.get("tune_rows") != TUNE_ROWS or protocol.get("minimum_rows") != REQUIRED_ROWS:
        findings.append("protocol split mismatch")
    if protocol.get("grid_digest") != _grid_digest(SURVIVING_ALGORITHMS):
        findings.append("protocol grid digest mismatch")
    for algorithm in SURVIVING_ALGORITHMS:
        if protocol.get("grid", {}).get(algorithm) != [dict(item) for item in REAL_SENSITIVITY_GRID[algorithm]]:
            findings.append(f"{algorithm}: protocol grid mismatch")
    if source_root is not None:
        from .acquire_real_data_v1 import validate_manifest
        custody = validate_manifest(source_root)
        if custody["manifest_sha256"] != protocol.get("source_manifest_sha256"):
            findings.append("source custody digest mismatch")
    return findings


def validate_review(review: dict, protocol: dict) -> list[str]:
    findings: list[str] = []
    if review.get("schema_version") != REVIEW_SCHEMA_VERSION or review.get("state_slice") != STATE_SLICE:
        findings.append("review schema/state mismatch")
    if review.get("protocol_digest") != protocol.get("protocol_digest"):
        findings.append("review protocol digest mismatch")
    if review.get("decision") != "accepted_for_execution" or review.get("assessment_authorization") is not True:
        findings.append("assessment authorization missing")
    if review.get("review_digest") != _digest({key: value for key, value in review.items() if key != "review_digest"}):
        findings.append("review digest mismatch")
    return findings


def validate_result(result: dict, protocol: dict | None = None, review: dict | None = None) -> list[str]:
    findings: list[str] = []
    if result.get("schema_version") != SCHEMA_VERSION or result.get("state_slice") != STATE_SLICE:
        findings.append("result schema/state mismatch")
    if result.get("result_digest") != _digest(result):
        findings.append("result digest mismatch")
    if protocol is not None:
        findings.extend(validate_protocol(protocol))
        if result.get("protocol_digest") != protocol.get("protocol_digest"):
            findings.append("result protocol digest mismatch")
        if result.get("grid_digest") != protocol.get("grid_digest"):
            findings.append("result grid digest mismatch")
    if review is not None and result.get("review_digest") != review.get("review_digest"):
        findings.append("result review digest mismatch")
    if result.get("algorithm_names") != list(SURVIVING_ALGORITHMS):
        findings.append("result algorithm set mismatch")
    if result.get("dataset_names") != list(DATASET_NAMES):
        findings.append("result dataset set mismatch")
    if result.get("publication_status", {}).get("status") != "no_candidate":
        findings.append("publication status must remain no_candidate")
    datasets = result.get("datasets", {})
    if set(datasets) != set(DATASET_NAMES):
        findings.append("dataset records incomplete")
    metric_names = ("mean_loss", "adaptation_lag", "updates", "active_synaptic_ops",
                    "state_bytes", "event_count", "replay_storage_bytes")
    for dataset in DATASET_NAMES:
        record = datasets.get(dataset, {})
        if record.get("rows", 0) < REQUIRED_ROWS or record.get("assessment_cohort_count") != (REQUIRED_ROWS - FIT_ROWS - TUNE_ROWS) // 128:
            findings.append(f"{dataset}: fresh cohort sizing mismatch")
        algorithms = record.get("algorithms", {})
        if set(algorithms) != set(SURVIVING_ALGORITHMS):
            findings.append(f"{dataset}: algorithm records incomplete")
            continue
        for algorithm in SURVIVING_ALGORITHMS:
            arm = algorithms[algorithm]
            if algorithm == "tidbd" and arm.get("status") == "not_applicable":
                continue
            if arm.get("status") not in {"executed", "no_valid_candidate", "assessment_failed"}:
                findings.append(f"{dataset}/{algorithm}: invalid status")
                continue
            candidates = arm.get("candidates", [])
            if not isinstance(candidates, list) or len(candidates) != 3:
                findings.append(f"{dataset}/{algorithm}: candidate grid missing")
            for candidate in candidates:
                if candidate.get("status") == "executed":
                    tune = candidate.get("tune_metrics", {})
                    _metric(findings, f"{dataset}/{algorithm}/tune", tune.get("mean_loss"), 1)
            if arm.get("status") == "executed":
                selection = arm.get("selection", {})
                if selection.get("assessment_selection_used") is not False or not isinstance(selection.get("selected_index"), int):
                    findings.append(f"{dataset}/{algorithm}: assessment selection lock invalid")
                if algorithm == "sgd_b1" and not isinstance(arm.get("selected_assessment"), dict):
                    findings.append(f"{dataset}/{algorithm}: selected sensitivity assessment missing")
                assessment = arm.get("assessment", {})
                for metric in metric_names:
                    _metric(findings, f"{dataset}/{algorithm}/{metric}", assessment.get(metric), 1)
                cohorts = arm.get("assessment_cohorts", [])
                if len(cohorts) != record.get("assessment_cohort_count") or not all(_finite(c.get("mean_loss")) and c.get("mean_loss") >= 0 for c in cohorts):
                    findings.append(f"{dataset}/{algorithm}: assessment cohorts invalid")
                paired = arm.get("paired_vs_frozen_sgd_b1")
                if algorithm != "sgd_b1":
                    if not isinstance(paired, dict) or paired.get("n") != record.get("assessment_cohort_count") or not _finite(paired.get("p_value")) or not _finite(paired.get("adjusted_p_value")):
                        findings.append(f"{dataset}/{algorithm}: multiplicity-adjusted paired test invalid")
        controls = record.get("controls", {})
        for name in ("noise_floor", "fit_only_topk_feature_sgd_b1"):
            control = controls.get(name, {})
            if control.get("status") != "executed":
                findings.append(f"{dataset}/{name}: control missing")
            for metric in ("mean_loss", "updates", "active_synaptic_ops", "state_bytes"):
                _metric(findings, f"{dataset}/{name}/{metric}", control.get(metric), 1)
        if controls.get("oracle_feature_sgd_b1", {}).get("status") != "not_available":
            findings.append(f"{dataset}/oracle_feature_sgd_b1: availability mismatch")
    gate = result.get("real_sensitivity_gate")
    if not isinstance(gate, dict) or gate.get("status") not in {"candidate", "no_candidate"}:
        findings.append("real sensitivity gate missing")
    return findings


def validate_file(path: str) -> list[str]:
    result = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_result(result)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m experiments.experience_learning.validate_real_sensitivity_v1 RESULT.json")
    errors = validate_file(sys.argv[1])
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("VALID")

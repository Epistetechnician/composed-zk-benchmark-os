"""Preflight a repository-change capture before benchmark conversion.

State slice: ``verified-self-model-benchmark-capture-preflight-v1``.

This module validates corpus-level readiness only. It does not execute a
repository workflow, call an agent or model, use the network, or convert a
capture into benchmark evidence. A well-formed but insufficient capture emits
an explicit rejected report; malformed or unsafe records fail closed.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
import sys
from typing import Any

from .protocol import (
    LIVE_SOURCE,
    MIN_LIVE_SPLIT_TRAJECTORIES,
    MIN_LIVE_TRAJECTORIES,
    SMOKE_SOURCE,
    SPLITS,
    VARIANTS,
    digest_json,
)
from .repository_change_capture import (
    CAPTURE_SCHEMA_VERSION,
    CAPTURE_STATE_SLICE,
    REPOSITORY_CHECK_IDS,
    CaptureError,
    load_capture,
)


PREFLIGHT_STATE_SLICE = "verified-self-model-benchmark-capture-preflight-v1"
REPORT_SCHEMA_VERSION = "verified-self-model-capture-preflight-report-v1"
CLAIM_CEILING = "LocalDevelopmentSelfModelCapturePreflightOnly"
MIN_TASK_FAMILIES = 5


class PreflightError(ValueError):
    """Raised when a capture cannot be evaluated under the preflight contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightError(message)


def _groups(observations: tuple[dict[str, Any], ...]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in observations:
        grouped[observation["trajectory_id"]].append(observation)
    return dict(grouped)


def _checks(manifest: dict[str, Any], observations: tuple[dict[str, Any], ...]) -> tuple[dict[str, bool], dict[str, Any]]:
    grouped = _groups(observations)
    trajectory_metadata = {
        trajectory: {(row["task_family"], row["split"]) for row in rows}
        for trajectory, rows in grouped.items()
    }
    trajectory_splits = {
        trajectory: {row["split"] for row in rows}
        for trajectory, rows in grouped.items()
    }
    split_counts = {
        split: sum(split in splits for splits in trajectory_splits.values())
        for split in SPLITS
    }
    variant_sets = {
        trajectory: {row["variant"] for row in rows}
        for trajectory, rows in grouped.items()
    }
    horizon_sets = {
        trajectory: {
            variant: {row["horizon_step"] for row in rows if row["variant"] == variant}
            for variant in VARIANTS
        }
        for trajectory, rows in grouped.items()
    }
    contiguous = all(
        steps
        and min(steps) == 1
        and sorted(steps) == list(range(1, max(steps) + 1))
        for by_variant in horizon_sets.values()
        for steps in by_variant.values()
    )
    horizons_match = all(
        all(steps == values[0] for steps in values[1:])
        for values in ([*by_variant.values()] for by_variant in horizon_sets.values())
    )
    observation_keys = [
        (row["trajectory_id"], row["variant"], row["horizon_step"])
        for row in observations
    ]
    observation_digests = [row["validator_observation_digest"] for row in observations]
    budget = manifest["budget"]
    resources_within_budget = all(
        row["latency_ms"] <= budget["max_latency_ms"]
        and row["compute_units"] <= budget["max_compute_units"]
        and row["tool_calls"] <= budget["max_tool_calls"]
        and row["attempts"] <= budget["max_attempts"]
        for row in observations
    )
    safety_clear = (
        manifest["raw_reasoning_retained"] is False
        and manifest["authority_granted"] is False
        and manifest["network_access"] is False
        and all(
            row["raw_reasoning_retained"] is False
            and row["authority_granted"] is False
            and row["network_access"] is False
            for row in observations
        )
    )
    custody_ready = (
        manifest["external_outcomes_verified"] is True
        and manifest["recorded_by_external_validator"] is True
        and manifest["validator_custody"] is True
        and manifest["agent_execution_recorded"] is True
    )
    prediction_locked = (
        manifest["prediction_locked_before_assessment"] is True
        and all(row["prediction_locked_before_outcome"] is True for row in observations)
    )
    required_checks_frozen = manifest["required_check_ids"] == list(REPOSITORY_CHECK_IDS)
    checks = {
        "source_type_is_live": manifest["source_type"] == LIVE_SOURCE,
        "minimum_trajectory_count": len(grouped) >= MIN_LIVE_TRAJECTORIES,
        "minimum_task_family_count": len({row["task_family"] for row in observations}) >= MIN_TASK_FAMILIES,
        "minimum_split_trajectory_counts": all(
            split_counts[split] >= MIN_LIVE_SPLIT_TRAJECTORIES[split]
            for split in SPLITS
        ),
        "trajectory_split_isolation": all(len(splits) == 1 for splits in trajectory_splits.values()),
        "trajectory_metadata_is_constant": all(len(metadata) == 1 for metadata in trajectory_metadata.values()),
        "complete_variant_sets": all(variants == set(VARIANTS) for variants in variant_sets.values()),
        "horizon_sets_match_across_variants": horizons_match,
        "horizon_sequences_are_contiguous": contiguous,
        "observation_keys_are_unique": len(observation_keys) == len(set(observation_keys)),
        "observation_digests_are_unique": len(observation_digests) == len(set(observation_digests)),
        "fixed_resources_within_budget": resources_within_budget,
        "required_checks_are_frozen": required_checks_frozen,
        "validator_custody_is_declared": custody_ready,
        "prediction_lock_is_declared": prediction_locked,
        "safety_flags_are_clear": safety_clear,
    }
    counts = {
        "observation_count": len(observations),
        "trajectory_count": len(grouped),
        "task_family_count": len({row["task_family"] for row in observations}),
        "split_trajectory_counts": split_counts,
        "variant_counts": {variant: sum(row["variant"] == variant for row in observations) for variant in VARIANTS},
        "maximum_horizon_step": max((row["horizon_step"] for row in observations), default=0),
    }
    return checks, counts


def _report_without_digest(report: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in report.items() if key != "report_digest"}


def validate_report(report: dict[str, Any]) -> None:
    """Validate a generated report and its deterministic digest binding."""

    _require(isinstance(report, dict), "preflight report must be an object")
    _require(report.get("record_type") == "self_model_capture_preflight_report", "wrong preflight report record type")
    _require(report.get("schema_version") == REPORT_SCHEMA_VERSION, "wrong preflight report schema")
    _require(report.get("state_slice") == PREFLIGHT_STATE_SLICE, "wrong preflight state slice")
    _require(report.get("capture_schema_version") == CAPTURE_SCHEMA_VERSION, "wrong capture schema binding")
    _require(report.get("capture_state_slice") == CAPTURE_STATE_SLICE, "wrong capture state binding")
    _require(isinstance(report.get("workflow_id"), str) and report["workflow_id"], "workflow_id required")
    _require(report.get("claim_ceiling") == CLAIM_CEILING, "wrong claim ceiling")
    _require(report.get("valid") is (report.get("status") == "preflight_valid"), "status/valid mismatch")
    _require(report.get("source_type") in {SMOKE_SOURCE, LIVE_SOURCE}, "wrong source type")
    for field in ("scientific_evidence", "authority_granted", "network_access"):
        _require(report.get(field) is False, f"{field} must be false")
    _require(isinstance(report.get("checks"), dict) and report["checks"], "checks required")
    _require(all(isinstance(value, bool) for value in report["checks"].values()), "checks must be boolean")
    _require(report["valid"] is all(report["checks"].values()), "valid must equal all checks")
    _require(isinstance(report.get("failure_reasons"), list), "failure_reasons must be a list")
    _require(report["failure_reasons"] == sorted(report["failure_reasons"]), "failure_reasons must be sorted")
    _require(isinstance(report.get("counts"), dict), "counts required")
    _require(isinstance(report.get("non_claims"), list) and report["non_claims"], "non_claims required")
    _require(
        isinstance(report.get("capture_manifest_digest"), str)
        and len(report["capture_manifest_digest"]) == 64
        and all(character in "0123456789abcdef" for character in report["capture_manifest_digest"]),
        "capture_manifest_digest must be lowercase SHA-256",
    )
    _require(
        report.get("report_digest") == digest_json(_report_without_digest(report)),
        "preflight report digest mismatch",
    )


def preflight_capture(path: str | Path) -> dict[str, Any]:
    """Return a deterministic readiness report for a validated capture."""

    try:
        manifest, observations = load_capture(path)
    except CaptureError as exc:
        raise PreflightError(str(exc)) from exc
    checks, counts = _checks(manifest, observations)
    valid = all(checks.values())
    report: dict[str, Any] = {
        "record_type": "self_model_capture_preflight_report",
        "schema_version": REPORT_SCHEMA_VERSION,
        "state_slice": PREFLIGHT_STATE_SLICE,
        "capture_schema_version": CAPTURE_SCHEMA_VERSION,
        "capture_state_slice": CAPTURE_STATE_SLICE,
        "workflow_id": manifest["workflow_id"],
        "source_type": manifest["source_type"],
        "status": "preflight_valid" if valid else "preflight_rejected",
        "valid": valid,
        "claim_ceiling": CLAIM_CEILING,
        "scientific_evidence": False,
        "authority_granted": False,
        "network_access": False,
        "capture_manifest_digest": digest_json(manifest),
        "checks": checks,
        "counts": counts,
        "required_minima": {
            "trajectories": MIN_LIVE_TRAJECTORIES,
            "split_trajectories": dict(MIN_LIVE_SPLIT_TRAJECTORIES),
            "task_families": MIN_TASK_FAMILIES,
            "variants": list(VARIANTS),
            "required_check_ids": list(REPOSITORY_CHECK_IDS),
        },
        "failure_reasons": sorted(key for key, value in checks.items() if not value),
        "non_claims": [
            "not_agent_execution",
            "not_model_execution",
            "not_benchmark_evidence",
            "not_scientific_evidence",
            "not_production_ready",
            "not_authority_grant",
        ],
    }
    report["report_digest"] = digest_json(_report_without_digest(report))
    validate_report(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="repository-change capture JSONL")
    parser.add_argument("--output", required=True, help="capture preflight report JSON")
    args = parser.parse_args()
    try:
        report = preflight_capture(args.input)
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, PreflightError, json.JSONDecodeError) as exc:
        print(f"capture_preflight_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {"report": args.output, "status": report["status"], "claim_ceiling": report["claim_ceiling"]},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

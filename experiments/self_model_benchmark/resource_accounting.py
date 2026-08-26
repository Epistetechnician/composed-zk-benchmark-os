"""Summarize validator-owned resource measurements without promoting a capture.

State slice: ``verified-self-model-benchmark-resource-accounting-v1``.

This module preserves aggregate latency, compute, tool-call, and attempt
measurements from a validated repository capture. The report is bound to the
capture-manifest digest and remains local development metadata. It does not
execute a workflow, call a model, use the network, accept evidence, or enable
live benchmark conversion.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

from .protocol import LIVE_SOURCE, SMOKE_SOURCE, VARIANTS, digest_json
from .repository_change_capture import (
    CaptureError,
    _assert_no_forbidden_keys,
    _derive_validator_label,
    load_capture,
    validate_capture_manifest,
    validate_observation,
)


RESOURCE_ACCOUNTING_STATE_SLICE = "verified-self-model-benchmark-resource-accounting-v1"
SCHEMA_VERSION = "verified-self-model-resource-accounting-v1"
RECORD_TYPE = "self_model_resource_accounting_report"
CLAIM_CEILING = "LocalDevelopmentSelfModelResourceAccountingOnly"
RESOURCE_FIELDS = ("latency_ms", "compute_units", "tool_calls", "attempts")
SUMMARY_FIELDS = frozenset(
    {
        "observation_count",
        "success_count",
        "failure_count",
        "failure_rate",
        "mean_latency_ms",
        "max_latency_ms",
        "mean_compute_units",
        "max_compute_units",
        "mean_tool_calls",
        "max_tool_calls",
        "mean_attempts",
        "max_attempts",
    }
)
REPORT_FIELDS = frozenset(
    {
        "record_type",
        "schema_version",
        "state_slice",
        "workflow_id",
        "source_type",
        "capture_schema_version",
        "capture_state_slice",
        "capture_manifest_digest",
        "fixed_budget",
        "budget",
        "observation_count",
        "overall",
        "by_variant",
        "scientific_evidence",
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "claim_ceiling",
        "non_claims",
        "report_digest",
    }
)
NON_CLAIMS = [
    "not_benchmark_evidence",
    "not_scientific_evidence",
    "not_external_custody_proof",
    "not_authority_grant",
    "not_production_ready",
]


class ResourceAccountingError(ValueError):
    """Raised when a resource-accounting report violates its contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ResourceAccountingError(message)


def _digest(value: Any, field: str) -> None:
    _require(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value),
        f"{field} must be lowercase SHA-256",
    )


def _positive_integer(value: Any, field: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{field} must be positive integer")


def _nonnegative_integer(value: Any, field: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{field} must be nonnegative integer")


def _finite_nonnegative(value: Any, field: str) -> None:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    _require(math.isfinite(value) and value >= 0, f"{field} must be finite and nonnegative")


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _summary(observations: list[dict[str, Any]], budget: dict[str, int]) -> dict[str, Any]:
    _require(observations, "resource summary requires observations")
    success_count = sum(_derive_validator_label(observation)[1] for observation in observations)
    summary: dict[str, Any] = {
        "observation_count": len(observations),
        "success_count": success_count,
        "failure_count": len(observations) - success_count,
        "failure_rate": (len(observations) - success_count) / len(observations),
    }
    for field in RESOURCE_FIELDS:
        values = [float(observation[field]) for observation in observations]
        summary[f"mean_{field}"] = _mean(values)
        summary[f"max_{field}"] = max(values)
        _require(summary[f"max_{field}"] <= budget[f"max_{field}"], f"{field} exceeds fixed budget")
    return summary


def _validate_budget(budget: Any) -> None:
    _require(isinstance(budget, dict), "budget must be an object")
    expected = {f"max_{field}" for field in RESOURCE_FIELDS}
    _require(set(budget) == expected, "budget fields drift")
    for field in expected:
        _positive_integer(budget[field], f"budget.{field}")


def _validate_summary(summary: Any, budget: dict[str, int], path: str) -> None:
    _require(isinstance(summary, dict), f"{path} must be an object")
    _require(frozenset(summary) == SUMMARY_FIELDS, f"{path} fields drift")
    _positive_integer(summary["observation_count"], f"{path}.observation_count")
    for field in ("success_count", "failure_count"):
        _nonnegative_integer(summary[field], f"{path}.{field}")
    _require(
        summary["success_count"] + summary["failure_count"] == summary["observation_count"],
        f"{path} success/failure counts do not add up",
    )
    _finite_nonnegative(summary["failure_rate"], f"{path}.failure_rate")
    _require(summary["failure_rate"] <= 1, f"{path}.failure_rate must be at most one")
    expected_failure_rate = summary["failure_count"] / summary["observation_count"]
    _require(
        math.isclose(summary["failure_rate"], expected_failure_rate, rel_tol=0, abs_tol=1e-12),
        f"{path}.failure_rate does not match counts",
    )
    for field in RESOURCE_FIELDS:
        mean_field = f"mean_{field}"
        max_field = f"max_{field}"
        _finite_nonnegative(summary[mean_field], f"{path}.{mean_field}")
        _finite_nonnegative(summary[max_field], f"{path}.{max_field}")
        _require(summary[mean_field] <= summary[max_field], f"{path}.{mean_field} exceeds maximum")
        _require(summary[max_field] <= budget[f"max_{field}"], f"{path}.{max_field} exceeds fixed budget")


def validate_report(report: dict[str, Any], manifest: dict[str, Any] | None = None) -> None:
    """Validate the aggregate report and optionally its source manifest binding."""

    _require(isinstance(report, dict), "resource report must be an object")
    try:
        _assert_no_forbidden_keys(report, "resource_report")
    except CaptureError as exc:
        raise ResourceAccountingError(str(exc)) from exc
    _require(frozenset(report) == REPORT_FIELDS, "resource report fields drift")
    _require(report.get("record_type") == RECORD_TYPE, "wrong resource report record type")
    _require(report.get("schema_version") == SCHEMA_VERSION, "wrong resource report schema")
    _require(report.get("state_slice") == RESOURCE_ACCOUNTING_STATE_SLICE, "wrong resource accounting state slice")
    _require(isinstance(report.get("workflow_id"), str) and report["workflow_id"], "workflow_id required")
    _require(report.get("source_type") in {SMOKE_SOURCE, LIVE_SOURCE}, "wrong resource report source type")
    _require(report.get("capture_schema_version") == "verified-self-model-repository-capture-v1", "wrong capture schema")
    _require(report.get("capture_state_slice") == "verified-self-model-benchmark-repository-capture-v1", "wrong capture state slice")
    _digest(report.get("capture_manifest_digest"), "capture_manifest_digest")
    _require(report.get("fixed_budget") is True, "fixed_budget must be true")
    _validate_budget(report.get("budget"))
    _positive_integer(report.get("observation_count"), "observation_count")
    _validate_summary(report.get("overall"), report["budget"], "overall")
    by_variant = report.get("by_variant")
    _require(isinstance(by_variant, dict), "by_variant must be an object")
    _require(set(by_variant) == set(VARIANTS), "by_variant must contain every frozen variant")
    total_observations = 0
    total_successes = 0
    total_failures = 0
    for variant in VARIANTS:
        _validate_summary(by_variant[variant], report["budget"], f"by_variant.{variant}")
        total_observations += by_variant[variant]["observation_count"]
        total_successes += by_variant[variant]["success_count"]
        total_failures += by_variant[variant]["failure_count"]
    _require(total_observations == report["observation_count"], "variant observation counts do not add up")
    _require(total_successes == report["overall"]["success_count"], "variant success counts do not add up")
    _require(total_failures == report["overall"]["failure_count"], "variant failure counts do not add up")
    for field in ("scientific_evidence", "authority_granted", "network_access", "raw_reasoning_retained"):
        _require(report.get(field) is False, f"{field} must be false")
    _require(report.get("claim_ceiling") == CLAIM_CEILING, "wrong resource accounting claim ceiling")
    _require(report.get("non_claims") == NON_CLAIMS, "non-claims must match the frozen order")
    _require(
        report.get("report_digest") == digest_json({key: value for key, value in report.items() if key != "report_digest"}),
        "resource report digest mismatch",
    )
    if manifest is not None:
        validate_capture_manifest(manifest)
        _require(report["workflow_id"] == manifest["workflow_id"], "workflow binding mismatch")
        _require(report["source_type"] == manifest["source_type"], "source type binding mismatch")
        _require(report["capture_manifest_digest"] == digest_json(manifest), "capture manifest digest binding mismatch")
        _require(report["budget"] == manifest["budget"], "budget binding mismatch")


def build_report(manifest: dict[str, Any], observations: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    """Build a digest-bound report from an already validated capture."""

    validate_capture_manifest(manifest)
    for observation in observations:
        validate_observation(observation, manifest)
    _require(observations, "resource report requires observations")
    by_variant = {variant: [observation for observation in observations if observation["variant"] == variant] for variant in VARIANTS}
    _require(all(by_variant.values()), "resource report requires every frozen variant")
    report: dict[str, Any] = {
        "record_type": RECORD_TYPE,
        "schema_version": SCHEMA_VERSION,
        "state_slice": RESOURCE_ACCOUNTING_STATE_SLICE,
        "workflow_id": manifest["workflow_id"],
        "source_type": manifest["source_type"],
        "capture_schema_version": manifest["schema_version"],
        "capture_state_slice": manifest["state_slice"],
        "capture_manifest_digest": digest_json(manifest),
        "fixed_budget": manifest["fixed_budget"],
        "budget": dict(manifest["budget"]),
        "observation_count": len(observations),
        "overall": _summary(list(observations), manifest["budget"]),
        "by_variant": {variant: _summary(rows, manifest["budget"]) for variant, rows in by_variant.items()},
        "scientific_evidence": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": NON_CLAIMS,
    }
    report["report_digest"] = digest_json(report)
    validate_report(report, manifest)
    return report


def build_report_from_capture(path: str | Path) -> dict[str, Any]:
    """Load and summarize a validated capture without converting it."""

    manifest, observations = load_capture(path)
    return build_report(manifest, observations)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="validated capture manifest plus observations")
    parser.add_argument("--output", required=True, help="aggregate resource report")
    args = parser.parse_args()
    try:
        report = build_report_from_capture(args.input)
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, CaptureError, ResourceAccountingError, json.JSONDecodeError) as exc:
        print(f"resource_accounting_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "observation_count": report["observation_count"],
                "claim_ceiling": report["claim_ceiling"],
                "report_digest": report["report_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

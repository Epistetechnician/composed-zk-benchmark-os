"""Bind a received capture to its handoff and validator receipt.

State slice: ``verified-self-model-benchmark-capture-admission-v1``.

This module is the local admission boundary after an external runner has
returned a capture. It recomputes capture-manifest and preflight digests,
checks handoff/runtime/identity bindings, and emits either an
``eligible_for_manual_review`` report or an explicit preflight rejection. It
does not grant authority, accept evidence, execute a workflow, call a model,
use the network, or retain raw material.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from .capture_handoff import validate_packet
from .capture_preflight import preflight_capture
from .protocol import LIVE_SOURCE, SMOKE_SOURCE, digest_json
from .repository_change_capture import load_capture


ADMISSION_STATE_SLICE = "verified-self-model-benchmark-capture-admission-v1"
RECEIPT_SCHEMA_VERSION = "verified-self-model-capture-validator-receipt-v1"
REPORT_SCHEMA_VERSION = "verified-self-model-capture-admission-report-v1"
CLAIM_CEILING = "LocalDevelopmentSelfModelCaptureAdmissionOnly"
RECEIPT_RECORD_TYPE = "self_model_capture_validator_receipt"
REPORT_RECORD_TYPE = "self_model_capture_admission_report"
ELIGIBLE_STATUS = "eligible_for_manual_review"
REJECTED_STATUS = "rejected_preflight"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NON_CLAIMS = [
    "not_accepted_evidence",
    "not_scientific_evidence",
    "not_authority_grant",
    "not_independent_custody_proof",
    "not_production_ready",
]

RECEIPT_FIELDS = frozenset(
    {
        "record_type",
        "schema_version",
        "state_slice",
        "workflow_id",
        "capture_source_type",
        "handoff_packet_digest",
        "capture_manifest_digest",
        "preflight_report_digest",
        "validator_report_digest",
        "task_spec_digest",
        "corpus_plan_digest",
        "runner_identity_digest",
        "validator_identity_digest",
        "model_digest",
        "runtime_digest",
        "checker_digest",
        "operator_authorization_reference_digest",
        "capture_received",
        "prediction_lock_verified",
        "external_outcomes_verified",
        "validator_custody",
        "execution_recorded",
        "operator_authorization_status",
        "raw_reasoning_retained",
        "authority_granted",
        "network_access",
        "non_claims",
        "receipt_digest",
    }
)

REPORT_FIELDS = frozenset(
    {
        "record_type",
        "schema_version",
        "state_slice",
        "workflow_id",
        "source_type",
        "admission_status",
        "valid",
        "claim_ceiling",
        "scientific_evidence",
        "authority_granted",
        "network_access",
        "handoff_packet_digest",
        "capture_manifest_digest",
        "preflight_report_digest",
        "receipt_digest",
        "checks",
        "counts",
        "failure_reasons",
        "non_claims",
        "report_digest",
    }
)


class AdmissionError(ValueError):
    """Raised when capture admission input violates its frozen contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdmissionError(message)


def _assert_no_forbidden_keys(value: Any, path: str = "record") -> None:
    forbidden = (
        "prompt",
        "raw_output",
        "model_output",
        "chain_of_thought",
        "reasoning",
        "secret",
        "credential",
        "pii",
        "provider_artifact",
    )
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key).lower()
            if key != "raw_reasoning_retained" and any(token in key_text for token in forbidden):
                raise AdmissionError(f"raw or sensitive field forbidden: {path}.{key}")
            _assert_no_forbidden_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_no_forbidden_keys(nested, f"{path}[{index}]")


def _require_exact_fields(value: dict[str, Any], expected: frozenset[str], path: str) -> None:
    actual = frozenset(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    _require(not missing and not extra, f"{path} fields drift: missing={missing}, extra={extra}")


def _require_digest(value: Any, field: str) -> None:
    _require(isinstance(value, str) and SHA256_RE.fullmatch(value) is not None, f"{field} must be lowercase SHA-256")


def _validate_receipt_basics(receipt: dict[str, Any]) -> None:
    _require(isinstance(receipt, dict), "validator receipt must be an object")
    _assert_no_forbidden_keys(receipt, "receipt")
    _require_exact_fields(receipt, RECEIPT_FIELDS, "validator receipt")
    _require(receipt.get("record_type") == RECEIPT_RECORD_TYPE, "wrong validator receipt record type")
    _require(receipt.get("schema_version") == RECEIPT_SCHEMA_VERSION, "wrong validator receipt schema")
    _require(receipt.get("state_slice") == ADMISSION_STATE_SLICE, "wrong admission state slice")
    _require(isinstance(receipt.get("workflow_id"), str) and receipt["workflow_id"], "workflow_id required")
    _require(receipt.get("capture_source_type") in {SMOKE_SOURCE, LIVE_SOURCE}, "wrong capture source type")
    for field in (
        "handoff_packet_digest",
        "capture_manifest_digest",
        "preflight_report_digest",
        "validator_report_digest",
        "task_spec_digest",
        "corpus_plan_digest",
        "runner_identity_digest",
        "validator_identity_digest",
        "model_digest",
        "runtime_digest",
        "checker_digest",
        "operator_authorization_reference_digest",
    ):
        _require_digest(receipt.get(field), field)
    _require(
        receipt["runner_identity_digest"] != receipt["validator_identity_digest"],
        "runner and validator identities must differ",
    )
    for field in ("capture_received", "prediction_lock_verified", "external_outcomes_verified", "validator_custody", "execution_recorded"):
        _require(receipt.get(field) is True, f"{field} must be true")
    _require(receipt.get("operator_authorization_status") == "reference_supplied", "operator authorization reference required")
    for field in ("raw_reasoning_retained", "authority_granted", "network_access"):
        _require(receipt.get(field) is False, f"{field} must be false")
    _require(receipt.get("non_claims") == NON_CLAIMS, "non-claims must match the frozen order")
    _require(
        receipt.get("receipt_digest") == digest_json({key: value for key, value in receipt.items() if key != "receipt_digest"}),
        "validator receipt digest mismatch",
    )


def validate_receipt(
    receipt: dict[str, Any],
    packet: dict[str, Any],
    manifest: dict[str, Any],
    preflight_report: dict[str, Any],
) -> None:
    """Validate receipt bindings against the handoff and recomputed capture facts."""

    # State slice: verified-self-model-benchmark-capture-admission-v1.
    _validate_receipt_basics(receipt)
    _require(isinstance(packet, dict), "handoff packet must be an object")
    _require(isinstance(manifest, dict), "capture manifest must be an object")
    _require(isinstance(preflight_report, dict), "preflight report must be an object")
    validate_packet(packet)
    _require(receipt["workflow_id"] == packet["workflow_id"] == manifest["workflow_id"], "workflow binding mismatch")
    _require(receipt["capture_source_type"] == manifest["source_type"], "capture source binding mismatch")
    _require(receipt["handoff_packet_digest"] == packet["packet_digest"], "handoff packet digest binding mismatch")
    _require(receipt["capture_manifest_digest"] == digest_json(manifest), "capture manifest digest binding mismatch")
    _require(receipt["preflight_report_digest"] == preflight_report["report_digest"], "preflight report digest binding mismatch")
    _require(receipt["validator_report_digest"] == manifest["validator_report_digest"], "validator report digest binding mismatch")
    _require(receipt["task_spec_digest"] == packet["task_spec_digest"], "task spec digest binding mismatch")
    _require(receipt["corpus_plan_digest"] == packet["corpus_plan_digest"], "corpus plan digest binding mismatch")
    for field in ("runner_identity_digest", "validator_identity_digest", "model_digest", "runtime_digest", "checker_digest"):
        _require(receipt[field] == packet[field], f"{field} binding mismatch")
    _require(receipt["model_digest"] == manifest["model_digest"], "model digest binding mismatch")
    _require(receipt["runtime_digest"] == manifest["runtime_digest"], "runtime digest binding mismatch")
    _require(receipt["checker_digest"] == manifest["checker_digest"], "checker digest binding mismatch")
    _require(manifest["prediction_locked_before_assessment"] is True, "manifest prediction lock missing")
    _require(manifest["external_outcomes_verified"] is True, "manifest external verification missing")
    _require(manifest["recorded_by_external_validator"] is True, "manifest validator recording missing")
    _require(manifest["validator_custody"] is True, "manifest validator custody missing")
    _require(manifest["agent_execution_recorded"] is True, "manifest execution record missing")
    _require(manifest["raw_reasoning_retained"] is False, "manifest raw reasoning flag must be false")
    _require(manifest["authority_granted"] is False, "manifest authority_granted must be false")
    _require(manifest["network_access"] is False, "manifest network_access must be false")
    _require(preflight_report["workflow_id"] == manifest["workflow_id"], "preflight workflow binding mismatch")
    _require(preflight_report["capture_manifest_digest"] == digest_json(manifest), "preflight capture digest mismatch")


def _report_without_digest(report: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in report.items() if key != "report_digest"}


def validate_report(report: dict[str, Any]) -> None:
    """Validate an admission report and its deterministic digest."""

    _require(isinstance(report, dict), "admission report must be an object")
    _assert_no_forbidden_keys(report, "report")
    _require_exact_fields(report, REPORT_FIELDS, "admission report")
    _require(report.get("record_type") == REPORT_RECORD_TYPE, "wrong admission report record type")
    _require(report.get("schema_version") == REPORT_SCHEMA_VERSION, "wrong admission report schema")
    _require(report.get("state_slice") == ADMISSION_STATE_SLICE, "wrong admission report state slice")
    _require(isinstance(report.get("workflow_id"), str) and report["workflow_id"], "workflow_id required")
    _require(report.get("source_type") in {SMOKE_SOURCE, LIVE_SOURCE}, "wrong report source type")
    _require(report.get("admission_status") in {ELIGIBLE_STATUS, REJECTED_STATUS}, "wrong admission status")
    _require(report.get("valid") is (report.get("admission_status") == ELIGIBLE_STATUS), "status/valid mismatch")
    _require(report.get("claim_ceiling") == CLAIM_CEILING, "wrong claim ceiling")
    for field in ("scientific_evidence", "authority_granted", "network_access"):
        _require(report.get(field) is False, f"{field} must be false")
    for field in ("handoff_packet_digest", "capture_manifest_digest", "preflight_report_digest", "receipt_digest", "report_digest"):
        _require_digest(report.get(field), field)
    _require(isinstance(report.get("checks"), dict) and report["checks"], "checks required")
    _require(all(isinstance(value, bool) for value in report["checks"].values()), "checks must be boolean")
    _require(report["valid"] is all(report["checks"].values()), "valid must equal all checks")
    _require(isinstance(report.get("counts"), dict), "counts required")
    _require(isinstance(report.get("failure_reasons"), list), "failure_reasons must be a list")
    _require(report["failure_reasons"] == sorted(report["failure_reasons"]), "failure_reasons must be sorted")
    _require(report.get("non_claims") == NON_CLAIMS, "non-claims must match the frozen order")
    _require(report.get("report_digest") == digest_json(_report_without_digest(report)), "admission report digest mismatch")


def admit(packet: dict[str, Any], capture_path: str | Path, receipt: dict[str, Any]) -> dict[str, Any]:
    """Admit a received capture for manual review, or report preflight rejection."""

    validate_packet(packet)
    manifest, _ = load_capture(capture_path)
    preflight_report = preflight_capture(capture_path)
    validate_receipt(receipt, packet, manifest, preflight_report)
    valid = preflight_report["valid"]
    checks = {
        "handoff_binding": True,
        "capture_manifest_binding": True,
        "preflight_report_binding": True,
        "validator_receipt_binding": True,
        "runtime_identity_binding": True,
        "operator_authorization_reference_present": True,
        "safety_clear": True,
        "preflight_valid": valid,
    }
    report: dict[str, Any] = {
        "record_type": REPORT_RECORD_TYPE,
        "schema_version": REPORT_SCHEMA_VERSION,
        "state_slice": ADMISSION_STATE_SLICE,
        "workflow_id": manifest["workflow_id"],
        "source_type": manifest["source_type"],
        "admission_status": ELIGIBLE_STATUS if valid else REJECTED_STATUS,
        "valid": valid,
        "claim_ceiling": CLAIM_CEILING,
        "scientific_evidence": False,
        "authority_granted": False,
        "network_access": False,
        "handoff_packet_digest": packet["packet_digest"],
        "capture_manifest_digest": digest_json(manifest),
        "preflight_report_digest": preflight_report["report_digest"],
        "receipt_digest": receipt["receipt_digest"],
        "checks": checks,
        "counts": preflight_report["counts"],
        "failure_reasons": sorted(key for key, value in checks.items() if not value),
        "non_claims": NON_CLAIMS,
    }
    report["report_digest"] = digest_json(_report_without_digest(report))
    validate_report(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff", required=True, help="validated handoff packet JSON")
    parser.add_argument("--capture", required=True, help="validator-owned capture JSONL")
    parser.add_argument("--receipt", required=True, help="external validator receipt JSON")
    parser.add_argument("--output", required=True, help="admission report JSON")
    args = parser.parse_args()
    try:
        packet = json.loads(Path(args.handoff).read_text(encoding="utf-8"))
        receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
        report = admit(packet, args.capture, receipt)
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, AdmissionError, ValueError) as exc:
        print(f"capture_admission_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "report": args.output,
                "admission_status": report["admission_status"],
                "claim_ceiling": report["claim_ceiling"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Hold an admitted capture in a non-releasing quarantine manifest.

State slice: ``verified-self-model-benchmark-capture-quarantine-v1``.

The manifest makes the quarantine state explicit between capture admission and
manual review. It stores only provenance digests and validator-derived failure
keys. It cannot release a capture, authorize conversion, accept evidence,
grant authority, retain raw material, or establish a scientific result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .capture_admission import AdmissionError, REJECTED_STATUS, validate_report
from .protocol import LIVE_SOURCE, SMOKE_SOURCE, digest_json
from .repository_change_capture import CaptureError, _assert_no_forbidden_keys


QUARANTINE_STATE_SLICE = "verified-self-model-benchmark-capture-quarantine-v1"
SCHEMA_VERSION = "verified-self-model-capture-quarantine-manifest-v1"
CLAIM_CEILING = "LocalDevelopmentSelfModelCaptureQuarantineOnly"
RECORD_TYPE = "self_model_capture_quarantine_manifest"
PENDING_STATUS = "pending_manual_review"
REJECTED_QUARANTINE_STATUS = "rejected_preflight"
NON_CLAIMS = [
    "not_external_custody_proof",
    "not_manual_review",
    "not_accepted_evidence",
    "not_benchmark_input",
    "not_scientific_evidence",
    "not_authority_grant",
    "not_production_ready",
]
MANIFEST_FIELDS = frozenset(
    {
        "record_type",
        "schema_version",
        "state_slice",
        "workflow_id",
        "source_type",
        "admission_status",
        "quarantine_status",
        "release_status",
        "reason",
        "failure_reasons",
        "admission_report_digest",
        "handoff_packet_digest",
        "capture_manifest_digest",
        "preflight_report_digest",
        "receipt_digest",
        "accepted",
        "conversion_eligible",
        "scientific_evidence",
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "claim_ceiling",
        "non_claims",
        "quarantine_digest",
    }
)


class QuarantineError(ValueError):
    """Raised when a capture quarantine manifest violates its contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise QuarantineError(message)


def _digest(value: Any, field: str) -> None:
    _require(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value),
        f"{field} must be lowercase SHA-256",
    )


def _unsigned_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "quarantine_digest"}


def validate_quarantine_manifest(manifest: dict[str, Any]) -> None:
    """Validate held status, provenance bindings, and non-promotion flags."""

    _require(isinstance(manifest, dict), "quarantine manifest must be an object")
    try:
        _assert_no_forbidden_keys(manifest, "quarantine_manifest")
    except CaptureError as exc:
        raise QuarantineError(str(exc)) from exc
    _require(frozenset(manifest) == MANIFEST_FIELDS, "quarantine manifest fields drift")
    _require(manifest.get("record_type") == RECORD_TYPE, "wrong quarantine record type")
    _require(manifest.get("schema_version") == SCHEMA_VERSION, "wrong quarantine schema")
    _require(manifest.get("state_slice") == QUARANTINE_STATE_SLICE, "wrong quarantine state slice")
    _require(isinstance(manifest.get("workflow_id"), str) and manifest["workflow_id"], "workflow_id required")
    _require(manifest.get("source_type") in {SMOKE_SOURCE, LIVE_SOURCE}, "wrong quarantine source type")
    _require(manifest.get("admission_status") in {"eligible_for_manual_review", REJECTED_STATUS}, "wrong admission status")
    _require(manifest.get("quarantine_status") in {PENDING_STATUS, REJECTED_QUARANTINE_STATUS}, "wrong quarantine status")
    _require(manifest.get("release_status") == "held", "release status must remain held")
    if manifest["admission_status"] == "eligible_for_manual_review":
        _require(manifest["quarantine_status"] == PENDING_STATUS, "eligible admission must remain pending review")
        _require(manifest["reason"] == "eligible_capture_held_pending_manual_review", "wrong pending quarantine reason")
    else:
        _require(manifest["quarantine_status"] == REJECTED_QUARANTINE_STATUS, "rejected admission must remain rejected")
        _require(manifest["reason"] == "preflight_rejected", "wrong rejected quarantine reason")
    _require(isinstance(manifest.get("failure_reasons"), list), "failure_reasons must be a list")
    _require(manifest["failure_reasons"] == sorted(manifest["failure_reasons"]), "failure_reasons must be sorted")
    _require(all(isinstance(item, str) for item in manifest["failure_reasons"]), "failure_reasons must contain strings")
    for field in (
        "accepted",
        "conversion_eligible",
        "scientific_evidence",
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
    ):
        _require(manifest.get(field) is False, f"{field} must be false")
    _require(manifest.get("claim_ceiling") == CLAIM_CEILING, "wrong quarantine claim ceiling")
    _require(manifest.get("non_claims") == NON_CLAIMS, "non-claims must match the frozen order")
    for field in (
        "admission_report_digest",
        "handoff_packet_digest",
        "capture_manifest_digest",
        "preflight_report_digest",
        "receipt_digest",
        "quarantine_digest",
    ):
        _digest(manifest.get(field), field)
    _require(digest_json(_unsigned_manifest(manifest)) == manifest["quarantine_digest"], "quarantine digest mismatch")


def _load_report(path: str | Path) -> dict[str, Any]:
    try:
        report = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QuarantineError(f"invalid admission report: {exc}") from exc
    _require(isinstance(report, dict), "admission report must be an object")
    try:
        validate_report(report)
    except AdmissionError as exc:
        raise QuarantineError(f"admission report invalid: {exc}") from exc
    return report


def build_quarantine_manifest(admission_report: dict[str, Any]) -> dict[str, Any]:
    """Create a held quarantine manifest for either eligible or rejected admission."""

    try:
        validate_report(admission_report)
    except AdmissionError as exc:
        raise QuarantineError(f"admission report invalid: {exc}") from exc
    eligible = admission_report["admission_status"] == "eligible_for_manual_review"
    manifest: dict[str, Any] = {
        "record_type": RECORD_TYPE,
        "schema_version": SCHEMA_VERSION,
        "state_slice": QUARANTINE_STATE_SLICE,
        "workflow_id": admission_report["workflow_id"],
        "source_type": admission_report["source_type"],
        "admission_status": admission_report["admission_status"],
        "quarantine_status": PENDING_STATUS if eligible else REJECTED_QUARANTINE_STATUS,
        "release_status": "held",
        "reason": "eligible_capture_held_pending_manual_review" if eligible else "preflight_rejected",
        "failure_reasons": list(admission_report["failure_reasons"]),
        "admission_report_digest": admission_report["report_digest"],
        "handoff_packet_digest": admission_report["handoff_packet_digest"],
        "capture_manifest_digest": admission_report["capture_manifest_digest"],
        "preflight_report_digest": admission_report["preflight_report_digest"],
        "receipt_digest": admission_report["receipt_digest"],
        "accepted": False,
        "conversion_eligible": False,
        "scientific_evidence": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": NON_CLAIMS,
    }
    manifest["quarantine_digest"] = digest_json(manifest)
    validate_quarantine_manifest(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--admission-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        manifest = build_quarantine_manifest(_load_report(args.admission_report))
        Path(args.output).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, QuarantineError, json.JSONDecodeError) as exc:
        print(f"capture_quarantine_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "quarantine_status": manifest["quarantine_status"],
                "release_status": manifest["release_status"],
                "conversion_eligible": manifest["conversion_eligible"],
                "claim_ceiling": manifest["claim_ceiling"],
                "quarantine_digest": manifest["quarantine_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Create a non-promoting manual-review packet for a held capture.

State slice: ``verified-self-model-benchmark-capture-review-v1``.

The packet is the deterministic handoff from capture quarantine to a human
reviewer. It may inspect a held eligible manifest, but it cannot accept
evidence, authorize conversion, retain raw material, grant authority, or
establish a scientific result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .capture_quarantine import PENDING_STATUS, QuarantineError, validate_quarantine_manifest
from .protocol import LIVE_SOURCE, digest_json
from .repository_change_capture import CaptureError, _assert_no_forbidden_keys


REVIEW_STATE_SLICE = "verified-self-model-benchmark-capture-review-v1"
PACKET_SCHEMA_VERSION = "verified-self-model-capture-review-packet-v1"
CLAIM_CEILING = "LocalDevelopmentSelfModelCaptureReviewOnly"
PACKET_RECORD_TYPE = "self_model_capture_review_packet"
DECISION_OPTIONS = ["not_evidence", "request_recapture", "reject"]
CHECKLIST_FIELDS = [
    "admission_report_valid",
    "handoff_binding",
    "capture_manifest_binding",
    "preflight_report_binding",
    "validator_receipt_binding",
    "runtime_identity_binding",
    "operator_authorization_reference_present",
    "safety_clear",
    "preflight_valid",
]
NON_CLAIMS = [
    "not_reviewed_by_a_verified_human",
    "not_accepted_evidence",
    "not_benchmark_input",
    "not_scientific_evidence",
    "not_authority_grant",
    "not_independent_custody_proof",
    "not_production_ready",
]

PACKET_FIELDS = frozenset(
    {
        "record_type",
        "schema_version",
        "state_slice",
        "workflow_id",
        "source_type",
        "admission_status",
        "quarantine_status",
        "release_status",
        "admission_report_digest",
        "quarantine_manifest_digest",
        "handoff_packet_digest",
        "capture_manifest_digest",
        "preflight_report_digest",
        "receipt_digest",
        "review_status",
        "human_review_required",
        "reviewed",
        "accepted",
        "conversion_eligible",
        "scientific_evidence",
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "review_notes_required",
        "decision_options",
        "checklist",
        "claim_ceiling",
        "non_claims",
        "packet_digest",
    }
)


class ReviewPacketError(ValueError):
    """Raised when an admission report cannot become a review packet."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewPacketError(message)


def _digest(value: Any, field: str) -> None:
    _require(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value),
        f"{field} must be lowercase SHA-256",
    )


def _unsigned_packet(packet: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in packet.items() if key != "packet_digest"}


def validate_review_packet(packet: dict[str, Any]) -> None:
    """Validate the frozen review packet and its non-promotion claims."""

    _require(isinstance(packet, dict), "review packet must be an object")
    try:
        _assert_no_forbidden_keys(packet, "review_packet")
    except CaptureError as exc:
        raise ReviewPacketError(str(exc)) from exc
    _require(frozenset(packet) == PACKET_FIELDS, "review packet fields drift")
    _require(packet.get("record_type") == PACKET_RECORD_TYPE, "wrong review packet record type")
    _require(packet.get("schema_version") == PACKET_SCHEMA_VERSION, "wrong review packet schema")
    _require(packet.get("state_slice") == REVIEW_STATE_SLICE, "wrong review state slice")
    _require(isinstance(packet.get("workflow_id"), str) and packet["workflow_id"], "workflow_id required")
    _require(packet.get("source_type") == LIVE_SOURCE, "review requires a live capture source")
    _require(packet.get("admission_status") == "eligible_for_manual_review", "admission must be eligible_for_manual_review")
    _require(packet.get("quarantine_status") == PENDING_STATUS, "quarantine must remain pending_manual_review")
    _require(packet.get("release_status") == "held", "quarantine release status must remain held")
    _require(packet.get("review_status") == PENDING_STATUS, "review packet must remain pending")
    _require(packet.get("human_review_required") is True, "human review must be required")
    _require(packet.get("reviewed") is False, "review packet cannot claim review completion")
    for field in (
        "accepted",
        "conversion_eligible",
        "scientific_evidence",
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
    ):
        _require(packet.get(field) is False, f"{field} must be false")
    _require(packet.get("review_notes_required") is True, "review notes must be required")
    _require(packet.get("decision_options") == DECISION_OPTIONS, "decision options must match the frozen order")
    _require(packet.get("claim_ceiling") == CLAIM_CEILING, "wrong review claim ceiling")
    _require(packet.get("non_claims") == NON_CLAIMS, "non-claims must match the frozen order")
    for field in (
        "admission_report_digest",
        "quarantine_manifest_digest",
        "handoff_packet_digest",
        "capture_manifest_digest",
        "preflight_report_digest",
        "receipt_digest",
        "packet_digest",
    ):
        _digest(packet.get(field), field)
    checklist = packet.get("checklist")
    _require(isinstance(checklist, dict), "review checklist required")
    _require(frozenset(checklist) == frozenset(CHECKLIST_FIELDS), "review checklist fields drift")
    _require(all(value is True for value in checklist.values()), "review checklist must be all true")
    _require(digest_json(_unsigned_packet(packet)) == packet["packet_digest"], "review packet digest mismatch")


def _load_quarantine(path: str | Path) -> dict[str, Any]:
    try:
        manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewPacketError(f"invalid quarantine manifest: {exc}") from exc
    _require(isinstance(manifest, dict), "quarantine manifest must be an object")
    try:
        validate_quarantine_manifest(manifest)
    except QuarantineError as exc:
        raise ReviewPacketError(f"quarantine manifest invalid: {exc}") from exc
    return manifest


def build_review_packet(quarantine_manifest: dict[str, Any]) -> dict[str, Any]:
    """Build a pending packet only from an eligible, held quarantine manifest."""

    try:
        validate_quarantine_manifest(quarantine_manifest)
    except QuarantineError as exc:
        raise ReviewPacketError(f"quarantine manifest invalid: {exc}") from exc
    _require(
        quarantine_manifest["admission_status"] == "eligible_for_manual_review",
        "admission must be eligible_for_manual_review",
    )
    _require(quarantine_manifest["quarantine_status"] == PENDING_STATUS, "quarantine must remain pending_manual_review")
    _require(quarantine_manifest["release_status"] == "held", "quarantine release status must remain held")
    _require(quarantine_manifest["source_type"] == LIVE_SOURCE, "review requires a live capture source")
    _require(quarantine_manifest["failure_reasons"] == [], "eligible quarantine cannot contain failure reasons")
    packet: dict[str, Any] = {
        "record_type": PACKET_RECORD_TYPE,
        "schema_version": PACKET_SCHEMA_VERSION,
        "state_slice": REVIEW_STATE_SLICE,
        "workflow_id": quarantine_manifest["workflow_id"],
        "source_type": quarantine_manifest["source_type"],
        "admission_status": quarantine_manifest["admission_status"],
        "quarantine_status": quarantine_manifest["quarantine_status"],
        "release_status": quarantine_manifest["release_status"],
        "admission_report_digest": quarantine_manifest["admission_report_digest"],
        "quarantine_manifest_digest": quarantine_manifest["quarantine_digest"],
        "handoff_packet_digest": quarantine_manifest["handoff_packet_digest"],
        "capture_manifest_digest": quarantine_manifest["capture_manifest_digest"],
        "preflight_report_digest": quarantine_manifest["preflight_report_digest"],
        "receipt_digest": quarantine_manifest["receipt_digest"],
        "review_status": PENDING_STATUS,
        "human_review_required": True,
        "reviewed": False,
        "accepted": False,
        "conversion_eligible": False,
        "scientific_evidence": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "review_notes_required": True,
        "decision_options": DECISION_OPTIONS,
        "checklist": {field: True for field in CHECKLIST_FIELDS},
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": NON_CLAIMS,
    }
    packet["packet_digest"] = digest_json(packet)
    validate_review_packet(packet)
    return packet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarantine-manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        packet = build_review_packet(_load_quarantine(args.quarantine_manifest))
        Path(args.output).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ReviewPacketError, json.JSONDecodeError) as exc:
        print(f"capture_review_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "review_status": packet["review_status"],
                "conversion_eligible": packet["conversion_eligible"],
                "claim_ceiling": packet["claim_ceiling"],
                "packet_digest": packet["packet_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Record an explicit non-promoting decision for a capture review packet.

State slice: ``verified-self-model-benchmark-capture-review-decision-v1``.

Reviewer references, notes, and recapture rationale are represented only by
digests. A decision closes the manual-review state but cannot accept evidence,
authorize conversion, grant authority, retain raw material, or establish a
scientific result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .capture_review import (
    DECISION_OPTIONS,
    PENDING_STATUS,
    ReviewPacketError,
    validate_review_packet,
)
from .protocol import digest_json
from .repository_change_capture import CaptureError, _assert_no_forbidden_keys


DECISION_STATE_SLICE = "verified-self-model-benchmark-capture-review-decision-v1"
DECISION_SCHEMA_VERSION = "verified-self-model-capture-review-decision-v1"
DECISION_CLAIM_CEILING = "LocalDevelopmentSelfModelCaptureReviewDecisionOnly"
DECISION_RECORD_TYPE = "self_model_capture_review_decision"
NON_CLAIMS = [
    "not_accepted_evidence",
    "not_benchmark_input",
    "not_scientific_evidence",
    "not_authority_grant",
    "not_independent_custody_proof",
    "not_production_ready",
]

DECISION_FIELDS = frozenset(
    {
        "record_type",
        "schema_version",
        "state_slice",
        "workflow_id",
        "source_packet_digest",
        "admission_report_digest",
        "quarantine_manifest_digest",
        "quarantine_status",
        "release_status",
        "handoff_packet_digest",
        "capture_manifest_digest",
        "preflight_report_digest",
        "receipt_digest",
        "review_status",
        "reviewed",
        "human_review_required",
        "decision",
        "reviewer_ref_digest",
        "review_notes_digest",
        "review_notes_retained",
        "accepted",
        "conversion_eligible",
        "scientific_evidence",
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "claim_ceiling",
        "non_claims",
        "decision_digest",
    }
)


class ReviewDecisionError(ValueError):
    """Raised when a manual-review decision violates the frozen contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReviewDecisionError(message)


def _digest(value: Any, field: str) -> None:
    _require(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value),
        f"{field} must be lowercase SHA-256",
    )


def _unsigned_decision(decision: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in decision.items() if key != "decision_digest"}


def validate_review_decision(decision: dict[str, Any]) -> None:
    """Validate a reviewed disposition and its permanent non-promotion flags."""

    _require(isinstance(decision, dict), "review decision must be an object")
    try:
        _assert_no_forbidden_keys(decision, "review_decision")
    except CaptureError as exc:
        raise ReviewDecisionError(str(exc)) from exc
    _require(frozenset(decision) == DECISION_FIELDS, "review decision fields drift")
    _require(decision.get("record_type") == DECISION_RECORD_TYPE, "wrong review decision record type")
    _require(decision.get("schema_version") == DECISION_SCHEMA_VERSION, "wrong review decision schema")
    _require(decision.get("state_slice") == DECISION_STATE_SLICE, "wrong review decision state slice")
    _require(isinstance(decision.get("workflow_id"), str) and decision["workflow_id"], "workflow_id required")
    _require(decision.get("review_status") == "reviewed", "review decision must be reviewed")
    _require(decision.get("reviewed") is True, "reviewed must be true")
    _require(decision.get("human_review_required") is False, "human review must be complete")
    _require(decision.get("decision") in DECISION_OPTIONS, "invalid review decision")
    _require(decision.get("quarantine_status") == PENDING_STATUS, "quarantine status must remain pending_manual_review")
    _require(decision.get("release_status") == "held", "quarantine release status must remain held")
    for field in (
        "accepted",
        "conversion_eligible",
        "scientific_evidence",
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
    ):
        _require(decision.get(field) is False, f"{field} must be false")
    _require(decision.get("review_notes_retained") is False, "review notes must not be retained")
    _require(decision.get("claim_ceiling") == DECISION_CLAIM_CEILING, "wrong review decision claim ceiling")
    _require(decision.get("non_claims") == NON_CLAIMS, "non-claims must match the frozen order")
    for field in (
        "source_packet_digest",
        "admission_report_digest",
        "handoff_packet_digest",
        "capture_manifest_digest",
        "preflight_report_digest",
        "receipt_digest",
        "reviewer_ref_digest",
        "review_notes_digest",
        "decision_digest",
    ):
        _digest(decision.get(field), field)
    _require(digest_json(_unsigned_decision(decision)) == decision["decision_digest"], "review decision digest mismatch")


def _digest_text(value: str, field: str) -> str:
    _require(isinstance(value, str) and value.strip(), f"{field} is required")
    return digest_json({field: value})


def record_review_decision(
    packet: dict[str, Any],
    decision: str,
    reviewer_ref: str,
    notes: str,
) -> dict[str, Any]:
    """Record a manual disposition without retaining reviewer prose."""

    try:
        validate_review_packet(packet)
    except ReviewPacketError as exc:
        raise ReviewDecisionError(f"review packet invalid: {exc}") from exc
    _require(decision in DECISION_OPTIONS, "invalid review decision")
    reviewer_ref_digest = _digest_text(reviewer_ref, "reviewer_ref")
    review_notes_digest = _digest_text(notes, "review_notes")
    result: dict[str, Any] = {
        "record_type": DECISION_RECORD_TYPE,
        "schema_version": DECISION_SCHEMA_VERSION,
        "state_slice": DECISION_STATE_SLICE,
        "workflow_id": packet["workflow_id"],
        "source_packet_digest": packet["packet_digest"],
        "admission_report_digest": packet["admission_report_digest"],
        "quarantine_manifest_digest": packet["quarantine_manifest_digest"],
        "quarantine_status": packet["quarantine_status"],
        "release_status": packet["release_status"],
        "handoff_packet_digest": packet["handoff_packet_digest"],
        "capture_manifest_digest": packet["capture_manifest_digest"],
        "preflight_report_digest": packet["preflight_report_digest"],
        "receipt_digest": packet["receipt_digest"],
        "review_status": "reviewed",
        "reviewed": True,
        "human_review_required": False,
        "decision": decision,
        "reviewer_ref_digest": reviewer_ref_digest,
        "review_notes_digest": review_notes_digest,
        "review_notes_retained": False,
        "accepted": False,
        "conversion_eligible": False,
        "scientific_evidence": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "claim_ceiling": DECISION_CLAIM_CEILING,
        "non_claims": NON_CLAIMS,
    }
    result["decision_digest"] = digest_json(result)
    validate_review_decision(result)
    return result


def _load_packet(path: str | Path) -> dict[str, Any]:
    try:
        packet = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewDecisionError(f"invalid review packet: {exc}") from exc
    _require(isinstance(packet, dict), "review packet must be an object")
    try:
        validate_review_packet(packet)
    except ReviewPacketError as exc:
        raise ReviewDecisionError(f"review packet invalid: {exc}") from exc
    return packet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-packet", required=True)
    parser.add_argument("--decision", required=True, choices=DECISION_OPTIONS)
    parser.add_argument("--reviewer-ref", required=True)
    parser.add_argument("--notes", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        packet = _load_packet(args.review_packet)
        result = record_review_decision(packet, args.decision, args.reviewer_ref, args.notes)
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ReviewDecisionError, json.JSONDecodeError) as exc:
        print(f"capture_review_decision_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "review_status": result["review_status"],
                "decision": result["decision"],
                "conversion_eligible": result["conversion_eligible"],
                "claim_ceiling": result["claim_ceiling"],
                "decision_digest": result["decision_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

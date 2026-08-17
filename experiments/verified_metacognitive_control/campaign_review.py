"""Create a non-authorizing human-review packet for a verified campaign.

State slice: ``verified-metacognitive-control-campaign-review-v1``.

The packet is the handoff from deterministic artifact verification to human
review. It derives a bounded disposition recommendation but cannot approve a
candidate, mutate the repository Evidence Ledger, grant authority, or claim
scientific evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .campaign_ledger import CampaignLedgerError, validate_ledger
from .campaign_verifier import CampaignVerificationError
from .protocol import digest_json
from .repository_change_capture import CaptureError, _assert_no_forbidden_keys


REVIEW_STATE_SLICE = "verified-metacognitive-control-campaign-review-v1"
REVIEW_SCHEMA_VERSION = "verified-metacognitive-campaign-review-v1"
CLAIM_CEILING = "LocalDevelopmentCampaignReviewOnly"
RECOMMENDATIONS = {"keep_candidate", "revert_candidate", "not_evidence"}


class CampaignReviewError(ValueError):
    """Raised when a verified campaign cannot become a review packet."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignReviewError(message)


def _digest(value: Any, field: str) -> None:
    _require(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value),
        f"{field} must be lowercase SHA-256",
    )


def _load_object(path: str | Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignReviewError(f"invalid {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _recommendation(result: dict[str, Any]) -> str:
    decision = result.get("decision")
    if decision == "keep_candidate" and result.get("classification") == "LocalDevelopmentCandidate":
        return "keep_candidate"
    if decision == "revert_candidate":
        return "revert_candidate"
    return "not_evidence"


def _unsigned_packet(packet: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in packet.items() if key != "packet_digest"}


def validate_review_packet(packet: dict[str, Any]) -> None:
    """Validate review status, artifact anchors, and non-authority claims."""

    _require(isinstance(packet, dict), "campaign review packet must be an object")
    try:
        _assert_no_forbidden_keys(packet, "campaign_review_packet")
    except CaptureError as exc:
        raise CampaignReviewError(str(exc)) from exc
    _require(packet.get("record_type") == "campaign_review_packet", "wrong review packet type")
    _require(packet.get("schema_version") == REVIEW_SCHEMA_VERSION, "wrong review packet schema")
    _require(packet.get("state_slice") == REVIEW_STATE_SLICE, "wrong review state slice")
    _require(isinstance(packet.get("workflow_id"), str) and packet["workflow_id"], "workflow_id required")
    _require(packet.get("review_status") == "pending_manual_review", "review packet must remain pending")
    _require(packet.get("human_review_required") is True, "human review must be required")
    _require(packet.get("reviewed") is False, "review packet cannot claim review completion")
    _require(packet.get("accepted") is False, "review packet cannot accept a candidate")
    for field in ("authority_granted", "network_access", "raw_reasoning_retained", "scientific_evidence"):
        _require(packet.get(field) is False, f"{field} must be false")
    _require(packet.get("claim_ceiling") == CLAIM_CEILING, "wrong review claim ceiling")
    _require(packet.get("recommended_disposition") in RECOMMENDATIONS, "invalid review recommendation")
    _require(isinstance(packet.get("review_notes_required"), bool), "review_notes_required must be boolean")
    for field in (
        "execution_plan_digest",
        "ledger_digest",
        "verification_report_digest",
        "result_digest",
        "packet_digest",
    ):
        _digest(packet.get(field), field)
    checklist = packet.get("checklist")
    _require(isinstance(checklist, dict), "review checklist required")
    for field in ("artifact_chain_verified", "result_recomputed", "no_authority", "retention_lock"):
        _require(checklist.get(field) is True, f"review checklist failed: {field}")
    _require(digest_json(_unsigned_packet(packet)) == packet["packet_digest"], "review packet digest mismatch")


def build_review_packet(
    result_path: str | Path,
    verification_path: str | Path,
    ledger_path: str | Path,
) -> dict[str, Any]:
    """Build a pending review packet from matching verified artifacts."""

    result = _load_object(result_path, "aggregate result")
    verification = _load_object(verification_path, "campaign verification report")
    ledger = _load_object(ledger_path, "campaign operational ledger")
    try:
        validate_ledger(ledger)
    except CampaignLedgerError as exc:
        raise CampaignReviewError(f"ledger invalid: {exc}") from exc
    _require(verification.get("valid") is True, "campaign verification must be valid")
    _require(verification.get("claim_ceiling") == "LocalDevelopmentCampaignVerificationOnly", "wrong verification ceiling")
    _digest(verification.get("report_digest"), "verification report_digest")
    unsigned_verification = dict(verification)
    unsigned_verification.pop("report_digest", None)
    _require(
        digest_json(unsigned_verification) == verification["report_digest"],
        "campaign verification digest mismatch",
    )
    _digest(result.get("result_digest"), "result_digest")
    unsigned_result = dict(result)
    unsigned_result.pop("result_digest", None)
    _require(digest_json(unsigned_result) == result["result_digest"], "aggregate result digest mismatch")
    _require(verification["result_digest"] == result.get("result_digest"), "verification/result mismatch")
    _require(verification["execution_plan_digest"] == ledger["execution_plan_digest"], "verification/plan mismatch")
    _require(verification["report_digest"] == ledger["events"][-1]["artifact_digest"], "verification/ledger mismatch")
    _require(result.get("result_digest") == ledger["events"][-2]["artifact_digest"], "result/ledger mismatch")
    _require(verification["workflow_id"] == ledger["workflow_id"], "workflow mismatch")
    recommendation = _recommendation(result)
    packet: dict[str, Any] = {
        "record_type": "campaign_review_packet",
        "schema_version": REVIEW_SCHEMA_VERSION,
        "state_slice": REVIEW_STATE_SLICE,
        "workflow_id": ledger["workflow_id"],
        "execution_plan_digest": ledger["execution_plan_digest"],
        "ledger_digest": ledger["ledger_digest"],
        "verification_report_digest": verification["report_digest"],
        "result_digest": result["result_digest"],
        "review_status": "pending_manual_review",
        "human_review_required": True,
        "reviewed": False,
        "accepted": False,
        "recommended_disposition": recommendation,
        "review_notes_required": True,
        "checklist": {
            "artifact_chain_verified": True,
            "result_recomputed": True,
            "no_authority": True,
            "retention_lock": True,
        },
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "scientific_evidence": False,
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": [
            "not_human_review",
            "not_acceptance",
            "not_repository_evidence_ledger_append",
            "not_experiment_evidence",
            "not_production_ready",
            "not_authority",
        ],
    }
    packet["packet_digest"] = digest_json(packet)
    validate_review_packet(packet)
    return packet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    parser.add_argument("--campaign-verification", required=True)
    parser.add_argument("--campaign-ledger", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        packet = build_review_packet(args.result, args.campaign_verification, args.campaign_ledger)
        Path(args.output).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, CampaignReviewError, CampaignVerificationError, json.JSONDecodeError) as exc:
        print(f"campaign_review_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "review_status": packet["review_status"],
                "recommended_disposition": packet["recommended_disposition"],
                "accepted": packet["accepted"],
                "claim_ceiling": packet["claim_ceiling"],
                "packet_digest": packet["packet_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

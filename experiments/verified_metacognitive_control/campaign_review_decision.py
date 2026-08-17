"""Record an explicit, non-authorizing disposition for a review packet.

State slice: ``verified-metacognitive-control-campaign-review-decision-v1``.

This contract closes the human-review handoff without turning it into an
acceptance mechanism. Reviewer identity, notes, and any override rationale are
represented only by digests. The decision cannot append the repository
Evidence Ledger, grant authority, retain raw reasoning, or establish
scientific evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .campaign_review import CampaignReviewError, RECOMMENDATIONS, validate_review_packet
from .protocol import digest_json
from .repository_change_capture import CaptureError, _assert_no_forbidden_keys


DECISION_STATE_SLICE = "verified-metacognitive-control-campaign-review-decision-v1"
DECISION_SCHEMA_VERSION = "verified-metacognitive-campaign-review-decision-v1"
CLAIM_CEILING = "LocalDevelopmentCampaignReviewDecisionOnly"


class CampaignReviewDecisionError(ValueError):
    """Raised when a review disposition violates the decision contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignReviewDecisionError(message)


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
    """Validate a reviewed disposition while preserving the non-acceptance gate."""

    _require(isinstance(decision, dict), "campaign review decision must be an object")
    try:
        _assert_no_forbidden_keys(decision, "campaign_review_decision")
    except CaptureError as exc:
        raise CampaignReviewDecisionError(str(exc)) from exc
    _require(decision.get("record_type") == "campaign_review_decision", "wrong review decision type")
    _require(decision.get("schema_version") == DECISION_SCHEMA_VERSION, "wrong review decision schema")
    _require(decision.get("state_slice") == DECISION_STATE_SLICE, "wrong review decision state slice")
    _require(isinstance(decision.get("workflow_id"), str) and decision["workflow_id"], "workflow_id required")
    _require(decision.get("review_status") == "reviewed", "review decision must be reviewed")
    _require(decision.get("reviewed") is True, "reviewed must be true")
    _require(decision.get("human_review_required") is False, "human review must be complete")
    _require(decision.get("accepted") is False, "review decision cannot accept a candidate")
    for field in (
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "scientific_evidence",
        "repository_evidence_ledger_appended",
        "production_ready",
    ):
        _require(decision.get(field) is False, f"{field} must be false")
    _require(decision.get("claim_ceiling") == CLAIM_CEILING, "wrong review decision claim ceiling")
    _require(decision.get("decision") in RECOMMENDATIONS, "invalid review decision")
    for field in (
        "source_packet_digest",
        "execution_plan_digest",
        "ledger_digest",
        "verification_report_digest",
        "result_digest",
        "reviewer_ref_digest",
        "review_notes_digest",
        "decision_digest",
    ):
        _digest(decision.get(field), field)
    _require(decision.get("review_notes_retained") is False, "review notes must not be retained")
    override_digest = decision.get("override_reason_digest")
    if override_digest is not None:
        _digest(override_digest, "override_reason_digest")
    _require(isinstance(decision.get("recommended_disposition"), str), "recommended disposition required")
    _require(decision["recommended_disposition"] in RECOMMENDATIONS, "invalid recommended disposition")
    if decision["decision"] != decision["recommended_disposition"]:
        _require(override_digest is not None, "override_reason_digest required for a changed disposition")
    else:
        _require(override_digest is None, "override_reason_digest is only allowed for an override")
    non_claims = decision.get("non_claims")
    _require(isinstance(non_claims, list) and all(isinstance(item, str) for item in non_claims), "non_claims required")
    _require(digest_json(_unsigned_decision(decision)) == decision["decision_digest"], "review decision digest mismatch")


def _load_packet(path: str | Path) -> dict[str, Any]:
    try:
        packet = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignReviewDecisionError(f"invalid review packet: {exc}") from exc
    _require(isinstance(packet, dict), "review packet must be an object")
    try:
        validate_review_packet(packet)
    except CampaignReviewError as exc:
        raise CampaignReviewDecisionError(f"review packet invalid: {exc}") from exc
    return packet


def _digest_text(value: str, field: str) -> str:
    _require(isinstance(value, str) and value.strip(), f"{field} is required")
    return digest_json({field: value})


def record_review_decision(
    packet: dict[str, Any],
    decision: str,
    reviewer_ref: str,
    notes: str,
    override_reason: str | None = None,
) -> dict[str, Any]:
    """Record a disposition from a valid pending packet without retaining prose."""

    try:
        validate_review_packet(packet)
    except CampaignReviewError as exc:
        raise CampaignReviewDecisionError(f"review packet invalid: {exc}") from exc
    _require(decision in RECOMMENDATIONS, "invalid review decision")
    _require(isinstance(reviewer_ref, str) and reviewer_ref.strip(), "reviewer_ref is required")
    _require(isinstance(notes, str) and notes.strip(), "notes are required")
    recommended = packet["recommended_disposition"]
    if decision != recommended:
        _require(
            isinstance(override_reason, str) and override_reason.strip(),
            "override_reason is required when changing the recommended disposition",
        )
    else:
        _require(override_reason is None, "override_reason is only allowed when changing the recommendation")
    result: dict[str, Any] = {
        "record_type": "campaign_review_decision",
        "schema_version": DECISION_SCHEMA_VERSION,
        "state_slice": DECISION_STATE_SLICE,
        "workflow_id": packet["workflow_id"],
        "source_packet_digest": packet["packet_digest"],
        "execution_plan_digest": packet["execution_plan_digest"],
        "ledger_digest": packet["ledger_digest"],
        "verification_report_digest": packet["verification_report_digest"],
        "result_digest": packet["result_digest"],
        "review_status": "reviewed",
        "reviewed": True,
        "human_review_required": False,
        "decision": decision,
        "recommended_disposition": recommended,
        "reviewer_ref_digest": _digest_text(reviewer_ref, "reviewer_ref"),
        "review_notes_digest": _digest_text(notes, "review_notes"),
        "review_notes_retained": False,
        "override_reason_digest": (
            _digest_text(override_reason, "override_reason") if override_reason is not None else None
        ),
        "accepted": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "scientific_evidence": False,
        "repository_evidence_ledger_appended": False,
        "production_ready": False,
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": [
            "not_candidate_acceptance",
            "not_repository_evidence_ledger_append",
            "not_experiment_evidence",
            "not_production_ready",
            "not_authority",
        ],
    }
    result["decision_digest"] = digest_json(result)
    validate_review_decision(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-packet", required=True)
    parser.add_argument("--decision", required=True, choices=sorted(RECOMMENDATIONS))
    parser.add_argument("--reviewer-ref", required=True)
    parser.add_argument("--notes", required=True)
    parser.add_argument("--override-reason")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        packet = _load_packet(args.review_packet)
        decision = record_review_decision(
            packet,
            args.decision,
            args.reviewer_ref,
            args.notes,
            args.override_reason,
        )
        Path(args.output).write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, CampaignReviewDecisionError, json.JSONDecodeError) as exc:
        print(f"campaign_review_decision_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "review_status": decision["review_status"],
                "decision": decision["decision"],
                "accepted": decision["accepted"],
                "claim_ceiling": decision["claim_ceiling"],
                "decision_digest": decision["decision_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

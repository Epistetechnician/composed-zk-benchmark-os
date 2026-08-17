"""Prepare a non-authorizing preflight for a future sealed pilot.

State slice: ``verified-metacognitive-control-sealed-pilot-preflight-v1``.

This module verifies the complete local campaign chain and the explicit human
review decision, then emits a digest-bound preflight. It never runs a pilot,
reuses the source corpus as a future assessment, grants authority, mutates the
repository Evidence Ledger, or retains review prose or raw reasoning.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .campaign_ledger import CampaignLedgerError, validate_ledger
from .campaign_review import CampaignReviewError, validate_review_packet
from .campaign_review_decision import CampaignReviewDecisionError, validate_review_decision
from .campaign_verifier import CampaignVerificationError, verify_campaign
from .corpus_execution_launcher import LauncherError, validate_execution_plan
from .protocol import PROMOTION_ARMS, ProtocolError, digest_json, load_input
from .repository_change_capture import CaptureError, _assert_no_forbidden_keys


PREFLIGHT_STATE_SLICE = "verified-metacognitive-control-sealed-pilot-preflight-v1"
PREFLIGHT_SCHEMA_VERSION = "verified-metacognitive-sealed-pilot-preflight-v1"
CLAIM_CEILING = "LocalDevelopmentSealedPilotPreflightOnly"
PREPARED_STATUS = "ready_for_sealed_pilot_authorization"
BLOCKED_STATUS = "blocked"
BLOCK_REASONS = {"review_did_not_keep_candidate", "source_result_not_candidate"}


class SealedPilotPreflightError(ValueError):
    """Raised when a sealed-pilot preflight cannot be produced or validated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SealedPilotPreflightError(message)


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
        raise SealedPilotPreflightError(f"invalid {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _unsigned_preflight(preflight: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in preflight.items() if key != "preflight_digest"}


def case_set_digest(execution_plan: dict[str, Any]) -> str:
    """Digest canonical case identities without retaining task content."""

    cases = {
        (row["case_id"], row["task_family"], row["split"])
        for row in execution_plan["rows"]
    }
    return digest_json(
        [
            {"case_id": case_id, "task_family": task_family, "split": split}
            for case_id, task_family, split in sorted(cases)
        ]
    )


def validate_preflight(preflight: dict[str, Any]) -> None:
    """Validate the sealed configuration, status, links, and claim boundary."""

    _require(isinstance(preflight, dict), "sealed pilot preflight must be an object")
    try:
        _assert_no_forbidden_keys(preflight, "sealed_pilot_preflight")
    except CaptureError as exc:
        raise SealedPilotPreflightError(str(exc)) from exc
    _require(preflight.get("record_type") == "sealed_pilot_preflight", "wrong preflight record type")
    _require(preflight.get("schema_version") == PREFLIGHT_SCHEMA_VERSION, "wrong preflight schema")
    _require(preflight.get("state_slice") == PREFLIGHT_STATE_SLICE, "wrong preflight state slice")
    _require(isinstance(preflight.get("workflow_id"), str) and preflight["workflow_id"], "workflow_id required")
    _require(preflight.get("preflight_status") in {PREPARED_STATUS, BLOCKED_STATUS}, "invalid preflight status")
    if preflight["preflight_status"] == BLOCKED_STATUS:
        _require(preflight.get("block_reason") in BLOCK_REASONS, "invalid preflight block reason")
    else:
        _require(preflight.get("block_reason") is None, "prepared preflight cannot have a block reason")
    _require(preflight.get("execution_status") == "not_started", "sealed pilot must not have started")
    _require(preflight.get("authorization_status") == "not_granted", "preflight cannot grant authorization")
    _require(preflight.get("accepted") is False, "preflight cannot accept a candidate")
    for field in (
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "scientific_evidence",
        "repository_evidence_ledger_appended",
        "source_corpus_reuse_allowed",
    ):
        _require(preflight.get(field) is False, f"{field} must be false")
    _require(preflight.get("future_fresh_corpus_required") is True, "future fresh corpus requirement missing")
    _require(preflight.get("claim_ceiling") == CLAIM_CEILING, "wrong preflight claim ceiling")
    for field in (
        "execution_plan_digest",
        "protocol_input_digest",
        "result_digest",
        "verification_report_digest",
        "ledger_digest",
        "review_packet_digest",
        "review_decision_digest",
        "preflight_digest",
    ):
        _digest(preflight.get(field), field)
    sealed = preflight.get("sealed_configuration")
    _require(isinstance(sealed, dict), "sealed configuration required")
    _require(sealed.get("arm_order") == list(PROMOTION_ARMS), "sealed arm order is not frozen")
    _require(sealed.get("prediction_lock_required") is True, "sealed prediction lock is required")
    _require(sealed.get("fixed_budget") is True, "sealed fixed budget is required")
    _require(sealed.get("assessment_outcomes_available_to_controller") is False, "assessment outcomes must remain sealed")
    _require(sealed.get("future_corpus_must_be_fresh") is True, "future corpus freshness is required")
    for field in (
        "task_spec_digest",
        "controller_config_digest",
        "model_digest",
        "runtime_digest",
        "checker_digest",
        "source_corpus_digest",
        "source_case_set_digest",
        "source_manifest_digest",
    ):
        _digest(sealed.get(field), f"sealed_configuration.{field}")
    arm_digests = sealed.get("arm_digests")
    _require(isinstance(arm_digests, dict), "sealed arm digests required")
    _require(set(arm_digests) == set(PROMOTION_ARMS), "sealed arm digest keys are not frozen")
    for arm in PROMOTION_ARMS:
        _digest(arm_digests.get(arm), f"sealed_configuration.arm_digests.{arm}")
    budget = sealed.get("budget")
    _require(isinstance(budget, dict), "sealed budget required")
    for field in ("max_latency_ms", "max_compute_units", "max_tool_calls", "max_attempts"):
        _require(
            isinstance(budget.get(field), int) and not isinstance(budget[field], bool) and budget[field] > 0,
            f"sealed budget requires positive integer {field}",
        )
    source_artifact_digests = preflight.get("source_artifact_digests")
    _require(isinstance(source_artifact_digests, dict), "source artifact digests required")
    for field in (
        "execution_plan",
        "protocol_input",
        "aggregate_result",
        "campaign_verification",
        "campaign_ledger",
        "review_packet",
        "review_decision",
    ):
        _digest(source_artifact_digests.get(field), f"source_artifact_digests.{field}")
    non_claims = preflight.get("non_claims")
    _require(isinstance(non_claims, list) and all(isinstance(item, str) for item in non_claims), "non_claims required")
    _require(digest_json(_unsigned_preflight(preflight)) == preflight["preflight_digest"], "preflight digest mismatch")


def _validate_protocol_manifest(protocol_path: str | Path) -> tuple[dict[str, Any], str, str]:
    try:
        bundle = load_input(protocol_path)
    except (OSError, ProtocolError, json.JSONDecodeError) as exc:
        raise SealedPilotPreflightError(f"protocol input invalid: {exc}") from exc
    manifest = bundle.manifest
    _require(manifest.get("source_type") == "live_workflow_capture", "sealed pilot requires live workflow capture")
    _require(manifest.get("arms") == list(PROMOTION_ARMS), "sealed pilot arms are not frozen")
    _require(manifest.get("fixed_budget") is True, "sealed pilot requires fixed budget")
    _require(manifest.get("prediction_locked_before_assessment") is True, "sealed pilot requires prediction locking")
    _require(manifest.get("authority_granted") is False, "sealed pilot manifest grants authority")
    _require(manifest.get("network_access") is False, "sealed pilot manifest uses network")
    _require(manifest.get("raw_reasoning_retained") is False, "sealed pilot manifest retains raw reasoning")
    budget = manifest.get("budget")
    _require(isinstance(budget, dict), "sealed pilot manifest budget required")
    for field in ("max_latency_ms", "max_compute_units", "max_tool_calls", "max_attempts"):
        _require(
            isinstance(budget.get(field), int) and not isinstance(budget[field], bool) and budget[field] > 0,
            f"sealed pilot manifest requires positive integer {field}",
        )
    return manifest, digest_json(manifest), digest_json([manifest, *bundle.trials])


def build_sealed_pilot_preflight(
    execution_plan_path: str | Path,
    validator_report_path: str | Path,
    agent_records_path: str | Path,
    capture_path: str | Path,
    protocol_input_path: str | Path,
    result_path: str | Path,
    verification_path: str | Path,
    ledger_path: str | Path,
    review_packet_path: str | Path,
    review_decision_path: str | Path,
) -> dict[str, Any]:
    """Verify current artifacts and prepare, or block, a future pilot."""

    execution_plan = _load_object(execution_plan_path, "execution plan")
    try:
        validate_execution_plan(execution_plan)
    except LauncherError as exc:
        raise SealedPilotPreflightError(f"execution plan invalid: {exc}") from exc
    protocol_manifest, protocol_manifest_digest, protocol_input_digest = _validate_protocol_manifest(protocol_input_path)
    result = _load_object(result_path, "aggregate result")
    verification = _load_object(verification_path, "campaign verification report")
    ledger = _load_object(ledger_path, "campaign operational ledger")
    packet = _load_object(review_packet_path, "review packet")
    decision = _load_object(review_decision_path, "review decision")
    try:
        validate_ledger(ledger)
        validate_review_packet(packet)
        validate_review_decision(decision)
    except (CampaignLedgerError, CampaignReviewError, CampaignReviewDecisionError) as exc:
        raise SealedPilotPreflightError(f"review chain invalid: {exc}") from exc
    try:
        recomputed_verification = verify_campaign(
            execution_plan_path,
            validator_report_path,
            agent_records_path,
            capture_path,
            protocol_input_path,
            result_path,
        )
    except CampaignVerificationError as exc:
        raise SealedPilotPreflightError(f"campaign verification failed: {exc}") from exc
    _require(verification == recomputed_verification, "campaign verification report is not deterministic")
    _require(verification["result_digest"] == result.get("result_digest"), "verification/result mismatch")
    _require(verification["execution_plan_digest"] == execution_plan["plan_digest"], "verification/plan mismatch")
    _require(verification["protocol_input_digest"] == protocol_input_digest, "verification/protocol input mismatch")
    _require(verification["report_digest"] == ledger["events"][-1]["artifact_digest"], "verification/ledger mismatch")
    _require(packet["verification_report_digest"] == verification["report_digest"], "packet/verification mismatch")
    _require(packet["ledger_digest"] == ledger["ledger_digest"], "packet/ledger mismatch")
    _require(packet["result_digest"] == result["result_digest"], "packet/result mismatch")
    _require(decision["source_packet_digest"] == packet["packet_digest"], "decision/packet mismatch")
    for field in (
        "execution_plan_digest",
        "ledger_digest",
        "verification_report_digest",
        "result_digest",
    ):
        _require(decision[field] == packet[field], f"decision/{field} mismatch")
    _require(decision["workflow_id"] == execution_plan["workflow_id"], "decision/workflow mismatch")
    _require(packet["workflow_id"] == execution_plan["workflow_id"], "packet/workflow mismatch")
    _require(protocol_manifest["workflow_id"] == execution_plan["workflow_id"], "protocol/workflow mismatch")

    source_is_candidate = (
        result.get("classification") == "LocalDevelopmentCandidate"
        and result.get("decision") == "keep_candidate"
        and result.get("claim_ceiling") == "LocalDevelopmentMetacognitiveControlCandidate"
    )
    if decision["decision"] != "keep_candidate":
        preflight_status = BLOCKED_STATUS
        block_reason = "review_did_not_keep_candidate"
    elif not source_is_candidate:
        preflight_status = BLOCKED_STATUS
        block_reason = "source_result_not_candidate"
    else:
        preflight_status = PREPARED_STATUS
        block_reason = None

    sealed_configuration = {
        "arm_order": list(PROMOTION_ARMS),
        "fixed_budget": True,
        "budget": dict(protocol_manifest["budget"]),
        "prediction_lock_required": True,
        "task_spec_digest": execution_plan["task_spec_digest"],
        "controller_config_digest": execution_plan["controller_config_digest"],
        "source_corpus_digest": execution_plan["source_corpus_digest"],
        "source_case_set_digest": case_set_digest(execution_plan),
        "source_manifest_digest": protocol_manifest_digest,
        "arm_digests": dict(execution_plan["arm_digests"]),
        "model_digest": protocol_manifest["model_digest"],
        "runtime_digest": protocol_manifest["runtime_digest"],
        "checker_digest": protocol_manifest["checker_digest"],
        "assessment_outcomes_available_to_controller": False,
        "future_corpus_must_be_fresh": True,
    }
    preflight: dict[str, Any] = {
        "record_type": "sealed_pilot_preflight",
        "schema_version": PREFLIGHT_SCHEMA_VERSION,
        "state_slice": PREFLIGHT_STATE_SLICE,
        "workflow_id": execution_plan["workflow_id"],
        "execution_plan_digest": execution_plan["plan_digest"],
        "protocol_input_digest": protocol_input_digest,
        "result_digest": result["result_digest"],
        "verification_report_digest": verification["report_digest"],
        "ledger_digest": ledger["ledger_digest"],
        "review_packet_digest": packet["packet_digest"],
        "review_decision_digest": decision["decision_digest"],
        "preflight_status": preflight_status,
        "block_reason": block_reason,
        "execution_status": "not_started",
        "authorization_status": "not_granted",
        "accepted": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "scientific_evidence": False,
        "repository_evidence_ledger_appended": False,
        "source_corpus_reuse_allowed": False,
        "future_fresh_corpus_required": True,
        "sealed_configuration": sealed_configuration,
        "source_artifact_digests": {
            "execution_plan": execution_plan["plan_digest"],
            "protocol_input": protocol_input_digest,
            "aggregate_result": result["result_digest"],
            "campaign_verification": verification["report_digest"],
            "campaign_ledger": ledger["ledger_digest"],
            "review_packet": packet["packet_digest"],
            "review_decision": decision["decision_digest"],
        },
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": [
            "not_pilot_execution",
            "not_runtime_authorization",
            "not_candidate_acceptance",
            "not_repository_evidence_ledger_append",
            "not_experiment_evidence",
            "not_production_ready",
            "not_general_metacognition",
        ],
    }
    preflight["preflight_digest"] = digest_json(preflight)
    validate_preflight(preflight)
    return preflight


def main() -> int:
    parser = argparse.ArgumentParser()
    for option in (
        "execution-plan",
        "validator-report",
        "agent-records",
        "capture",
        "protocol-input",
        "result",
        "campaign-verification",
        "campaign-ledger",
        "review-packet",
        "review-decision",
    ):
        parser.add_argument(f"--{option}", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        preflight = build_sealed_pilot_preflight(
            args.execution_plan,
            args.validator_report,
            args.agent_records,
            args.capture,
            args.protocol_input,
            args.result,
            args.campaign_verification,
            args.campaign_ledger,
            args.review_packet,
            args.review_decision,
        )
        Path(args.output).write_text(json.dumps(preflight, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, SealedPilotPreflightError, json.JSONDecodeError) as exc:
        print(f"sealed_pilot_preflight_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "preflight_status": preflight["preflight_status"],
                "block_reason": preflight["block_reason"],
                "execution_status": preflight["execution_status"],
                "authorization_status": preflight["authorization_status"],
                "claim_ceiling": preflight["claim_ceiling"],
                "preflight_digest": preflight["preflight_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Create a non-authorizing request to execute an admitted sealed pilot.

State slice: ``verified-metacognitive-control-sealed-pilot-execution-request-v1``.

The request is the final local handoff before a separately authorized external
runner. It binds the fresh-corpus admission and fixed 300-row matrix, exposes
the operator checks and required aggregate artifacts, and remains pending with
execution and authorization inactive.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .corpus_execution_launcher import LauncherError, validate_execution_plan
from .fresh_corpus_admission import FreshCorpusAdmissionError, validate_admission
from .protocol import PROMOTION_ARMS, digest_json
from .repository_change_capture import CaptureError, _assert_no_forbidden_keys


REQUEST_STATE_SLICE = "verified-metacognitive-control-sealed-pilot-execution-request-v1"
REQUEST_SCHEMA_VERSION = "verified-metacognitive-sealed-pilot-execution-request-v1"
CLAIM_CEILING = "LocalDevelopmentSealedPilotExecutionRequestOnly"
REQUEST_STATUS = "pending_operator_authorization"

REQUIRED_OPERATOR_CHECKS = (
    "confirm_runtime_and_model_identity",
    "confirm_external_runner_custody",
    "confirm_operator_authorization",
    "confirm_artifact_destination",
    "confirm_abort_on_scope_or_budget_drift",
)
REQUIRED_AGGREGATE_ARTIFACTS = (
    "validator_report",
    "agent_execution_manifest",
    "agent_execution_records",
    "capture_bundle",
    "protocol_input",
    "aggregate_result",
)


class SealedPilotExecutionRequestError(ValueError):
    """Raised when a sealed-pilot execution request is malformed or elevated."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SealedPilotExecutionRequestError(message)


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
        raise SealedPilotExecutionRequestError(f"invalid {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _unsigned_request(request: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in request.items() if key != "request_digest"}


def validate_execution_request(request: dict[str, Any]) -> None:
    """Validate request status, admission binding, operator controls, and flags."""

    _require(isinstance(request, dict), "sealed pilot execution request must be an object")
    try:
        _assert_no_forbidden_keys(request, "sealed_pilot_execution_request")
    except CaptureError as exc:
        raise SealedPilotExecutionRequestError(str(exc)) from exc
    _require(request.get("record_type") == "sealed_pilot_execution_request", "wrong request record type")
    _require(request.get("schema_version") == REQUEST_SCHEMA_VERSION, "wrong request schema")
    _require(request.get("state_slice") == REQUEST_STATE_SLICE, "wrong request state slice")
    _require(isinstance(request.get("workflow_id"), str) and request["workflow_id"], "workflow_id required")
    _require(request.get("request_status") == REQUEST_STATUS, "wrong request status")
    _require(request.get("execution_status") == "not_started", "request cannot start execution")
    _require(request.get("authorization_status") == "not_granted", "request cannot grant authorization")
    _require(request.get("accepted") is False, "request cannot accept a candidate")
    for field in (
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "scientific_evidence",
        "repository_evidence_ledger_appended",
        "source_corpus_reuse_allowed",
    ):
        _require(request.get(field) is False, f"{field} must be false")
    _require(request.get("fresh_corpus_verified") is True, "fresh corpus must be verified")
    _require(request.get("operator_ack_required") is True, "operator acknowledgement must be required")
    _require(request.get("external_runner_required") is True, "external runner requirement must be explicit")
    _require(request.get("claim_ceiling") == CLAIM_CEILING, "wrong request claim ceiling")
    for field in (
        "admission_digest",
        "fresh_corpus_digest",
        "fresh_execution_plan_digest",
        "request_digest",
    ):
        _digest(request.get(field), field)
    plan = request.get("execution_plan_summary")
    _require(isinstance(plan, dict), "execution plan summary required")
    _require(plan.get("execution_plan_digest") == request["fresh_execution_plan_digest"], "plan digest mismatch")
    _require(plan.get("planned_execution_count") == 300, "request must bind 300 planned executions")
    _require(plan.get("paired_task_count") == 60, "request must bind 60 paired tasks")
    _require(plan.get("arm_order") == list(PROMOTION_ARMS), "request arm order is not frozen")
    _require(plan.get("prediction_lock_required") is True, "request prediction locking is required")
    _require(plan.get("assessment_outcomes_available_to_controller") is False, "assessment outcomes must remain sealed")
    _digest(plan.get("task_spec_digest"), "execution_plan_summary.task_spec_digest")
    _digest(plan.get("controller_config_digest"), "execution_plan_summary.controller_config_digest")
    arm_digests = plan.get("arm_digests")
    _require(isinstance(arm_digests, dict), "request arm digests required")
    _require(set(arm_digests) == set(PROMOTION_ARMS), "request arm digest keys are not frozen")
    for arm in PROMOTION_ARMS:
        _digest(arm_digests.get(arm), f"execution_plan_summary.arm_digests.{arm}")
    budget = plan.get("budget")
    _require(isinstance(budget, dict), "request budget required")
    for field in ("max_latency_ms", "max_compute_units", "max_tool_calls", "max_attempts"):
        _require(
            isinstance(budget.get(field), int) and not isinstance(budget[field], bool) and budget[field] > 0,
            f"request budget requires positive integer {field}",
        )
    _require(request.get("required_operator_checks") == list(REQUIRED_OPERATOR_CHECKS), "operator checks drifted")
    _require(
        request.get("required_aggregate_artifacts") == list(REQUIRED_AGGREGATE_ARTIFACTS),
        "aggregate artifact requirements drifted",
    )
    non_claims = request.get("non_claims")
    _require(isinstance(non_claims, list) and all(isinstance(item, str) for item in non_claims), "non_claims required")
    _require(digest_json(_unsigned_request(request)) == request["request_digest"], "request digest mismatch")


def build_execution_request(admission_path: str | Path) -> dict[str, Any]:
    """Create a pending request from a valid fresh-corpus admission."""

    admission = _load_object(admission_path, "fresh-corpus admission")
    try:
        validate_admission(admission)
    except FreshCorpusAdmissionError as exc:
        raise SealedPilotExecutionRequestError(f"fresh-corpus admission invalid: {exc}") from exc
    fresh_plan = admission["fresh_execution_plan"]
    sealed_configuration = admission["sealed_configuration"]
    try:
        validate_execution_plan(fresh_plan)
    except LauncherError as exc:
        raise SealedPilotExecutionRequestError(f"fresh execution plan invalid: {exc}") from exc
    request: dict[str, Any] = {
        "record_type": "sealed_pilot_execution_request",
        "schema_version": REQUEST_SCHEMA_VERSION,
        "state_slice": REQUEST_STATE_SLICE,
        "workflow_id": admission["workflow_id"],
        "admission_digest": admission["admission_digest"],
        "fresh_corpus_digest": admission["fresh_corpus_digest"],
        "fresh_execution_plan_digest": admission["fresh_execution_plan_digest"],
        "request_status": REQUEST_STATUS,
        "execution_status": "not_started",
        "authorization_status": "not_granted",
        "accepted": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "scientific_evidence": False,
        "repository_evidence_ledger_appended": False,
        "source_corpus_reuse_allowed": False,
        "fresh_corpus_verified": True,
        "operator_ack_required": True,
        "external_runner_required": True,
        "execution_plan_summary": {
            "execution_plan_digest": fresh_plan["plan_digest"],
            "planned_execution_count": fresh_plan["planned_execution_count"],
            "paired_task_count": fresh_plan["paired_task_count"],
            "arm_order": list(PROMOTION_ARMS),
            "task_spec_digest": fresh_plan["task_spec_digest"],
            "controller_config_digest": fresh_plan["controller_config_digest"],
            "arm_digests": dict(fresh_plan["arm_digests"]),
            "budget": dict(sealed_configuration["budget"]),
            "prediction_lock_required": True,
            "assessment_outcomes_available_to_controller": False,
        },
        "required_operator_checks": list(REQUIRED_OPERATOR_CHECKS),
        "required_aggregate_artifacts": list(REQUIRED_AGGREGATE_ARTIFACTS),
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": [
            "not_operator_authorization",
            "not_pilot_execution",
            "not_candidate_acceptance",
            "not_repository_evidence_ledger_append",
            "not_experiment_evidence",
            "not_production_ready",
            "not_semantic_freshness_proof",
        ],
    }
    request["request_digest"] = digest_json(request)
    validate_execution_request(request)
    return request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh-corpus-admission", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        request = build_execution_request(args.fresh_corpus_admission)
        Path(args.output).write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, SealedPilotExecutionRequestError, json.JSONDecodeError) as exc:
        print(f"sealed_pilot_execution_request_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "request_status": request["request_status"],
                "execution_status": request["execution_status"],
                "authorization_status": request["authorization_status"],
                "claim_ceiling": request["claim_ceiling"],
                "request_digest": request["request_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

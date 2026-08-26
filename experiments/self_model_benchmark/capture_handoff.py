"""Build a plan-only handoff for a separately controlled capture runner.

State slice: ``verified-self-model-benchmark-capture-handoff-v1``.

The handoff binds the repository revision, task/corpus digests, runner and
validator identities, runtime digests, fixed budgets, and the expected capture
schema before execution. It requires declared runner/validator separation and
explicitly remains unauthorized, uncaptured, non-scientific metadata. It does
not execute a workflow, call a model, use the network, or retain raw material.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from .protocol import (
    LIVE_SOURCE,
    MIN_LIVE_SPLIT_TRAJECTORIES,
    MIN_LIVE_TRAJECTORIES,
    SPLITS,
    VARIANTS,
    digest_json,
)
from .repository_change_capture import (
    CAPTURE_SCHEMA_VERSION,
    CAPTURE_STATE_SLICE,
    REPOSITORY_CHECK_IDS,
)


HANDOFF_STATE_SLICE = "verified-self-model-benchmark-capture-handoff-v1"
REQUEST_SCHEMA_VERSION = "verified-self-model-capture-handoff-request-v1"
PACKET_SCHEMA_VERSION = "verified-self-model-capture-handoff-packet-v1"
CLAIM_CEILING = "LocalDevelopmentSelfModelCaptureHandoffOnly"
REQUEST_RECORD_TYPE = "self_model_capture_handoff_request"
PACKET_RECORD_TYPE = "self_model_capture_handoff_packet"
PACKET_STATUS = "ready_for_external_runner"
CAPTURE_STATUS = "not_captured"
MIN_TASK_FAMILIES = 5
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_RECORD_TYPES = ["self_model_capture_manifest", "self_model_repository_observation"]
NON_CLAIMS = [
    "not_agent_execution",
    "not_model_execution",
    "not_validator_custody",
    "not_benchmark_evidence",
    "not_authority_grant",
]

REQUEST_FIELDS = frozenset(
    {
        "record_type",
        "schema_version",
        "state_slice",
        "workflow_id",
        "source_type",
        "repository_revision",
        "task_spec_digest",
        "corpus_plan_digest",
        "runner_identity_digest",
        "validator_identity_digest",
        "model_digest",
        "runtime_digest",
        "checker_digest",
        "fixed_budget",
        "budget",
        "trajectory_count",
        "task_family_count",
        "split_trajectory_counts",
        "variants",
        "required_check_ids",
        "prediction_lock_required",
        "external_outcomes_required",
        "validator_custody_required",
        "operator_authorization_status",
        "execution_authorized",
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "expected_capture_schema_version",
        "expected_capture_state_slice",
        "expected_record_types",
        "non_claims",
        "request_digest",
    }
)

PACKET_FIELDS = frozenset(
    {
        "record_type",
        "schema_version",
        "state_slice",
        "workflow_id",
        "source_type",
        "repository_revision",
        "task_spec_digest",
        "corpus_plan_digest",
        "runner_identity_digest",
        "validator_identity_digest",
        "model_digest",
        "runtime_digest",
        "checker_digest",
        "fixed_budget",
        "budget",
        "trajectory_count",
        "task_family_count",
        "split_trajectory_counts",
        "variants",
        "required_check_ids",
        "prediction_lock_required",
        "external_outcomes_required",
        "validator_custody_required",
        "operator_authorization_status",
        "execution_authorized",
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "expected_capture_schema_version",
        "expected_capture_state_slice",
        "expected_record_types",
        "non_claims",
        "request_digest",
        "packet_status",
        "capture_status",
        "claim_ceiling",
        "scientific_evidence",
        "packet_digest",
    }
)


class HandoffError(ValueError):
    """Raised when a capture handoff request or packet violates its contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HandoffError(message)


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
                raise HandoffError(f"raw or sensitive field forbidden: {path}.{key}")
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


def _require_revision(value: Any, field: str) -> None:
    _require(isinstance(value, str) and REVISION_RE.fullmatch(value) is not None, f"{field} must be a 40-character revision")


def _require_positive_integer(value: Any, field: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{field} must be positive integer")


def _validate_common(request: dict[str, Any]) -> None:
    _require(request.get("record_type") == REQUEST_RECORD_TYPE, "wrong handoff request record type")
    _require(request.get("schema_version") == REQUEST_SCHEMA_VERSION, "wrong handoff request schema")
    _require(request.get("state_slice") == HANDOFF_STATE_SLICE, "wrong handoff state slice")
    _require(isinstance(request.get("workflow_id"), str) and request["workflow_id"], "workflow_id required")
    _require(request.get("source_type") == LIVE_SOURCE, "handoff source type must be live_workflow_capture")
    _require_revision(request.get("repository_revision"), "repository_revision")
    for field in (
        "task_spec_digest",
        "corpus_plan_digest",
        "runner_identity_digest",
        "validator_identity_digest",
        "model_digest",
        "runtime_digest",
        "checker_digest",
    ):
        _require_digest(request.get(field), field)
    _require(
        request["runner_identity_digest"] != request["validator_identity_digest"],
        "runner and validator identities must differ",
    )
    _require(request.get("fixed_budget") is True, "fixed_budget must be true")
    budget = request.get("budget")
    _require(isinstance(budget, dict), "budget required")
    _require(
        frozenset(budget) == frozenset({"max_latency_ms", "max_compute_units", "max_tool_calls", "max_attempts"}),
        "budget fields drift",
    )
    for field in budget:
        _require_positive_integer(budget[field], f"budget.{field}")
    _require(
        isinstance(request.get("trajectory_count"), int)
        and not isinstance(request["trajectory_count"], bool)
        and request["trajectory_count"] >= MIN_LIVE_TRAJECTORIES,
        "trajectory_count is below the live minimum",
    )
    _require(
        isinstance(request.get("task_family_count"), int)
        and not isinstance(request["task_family_count"], bool)
        and request["task_family_count"] >= MIN_TASK_FAMILIES,
        "task_family_count is below the live minimum",
    )
    split_counts = request.get("split_trajectory_counts")
    _require(isinstance(split_counts, dict) and set(split_counts) == set(SPLITS), "split trajectory counts drift")
    for split in SPLITS:
        _require(
            isinstance(split_counts[split], int)
            and not isinstance(split_counts[split], bool)
            and split_counts[split] >= MIN_LIVE_SPLIT_TRAJECTORIES[split],
            f"split trajectory count below minimum: {split}",
        )
    _require(request.get("variants") == list(VARIANTS), "variants must match the frozen order")
    _require(request.get("required_check_ids") == list(REPOSITORY_CHECK_IDS), "required checks must match the frozen order")
    for field in ("prediction_lock_required", "external_outcomes_required", "validator_custody_required"):
        _require(request.get(field) is True, f"{field} must be true")
    _require(request.get("operator_authorization_status") == "not_authorized", "operator authorization must remain not_authorized")
    for field in ("execution_authorized", "authority_granted", "network_access", "raw_reasoning_retained"):
        _require(request.get(field) is False, f"{field} must be false")
    _require(request.get("expected_capture_schema_version") == CAPTURE_SCHEMA_VERSION, "wrong expected capture schema")
    _require(request.get("expected_capture_state_slice") == CAPTURE_STATE_SLICE, "wrong expected capture state slice")
    _require(request.get("expected_record_types") == EXPECTED_RECORD_TYPES, "wrong expected capture record types")
    _require(request.get("non_claims") == NON_CLAIMS, "non-claims must match the frozen order")


def validate_request(request: dict[str, Any]) -> None:
    """Validate the request and its deterministic digest."""

    _require(isinstance(request, dict), "handoff request must be an object")
    _assert_no_forbidden_keys(request, "request")
    _require_exact_fields(request, REQUEST_FIELDS, "handoff request")
    _validate_common(request)
    _require(
        request.get("request_digest") == digest_json({key: value for key, value in request.items() if key != "request_digest"}),
        "request digest mismatch",
    )


def _request_projection(packet: dict[str, Any]) -> dict[str, Any]:
    request = {key: packet[key] for key in REQUEST_FIELDS}
    request["record_type"] = REQUEST_RECORD_TYPE
    request["schema_version"] = REQUEST_SCHEMA_VERSION
    return request


def _packet_without_digest(packet: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in packet.items() if key != "packet_digest"}


def build_handoff(request: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic, non-authorizing handoff packet."""

    validate_request(request)
    packet = dict(request)
    packet.update(
        {
            "record_type": PACKET_RECORD_TYPE,
            "schema_version": PACKET_SCHEMA_VERSION,
            "packet_status": PACKET_STATUS,
            "capture_status": CAPTURE_STATUS,
            "claim_ceiling": CLAIM_CEILING,
            "scientific_evidence": False,
        }
    )
    packet["packet_digest"] = digest_json(_packet_without_digest(packet))
    validate_packet(packet)
    return packet


def validate_packet(packet: dict[str, Any]) -> None:
    """Validate a generated packet, its request binding, and packet digest."""

    _require(isinstance(packet, dict), "handoff packet must be an object")
    _assert_no_forbidden_keys(packet, "packet")
    _require_exact_fields(packet, PACKET_FIELDS, "handoff packet")
    _require(packet.get("record_type") == PACKET_RECORD_TYPE, "wrong handoff packet record type")
    _require(packet.get("schema_version") == PACKET_SCHEMA_VERSION, "wrong handoff packet schema")
    _require(packet.get("packet_status") == PACKET_STATUS, "handoff packet must remain ready_for_external_runner")
    _require(packet.get("capture_status") == CAPTURE_STATUS, "handoff packet cannot contain a capture")
    _require(packet.get("claim_ceiling") == CLAIM_CEILING, "wrong claim ceiling")
    _require(packet.get("scientific_evidence") is False, "scientific evidence must be false")
    _require(packet.get("packet_digest") == digest_json(_packet_without_digest(packet)), "packet digest mismatch")
    request = _request_projection(packet)
    validate_request(request)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="plan-only handoff request JSON")
    parser.add_argument("--output", required=True, help="plan-only handoff packet JSON")
    args = parser.parse_args()
    try:
        request = json.loads(Path(args.input).read_text(encoding="utf-8"))
        packet = build_handoff(request)
        Path(args.output).write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, HandoffError) as exc:
        print(f"capture_handoff_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "packet": args.output,
                "packet_status": packet["packet_status"],
                "capture_status": packet["capture_status"],
                "claim_ceiling": packet["claim_ceiling"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Maintain a digest-chained operational ledger for one local campaign.

State slice: ``verified-metacognitive-control-campaign-ledger-v1``.

This is an operational artifact ledger, not the repository Evidence Ledger.
It records monotonic handoff state for the plan, execution bundle, validator
report, capture, protocol input, aggregate result, and campaign verification
report. It never executes an agent, mutates a checkout, grants authority, or
promotes scientific evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .campaign_verifier import CampaignVerificationError, verify_campaign
from .corpus_execution_launcher import LauncherError, validate_execution_plan
from .protocol import digest_json
from .repository_change_capture import _assert_no_forbidden_keys


LEDGER_STATE_SLICE = "verified-metacognitive-control-campaign-ledger-v1"
LEDGER_SCHEMA_VERSION = "verified-metacognitive-campaign-ledger-v1"
CLAIM_CEILING = "LocalDevelopmentCampaignLedgerOnly"
ZERO_DIGEST = "0" * 64
EVENT_TYPES = (
    "campaign_planned",
    "execution_attached",
    "validator_attached",
    "capture_attached",
    "protocol_input_attached",
    "result_attached",
    "campaign_verification_attached",
)
EVENT_KINDS = {
    "campaign_planned": ("execution_plan", None),
    "execution_attached": ("agent_execution_bundle", 301),
    "validator_attached": ("validator_report", 300),
    "capture_attached": ("capture_bundle", 301),
    "protocol_input_attached": ("protocol_input", 301),
    "result_attached": ("aggregate_result", None),
    "campaign_verification_attached": ("campaign_verification_report", None),
}


def _status_for_event(event_type: str) -> str:
    return "planned" if event_type == "campaign_planned" else event_type.removesuffix("_attached")


class CampaignLedgerError(ValueError):
    """Raised when the campaign operational ledger is malformed or out of order."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignLedgerError(message)


def _digest(value: Any, field: str) -> None:
    _require(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value),
        f"{field} must be lowercase SHA-256",
    )


def _unsigned_event(event: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in event.items() if key != "event_digest"}


def _unsigned_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in ledger.items() if key != "ledger_digest"}


def _event(
    sequence: int,
    event_type: str,
    artifact_digest: str,
    artifact_kind: str,
    previous_event_digest: str,
    record_count: int | None = None,
) -> dict[str, Any]:
    expected_kind, expected_count = EVENT_KINDS[event_type]
    _require(artifact_kind == expected_kind, f"wrong artifact kind for {event_type}")
    if expected_count is None:
        _require(record_count is None, f"record_count not allowed for {event_type}")
    else:
        _require(record_count == expected_count, f"{event_type} requires {expected_count} records")
    _digest(artifact_digest, "artifact_digest")
    _digest(previous_event_digest, "previous_event_digest")
    value: dict[str, Any] = {
        "sequence": sequence,
        "event_type": event_type,
        "artifact_kind": artifact_kind,
        "artifact_digest": artifact_digest,
        "previous_event_digest": previous_event_digest,
    }
    if record_count is not None:
        value["record_count"] = record_count
    value["event_digest"] = digest_json(value)
    return value


def initialize_ledger(execution_plan: dict[str, Any]) -> dict[str, Any]:
    """Create the immutable planned state from a validated execution plan."""

    try:
        validate_execution_plan(execution_plan)
    except LauncherError as exc:
        raise CampaignLedgerError(f"execution plan invalid: {exc}") from exc
    planned = _event(
        sequence=0,
        event_type="campaign_planned",
        artifact_digest=execution_plan["plan_digest"],
        artifact_kind="execution_plan",
        previous_event_digest=ZERO_DIGEST,
    )
    ledger: dict[str, Any] = {
        "record_type": "campaign_operational_ledger",
        "schema_version": LEDGER_SCHEMA_VERSION,
        "state_slice": LEDGER_STATE_SLICE,
        "workflow_id": execution_plan["workflow_id"],
        "execution_plan_digest": execution_plan["plan_digest"],
        "status": "planned",
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "scientific_evidence": False,
        "claim_ceiling": CLAIM_CEILING,
        "events": [planned],
        "non_claims": [
            "not_repository_evidence_ledger",
            "not_agent_execution",
            "not_validator_custody",
            "not_experiment_evidence",
            "not_production_ready",
            "not_authority",
        ],
    }
    ledger["ledger_digest"] = digest_json(ledger)
    return ledger


def append_event(
    ledger: dict[str, Any],
    event_type: str,
    artifact_digest: str,
    artifact_kind: str,
    record_count: int | None = None,
) -> dict[str, Any]:
    """Return a new ledger with exactly the next legal event appended."""

    validate_ledger(ledger)
    _require(event_type in EVENT_TYPES, f"unknown event type: {event_type}")
    events = ledger["events"]
    _require(len(events) < len(EVENT_TYPES), "campaign ledger is already complete")
    expected_type = EVENT_TYPES[len(events)]
    _require(event_type == expected_type, f"expected {expected_type}, received {event_type}")
    previous_digest = events[-1]["event_digest"]
    next_event = _event(
        sequence=len(events),
        event_type=event_type,
        artifact_digest=artifact_digest,
        artifact_kind=artifact_kind,
        previous_event_digest=previous_digest,
        record_count=record_count,
    )
    updated = dict(ledger)
    updated["events"] = [*events, next_event]
    updated["status"] = "verified_local_chain" if event_type == EVENT_TYPES[-1] else _status_for_event(event_type)
    updated["ledger_digest"] = digest_json(_unsigned_ledger(updated))
    validate_ledger(updated)
    return updated


def validate_ledger(ledger: dict[str, Any]) -> None:
    """Validate envelope, event sequence, hash chain, and claim boundary."""

    _require(isinstance(ledger, dict), "campaign ledger must be an object")
    _assert_no_forbidden_keys(ledger, "campaign_operational_ledger")
    _require(ledger.get("record_type") == "campaign_operational_ledger", "wrong ledger record type")
    _require(ledger.get("schema_version") == LEDGER_SCHEMA_VERSION, "wrong ledger schema")
    _require(ledger.get("state_slice") == LEDGER_STATE_SLICE, "wrong ledger state slice")
    _require(isinstance(ledger.get("workflow_id"), str) and ledger["workflow_id"], "workflow_id required")
    _require(ledger.get("status") in {"planned", "execution", "validator", "capture", "protocol_input", "result", "verified_local_chain"}, "invalid ledger status")
    _require(ledger.get("authority_granted") is False, "ledger authority must be false")
    _require(ledger.get("network_access") is False, "ledger network access must be false")
    _require(ledger.get("raw_reasoning_retained") is False, "ledger raw reasoning retention must be false")
    _require(ledger.get("scientific_evidence") is False, "ledger cannot claim scientific evidence")
    _require(ledger.get("claim_ceiling") == CLAIM_CEILING, "wrong ledger claim ceiling")
    _digest(ledger.get("execution_plan_digest"), "execution_plan_digest")
    _digest(ledger.get("ledger_digest"), "ledger_digest")
    events = ledger.get("events")
    _require(isinstance(events, list) and events, "ledger events required")
    _require(len(events) <= len(EVENT_TYPES), "ledger has too many events")
    previous = ZERO_DIGEST
    for expected_sequence, event in enumerate(events):
        _require(isinstance(event, dict), f"event {expected_sequence} must be an object")
        _require(event.get("sequence") == expected_sequence, f"event {expected_sequence} sequence mismatch")
        _require(event.get("event_type") == EVENT_TYPES[expected_sequence], f"event {expected_sequence} type mismatch")
        expected_kind, expected_count = EVENT_KINDS[event["event_type"]]
        _require(event.get("artifact_kind") == expected_kind, f"event {expected_sequence} artifact kind mismatch")
        _digest(event.get("artifact_digest"), f"event {expected_sequence}.artifact_digest")
        _require(event.get("previous_event_digest") == previous, f"event {expected_sequence} previous digest mismatch")
        if expected_count is None:
            _require("record_count" not in event, f"event {expected_sequence} record count is not allowed")
        else:
            _require(event.get("record_count") == expected_count, f"event {expected_sequence} record count mismatch")
        _digest(event.get("event_digest"), f"event {expected_sequence}.event_digest")
        _require(digest_json(_unsigned_event(event)) == event["event_digest"], f"event {expected_sequence} digest mismatch")
        previous = event["event_digest"]
    _require(digest_json(_unsigned_ledger(ledger)) == ledger["ledger_digest"], "ledger digest mismatch")
    _require(ledger["execution_plan_digest"] == events[0]["artifact_digest"], "plan digest anchor mismatch")
    expected_status = "verified_local_chain" if len(events) == len(EVENT_TYPES) else _status_for_event(EVENT_TYPES[len(events) - 1])
    _require(ledger["status"] == expected_status, "ledger status does not match event frontier")


def _load_json(path: str | Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignLedgerError(f"invalid {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _load_jsonl(path: str | Path, label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with Path(path).open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if line.strip():
                    value = json.loads(line)
                    _require(isinstance(value, dict), f"{label} line {line_number} must be an object")
                    records.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignLedgerError(f"invalid {label}: {exc}") from exc
    _require(records, f"{label} is empty")
    return records


def build_verified_ledger(
    execution_plan_path: str | Path,
    validator_report_path: str | Path,
    agent_records_path: str | Path,
    capture_path: str | Path,
    protocol_input_path: str | Path,
    result_path: str | Path,
    verification_path: str | Path,
) -> dict[str, Any]:
    """Verify the campaign and materialize its complete local state ledger."""

    plan = _load_json(execution_plan_path, "execution plan")
    verification = verify_campaign(
        execution_plan_path,
        validator_report_path,
        agent_records_path,
        capture_path,
        protocol_input_path,
        result_path,
    )
    supplied_verification = _load_json(verification_path, "campaign verification report")
    _require(supplied_verification == verification, "campaign verification report is not deterministic")
    execution_records = _load_jsonl(agent_records_path, "agent execution bundle")
    validator_report = _load_json(validator_report_path, "validator report")
    capture_records = _load_jsonl(capture_path, "capture bundle")
    protocol_records = _load_jsonl(protocol_input_path, "protocol input")
    result = _load_json(result_path, "aggregate result")
    ledger = initialize_ledger(plan)
    ledger = append_event(
        ledger,
        "execution_attached",
        digest_json(execution_records),
        "agent_execution_bundle",
        len(execution_records),
    )
    ledger = append_event(
        ledger,
        "validator_attached",
        validator_report["report_digest"],
        "validator_report",
        len(validator_report["rows"]),
    )
    ledger = append_event(
        ledger,
        "capture_attached",
        digest_json(capture_records),
        "capture_bundle",
        len(capture_records),
    )
    ledger = append_event(
        ledger,
        "protocol_input_attached",
        digest_json(protocol_records),
        "protocol_input",
        len(protocol_records),
    )
    ledger = append_event(ledger, "result_attached", result["result_digest"], "aggregate_result")
    ledger = append_event(
        ledger,
        "campaign_verification_attached",
        verification["report_digest"],
        "campaign_verification_report",
    )
    validate_ledger(ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution-plan", required=True)
    parser.add_argument("--validator-report", required=True)
    parser.add_argument("--agent-records", required=True)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--protocol-input", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--campaign-verification", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        ledger = build_verified_ledger(
            args.execution_plan,
            args.validator_report,
            args.agent_records,
            args.capture,
            args.protocol_input,
            args.result,
            args.campaign_verification,
        )
        Path(args.output).write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (
        OSError,
        CampaignLedgerError,
        CampaignVerificationError,
        json.JSONDecodeError,
    ) as exc:
        print(f"campaign_ledger_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": ledger["status"],
                "events": len(ledger["events"]),
                "claim_ceiling": ledger["claim_ceiling"],
                "ledger_digest": ledger["ledger_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

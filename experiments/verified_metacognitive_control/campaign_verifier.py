"""Verify the complete metacognitive-control artifact chain.

State slice: ``verified-metacognitive-control-campaign-verification-v1``.

This module verifies consistency between already-produced local artifacts. It
does not execute an agent, run a provider, mutate a checkout, infer missing
rows, or promote a result. Its output is a structural campaign-verification
report only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .corpus_execution_launcher import LauncherError, validate_execution_plan
from .execution_record_validator import ExecutionRecordError, validate_plan_bound_records
from .paired_execution_join import (
    JoinError,
    join,
    load_agent_records,
    load_validator_report,
)
from .protocol import ProtocolError, digest_json, evaluate, load_input
from .repository_change_capture import CaptureError, convert, load_capture
from .validate_result import validate as validate_result


VERIFICATION_STATE_SLICE = "verified-metacognitive-control-campaign-verification-v1"
VERIFICATION_SCHEMA_VERSION = "verified-metacognitive-campaign-verification-v1"
CLAIM_CEILING = "LocalDevelopmentCampaignVerificationOnly"


class CampaignVerificationError(ValueError):
    """Raised when the local artifact chain is inconsistent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignVerificationError(message)


def _load_object(path: str | Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignVerificationError(f"invalid {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _load_jsonl(path: str | Path, label: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with Path(path).open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                _require(isinstance(value, dict), f"{label} line {line_number} must be an object")
                records.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignVerificationError(f"invalid {label}: {exc}") from exc
    _require(records, f"{label} is empty")
    return records


def _digest_records(records: list[dict[str, Any]], label: str) -> str:
    _require(records, f"{label} is empty")
    return digest_json(records)


def verify_campaign(
    execution_plan_path: str | Path,
    validator_report_path: str | Path,
    agent_records_path: str | Path,
    capture_path: str | Path,
    protocol_input_path: str | Path,
    result_path: str | Path,
) -> dict[str, Any]:
    """Verify every handoff in the local campaign artifact chain."""

    execution_plan = _load_object(execution_plan_path, "execution plan")
    try:
        validate_execution_plan(execution_plan)
    except LauncherError as exc:
        raise CampaignVerificationError(f"execution plan invalid: {exc}") from exc

    execution_manifest, agent_records = load_agent_records(agent_records_path)
    try:
        validate_plan_bound_records(execution_plan, execution_manifest, agent_records)
    except ExecutionRecordError as exc:
        raise CampaignVerificationError(f"plan-bound execution invalid: {exc}") from exc

    validator_report = load_validator_report(
        validator_report_path,
        execution_manifest["validator_report_digest"],
    )
    joined_records = join(validator_report, execution_manifest, agent_records)

    capture_records = _load_jsonl(capture_path, "capture")
    _require(capture_records == joined_records, "capture does not match the deterministic validator/agent join")
    try:
        load_capture(capture_path)
    except (OSError, CaptureError, json.JSONDecodeError) as exc:
        raise CampaignVerificationError(f"capture validation failed: {exc}") from exc

    expected_protocol_records = convert(capture_path)
    protocol_records = _load_jsonl(protocol_input_path, "protocol input")
    _require(
        protocol_records == expected_protocol_records,
        "protocol input does not match deterministic capture conversion",
    )
    try:
        expected_result = evaluate(load_input(protocol_input_path))
    except (OSError, ProtocolError, json.JSONDecodeError) as exc:
        raise CampaignVerificationError(f"protocol evaluation failed: {exc}") from exc
    actual_result = _load_object(result_path, "aggregate result")
    result_errors = validate_result(
        actual_result,
        expected_result,
        allow_campaign_verification_pending=True,
    )
    _require(not result_errors, f"aggregate result failed validation: {result_errors}")

    report: dict[str, Any] = {
        "record_type": "campaign_verification_report",
        "schema_version": VERIFICATION_SCHEMA_VERSION,
        "state_slice": VERIFICATION_STATE_SLICE,
        "workflow_id": execution_plan["workflow_id"],
        "execution_plan_digest": execution_plan["plan_digest"],
        "validator_report_digest": execution_manifest["validator_report_digest"],
        "capture_digest": _digest_records(capture_records, "capture"),
        "protocol_input_digest": _digest_records(protocol_records, "protocol input"),
        "result_digest": actual_result["result_digest"],
        "planned_execution_count": execution_plan["planned_execution_count"],
        "joined_record_count": len(joined_records),
        "stages": {
            "execution_plan_valid": True,
            "plan_bound_execution_valid": True,
            "validator_report_valid": True,
            "capture_matches_join": True,
            "protocol_input_matches_capture_conversion": True,
            "result_recomputes": True,
        },
        "valid": True,
        "claim_ceiling": CLAIM_CEILING,
        "scientific_evidence": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "non_claims": [
            "not_agent_execution",
            "not_validator_custody",
            "not_experiment_evidence",
            "not_production_ready",
            "not_authority",
        ],
    }
    report["report_digest"] = digest_json(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution-plan", required=True)
    parser.add_argument("--validator-report", required=True)
    parser.add_argument("--agent-records", required=True)
    parser.add_argument("--capture", required=True)
    parser.add_argument("--protocol-input", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        report = verify_campaign(
            args.execution_plan,
            args.validator_report,
            args.agent_records,
            args.capture,
            args.protocol_input,
            args.result,
        )
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (
        OSError,
        CampaignVerificationError,
        CaptureError,
        JoinError,
        ProtocolError,
        json.JSONDecodeError,
    ) as exc:
        print(f"campaign_verification_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "valid": report["valid"],
                "claim_ceiling": report["claim_ceiling"],
                "report_digest": report["report_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

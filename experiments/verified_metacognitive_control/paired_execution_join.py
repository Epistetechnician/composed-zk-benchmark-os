"""Join validator reports with independently recorded paired agent runs.

State slice: ``verified-metacognitive-control-paired-execution-v1``.

The joiner is the handoff boundary between a read-only validator and the
aggregate experiment. It requires a digest-valid validator report, one
prediction-locked agent record for every validator row, distinct workspace and
run digests, and explicit no-authority/no-raw-retention flags. It emits the
capture schema; it does not execute an agent, infer outcomes, or promote a
result.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

from .protocol import (
    DECISIONS,
    PROMOTION_ARMS,
    SIGNAL_SOURCES,
    SPLITS,
    digest_json,
)
from .repository_change_capture import (
    CAPTURE_SCHEMA_VERSION,
    CAPTURE_STATE_SLICE,
    REQUIRED_CHECK_IDS,
    CaptureError,
    _assert_no_forbidden_keys,
    validate_capture_manifest,
    validate_observation,
    write_jsonl,
)
from .execution_record_validator import ExecutionRecordError, validate_plan_bound_records

JOIN_STATE_SLICE = "verified-metacognitive-control-paired-execution-v1"
EXECUTION_SCHEMA_VERSION = "verified-metacognitive-agent-execution-v1"
VALIDATOR_REPORT_SCHEMA_VERSION = "verified-metacognitive-repository-validator-report-v1"


class JoinError(ValueError):
    """Raised when validator and agent records cannot be joined safely."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise JoinError(message)


def _sha256(value: Any, field: str) -> None:
    _require(isinstance(value, str) and len(value) == 64, f"{field} must be a SHA-256 hex digest")
    _require(all(character in "0123456789abcdef" for character in value), f"{field} must be lowercase hexadecimal")


def _load_json(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JoinError(f"invalid JSON document: {path}: {exc}") from exc
    _require(isinstance(value, dict), f"JSON document must be an object: {path}")
    return value


def validate_execution_manifest(manifest: dict[str, Any]) -> None:
    _require(isinstance(manifest, dict), "agent execution manifest must be an object")
    _assert_no_forbidden_keys(manifest, "agent_execution_manifest")
    _require(manifest.get("record_type") == "agent_execution_manifest", "wrong agent execution record type")
    _require(manifest.get("schema_version") == EXECUTION_SCHEMA_VERSION, "wrong agent execution schema")
    _require(manifest.get("state_slice") == JOIN_STATE_SLICE, "wrong paired execution state slice")
    _require(isinstance(manifest.get("workflow_id"), str) and manifest["workflow_id"], "workflow_id required")
    _require(manifest.get("fixed_budget") is True, "fixed budget required")
    _require(manifest.get("prediction_locked_before_assessment") is True, "prediction locking required")
    _require(manifest.get("agent_execution_recorded") is True, "agent execution required")
    _require(manifest.get("validator_custody") is True, "validator custody required")
    for field in (
        "model_digest",
        "runtime_digest",
        "checker_digest",
        "validator_report_digest",
        "execution_plan_digest",
    ):
        _sha256(manifest.get(field), field)
    for field in ("raw_reasoning_retained", "authority_granted", "network_access"):
        _require(manifest.get(field) is False, f"{field} must be false")
    _require(manifest.get("arms") == list(PROMOTION_ARMS), "paired execution must use the frozen promotion arms")
    _require(manifest.get("required_check_ids") == list(REQUIRED_CHECK_IDS), "required check ids drifted")
    budget = manifest.get("budget")
    _require(isinstance(budget, dict), "budget required")
    for field in ("max_latency_ms", "max_compute_units", "max_tool_calls", "max_attempts"):
        _require(
            isinstance(budget.get(field), int)
            and not isinstance(budget[field], bool)
            and budget[field] > 0,
            f"positive budget required: {field}",
        )


def validate_agent_record(record: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require(isinstance(record, dict), "agent execution record must be an object")
    _require(isinstance(manifest, dict), "agent execution manifest must be an object")
    _assert_no_forbidden_keys(record, "agent_execution_record")
    required = (
        "record_type", "case_id", "task_family", "split", "arm", "decision",
        "monitor_score_milli", "monitor_signal_source", "candidate_workspace_digest",
        "agent_run_digest", "task_spec_digest", "controller_config_digest",
        "workflow_id", "execution_plan_digest", "source_corpus_digest", "task_digest", "arm_digest",
        "prediction_locked_before_assessment", "raw_reasoning_retained",
        "authority_granted", "network_access",
    )
    for field in required:
        _require(field in record, f"agent record missing {field}")
    _require(record["record_type"] == "agent_execution_record", "wrong agent record type")
    for field in ("workflow_id", "case_id", "task_family"):
        _require(isinstance(record[field], str) and record[field], f"{field} required")
    _require(record["split"] in SPLITS, "invalid agent split")
    _require(record["arm"] in manifest["arms"], "agent arm not declared")
    _require(record["decision"] in DECISIONS, "invalid agent decision")
    _require(
        isinstance(record["monitor_score_milli"], int)
        and not isinstance(record["monitor_score_milli"], bool)
        and 0 <= record["monitor_score_milli"] <= 1000,
        "agent monitor score out of range",
    )
    _require(record["monitor_signal_source"] in SIGNAL_SOURCES, "invalid agent signal source")
    for field in (
        "candidate_workspace_digest",
        "agent_run_digest",
        "task_spec_digest",
        "controller_config_digest",
        "execution_plan_digest",
        "source_corpus_digest",
        "task_digest",
        "arm_digest",
    ):
        _sha256(record[field], field)
    _require(record["prediction_locked_before_assessment"] is True, "agent prediction must be locked")
    for field in ("raw_reasoning_retained", "authority_granted", "network_access"):
        _require(record[field] is False, f"agent {field} must be false")


def validate_validator_row(row: dict[str, Any]) -> None:
    """Validate every validator field consumed by the join."""

    _require(isinstance(row, dict), "validator row must be an object")
    required = (
        "record_type", "case_id", "task_family", "split", "arm", "check_results",
        "scope_valid", "provenance_valid", "timed_out", "budget_exhausted",
        "capability_gap", "safe_abstention", "latency_ms", "compute_units",
        "tool_calls", "attempts", "monitor_overhead_ms", "monitor_compute_units",
    )
    for field in required:
        _require(field in row, f"validator row missing {field}")
    _require(row["record_type"] == "validator_observation", "wrong validator row type")
    for field in ("case_id", "task_family"):
        _require(isinstance(row[field], str) and row[field], f"validator row {field} required")
    _require(row["split"] in SPLITS, "validator row split invalid")
    _require(row["arm"] in PROMOTION_ARMS, "validator row arm invalid")
    check_results = row["check_results"]
    _require(isinstance(check_results, dict), "validator check results required")
    _require(set(check_results) == set(REQUIRED_CHECK_IDS), "validator check ids drifted")
    _require(
        all(status in {"pass", "fail", "not_run"} for status in check_results.values()),
        "invalid validator check status",
    )
    for field in (
        "scope_valid", "provenance_valid", "timed_out", "budget_exhausted",
        "capability_gap", "safe_abstention",
    ):
        _require(isinstance(row[field], bool), f"validator row {field} must be boolean")
    for field in ("latency_ms", "compute_units", "monitor_overhead_ms", "monitor_compute_units"):
        _require(
            isinstance(row[field], (int, float))
            and not isinstance(row[field], bool)
            and math.isfinite(row[field])
            and row[field] >= 0,
            f"validator row {field} must be finite and nonnegative",
        )
    for field in ("tool_calls", "attempts"):
        _require(
            isinstance(row[field], int) and not isinstance(row[field], bool) and row[field] >= 0,
            f"validator row {field} must be a nonnegative integer",
        )
    _require(row["monitor_overhead_ms"] <= row["latency_ms"], "validator monitor latency exceeds total")
    _require(row["monitor_compute_units"] <= row["compute_units"], "validator monitor compute exceeds total")


def load_agent_records(path: str | Path) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    records: list[dict[str, Any]] = []
    try:
        with Path(path).open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if line.strip():
                    value = json.loads(line)
                    _require(isinstance(value, dict), f"agent record at line {line_number} must be an object")
                    records.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise JoinError(f"invalid agent records: {exc}") from exc
    _require(records, "agent records are empty")
    manifest = records[0]
    validate_execution_manifest(manifest)
    agent_records = tuple(records[1:])
    _require(agent_records, "agent records require at least one execution row")
    seen: set[tuple[str, str, str]] = set()
    workspace_digests: set[str] = set()
    run_digests: set[str] = set()
    for record in agent_records:
        validate_agent_record(record, manifest)
        key = (record["case_id"], record["split"], record["arm"])
        _require(key not in seen, f"duplicate agent execution row: {key}")
        _require(record["candidate_workspace_digest"] not in workspace_digests, "workspace digest reused across paired rows")
        _require(record["agent_run_digest"] not in run_digests, "agent run digest reused across paired rows")
        seen.add(key)
        workspace_digests.add(record["candidate_workspace_digest"])
        run_digests.add(record["agent_run_digest"])
    return manifest, agent_records


def load_validator_report(path: str | Path, expected_digest: str) -> dict[str, Any]:
    report = _load_json(path)
    _require(report.get("record_type") == "validator_report", "wrong validator report type")
    _require(report.get("schema_version") == VALIDATOR_REPORT_SCHEMA_VERSION, "wrong validator report schema")
    _require(report.get("state_slice") == "verified-metacognitive-control-repository-validator-v1", "validator state slice drifted")
    _require(report.get("capture_state_slice") == CAPTURE_STATE_SLICE, "validator capture state slice drifted")
    _require(report.get("validator_custody") is True, "validator custody missing")
    _require(report.get("agent_execution_recorded") is False, "validator report must precede agent join")
    for field in ("authority_granted", "network_access", "raw_reasoning_retained"):
        _require(report.get(field) is False, f"validator report {field} must be false")
    declared_digest = report.get("report_digest")
    _sha256(declared_digest, "report_digest")
    unsigned = dict(report)
    unsigned.pop("report_digest")
    _require(digest_json(unsigned) == declared_digest, "validator report digest mismatch")
    _require(declared_digest == expected_digest, "agent manifest validator digest does not match report")
    rows = report.get("rows")
    _require(isinstance(rows, list) and rows, "validator report rows required")
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        _require(isinstance(row, dict), "validator report row must be an object")
        validate_validator_row(row)
        key = (row.get("case_id"), row.get("split"), row.get("arm"))
        _require(all(isinstance(part, str) and part for part in key), "validator row identity required")
        _require(key not in seen, f"duplicate validator row: {key}")
        seen.add(key)
    return report


def join(report: dict[str, Any], execution_manifest: dict[str, Any], agent_records: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    _require(report["workflow_id"] == execution_manifest["workflow_id"], "workflow id mismatch")
    for row in report["rows"]:
        validate_validator_row(row)
    validator_rows = {
        (row["case_id"], row["split"], row["arm"]): row
        for row in report["rows"]
    }
    agent_rows = {
        (row["case_id"], row["split"], row["arm"]): row
        for row in agent_records
    }
    _require(set(agent_rows) == set(validator_rows), "agent and validator row coverage mismatch")
    observations: list[dict[str, Any]] = []
    for key in sorted(validator_rows):
        validator_row = validator_rows[key]
        agent_row = agent_rows[key]
        _require(
            agent_row["task_family"] == validator_row["task_family"],
            f"task family mismatch: {key}",
        )
        observations.append(
            {
                "record_type": "observation",
                "case_id": validator_row["case_id"],
                "task_family": validator_row["task_family"],
                "split": validator_row["split"],
                "arm": validator_row["arm"],
                "decision": agent_row["decision"],
                "monitor_score_milli": agent_row["monitor_score_milli"],
                "monitor_signal_source": agent_row["monitor_signal_source"],
                "check_results": {
                    check_id: validator_row["check_results"][check_id]
                    for check_id in REQUIRED_CHECK_IDS
                },
                "scope_valid": validator_row["scope_valid"],
                "provenance_valid": validator_row["provenance_valid"],
                "timed_out": validator_row["timed_out"],
                "budget_exhausted": validator_row["budget_exhausted"],
                "capability_gap": validator_row["capability_gap"],
                "safe_abstention": validator_row["safe_abstention"],
                "latency_ms": validator_row["latency_ms"],
                "compute_units": validator_row["compute_units"],
                "tool_calls": validator_row["tool_calls"],
                "attempts": validator_row["attempts"],
                "monitor_overhead_ms": validator_row["monitor_overhead_ms"],
                "monitor_compute_units": validator_row["monitor_compute_units"],
                "prediction_locked_before_assessment": agent_row["prediction_locked_before_assessment"],
                "raw_reasoning_retained": agent_row["raw_reasoning_retained"],
                "authority_granted": agent_row["authority_granted"],
                "network_access": agent_row["network_access"],
            }
        )
    capture_manifest = {
        "record_type": "capture_manifest",
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "state_slice": CAPTURE_STATE_SLICE,
        "workflow_id": execution_manifest["workflow_id"],
        "fixed_budget": execution_manifest["fixed_budget"],
        "budget": execution_manifest["budget"],
        "arms": execution_manifest["arms"],
        "required_check_ids": list(REQUIRED_CHECK_IDS),
        "prediction_locked_before_assessment": execution_manifest["prediction_locked_before_assessment"],
        "agent_execution_recorded": True,
        "validator_custody": True,
        "validator_report_digest": execution_manifest["validator_report_digest"],
        "execution_plan_digest": execution_manifest["execution_plan_digest"],
        "model_digest": execution_manifest["model_digest"],
        "runtime_digest": execution_manifest["runtime_digest"],
        "checker_digest": execution_manifest["checker_digest"],
        "raw_reasoning_retained": False,
        "authority_granted": False,
        "network_access": False,
    }
    validate_capture_manifest(capture_manifest)
    for observation in observations:
        validate_observation(observation, capture_manifest)
    return [capture_manifest, *observations]


def join_files(
    validator_path: str | Path,
    agent_path: str | Path,
    execution_plan_path: str | Path,
) -> list[dict[str, Any]]:
    execution_manifest, agent_records = load_agent_records(agent_path)
    report = load_validator_report(validator_path, execution_manifest["validator_report_digest"])
    execution_plan = _load_json(execution_plan_path)
    try:
        validate_plan_bound_records(execution_plan, execution_manifest, agent_records)
    except ExecutionRecordError as exc:
        raise JoinError(str(exc)) from exc
    return join(report, execution_manifest, agent_records)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validator-report", required=True)
    parser.add_argument("--agent-records", required=True)
    parser.add_argument("--execution-plan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        records = join_files(args.validator_report, args.agent_records, args.execution_plan)
        write_jsonl(args.output, records)
    except (OSError, JoinError, CaptureError) as exc:
        print(f"join_error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"records_written": len(records), "output": args.output, "claim_ceiling": "LocalDevelopmentPairedCaptureOnly"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

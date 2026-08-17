"""Convert validator-owned repository observations into experiment trials.

State slice: ``verified-metacognitive-control-repository-workflow-v1``.

The adapter is deliberately process-free. A separately controlled workflow
runner supplies aggregate check statuses and resource measurements; this module
derives the outcome, strips no data because raw data are rejected at ingress,
binds the row to model/runtime/checker digests, and emits the frozen experiment
input schema. It never executes a command, changes a checkout, grants
authority, or retains prompts and model outputs.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from .protocol import (
    ARMS,
    DECISIONS,
    INPUT_SCHEMA_VERSION,
    SIGNAL_SOURCES,
    SPLITS,
    STATE_SLICE,
    ProtocolError,
    digest_json,
    validate_manifest,
    validate_trial,
)

CAPTURE_STATE_SLICE = "verified-metacognitive-control-repository-workflow-v1"
CAPTURE_SCHEMA_VERSION = "verified-metacognitive-repository-observation-v1"
REQUIRED_CHECK_IDS = (
    "format",
    "focused_tests",
    "contract_validation",
    "diff_hygiene",
    "claim_boundary",
)
CHECK_STATUSES = {"pass", "fail", "not_run"}
FORBIDDEN_KEY_TOKENS = (
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
ALLOWED_REASONING_KEY = "raw_reasoning_retained"


class CaptureError(ValueError):
    """Raised when a validator observation violates the capture contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CaptureError(message)


def _nonnegative_number(value: Any, field: str) -> None:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    _require(math.isfinite(value), f"{field} must be finite")
    _require(value >= 0, f"{field} must be nonnegative")


def _nonnegative_integer(value: Any, field: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{field} must be a nonnegative integer")


def _require_sha256(value: Any, field: str) -> None:
    _require(isinstance(value, str) and len(value) == 64, f"{field} must be a SHA-256 hex digest")
    _require(all(character in "0123456789abcdef" for character in value), f"{field} must be lowercase hexadecimal")


def _assert_no_forbidden_keys(value: Any, path: str = "observation") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key).lower()
            if key != ALLOWED_REASONING_KEY and any(token in key_text for token in FORBIDDEN_KEY_TOKENS):
                raise CaptureError(f"raw or sensitive field forbidden: {path}.{key}")
            _assert_no_forbidden_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_no_forbidden_keys(nested, f"{path}[{index}]")


def validate_capture_manifest(manifest: dict[str, Any]) -> None:
    _require(isinstance(manifest, dict), "capture manifest must be an object")
    _require(manifest.get("record_type") == "capture_manifest", "first capture record must be a capture_manifest")
    _require(manifest.get("schema_version") == CAPTURE_SCHEMA_VERSION, "wrong capture schema version")
    _require(manifest.get("state_slice") == CAPTURE_STATE_SLICE, "wrong capture state slice")
    _require(isinstance(manifest.get("workflow_id"), str) and manifest["workflow_id"], "workflow_id required")
    _require(manifest.get("fixed_budget") is True, "repository capture requires a fixed budget")
    _require(manifest.get("prediction_locked_before_assessment") is True, "repository capture requires prediction locking")
    _require(manifest.get("raw_reasoning_retained") is False, "raw reasoning retention forbidden")
    _require(manifest.get("authority_granted") is False, "authority grant forbidden")
    _require(manifest.get("network_access") is False, "network access forbidden")
    _require(manifest.get("agent_execution_recorded") is True, "agent execution is required")
    _require(manifest.get("validator_custody") is True, "validator custody is required")
    _require_sha256(manifest.get("validator_report_digest"), "validator_report_digest")
    for field in ("model_digest", "runtime_digest", "checker_digest"):
        _require_sha256(manifest.get(field), field)
    budget = manifest.get("budget")
    _require(isinstance(budget, dict), "budget required")
    for field in ("max_latency_ms", "max_compute_units", "max_tool_calls", "max_attempts"):
        _require(
            isinstance(budget.get(field), int)
            and not isinstance(budget[field], bool)
            and budget[field] > 0,
            f"positive integer budget required: {field}",
        )
    arms = manifest.get("arms")
    _require(isinstance(arms, list) and arms and len(set(arms)) == len(arms), "unique arms required")
    for arm in arms:
        _require(arm in ARMS, f"unknown arm: {arm}")
    _require("baseline" in arms, "baseline arm required")
    declared_checks = manifest.get("required_check_ids")
    _require(declared_checks == list(REQUIRED_CHECK_IDS), "required check ids must match the frozen order")
    _assert_no_forbidden_keys(manifest, "manifest")


def validate_observation(observation: dict[str, Any], manifest: dict[str, Any]) -> None:
    _require(isinstance(observation, dict), "observation must be an object")
    _assert_no_forbidden_keys(observation)
    required = (
        "record_type",
        "case_id",
        "task_family",
        "split",
        "arm",
        "decision",
        "monitor_score_milli",
        "monitor_signal_source",
        "check_results",
        "scope_valid",
        "provenance_valid",
        "timed_out",
        "budget_exhausted",
        "capability_gap",
        "safe_abstention",
        "latency_ms",
        "compute_units",
        "tool_calls",
        "attempts",
        "monitor_overhead_ms",
        "monitor_compute_units",
        "prediction_locked_before_assessment",
        "raw_reasoning_retained",
        "authority_granted",
        "network_access",
    )
    for field in required:
        _require(field in observation, f"missing observation field: {field}")
    _require(observation["record_type"] == "observation", "non-observation record after capture manifest")
    for field in ("case_id", "task_family"):
        _require(isinstance(observation[field], str) and observation[field], f"{field} required")
    _require(observation["split"] in SPLITS, f"wrong split: {observation['split']}")
    _require(observation["arm"] in manifest["arms"], f"arm not declared: {observation['arm']}")
    _require(observation["decision"] in DECISIONS, f"wrong decision: {observation['decision']}")
    _require(
        isinstance(observation["monitor_score_milli"], int)
        and not isinstance(observation["monitor_score_milli"], bool)
        and 0 <= observation["monitor_score_milli"] <= 1000,
        "monitor score must be in [0, 1000]",
    )
    _require(observation["monitor_signal_source"] in SIGNAL_SOURCES, "wrong monitor signal source")
    check_results = observation["check_results"]
    _require(isinstance(check_results, dict), "check_results must be an object")
    _require(
        set(check_results) == set(REQUIRED_CHECK_IDS),
        "check_results must contain exactly the frozen check ids",
    )
    for check_id, status in check_results.items():
        _require(status in CHECK_STATUSES, f"wrong status for {check_id}: {status}")
    for field in ("scope_valid", "provenance_valid", "timed_out", "budget_exhausted", "capability_gap", "safe_abstention", "prediction_locked_before_assessment", "raw_reasoning_retained", "authority_granted", "network_access"):
        _require(isinstance(observation[field], bool), f"{field} must be boolean")
    _require(observation["prediction_locked_before_assessment"] is True, "assessment prediction must be locked")
    _require(observation["raw_reasoning_retained"] is False, "raw reasoning retention forbidden")
    _require(observation["authority_granted"] is False, "authority grant forbidden")
    _require(observation["network_access"] is False, "network access forbidden")
    for field in ("latency_ms", "compute_units", "monitor_overhead_ms", "monitor_compute_units"):
        _nonnegative_number(observation[field], field)
    for field in ("tool_calls", "attempts"):
        _nonnegative_integer(observation[field], field)
    _require(observation["monitor_overhead_ms"] <= observation["latency_ms"], "monitor latency exceeds total latency")
    _require(observation["monitor_compute_units"] <= observation["compute_units"], "monitor compute exceeds total compute")


def derive_outcome(observation: dict[str, Any]) -> str:
    """Derive the final label from validator-owned facts, never self-report."""

    checks_green = all(status == "pass" for status in observation["check_results"].values())
    if (
        not observation["scope_valid"]
        or not observation["provenance_valid"]
        or observation["timed_out"]
        or observation["budget_exhausted"]
    ):
        return "costly_failure"
    if observation["capability_gap"]:
        return "capability_gap"
    if observation["safe_abstention"] and observation["decision"] == "abstain":
        return "safe_abstention"
    if checks_green:
        return "success"
    return "ordinary_failure"


def observation_to_trial(observation: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    validate_observation(observation, manifest)
    trial = {
        "record_type": "trial",
        "case_id": observation["case_id"],
        "task_family": observation["task_family"],
        "split": observation["split"],
        "arm": observation["arm"],
        "decision": observation["decision"],
        "outcome": derive_outcome(observation),
        "costly_failure": False,
        "latency_ms": observation["latency_ms"],
        "compute_units": observation["compute_units"],
        "tool_calls": observation["tool_calls"],
        "attempts": observation["attempts"],
        "monitor_overhead_ms": observation["monitor_overhead_ms"],
        "monitor_compute_units": observation["monitor_compute_units"],
        "monitor_signal_source": observation["monitor_signal_source"],
        "monitor_score_milli": observation["monitor_score_milli"],
        "prediction_locked_before_assessment": observation["prediction_locked_before_assessment"],
        "raw_reasoning_retained": observation["raw_reasoning_retained"],
        "authority_granted": observation["authority_granted"],
        "network_access": observation["network_access"],
        "model_digest": manifest["model_digest"],
        "runtime_digest": manifest["runtime_digest"],
        "checker_digest": manifest["checker_digest"],
    }
    trial["costly_failure"] = trial["outcome"] == "costly_failure"
    trial["record_digest"] = digest_json(trial)
    validate_trial(trial, protocol_manifest(manifest))
    return trial


def protocol_manifest(capture_manifest: dict[str, Any]) -> dict[str, Any]:
    """Map the capture manifest to the frozen evaluator manifest."""

    manifest = dict(capture_manifest)
    manifest.update(
        {
            "record_type": "manifest",
            "schema_version": INPUT_SCHEMA_VERSION,
            "state_slice": STATE_SLICE,
            "source_type": "live_workflow_capture",
        }
    )
    validate_manifest(manifest)
    return manifest


def load_capture(path: str | Path) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    records: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise CaptureError(f"invalid JSON at line {line_number}: {exc}") from exc
    _require(records, "capture input is empty")
    manifest = records[0]
    validate_capture_manifest(manifest)
    observations = tuple(records[1:])
    _require(observations, "at least one observation required")
    for observation in observations:
        validate_observation(observation, manifest)
    return manifest, observations


def convert(path: str | Path) -> list[dict[str, Any]]:
    capture_manifest, observations = load_capture(path)
    manifest = protocol_manifest(capture_manifest)
    trials = [observation_to_trial(observation, capture_manifest) for observation in observations]
    return [manifest, *trials]


def write_jsonl(path: str | Path, records: list[dict[str, Any]]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="capture manifest plus validator observations")
    parser.add_argument("--output", required=True, help="frozen experiment manifest plus aggregate trials")
    args = parser.parse_args()
    try:
        records = convert(args.input)
        write_jsonl(args.output, records)
    except (OSError, CaptureError, ProtocolError, json.JSONDecodeError) as exc:
        print(f"capture_error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"records_written": len(records), "output": args.output}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

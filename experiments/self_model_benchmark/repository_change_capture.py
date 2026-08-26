"""Convert validator-owned repository observations into self-model trials.

State slice: ``verified-self-model-benchmark-repository-capture-v1``.

This adapter is process-free. A separately controlled repository workflow
supplies aggregate check results, resource measurements, forecasts, and
validator-owned labels. The adapter derives the benchmark outcome from the
validator facts, rejects raw or authority-bearing fields, and emits the frozen
self-model benchmark input. Public conversion is currently limited to the
contract-smoke source; live conversion remains closed until a separately
authorized release phase binds quarantine, review, and custody. It never
executes a command, changes a checkout, calls a model, uses the network, or
retains raw model material.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from .protocol import (
    INPUT_SCHEMA_VERSION,
    LIMITATIONS,
    LIVE_SOURCE,
    OUTCOMES,
    SMOKE_SOURCE,
    SPLITS,
    STATE_SLICE,
    UPDATE_DIRECTIONS,
    VARIANTS,
    BenchmarkProtocolError,
    digest_json,
    validate_manifest,
    validate_trial,
)


CAPTURE_STATE_SLICE = "verified-self-model-benchmark-repository-capture-v1"
CAPTURE_SCHEMA_VERSION = "verified-self-model-repository-capture-v1"
REPOSITORY_CHECK_IDS = (
    "format",
    "focused_tests",
    "contract_validation",
    "diff_hygiene",
    "claim_boundary",
)
CHECK_STATUSES = {"pass", "fail", "not_run"}
CAPTURE_SOURCE_TYPES = {SMOKE_SOURCE, LIVE_SOURCE}
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

CAPTURE_MANIFEST_FIELDS = frozenset(
    {
        "record_type",
        "schema_version",
        "state_slice",
        "workflow_id",
        "source_type",
        "fixed_budget",
        "budget",
        "variants",
        "required_check_ids",
        "prediction_locked_before_assessment",
        "external_outcomes_verified",
        "recorded_by_external_validator",
        "agent_execution_recorded",
        "validator_custody",
        "validator_report_digest",
        "model_digest",
        "runtime_digest",
        "checker_digest",
        "raw_reasoning_retained",
        "authority_granted",
        "network_access",
    }
)

CAPTURE_OBSERVATION_FIELDS = frozenset(
    {
        "record_type",
        "trajectory_id",
        "task_family",
        "split",
        "variant",
        "horizon_step",
        "predicted_success_probability_milli",
        "predicted_limitation",
        "predicted_variant_effect_milli",
        "prior_belief_milli",
        "posterior_belief_milli",
        "validator_update_direction",
        "check_results",
        "scope_valid",
        "provenance_valid",
        "timed_out",
        "budget_exhausted",
        "capability_gap",
        "validator_limitation",
        "actual_variant_effect_milli",
        "latency_ms",
        "compute_units",
        "tool_calls",
        "attempts",
        "prediction_locked_before_outcome",
        "raw_reasoning_retained",
        "authority_granted",
        "network_access",
        "validator_observation_digest",
    }
)


class CaptureError(ValueError):
    """Raised when a repository capture violates the frozen adapter contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CaptureError(message)


def _finite_nonnegative(value: Any, field: str) -> None:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    _require(math.isfinite(value), f"{field} must be finite")
    _require(value >= 0, f"{field} must be nonnegative")


def _nonnegative_integer(value: Any, field: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{field} must be a nonnegative integer")


def _positive_integer(value: Any, field: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{field} must be a positive integer")


def _milli_probability(value: Any, field: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{field} must be an integer")
    _require(0 <= value <= 1000, f"{field} must be in [0, 1000]")


def _milli_effect(value: Any, field: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool), f"{field} must be an integer")
    _require(-1000 <= value <= 1000, f"{field} must be in [-1000, 1000]")


def _require_sha256(value: Any, field: str) -> None:
    _require(isinstance(value, str) and len(value) == 64, f"{field} must be a SHA-256 hex digest")
    _require(all(character in "0123456789abcdef" for character in value), f"{field} must be lowercase hexadecimal")


def _assert_no_forbidden_keys(value: Any, path: str = "record") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key).lower()
            if key != ALLOWED_REASONING_KEY and any(token in key_text for token in FORBIDDEN_KEY_TOKENS):
                raise CaptureError(f"raw or sensitive field forbidden: {path}.{key}")
            _assert_no_forbidden_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_no_forbidden_keys(nested, f"{path}[{index}]")


def _require_exact_fields(value: dict[str, Any], expected: frozenset[str], path: str) -> None:
    actual = frozenset(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    _require(not missing and not extra, f"{path} fields drift: missing={missing}, extra={extra}")


def validate_capture_manifest(manifest: dict[str, Any]) -> None:
    _require(isinstance(manifest, dict), "capture manifest must be an object")
    _assert_no_forbidden_keys(manifest, "manifest")
    _require_exact_fields(manifest, CAPTURE_MANIFEST_FIELDS, "capture manifest")
    _require(manifest.get("record_type") == "self_model_capture_manifest", "first record must be a self_model_capture_manifest")
    _require(manifest.get("schema_version") == CAPTURE_SCHEMA_VERSION, "wrong capture schema version")
    _require(manifest.get("state_slice") == CAPTURE_STATE_SLICE, "wrong capture state slice")
    _require(isinstance(manifest.get("workflow_id"), str) and manifest["workflow_id"], "workflow_id required")
    _require(manifest.get("source_type") in CAPTURE_SOURCE_TYPES, "wrong capture source type")
    _require(manifest.get("fixed_budget") is True, "fixed budget is required")
    _require(manifest.get("variants") == list(VARIANTS), "variants must match the frozen order")
    _require(manifest.get("required_check_ids") == list(REPOSITORY_CHECK_IDS), "required checks must match the frozen order")
    for field in (
        "prediction_locked_before_assessment",
        "external_outcomes_verified",
        "recorded_by_external_validator",
        "agent_execution_recorded",
        "validator_custody",
    ):
        _require(manifest.get(field) is True, f"{field} must be true")
    for field in ("raw_reasoning_retained", "authority_granted", "network_access"):
        _require(manifest.get(field) is False, f"{field} must be false")
    for field in ("validator_report_digest", "model_digest", "runtime_digest", "checker_digest"):
        _require_sha256(manifest.get(field), field)
    budget = manifest.get("budget")
    _require(isinstance(budget, dict), "budget required")
    _require(frozenset(budget) == frozenset({"max_latency_ms", "max_compute_units", "max_tool_calls", "max_attempts"}), "budget fields drift")
    for field in budget:
        _positive_integer(budget[field], f"budget.{field}")


def _unsigned_observation(observation: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in observation.items() if key != "validator_observation_digest"}


def _derive_validator_label(observation: dict[str, Any]) -> tuple[str, bool, str]:
    checks_green = all(status == "pass" for status in observation["check_results"].values())
    if not observation["scope_valid"]:
        return "scope_violation", False, "out_of_scope"
    if not observation["provenance_valid"]:
        return "stale_evidence", False, "stale_evidence"
    if observation["timed_out"] or observation["budget_exhausted"]:
        return "budget_exhausted", False, "budget"
    if observation["capability_gap"]:
        return "capability_gap", False, "missing_tool"
    if checks_green:
        return "success", True, "none"
    return "ordinary_failure", False, observation["validator_limitation"]


def validate_observation(observation: dict[str, Any], manifest: dict[str, Any]) -> None:
    # State slice: verified-self-model-benchmark-repository-capture-v1.
    _require(isinstance(observation, dict), "observation must be an object")
    _require(isinstance(manifest, dict), "capture manifest must be an object")
    _assert_no_forbidden_keys(observation)
    _require_exact_fields(observation, CAPTURE_OBSERVATION_FIELDS, "observation")
    _require(observation.get("record_type") == "self_model_repository_observation", "wrong observation record type")
    for field in ("trajectory_id", "task_family"):
        _require(isinstance(observation[field], str) and observation[field], f"{field} required")
    _require(observation["split"] in SPLITS, "wrong split")
    _require(observation["variant"] in VARIANTS, "wrong variant")
    _positive_integer(observation["horizon_step"], "horizon_step")
    _milli_probability(observation["predicted_success_probability_milli"], "predicted_success_probability_milli")
    _require(observation["predicted_limitation"] in LIMITATIONS, "wrong predicted limitation")
    _milli_effect(observation["predicted_variant_effect_milli"], "predicted_variant_effect_milli")
    _milli_probability(observation["prior_belief_milli"], "prior_belief_milli")
    _milli_probability(observation["posterior_belief_milli"], "posterior_belief_milli")
    _require(observation["validator_update_direction"] in UPDATE_DIRECTIONS, "wrong validator update direction")
    _milli_effect(observation["actual_variant_effect_milli"], "actual_variant_effect_milli")
    if observation["variant"] == "base":
        _require(observation["actual_variant_effect_milli"] == 0, "base actual variant effect must be zero")
    _require(observation["validator_limitation"] in LIMITATIONS, "wrong validator limitation")
    check_results = observation["check_results"]
    _require(isinstance(check_results, dict), "check_results must be an object")
    _require(set(check_results) == set(REPOSITORY_CHECK_IDS), "check_results must contain exactly the frozen checks")
    for check_id, status in check_results.items():
        _require(status in CHECK_STATUSES, f"wrong status for {check_id}")
    for field in ("scope_valid", "provenance_valid", "timed_out", "budget_exhausted", "capability_gap"):
        _require(isinstance(observation[field], bool), f"{field} must be boolean")
    for field in ("prediction_locked_before_outcome", "raw_reasoning_retained", "authority_granted", "network_access"):
        _require(isinstance(observation[field], bool), f"{field} must be boolean")
    _require(observation["prediction_locked_before_outcome"] is True, "prediction must be locked before outcome")
    _require(observation["raw_reasoning_retained"] is False, "raw reasoning retention forbidden")
    _require(observation["authority_granted"] is False, "authority grant forbidden")
    _require(observation["network_access"] is False, "network access forbidden")
    for field in ("latency_ms", "compute_units"):
        _finite_nonnegative(observation[field], field)
    for field in ("tool_calls", "attempts"):
        _nonnegative_integer(observation[field], field)
    budget = manifest["budget"]
    _require(observation["latency_ms"] <= budget["max_latency_ms"], "latency budget exceeded")
    _require(observation["compute_units"] <= budget["max_compute_units"], "compute budget exceeded")
    _require(observation["tool_calls"] <= budget["max_tool_calls"], "tool-call budget exceeded")
    _require(observation["attempts"] <= budget["max_attempts"], "attempt budget exceeded")
    _require_sha256(observation["validator_observation_digest"], "validator_observation_digest")
    _require(
        digest_json(_unsigned_observation(observation)) == observation["validator_observation_digest"],
        "validator observation digest mismatch",
    )
    outcome, success, limitation = _derive_validator_label(observation)
    _require(outcome in OUTCOMES, "derived outcome outside frozen taxonomy")
    _require(success is (outcome == "success"), "derived success label mismatch")
    _require(limitation == observation["validator_limitation"], "validator limitation contradicts validator facts")
    if success:
        _require(observation["validator_limitation"] == "none", "successful observation must have no limitation")
    else:
        _require(observation["validator_limitation"] != "none", "failed observation must expose a limitation")


def protocol_manifest(capture_manifest: dict[str, Any]) -> dict[str, Any]:
    manifest = dict(capture_manifest)
    manifest.update(
        {
            "record_type": "manifest",
            "schema_version": INPUT_SCHEMA_VERSION,
            "state_slice": STATE_SLICE,
            "source_type": capture_manifest["source_type"],
            "capture_schema_version": CAPTURE_SCHEMA_VERSION,
            "capture_state_slice": CAPTURE_STATE_SLICE,
            "capture_manifest_digest": digest_json(capture_manifest),
        }
    )
    validate_manifest(manifest)
    return manifest


def observation_to_trial(observation: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    validate_observation(observation, manifest)
    actual_outcome, actual_success, actual_limitation = _derive_validator_label(observation)
    trial = {
        "record_type": "self_model_trial",
        "trajectory_id": observation["trajectory_id"],
        "task_family": observation["task_family"],
        "split": observation["split"],
        "variant": observation["variant"],
        "horizon_step": observation["horizon_step"],
        "predicted_success_probability_milli": observation["predicted_success_probability_milli"],
        "predicted_limitation": observation["predicted_limitation"],
        "predicted_variant_effect_milli": observation["predicted_variant_effect_milli"],
        "actual_outcome": actual_outcome,
        "actual_success": actual_success,
        "actual_limitation": actual_limitation,
        "actual_variant_effect_milli": observation["actual_variant_effect_milli"],
        "prior_belief_milli": observation["prior_belief_milli"],
        "posterior_belief_milli": observation["posterior_belief_milli"],
        "verified_update_direction": observation["validator_update_direction"],
        "prediction_locked_before_outcome": observation["prediction_locked_before_outcome"],
        "raw_reasoning_retained": observation["raw_reasoning_retained"],
        "authority_granted": observation["authority_granted"],
        "network_access": observation["network_access"],
        "validator_observation_digest": observation["validator_observation_digest"],
        "validator_report_digest": manifest["validator_report_digest"],
        "model_digest": manifest["model_digest"],
        "runtime_digest": manifest["runtime_digest"],
        "checker_digest": manifest["checker_digest"],
    }
    if manifest["source_type"] == LIVE_SOURCE:
        trial["record_digest"] = digest_json(trial)
    validate_trial(trial, protocol_manifest(manifest))
    return trial


def load_capture(path: str | Path) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    records: list[dict[str, Any]] = []
    try:
        with Path(path).open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                value = json.loads(line)
                _require(isinstance(value, dict), f"line {line_number} must be an object")
                records.append(value)
    except (OSError, json.JSONDecodeError) as exc:
        raise CaptureError(f"invalid capture input: {exc}") from exc
    _require(records, "capture input is empty")
    manifest = records[0]
    validate_capture_manifest(manifest)
    observations = tuple(records[1:])
    _require(observations, "at least one observation is required")
    for observation in observations:
        validate_observation(observation, manifest)
    return manifest, observations


def _convert_loaded_capture(
    capture_manifest: dict[str, Any], observations: tuple[dict[str, Any], ...]
) -> list[dict[str, Any]]:
    manifest = protocol_manifest(capture_manifest)
    trials = [observation_to_trial(observation, capture_manifest) for observation in observations]
    return [manifest, *trials]


def _convert_for_contract_test(path: str | Path) -> list[dict[str, Any]]:
    """Build synthetic live-shaped input for deterministic protocol tests only."""

    capture_manifest, observations = load_capture(path)
    _require(capture_manifest["source_type"] == LIVE_SOURCE, "contract-test conversion requires a live-shaped capture")
    return _convert_loaded_capture(capture_manifest, observations)


def convert(path: str | Path) -> list[dict[str, Any]]:
    """Convert smoke input; reject live input until separately released."""

    capture_manifest, observations = load_capture(path)
    _require(
        capture_manifest["source_type"] != LIVE_SOURCE,
        "live capture conversion requires a separately authorized release",
    )
    return _convert_loaded_capture(capture_manifest, observations)


def write_jsonl(path: str | Path, records: list[dict[str, Any]]) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="capture manifest plus validator-owned observations")
    parser.add_argument("--output", required=True, help="frozen self-model benchmark input")
    args = parser.parse_args()
    try:
        records = convert(args.input)
        write_jsonl(args.output, records)
    except (OSError, CaptureError, BenchmarkProtocolError, json.JSONDecodeError) as exc:
        print(f"self_model_capture_error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"records_written": len(records), "output": args.output}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Admit a fresh, plan-only corpus to the sealed-pilot authorization boundary.

State slice: ``verified-metacognitive-control-fresh-corpus-admission-v1``.

The admission record proves that a future corpus and execution plan differ from
the source campaign while preserving the sealed task, controller, arm, and
budget configuration. It does not authorize or execute the future pilot.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .corpus_execution_launcher import LauncherError, build_execution_plan, validate_execution_plan
from .corpus_preflight import PreflightError, validate_plan as validate_corpus_plan
from .protocol import PROMOTION_ARMS, digest_json
from .repository_change_capture import CaptureError, _assert_no_forbidden_keys
from .sealed_pilot_preflight import SealedPilotPreflightError, case_set_digest, validate_preflight


ADMISSION_STATE_SLICE = "verified-metacognitive-control-fresh-corpus-admission-v1"
ADMISSION_SCHEMA_VERSION = "verified-metacognitive-fresh-corpus-admission-v1"
CLAIM_CEILING = "LocalDevelopmentFreshCorpusAdmissionOnly"
ADMISSION_STATUS = "ready_for_sealed_pilot_execution_authorization"


class FreshCorpusAdmissionError(ValueError):
    """Raised when a future corpus cannot cross the local admission boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FreshCorpusAdmissionError(message)


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
        raise FreshCorpusAdmissionError(f"invalid {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must be an object")
    return value


def _unsigned_admission(admission: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in admission.items() if key != "admission_digest"}


def validate_admission(admission: dict[str, Any]) -> None:
    """Validate freshness, configuration binding, and non-authorization flags."""

    _require(isinstance(admission, dict), "fresh corpus admission must be an object")
    try:
        _assert_no_forbidden_keys(admission, "fresh_corpus_admission")
    except CaptureError as exc:
        raise FreshCorpusAdmissionError(str(exc)) from exc
    _require(admission.get("record_type") == "fresh_corpus_admission", "wrong admission record type")
    _require(admission.get("schema_version") == ADMISSION_SCHEMA_VERSION, "wrong admission schema")
    _require(admission.get("state_slice") == ADMISSION_STATE_SLICE, "wrong admission state slice")
    _require(isinstance(admission.get("workflow_id"), str) and admission["workflow_id"], "workflow_id required")
    _require(admission.get("admission_status") == ADMISSION_STATUS, "wrong admission status")
    _require(admission.get("execution_status") == "not_started", "admission cannot start execution")
    _require(admission.get("authorization_status") == "not_granted", "admission cannot grant authorization")
    _require(admission.get("accepted") is False, "admission cannot accept a candidate")
    for field in (
        "authority_granted",
        "network_access",
        "raw_reasoning_retained",
        "scientific_evidence",
        "repository_evidence_ledger_appended",
        "source_corpus_reuse_allowed",
    ):
        _require(admission.get(field) is False, f"{field} must be false")
    _require(admission.get("fresh_corpus_verified") is True, "fresh corpus was not verified")
    _require(admission.get("future_fresh_corpus_required") is True, "future freshness requirement missing")
    _require(admission.get("claim_ceiling") == CLAIM_CEILING, "wrong admission claim ceiling")
    for field in (
        "source_preflight_digest",
        "source_corpus_digest",
        "source_case_set_digest",
        "fresh_corpus_digest",
        "fresh_case_set_digest",
        "fresh_execution_plan_digest",
        "admission_digest",
    ):
        _digest(admission.get(field), field)
    _require(admission["source_corpus_digest"] != admission["fresh_corpus_digest"], "source corpus was reused")
    _require(admission["source_case_set_digest"] != admission["fresh_case_set_digest"], "source case set was reused")
    checks = admission.get("freshness_checks")
    _require(isinstance(checks, dict), "freshness checks required")
    for field in (
        "corpus_digest_diff",
        "case_set_digest_diff",
        "workflow_id_diff",
        "task_spec_bound",
        "controller_bound",
        "arms_bound",
        "plan_only",
    ):
        _require(checks.get(field) is True, f"freshness check failed: {field}")
    fresh_plan = admission.get("fresh_execution_plan")
    _require(isinstance(fresh_plan, dict), "fresh execution plan required")
    try:
        validate_execution_plan(fresh_plan)
    except LauncherError as exc:
        raise FreshCorpusAdmissionError(f"fresh execution plan invalid: {exc}") from exc
    _require(fresh_plan["plan_digest"] == admission["fresh_execution_plan_digest"], "fresh plan digest mismatch")
    _require(fresh_plan["workflow_id"] == admission["workflow_id"], "fresh plan workflow mismatch")
    _require(fresh_plan["source_corpus_digest"] == admission["fresh_corpus_digest"], "fresh plan corpus mismatch")
    _require(case_set_digest(fresh_plan) == admission["fresh_case_set_digest"], "fresh plan case-set mismatch")
    configuration = admission.get("sealed_configuration")
    _require(isinstance(configuration, dict), "sealed configuration required")
    _require(configuration.get("arm_order") == list(PROMOTION_ARMS), "sealed arm order drifted")
    _require(configuration.get("prediction_lock_required") is True, "sealed prediction lock is required")
    _require(configuration.get("assessment_outcomes_available_to_controller") is False, "assessment outcomes must remain sealed")
    for field in ("task_spec_digest", "controller_config_digest"):
        _digest(configuration.get(field), f"sealed_configuration.{field}")
    budget = configuration.get("budget")
    _require(isinstance(budget, dict), "sealed budget required")
    for field in ("max_latency_ms", "max_compute_units", "max_tool_calls", "max_attempts"):
        _require(
            isinstance(budget.get(field), int) and not isinstance(budget[field], bool) and budget[field] > 0,
            f"sealed budget requires positive integer {field}",
        )
    _require(fresh_plan["task_spec_digest"] == configuration["task_spec_digest"], "task specification drifted")
    _require(
        fresh_plan["controller_config_digest"] == configuration["controller_config_digest"],
        "controller configuration drifted",
    )
    _require(fresh_plan["arm_digests"] == configuration["arm_digests"], "arm configuration drifted")
    source_artifacts = admission.get("source_artifact_digests")
    _require(isinstance(source_artifacts, dict), "source artifact digests required")
    for field in ("sealed_pilot_preflight", "fresh_corpus_plan", "fresh_execution_plan"):
        _digest(source_artifacts.get(field), f"source_artifact_digests.{field}")
    _require(
        source_artifacts["sealed_pilot_preflight"] == admission["source_preflight_digest"],
        "source preflight digest link mismatch",
    )
    _require(
        source_artifacts["fresh_corpus_plan"] == admission["fresh_corpus_digest"],
        "fresh corpus digest link mismatch",
    )
    _require(
        source_artifacts["fresh_execution_plan"] == admission["fresh_execution_plan_digest"],
        "fresh plan digest link mismatch",
    )
    non_claims = admission.get("non_claims")
    _require(isinstance(non_claims, list) and all(isinstance(item, str) for item in non_claims), "non_claims required")
    _require(digest_json(_unsigned_admission(admission)) == admission["admission_digest"], "admission digest mismatch")


def build_admission(preflight_path: str | Path, fresh_corpus_path: str | Path) -> dict[str, Any]:
    """Create a plan-only fresh-corpus admission from a ready preflight."""

    preflight = _load_object(preflight_path, "sealed-pilot preflight")
    try:
        validate_preflight(preflight)
    except SealedPilotPreflightError as exc:
        raise FreshCorpusAdmissionError(f"sealed-pilot preflight invalid: {exc}") from exc
    _require(
        preflight["preflight_status"] == "ready_for_sealed_pilot_authorization",
        "fresh corpus admission requires a ready sealed-pilot preflight",
    )
    fresh_corpus = _load_object(fresh_corpus_path, "fresh corpus plan")
    try:
        corpus_report = validate_corpus_plan(fresh_corpus)
    except (PreflightError, CaptureError) as exc:
        raise FreshCorpusAdmissionError(f"fresh corpus invalid: {exc}") from exc
    _require(corpus_report["valid"] is True, "fresh corpus preflight is not valid")
    fresh_corpus_digest = digest_json(fresh_corpus)
    sealed = preflight["sealed_configuration"]
    _require(fresh_corpus_digest != sealed["source_corpus_digest"], "fresh corpus reuses source corpus digest")
    _require(fresh_corpus["workflow_id"] != preflight["workflow_id"], "fresh workflow id must differ from source")
    _require(fresh_corpus["task_spec_digest"] == sealed["task_spec_digest"], "fresh task specification drifted")
    _require(
        fresh_corpus["controller_config_digest"] == sealed["controller_config_digest"],
        "fresh controller configuration drifted",
    )
    _require(fresh_corpus["arm_digests"] == sealed["arm_digests"], "fresh arm configuration drifted")
    try:
        fresh_execution_plan = build_execution_plan(fresh_corpus)
        validate_execution_plan(fresh_execution_plan)
    except LauncherError as exc:
        raise FreshCorpusAdmissionError(f"fresh execution plan invalid: {exc}") from exc
    fresh_case_set_digest = case_set_digest(fresh_execution_plan)
    _require(fresh_case_set_digest != sealed["source_case_set_digest"], "fresh case set reuses source case set")
    admission: dict[str, Any] = {
        "record_type": "fresh_corpus_admission",
        "schema_version": ADMISSION_SCHEMA_VERSION,
        "state_slice": ADMISSION_STATE_SLICE,
        "workflow_id": fresh_execution_plan["workflow_id"],
        "source_preflight_digest": preflight["preflight_digest"],
        "source_corpus_digest": sealed["source_corpus_digest"],
        "source_case_set_digest": sealed["source_case_set_digest"],
        "fresh_corpus_digest": fresh_corpus_digest,
        "fresh_case_set_digest": fresh_case_set_digest,
        "fresh_execution_plan_digest": fresh_execution_plan["plan_digest"],
        "admission_status": ADMISSION_STATUS,
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
        "future_fresh_corpus_required": True,
        "freshness_checks": {
            "corpus_digest_diff": True,
            "case_set_digest_diff": True,
            "workflow_id_diff": True,
            "task_spec_bound": True,
            "controller_bound": True,
            "arms_bound": True,
            "plan_only": True,
        },
        "sealed_configuration": {
            "arm_order": list(PROMOTION_ARMS),
            "task_spec_digest": sealed["task_spec_digest"],
            "controller_config_digest": sealed["controller_config_digest"],
            "arm_digests": dict(sealed["arm_digests"]),
            "budget": dict(sealed["budget"]),
            "prediction_lock_required": True,
            "assessment_outcomes_available_to_controller": False,
        },
        "fresh_execution_plan": fresh_execution_plan,
        "source_artifact_digests": {
            "sealed_pilot_preflight": preflight["preflight_digest"],
            "fresh_corpus_plan": fresh_corpus_digest,
            "fresh_execution_plan": fresh_execution_plan["plan_digest"],
        },
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": [
            "not_pilot_execution",
            "not_runtime_authorization",
            "not_candidate_acceptance",
            "not_repository_evidence_ledger_append",
            "not_experiment_evidence",
            "not_production_ready",
            "not_semantic_freshness_proof",
        ],
    }
    admission["admission_digest"] = digest_json(admission)
    validate_admission(admission)
    return admission


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sealed-pilot-preflight", required=True)
    parser.add_argument("--fresh-corpus", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        admission = build_admission(args.sealed_pilot_preflight, args.fresh_corpus)
        Path(args.output).write_text(json.dumps(admission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, FreshCorpusAdmissionError, json.JSONDecodeError) as exc:
        print(f"fresh_corpus_admission_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "admission_status": admission["admission_status"],
                "execution_status": admission["execution_status"],
                "authorization_status": admission["authorization_status"],
                "claim_ceiling": admission["claim_ceiling"],
                "admission_digest": admission["admission_digest"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

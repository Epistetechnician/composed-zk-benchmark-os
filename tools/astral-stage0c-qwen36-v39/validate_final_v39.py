#!/usr/bin/env python3
"""Independently validate the final aggregate V39 disposition.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This validator verifies the no-candidate decision basis and custody chain. It
does not load the model and does not retain or accept per-family effects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import protocol_v39 as protocol
import validate_assessment_v39 as assessment_validator
import validate_preassessment_v39 as preassessment_validator


CLASSIFICATION = "DevelopmentNoCandidate"
CLAIM_CEILING = "LocalDevelopmentV39DevelopmentNoCandidate"
FORBIDDEN_KEYS = {
    "prompts",
    "tokens",
    "hidden_states",
    "raw_activations",
    "raw_logits",
    "raw_traces",
    "per_family_effects",
    "effects_by_family",
    "reasoning_traces",
    "pii",
    "credentials",
}


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_digest(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_constant,
    )


def _contains_forbidden(value: Any) -> bool:
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            if any(key in FORBIDDEN_KEYS for key in current):
                return True
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return False


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _receipt(errors: list[str], final_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "classification": CLASSIFICATION if not errors else "FinalResultInvalid",
        "valid": not errors,
        "final_result_sha256": final_digest,
        "errors": errors,
    }


def validate(
    assessment_root: Path,
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    review_root: Path,
    model_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    assessment_root = assessment_root.resolve()
    final_path = assessment_root / "final-result.json"
    errors: list[str] = []
    try:
        final = _strict_json(final_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return _receipt([f"final_result_unreadable:{type(exc).__name__}:{exc}"], None)
    final_digest = _sha256_file(final_path)
    if not isinstance(final, dict):
        return _receipt(["final_result_not_object"], final_digest)
    if _contains_forbidden(final):
        errors.append("forbidden_raw_or_sensitive_field")
    for key, expected in (
        ("protocol", protocol.PROTOCOL_ID),
        ("state_slice", protocol.STATE_SLICE),
        ("claim_ceiling", CLAIM_CEILING),
        ("classification", CLASSIFICATION),
        ("assessment_family_count", 16),
        ("assessment_effects_present", True),
        ("assessment_effects_measured", True),
        ("prediction_locked_before_assessment", True),
        ("independent_review_accepted", True),
        ("raw_intermediates_retained", False),
        ("aggregate_only", True),
        ("network_access", False),
        ("model_training", False),
        ("stage_0c", False),
        ("stage_1", False),
        ("accepted_evidence", False),
    ):
        if final.get(key) != expected:
            errors.append(f"final_{key}_invalid")
    decision = final.get("decision_basis")
    if not isinstance(decision, dict):
        errors.append("decision_basis_invalid")
    else:
        if decision.get("candidate_panel") != "activation_only":
            errors.append("candidate_panel_invalid")
        if decision.get("utility_gate") != "activation_only_rmse_must_be_strictly_lower_than_constant_on_tune_and_assessment":
            errors.append("utility_gate_invalid")
        metric_keys = (
            "candidate_tune_rmse",
            "constant_tune_rmse",
            "candidate_assessment_rmse",
            "constant_assessment_rmse",
        )
        if any(not _finite(decision.get(key)) for key in metric_keys):
            errors.append("decision_metrics_invalid")
        else:
            if decision["candidate_tune_rmse"] < decision["constant_tune_rmse"]:
                errors.append("tune_no_candidate_gate_not_failed")
            if decision["candidate_assessment_rmse"] < decision["constant_assessment_rmse"]:
                errors.append("assessment_no_candidate_gate_not_failed")
        if decision.get("tune_utility_gate_passed") is not False or decision.get("assessment_utility_gate_passed") is not False:
            errors.append("decision_gate_flags_invalid")
        if decision.get("candidate_nominated") is not False:
            errors.append("candidate_nominated_invalid")

    assessment_receipt = assessment_validator.validate(
        assessment_root,
        preassessment_root,
        panel_root,
        corpus_root,
        qualification_root,
        review_root,
        model_root,
        repository_root,
    )
    if not assessment_receipt["valid"]:
        errors.append("assessment_validation_failed")
    summary_path = assessment_root / "assessment-summary.json"
    run_path = assessment_root / "assessment-run-manifest.json"
    if final.get("assessment_summary_sha256") != _sha256_file(summary_path):
        errors.append("assessment_summary_binding_mismatch")
    if final.get("assessment_run_manifest_sha256") != _sha256_file(run_path):
        errors.append("assessment_run_binding_mismatch")
    if final.get("assessment_validator_receipt_sha256") != _sha256_file(assessment_root / "validator-receipt.json"):
        errors.append("assessment_receipt_binding_mismatch")
    if final.get("preassessment_prediction_lock_sha256") != _sha256_file(preassessment_root / "prediction-lock.json"):
        errors.append("prediction_lock_binding_mismatch")
    if final.get("independent_review_receipt_sha256") != _sha256_file(review_root / "independent-review-receipt.json"):
        errors.append("review_binding_mismatch")
    if not _is_digest(final.get("model_manifest_sha256")):
        errors.append("model_manifest_binding_invalid")
    if final.get("source_sha256") != _sha256_file(HERE / "finalize_v39.py"):
        errors.append("finalizer_source_binding_mismatch")
    return _receipt(errors, final_digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assessment_root", type=Path)
    parser.add_argument("--preassessment-root", type=Path, required=True)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = validate(
            args.assessment_root,
            args.preassessment_root,
            args.panel_root,
            args.corpus_root,
            args.qualification_root,
            args.review_root,
            args.model,
            args.repository_root,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        receipt = _receipt([f"validator_error:{type(exc).__name__}:{exc}"], None)
    if args.write_receipt:
        receipt_path = args.assessment_root.resolve() / "final-validator-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

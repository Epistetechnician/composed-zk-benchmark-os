#!/usr/bin/env python3
"""Independently validate the aggregate-only V39 assessment bundle.

State slice: astral-stage0c-qwen36-layer-effect-v39.

The validator checks the post-review assessment custody chain, confirms that
the prediction lock preceded effects, and validates aggregate metric shape.
It never loads the model and never accepts raw per-family effects.
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
import validate_preassessment_v39 as preassessment_validator


CLAIM_CEILING = "LocalDevelopmentV39AssessmentAggregateEffects"
EXPECTED_FILES = {"assessment-summary.json", "assessment-run-manifest.json"}
OPTIONAL_FILES = {"final-result.json", "final-validator-receipt.json"}
CONTROL_NAMES = ["activation_only", "text_only", "shuffled", "constant"]
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


def _contains_forbidden_key(value: Any) -> bool:
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


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _receipt(errors: list[str], run_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "classification": "AssessmentEffectsMeasured" if not errors else "AssessmentInvalid",
        "valid": not errors,
        "assessment_run_manifest_sha256": run_digest,
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
    preassessment_root = preassessment_root.resolve()
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    review_root = review_root.resolve()
    model_root = model_root.resolve()
    repository_root = repository_root.resolve()
    errors: list[str] = []
    try:
        protocol.assert_external(assessment_root, repository_root)
    except ValueError as exc:
        errors.append(str(exc))
    if not assessment_root.is_dir() or assessment_root.is_symlink():
        return _receipt(errors + ["assessment root is not a regular directory"], None)
    entries = list(assessment_root.iterdir())
    if any(path.is_symlink() for path in entries):
        errors.append("symlink in assessment root")
    actual_files = {path.name for path in entries if path.is_file()}
    if actual_files - EXPECTED_FILES - OPTIONAL_FILES - {"validator-receipt.json"}:
        errors.append("unexpected assessment files")
    if EXPECTED_FILES - actual_files:
        errors.append("missing assessment files")
    summary_path = assessment_root / "assessment-summary.json"
    run_path = assessment_root / "assessment-run-manifest.json"
    try:
        summary = _strict_json(summary_path)
        run_manifest = _strict_json(run_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return _receipt(errors + [f"assessment files unreadable:{type(exc).__name__}:{exc}"], None)
    run_digest = _sha256_file(run_path)
    if not isinstance(summary, dict) or not isinstance(run_manifest, dict):
        return _receipt(errors + ["assessment documents must be objects"], run_digest)
    if _contains_forbidden_key(summary) or _contains_forbidden_key(run_manifest):
        errors.append("forbidden raw or sensitive field")

    for name, document in (("summary", summary), ("run", run_manifest)):
        if document.get("protocol") != protocol.PROTOCOL_ID:
            errors.append(f"{name}_protocol_mismatch")
        if document.get("state_slice") != protocol.STATE_SLICE:
            errors.append(f"{name}_state_slice_mismatch")
        if document.get("claim_ceiling") != CLAIM_CEILING:
            errors.append(f"{name}_claim_ceiling_mismatch")
        if document.get("classification") != "AssessmentEffectsMeasured":
            errors.append(f"{name}_classification_mismatch")

    for key, expected in (
        ("assessment_effects_present", True),
        ("assessment_effects_measured", True),
        ("prediction_locked_before_assessment", True),
        ("raw_intermediates_retained", False),
        ("aggregate_only", True),
        ("network_access", False),
        ("model_training", False),
        ("stage_0c", False),
        ("stage_1", False),
        ("accepted_evidence", False),
    ):
        if summary.get(key) is not expected:
            errors.append(f"summary_{key}_invalid")
    for key, expected in (
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
        if run_manifest.get(key) is not expected:
            errors.append(f"run_{key}_invalid")

    source = run_manifest.get("source")
    expected_source = {
        "runner_sha256": _sha256_file(HERE / "run_assessment_v39.py"),
        "preassessment_runner_sha256": _sha256_file(HERE / "run_preassessment_v39.py"),
        "protocol_sha256": _sha256_file(HERE / "protocol_v39.py"),
        "panel_source_sha256": _sha256_file(HERE / "panel_v39.py"),
    }
    if source != expected_source:
        errors.append("assessment_source_digest_mismatch")

    pre_receipt = preassessment_validator.validate(
        preassessment_root,
        panel_root,
        corpus_root,
        qualification_root,
        model_root,
        repository_root,
    )
    if not pre_receipt["valid"]:
        errors.append("preassessment_validation_failed")
    pre_lock_path = preassessment_root / "prediction-lock.json"
    pre_run_path = preassessment_root / "run-manifest.json"
    if run_manifest.get("preassessment_prediction_lock_sha256") != _sha256_file(pre_lock_path):
        errors.append("assessment_prediction_lock_digest_mismatch")
    if run_manifest.get("preassessment_run_manifest_sha256") != _sha256_file(pre_run_path):
        errors.append("assessment_preassessment_run_digest_mismatch")
    try:
        lock = _strict_json(pre_lock_path)
        pre_run = _strict_json(pre_run_path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        lock = {}
        pre_run = {}
        errors.append("preassessment_lock_unreadable")
    if lock.get("prediction_locked_before_assessment") is not True or lock.get("assessment_effects_measured") is not False:
        errors.append("prediction_lock_order_invalid")
    if pre_run.get("assessment_effects_present") is not False or pre_run.get("assessment_effects_measured") is not False:
        errors.append("preassessment_was_not_effects_closed")

    review_packet_path = review_root / "independent-review-packet.json"
    review_receipt_path = review_root / "independent-review-receipt.json"
    review_sidecar_path = review_root / "independent-review-packet.sha256"
    try:
        review_packet = _strict_json(review_packet_path)
        review_receipt = _strict_json(review_receipt_path)
        review_sidecar = review_sidecar_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"review_files_unreadable:{type(exc).__name__}")
        review_packet = {}
        review_receipt = {}
        review_sidecar = ""
    if review_sidecar != f"{_sha256_file(review_packet_path)}  independent-review-packet.json\n":
        errors.append("review_packet_sidecar_invalid")
    if review_packet.get("review_status") != "ACCEPTED_FOR_ASSESSMENT" or review_packet.get("independent_reviewer_receipt_present") is not True:
        errors.append("review_packet_not_accepted")
    if review_receipt.get("classification") != "IndependentReviewAccepted" or review_receipt.get("review_decision") != "APPROVED_FOR_ASSESSMENT":
        errors.append("review_receipt_not_accepted")
    if _canonical_digest(review_receipt) != review_packet.get("review_decision_digest"):
        errors.append("review_receipt_digest_invalid")
    if run_manifest.get("independent_review_receipt_sha256") != _sha256_file(review_receipt_path):
        errors.append("assessment_review_receipt_binding_mismatch")

    for document_name, document in (("summary", summary), ("run", run_manifest)):
        if document.get("panel_manifest_sha256") != run_manifest.get("panel_manifest_sha256"):
            errors.append(f"{document_name}_panel_binding_mismatch")
        if document.get("concept_registry_sha256") != run_manifest.get("concept_registry_sha256"):
            errors.append(f"{document_name}_registry_binding_mismatch")
        if document.get("split_manifest_sha256") != run_manifest.get("split_manifest_sha256"):
            errors.append(f"{document_name}_split_binding_mismatch")
        if document.get("model_manifest_sha256") != run_manifest.get("model_manifest_sha256"):
            errors.append(f"{document_name}_model_binding_mismatch")
    if run_manifest.get("summary_sha256") != _canonical_digest(summary):
        errors.append("assessment_summary_digest_mismatch")

    if summary.get("assessment_family_count") != 16 or run_manifest.get("assessment_family_count") != 16:
        errors.append("assessment_census_invalid")
    panels = summary.get("panels")
    if not isinstance(panels, dict) or set(panels) != set(CONTROL_NAMES):
        errors.append("assessment_panels_invalid")
    else:
        for name in CONTROL_NAMES:
            item = panels[name]
            if not isinstance(item, dict) or item.get("count") != 16:
                errors.append(f"assessment_panel_count_invalid:{name}")
                continue
            for metric in ("mse", "rmse", "mae", "mean_error"):
                if not _finite(item.get(metric)):
                    errors.append(f"assessment_metric_invalid:{name}:{metric}")
    target = summary.get("target_effect")
    if not isinstance(target, dict) or target.get("formula") != "mean_pair_margin(do(layer_19_final:=paired_opposite_final))-mean_pair_margin(clean)":
        errors.append("assessment_target_effect_invalid")
    elif any(not _finite(target.get(key)) for key in ("mean", "std", "min", "max")):
        errors.append("assessment_target_aggregate_invalid")
    matched = summary.get("matched_control")
    if not isinstance(matched, dict) or matched.get("used_for_tuning") is not False:
        errors.append("assessment_matched_control_invalid")
    elif any(not _finite(matched.get(key)) for key in ("mean", "std", "min", "max")) or not isinstance(matched.get("sequence_length_delta_max"), int):
        errors.append("assessment_matched_aggregate_invalid")

    return _receipt(errors, run_digest)


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
        receipt_path = args.assessment_root.resolve() / "validator-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

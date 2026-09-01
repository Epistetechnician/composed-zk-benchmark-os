#!/usr/bin/env python3
"""Independently validate the aggregate-only V39 preassessment bundle.

State slice: astral-stage0c-qwen36-layer-effect-v39.

The validator checks custody bindings, panel and qualification receipts,
fit/tune-only effect scope, fixed controls, prediction-lock contents, and
output privacy. It does not load the model, rerun effects, or open assessment.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_v39 as corpus
import panel_v39 as panel
import protocol_v39 as protocol
import validate_gutenberg_panel_v39 as panel_validator
import validator_v39 as qualification_validator


PREASSESSMENT_CLAIM_CEILING = "LocalDevelopmentV39PreassessmentPredictionLocked"
EXPECTED_FILES = {
    "fit-tune-summary.json",
    "prediction-lock.json",
    "run-manifest.json",
}
CONTROL_NAMES = ["activation_only", "text_only", "shuffled", "constant"]
RIDGE_ALPHAS = [1e-4, 1e-3, 1e-2, 1e-1]
FORBIDDEN_KEYS = {
    "prompts",
    "tokens",
    "hidden_states",
    "raw_activations",
    "raw_logits",
    "raw_traces",
    "reasoning_traces",
    "pii",
    "credentials",
}


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_digest(value: Any) -> str:
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


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _receipt(errors: list[str], run_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": PREASSESSMENT_CLAIM_CEILING,
        "classification": "PreassessmentPredictionLocked" if not errors else "PreassessmentInvalid",
        "valid": not errors,
        "run_manifest_sha256": run_digest,
        "errors": errors,
    }


def validate(
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    preassessment_root = preassessment_root.resolve()
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    repository_root = repository_root.resolve()
    errors: list[str] = []
    try:
        protocol.assert_external(preassessment_root, repository_root)
    except ValueError as exc:
        errors.append(str(exc))
    if not preassessment_root.is_dir() or preassessment_root.is_symlink():
        return _receipt(errors + ["preassessment root is not a regular directory"], None)
    entries = list(preassessment_root.iterdir())
    if any(path.is_symlink() for path in entries):
        errors.append("symlink in preassessment root")
    actual_files = {path.name for path in entries if path.is_file()}
    if actual_files - EXPECTED_FILES - {"validator-receipt.json"}:
        errors.append("unexpected preassessment files")
    if EXPECTED_FILES - actual_files:
        errors.append("missing preassessment files")
    paths = {name: preassessment_root / name for name in EXPECTED_FILES}
    try:
        run_manifest = _strict_json(paths["run-manifest.json"])
        summary = _strict_json(paths["fit-tune-summary.json"])
        lock = _strict_json(paths["prediction-lock.json"])
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return _receipt(errors + [f"preassessment files unreadable:{type(exc).__name__}:{exc}"], None)
    run_digest = _sha256_file(paths["run-manifest.json"])
    if _contains_forbidden_key(run_manifest) or _contains_forbidden_key(summary) or _contains_forbidden_key(lock):
        errors.append("forbidden raw or sensitive field")

    if not isinstance(run_manifest, dict) or not isinstance(summary, dict) or not isinstance(lock, dict):
        return _receipt(errors + ["preassessment documents must be objects"], run_digest)

    for name, document in (("run_manifest", run_manifest), ("summary", summary), ("lock", lock)):
        if document.get("protocol") != protocol.PROTOCOL_ID:
            errors.append(f"{name}_protocol_mismatch")
        if document.get("state_slice") != protocol.STATE_SLICE:
            errors.append(f"{name}_state_slice_mismatch")
        if document.get("claim_ceiling") != PREASSESSMENT_CLAIM_CEILING:
            errors.append(f"{name}_claim_ceiling_mismatch")
        if document.get("classification") != "PreassessmentPredictionLocked":
            errors.append(f"{name}_classification_mismatch")

    if run_manifest.get("panel_root") != str(panel_root):
        errors.append("run_panel_root_mismatch")
    if run_manifest.get("qualification_root") != str(qualification_root):
        errors.append("run_qualification_root_mismatch")
    if run_manifest.get("model_root") != str(model_root):
        errors.append("run_model_root_mismatch")
    if run_manifest.get("assessment_predictions_materialized") is not True:
        errors.append("assessment_predictions_not_materialized")
    for key, expected in (
        ("assessment_effects_present", False),
        ("assessment_effects_measured", False),
        ("prediction_locked_before_assessment", True),
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

    if run_manifest.get("source") != {
        "runner_sha256": _sha256_file(HERE / "run_preassessment_v39.py"),
        "protocol_sha256": _sha256_file(HERE / "protocol_v39.py"),
        "panel_source_sha256": _sha256_file(HERE / "panel_v39.py"),
    }:
        errors.append("run_source_digest_mismatch")
    runtime = run_manifest.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("mlx") != importlib.metadata.version("mlx") or runtime.get("mlx_lm") != importlib.metadata.version("mlx-lm"):
        errors.append("run_runtime_binding_mismatch")
    if not isinstance(runtime, dict) or runtime.get("python") != platform_python_version():
        errors.append("run_python_binding_mismatch")

    panel_receipt = panel_validator.validate(
        panel_root,
        corpus_root,
        qualification_root,
        model_root,
        repository_root,
    )
    if not panel_receipt["valid"]:
        errors.append("panel_validation_failed")
    panel_manifest_path = panel_root / "panel-manifest.json"
    registry_path = panel_root / "concept-registry.json"
    split_path = panel_root / "split-manifest.json"
    panel_receipt_path = panel_root / "validator-receipt.json"
    panel_paths = (panel_manifest_path, registry_path, split_path, panel_receipt_path)
    if any(not path.is_file() for path in panel_paths):
        errors.append("panel_binding_file_missing")
    else:
        if run_manifest.get("panel_manifest_sha256") != _sha256_file(panel_manifest_path):
            errors.append("run_panel_manifest_digest_mismatch")
        if run_manifest.get("concept_registry_sha256") != _sha256_file(registry_path):
            errors.append("run_concept_registry_digest_mismatch")
        if run_manifest.get("split_manifest_sha256") != _sha256_file(split_path):
            errors.append("run_split_manifest_digest_mismatch")
        if run_manifest.get("panel_validator_receipt_sha256") != _sha256_file(panel_receipt_path):
            errors.append("run_panel_receipt_digest_mismatch")
        try:
            stored_panel_receipt = _strict_json(panel_receipt_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            errors.append("panel_receipt_unreadable")
        else:
            if stored_panel_receipt != panel_receipt:
                errors.append("panel_receipt_stale")

    qualification_result_path = qualification_root / "qualification-result.json"
    qualification_receipt_path = qualification_root / "validator-receipt.json"
    try:
        qualification_result = qualification_validator._strict_json(qualification_result_path)
        stored_qualification_receipt = qualification_validator._strict_json(qualification_receipt_path)
        recomputed_qualification_receipt = qualification_validator.validate(
            qualification_result,
            qualification_result_path,
            model_root,
            repository_root,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"qualification_validation_failed:{type(exc).__name__}")
        qualification_result = {}
        stored_qualification_receipt = None
        recomputed_qualification_receipt = {"valid": False}
    if not recomputed_qualification_receipt.get("valid") or stored_qualification_receipt != recomputed_qualification_receipt:
        errors.append("qualification_receipt_invalid_or_stale")
    if run_manifest.get("qualification_result_sha256") != _sha256_file(qualification_result_path):
        errors.append("run_qualification_result_digest_mismatch")
    if run_manifest.get("qualification_validator_receipt_sha256") != _sha256_file(qualification_receipt_path):
        errors.append("run_qualification_receipt_digest_mismatch")
    if run_manifest.get("model_manifest_sha256") != qualification_result.get("model_manifest_sha256"):
        errors.append("run_model_manifest_digest_mismatch")

    for document_name, document in (("summary", summary), ("lock", lock)):
        if document.get("panel_manifest_sha256") != run_manifest.get("panel_manifest_sha256"):
            errors.append(f"{document_name}_panel_binding_mismatch")
        if document.get("concept_registry_sha256") != run_manifest.get("concept_registry_sha256"):
            errors.append(f"{document_name}_registry_binding_mismatch")
        if document.get("split_manifest_sha256") != run_manifest.get("split_manifest_sha256"):
            errors.append(f"{document_name}_split_binding_mismatch")
        if document.get("model_manifest_sha256") != run_manifest.get("model_manifest_sha256"):
            errors.append(f"{document_name}_model_binding_mismatch")
        if document.get("target_layer") != protocol.TARGET_LAYER:
            errors.append(f"{document_name}_target_layer_mismatch")
        if document.get("feature_width") != 64:
            errors.append(f"{document_name}_feature_width_mismatch")

    if run_manifest.get("prediction_lock_sha256") != _json_digest(lock):
        errors.append("prediction_lock_digest_mismatch")
    if run_manifest.get("fit_tune_summary_sha256") != _json_digest(summary):
        errors.append("fit_tune_summary_digest_mismatch")

    for document_name, document in (("summary", summary), ("lock", lock)):
        for key, expected in (
            ("assessment_effects_absent", True),
            ("assessment_effects_measured", False),
            ("prediction_locked_before_assessment", True),
            ("raw_intermediates_retained", False),
            ("aggregate_only", True),
            ("network_access", False),
            ("model_training", False),
        ):
            if document.get(key) is not expected:
                errors.append(f"{document_name}_{key}_invalid")

    if summary.get("fit_family_count") != 16 or summary.get("tune_family_count") != 16 or summary.get("assessment_family_count") != 16:
        errors.append("summary_split_counts_invalid")
    if summary.get("target_effects", {}).get("formula") != "mean_pair_margin(do(layer_19_final:=paired_opposite_final))-mean_pair_margin(clean)":
        errors.append("summary_target_formula_invalid")
    if summary.get("matched_control", {}).get("used_for_tuning") is not False:
        errors.append("matched_control_tuning_invalid")
    panels = summary.get("panels")
    if not isinstance(panels, dict) or set(panels) != set(CONTROL_NAMES):
        errors.append("summary_panels_invalid")
    else:
        for name in CONTROL_NAMES:
            item = panels[name]
            if not isinstance(item, dict) or item.get("name") != name:
                errors.append(f"summary_panel_invalid:{name}")
                continue
            if name == "constant":
                if item.get("candidate_alphas") != [] or item.get("selected_alpha") is not None:
                    errors.append("constant_candidate_contract_invalid")
            elif item.get("candidate_alphas") != RIDGE_ALPHAS or item.get("selected_alpha") not in RIDGE_ALPHAS:
                errors.append(f"ridge_candidate_contract_invalid:{name}")
            for metric in ("fit_mse", "fit_rmse", "tune_mse", "tune_rmse", "fit_target_mean", "fit_target_std", "tune_target_mean", "tune_target_std"):
                if not _is_finite_number(item.get(metric)):
                    errors.append(f"summary_metric_invalid:{name}:{metric}")

    if lock.get("controls") != CONTROL_NAMES or lock.get("ridge_candidate_alphas") != RIDGE_ALPHAS:
        errors.append("lock_control_contract_invalid")
    predictions = lock.get("predictions")
    expected_assessment_ids: list[str] = []
    try:
        split_manifest = _strict_json(split_path)
        expected_assessment_ids = sorted(split_manifest["by_split"]["assessment"])
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        errors.append("assessment_split_unreadable")
    if lock.get("assessment_family_count") != 16 or not isinstance(predictions, list):
        errors.append("lock_assessment_census_invalid")
    else:
        actual_ids = [row.get("family_id") for row in predictions if isinstance(row, dict)]
        if actual_ids != expected_assessment_ids:
            errors.append("lock_assessment_membership_invalid")
        for row in predictions:
            if not isinstance(row, dict) or set(row) != {"family_id", "predictions"}:
                errors.append("lock_prediction_row_invalid")
                continue
            if not isinstance(row["family_id"], str):
                errors.append("lock_family_id_invalid")
            values = row["predictions"]
            if not isinstance(values, dict) or set(values) != set(CONTROL_NAMES):
                errors.append("lock_prediction_controls_invalid")
                continue
            if any(not _is_finite_number(values[name]) for name in CONTROL_NAMES):
                errors.append("lock_prediction_value_invalid")

    return _receipt(errors, run_digest)


def platform_python_version() -> str:
    import platform

    return platform.python_version()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preassessment_root", type=Path)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
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
            args.preassessment_root,
            args.panel_root,
            args.corpus_root,
            args.qualification_root,
            args.model,
            args.repository_root,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        receipt = _receipt([f"validator_error:{type(exc).__name__}:{exc}"], None)
    if args.write_receipt:
        receipt_path = args.preassessment_root.resolve() / "validator-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independently validate the V41 fit/tune and prediction-lock bundle.

State slice: astral-stage0c-qwen36-directional-block-target-v41.

This validator recomputes the custody chain and checks that assessment effects
were absent when predictions were locked. It rejects raw or per-family output.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import protocol_v41 as protocol
import run_preassessment_v41 as preassessment
import validate_panel_v41 as panel_validator
import validate_qualification_v41 as qualification_validator


EXPECTED_FILES = {"fit-tune-summary.json", "prediction-lock.json", "run-manifest.json"}
FORBIDDEN_KEYS = frozenset(
    {
        "prompts",
        "source_excerpts",
        "tokens",
        "raw_activations",
        "activations",
        "raw_logits",
        "logits",
        "raw_traces",
        "traces",
        "per_family_effects",
        "per_family_predictions",
        "credentials",
        "pii",
    }
)


def _scan_forbidden(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_KEYS:
                errors.append(f"forbidden_key:{path}.{key}")
            errors.extend(_scan_forbidden(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_scan_forbidden(nested, f"{path}[{index}]"))
    return errors


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=reject_constant,
    )


def validate(
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    preassessment_root = preassessment_root.resolve()
    try:
        protocol.assert_external(preassessment_root, repository_root)
        panel_receipt = panel_validator.validate(
            panel_root.resolve(), corpus_root.resolve(), model_root.resolve(), repository_root
        )
        qualification_receipt = qualification_validator.validate(
            qualification_root.resolve(), model_root.resolve(), repository_root
        )
        if not panel_receipt["valid"]:
            errors.append("panel_validation_failed")
        if not qualification_receipt["valid"]:
            errors.append("qualification_validation_failed")
        panel_receipt_path = panel_root.resolve() / "validator-receipt.json"
        qualification_receipt_path = qualification_root.resolve() / "validator-receipt.json"
        if not panel_receipt_path.is_file() or not qualification_receipt_path.is_file():
            errors.append("recorded_independent_receipt_missing")
        else:
            if _strict_json(panel_receipt_path) != panel_receipt:
                errors.append("recorded_panel_receipt_mismatch")
            if _strict_json(qualification_receipt_path) != qualification_receipt:
                errors.append("recorded_qualification_receipt_mismatch")

        summary = _strict_json(preassessment_root / "fit-tune-summary.json")
        lock = _strict_json(preassessment_root / "prediction-lock.json")
        run = _strict_json(preassessment_root / "run-manifest.json")
        for value in (summary, lock, run):
            if not isinstance(value, dict):
                errors.append("bundle_document_not_object")
        errors.extend(_scan_forbidden(summary))
        errors.extend(_scan_forbidden(lock))
        errors.extend(_scan_forbidden(run))

        for value in (summary, lock, run):
            if value.get("protocol") != protocol.PROTOCOL_ID:
                errors.append("protocol_mismatch")
            if value.get("state_slice") != protocol.STATE_SLICE:
                errors.append("state_slice_mismatch")
            if value.get("assessment_effects_measured") is not False:
                errors.append("assessment_effects_were_measured")
            if value.get("raw_intermediates_retained") is not False or value.get("aggregate_only") is not True:
                errors.append("retention_state_invalid")
        if summary.get("classification") != "PreassessmentPredictionLocked":
            errors.append("classification_mismatch")
        if summary.get("claim_ceiling") != preassessment.CLAIM_CEILING:
            errors.append("claim_ceiling_mismatch")
        tune_delta = summary.get("tune_delta_rmse")
        expected_tune_gate = _finite(tune_delta) and float(tune_delta) <= -protocol.UTILITY_RMSE_MARGIN
        if not _finite(tune_delta) or not isinstance(summary.get("tune_utility_gate_passed"), bool) or summary.get("tune_utility_gate_passed") != expected_tune_gate:
            errors.append("tune_gate_record_invalid")
        if summary.get("assessment_effects_absent") is not True or lock.get("assessment_effects_absent") is not True:
            errors.append("assessment_effect_absence_missing")
        if lock.get("prediction_locked_before_assessment") is not True or run.get("prediction_locked_before_assessment") is not True:
            errors.append("prediction_lock_missing")
        if lock.get("per_family_predictions_retained") is not False or summary.get("per_family_predictions_retained") is not False:
            errors.append("per_family_predictions_present")
        if summary.get("per_family_effects_retained") is not False:
            errors.append("per_family_effects_present")

        if lock.get("assessment_family_ids") != sorted(lock.get("assessment_family_ids", [])):
            errors.append("assessment_family_order_not_canonical")
        if len(lock.get("assessment_family_ids", [])) != protocol.FAMILIES_PER_SPLIT:
            errors.append("assessment_family_count_mismatch")
        if lock.get("controls") != list(protocol.CONTROL_NAMES):
            errors.append("control_definition_mismatch")
        if lock.get("estimator_controls") != list(preassessment.ESTIMATOR_NAMES):
            errors.append("estimator_control_definition_mismatch")
        if lock.get("feature_width") != protocol.FEATURE_WIDTH or lock.get("feature_map_sha256") != protocol.feature_map_digest():
            errors.append("feature_map_binding_mismatch")
        states = lock.get("estimator_states")
        if not isinstance(states, dict) or set(states) != set(preassessment.ESTIMATOR_NAMES):
            errors.append("estimator_state_names_mismatch")
        else:
            for name, state in states.items():
                if not isinstance(state, dict):
                    errors.append(f"estimator_state_not_object:{name}")
                    continue
                if name == "constant":
                    if set(state) != {"target_mean"} or not _finite(state.get("target_mean")):
                        errors.append("constant_state_invalid")
                    continue
                if set(state) != {"alpha", "feature_mean", "feature_scale", "target_mean", "coefficients"}:
                    errors.append(f"ridge_state_keys_invalid:{name}")
                if state.get("alpha") not in protocol.RIDGE_ALPHAS or not _finite(state.get("target_mean")):
                    errors.append(f"ridge_state_scalar_invalid:{name}")
                for key in ("feature_mean", "feature_scale", "coefficients"):
                    values = state.get(key)
                    if not isinstance(values, list) or len(values) != protocol.FEATURE_WIDTH or not all(_finite(item) for item in values):
                        errors.append(f"ridge_state_width_or_finiteness_invalid:{name}:{key}")
                if isinstance(state.get("feature_scale"), list) and any(float(item) <= 0.0 for item in state["feature_scale"]):
                    errors.append(f"ridge_state_scale_invalid:{name}")

        expected_digests = {
            "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
            "feature_map_sha256": protocol.feature_map_digest(),
            "corpus_manifest_sha256": protocol.sha256_file(corpus_root / "corpus-manifest.json"),
            "corpus_validator_receipt_sha256": protocol.sha256_file(corpus_root / "validator-receipt.json"),
            "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
            "concept_registry_sha256": protocol.sha256_file(panel_root / "concept-registry.json"),
            "split_manifest_sha256": protocol.sha256_file(panel_root / "split-manifest.json"),
            "panel_validator_receipt_sha256": protocol.sha256_file(panel_root / "validator-receipt.json"),
            "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
            "qualification_validator_receipt_sha256": protocol.sha256_file(qualification_root / "validator-receipt.json"),
            "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
        }
        for key, expected in expected_digests.items():
            if summary.get(key) != expected or lock.get(key) != expected:
                errors.append(f"digest_binding_mismatch:{key}")
        for key in ("protocol_source_sha256", "feature_map_sha256", "corpus_manifest_sha256", "panel_manifest_sha256", "qualification_result_sha256", "model_manifest_sha256"):
            if run.get(key) != expected_digests[key]:
                errors.append(f"run_digest_binding_mismatch:{key}")
        if run.get("runner_source_sha256") != protocol.sha256_file(Path(preassessment.__file__).resolve()):
            errors.append("runner_source_mismatch")
        if run.get("features_source_sha256") != protocol.sha256_file(Path(preassessment.features.__file__).resolve()):
            errors.append("features_source_mismatch")
        if run.get("prediction_lock_sha256") != protocol.canonical_digest(lock):
            errors.append("prediction_lock_digest_mismatch")
        if run.get("fit_tune_summary_sha256") != protocol.canonical_digest(summary):
            errors.append("summary_digest_mismatch")

        panels = summary.get("panels")
        if not isinstance(panels, dict) or set(panels) != set(protocol.CONTROL_NAMES):
            errors.append("panel_names_mismatch")
        else:
            for name in preassessment.ESTIMATOR_NAMES:
                panel_summary = panels.get(name, {})
                if panel_summary.get("fit_count") != protocol.FAMILIES_PER_SPLIT or panel_summary.get("tune_count") != protocol.FAMILIES_PER_SPLIT:
                    errors.append(f"summary_count_mismatch:{name}")
                for metric_name in ("fit_rmse", "tune_rmse", "fit_target_mean", "fit_target_std", "tune_target_mean", "tune_target_std"):
                    if not _finite(panel_summary.get(metric_name)):
                        errors.append(f"summary_metric_invalid:{name}:{metric_name}")
            matched = panels.get("matched", {})
            for split in ("fit", "tune"):
                aggregate = matched.get(split, {})
                if aggregate.get("count") != protocol.FAMILIES_PER_SPLIT or not all(_finite(aggregate.get(key)) for key in ("mean", "std", "min", "max", "mean_abs")):
                    errors.append(f"matched_summary_invalid:{split}")
            if matched.get("used_for_tuning") is not False or matched.get("donor_violations") != 0 or not _finite(matched.get("norm_relative_error_max")):
                errors.append("matched_summary_gate_invalid")

        for key in ("fit", "tune"):
            aggregate = summary.get("target_effects", {}).get(key, {})
            if aggregate.get("count") != protocol.FAMILIES_PER_SPLIT or not all(_finite(aggregate.get(name)) for name in ("mean", "std", "min", "max", "mean_abs")):
                errors.append(f"target_aggregate_invalid:{key}")
        actual_files = {
            candidate.relative_to(preassessment_root).as_posix()
            for candidate in preassessment_root.rglob("*")
            if candidate.is_file()
        }
        allowed_files = EXPECTED_FILES | {"validator-receipt.json"}
        if not EXPECTED_FILES <= actual_files or not actual_files <= allowed_files:
            errors.append("output_census_mismatch")
    except (OSError, json.JSONDecodeError, TypeError, KeyError, AttributeError, protocol.ProtocolError, ValueError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": preassessment.CLAIM_CEILING,
        "classification": "PreassessmentPredictionLocked" if not errors else "PreassessmentInvalid",
        "valid": not errors,
        "errors": errors,
        "run_manifest_sha256": protocol.sha256_file(preassessment_root / "run-manifest.json") if (preassessment_root / "run-manifest.json").is_file() else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preassessment_root", type=Path)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(
        args.preassessment_root,
        args.panel_root,
        args.corpus_root,
        args.qualification_root,
        args.model,
        args.repository_root,
    )
    if args.write_receipt:
        protocol.write_json(args.preassessment_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

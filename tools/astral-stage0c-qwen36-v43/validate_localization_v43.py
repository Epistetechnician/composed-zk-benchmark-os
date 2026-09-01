#!/usr/bin/env python3
"""Independently validate the aggregate-only V43 localization result.

State slice: astral-stage0c-qwen36-causal-target-localization-v43.
The validator rejects raw prompts, activations, logits, traces, effects, and
predictions from the result root; panel inputs remain separately custody-bound.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import protocol_v43 as protocol
import run_localization_v43 as runner
import validate_gutenberg_corpus_v43 as corpus_validator
import validate_panel_v43 as panel_validator
import validate_qualification_v43 as qualification_validator


FORBIDDEN_KEYS = frozenset({
    "prompts", "source_excerpts", "tokens", "raw_activations", "activations",
    "raw_logits", "logits", "raw_traces", "traces", "per_family_effects",
    "per_family_predictions", "predictions", "credentials", "pii",
})


def _strict_json(file_path: Path) -> Any:
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(file_path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates, parse_constant=reject_constant)


def _scan_forbidden(value: Any, location: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_KEYS:
                errors.append(f"forbidden_key:{location}.{key}")
            errors.extend(_scan_forbidden(nested, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_scan_forbidden(nested, f"{location}[{index}]"))
    return errors


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _receipt(errors: list[str], result_digest: str | None) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV43LocalizationValidated",
        "classification": "LocalizationValidated" if not errors else "LocalizationInvalid",
        "valid": not errors,
        "errors": errors,
        "localization_result_sha256": result_digest,
        "independent_validation": True,
    }


def _check_stats(stats: Any, expected_count: int, errors: list[str], label: str) -> None:
    if not isinstance(stats, dict):
        errors.append(f"stats_missing:{label}")
        return
    if stats.get("count") != expected_count:
        errors.append(f"stats_count_mismatch:{label}")
    for key in ("mean", "std", "mean_abs", "min", "max"):
        if not _finite(stats.get(key)):
            errors.append(f"stats_nonfinite:{label}:{key}")


def _check_split(split: Any, errors: list[str], label: str) -> None:
    if not isinstance(split, dict):
        errors.append(f"split_missing:{label}")
        return
    if split.get("family_count") != protocol.FAMILIES_PER_SPLIT or split.get("document_count") != protocol.DOCUMENTS_PER_SPLIT:
        errors.append(f"split_census_mismatch:{label}")
    layers = split.get("layer_summaries")
    if not isinstance(layers, dict) or set(layers) != {str(layer) for layer in protocol.CANDIDATE_LAYERS}:
        errors.append(f"layer_census_invalid:{label}")
        return
    for layer in protocol.CANDIDATE_LAYERS:
        layer_key = str(layer)
        summary = layers[layer_key]
        if not isinstance(summary, dict) or summary.get("layer") != layer:
            errors.append(f"layer_binding_invalid:{label}:{layer}")
            continue
        activation = summary.get("activation_only")
        text_only = summary.get("text_only")
        if not isinstance(activation, dict) or not isinstance(text_only, dict):
            errors.append(f"activation_or_text_missing:{label}:{layer}")
        else:
            for wrapper in protocol.WRAPPER_NAMES:
                _check_stats(activation.get(wrapper), protocol.FAMILIES_PER_SPLIT, errors, f"{label}:{layer}:activation:{wrapper}")
                _check_stats(text_only.get(wrapper), protocol.FAMILIES_PER_SPLIT, errors, f"{label}:{layer}:text:{wrapper}")
        controls = summary.get("controls")
        if not isinstance(controls, dict) or set(controls) != {"exact_copy", "shuffled", "constant", "matched"}:
            errors.append(f"controls_invalid:{label}:{layer}")
        else:
            for control_name, stats in controls.items():
                _check_stats(stats, protocol.FAMILIES_PER_SPLIT * len(protocol.WRAPPER_NAMES), errors, f"{label}:{layer}:control:{control_name}")
        for key in ("matched_norm_relative_error_max", "repeat_max_abs_effect_delta"):
            if not _finite(summary.get(key)):
                errors.append(f"control_numeric_invalid:{label}:{layer}:{key}")
        if summary.get("matched_donor_violations") != 0:
            errors.append(f"matched_donor_violation:{label}:{layer}")
        if _finite(summary.get("matched_norm_relative_error_max")) and float(summary["matched_norm_relative_error_max"]) > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
            errors.append(f"matched_norm_invalid:{label}:{layer}")
        if _finite(summary.get("repeat_max_abs_effect_delta")) and float(summary["repeat_max_abs_effect_delta"]) > protocol.MAX_REPEAT_ABS_EFFECT_DELTA:
            errors.append(f"repeatability_invalid:{label}:{layer}")
        reliability = summary.get("reliability")
        expected_gates = {
            "target_effect_non_degenerate", "wrapper_correlation", "wrapper_sign_agreement", "bootstrap_correlation",
            "exact_copy_control", "shuffled_control", "constant_control", "matched_control", "repeatability",
        }
        if not isinstance(reliability, dict):
            errors.append(f"reliability_missing:{label}:{layer}")
            continue
        for key in ("wrapper_correlation", "wrapper_sign_agreement", "bootstrap_correlation_lower_95", "wrapper_alpha_effect_std", "wrapper_beta_effect_std", "target_effect_std_min"):
            if not _finite(reliability.get(key)):
                errors.append(f"reliability_nonfinite:{label}:{layer}:{key}")
        gates = reliability.get("gates")
        if not isinstance(gates, dict) or set(gates) != expected_gates or any(not isinstance(value, bool) for value in gates.values()):
            errors.append(f"reliability_gates_invalid:{label}:{layer}")
        elif isinstance(controls, dict) and isinstance(activation, dict) and isinstance(reliability, dict):
            expected_gate_values = {
                "target_effect_non_degenerate": reliability["target_effect_std_min"] >= protocol.MIN_TARGET_EFFECT_STD,
                "wrapper_correlation": reliability["wrapper_correlation"] >= protocol.MIN_TARGET_CORRELATION,
                "wrapper_sign_agreement": reliability["wrapper_sign_agreement"] >= protocol.MIN_TARGET_SIGN_AGREEMENT,
                "bootstrap_correlation": reliability["bootstrap_correlation_lower_95"] >= protocol.MIN_BOOTSTRAP_CORRELATION_LOWER,
                "exact_copy_control": controls["exact_copy"]["mean_abs"] <= protocol.MAX_EXACT_COPY_ABS_EFFECT,
                "shuffled_control": abs(controls["shuffled"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
                "constant_control": abs(controls["constant"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
                "matched_control": abs(controls["matched"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
                "repeatability": float(summary["repeat_max_abs_effect_delta"]) <= protocol.MAX_REPEAT_ABS_EFFECT_DELTA,
            }
            if gates != expected_gate_values:
                errors.append(f"reliability_gate_arithmetic_mismatch:{label}:{layer}")


def validate_with_corpus(localization_root: Path, panel_root: Path, corpus_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    localization_root = localization_root.resolve()
    try:
        protocol.assert_external(localization_root, repository_root)
        corpus_receipt = corpus_validator.validate(corpus_root.resolve(), repository_root)
        panel_receipt = panel_validator.validate(panel_root.resolve(), corpus_root.resolve(), model_root.resolve(), repository_root)
        qualification_receipt = qualification_validator.validate(qualification_root.resolve(), model_root.resolve(), repository_root)
        if not corpus_receipt["valid"]:
            errors.append("corpus_validation_failed")
        if not panel_receipt["valid"]:
            errors.append("panel_validation_failed")
        if not qualification_receipt["valid"]:
            errors.append("qualification_validation_failed")
        for file_path, expected in (
            (corpus_root.resolve() / "validator-receipt.json", corpus_receipt),
            (panel_root.resolve() / "validator-receipt.json", panel_receipt),
            (qualification_root.resolve() / "validator-receipt.json", qualification_receipt),
        ):
            if not file_path.is_file() or _strict_json(file_path) != expected:
                errors.append(f"recorded_receipt_mismatch:{file_path.name}")
        result_path = localization_root / "localization-result.json"
        lock_path = localization_root / "configuration-lock.json"
        result = _strict_json(result_path)
        lock = _strict_json(lock_path)
        if not isinstance(result, dict) or not isinstance(lock, dict):
            raise protocol.ProtocolError("localization documents must be objects")
        errors.extend(_scan_forbidden(result))
        errors.extend(_scan_forbidden(lock))
        if result.get("protocol") != protocol.PROTOCOL_ID or result.get("state_slice") != protocol.STATE_SLICE:
            errors.append("result_protocol_or_state_slice_mismatch")
        if lock.get("protocol") != protocol.PROTOCOL_ID or lock.get("state_slice") != protocol.STATE_SLICE:
            errors.append("lock_protocol_or_state_slice_mismatch")
        if result.get("aggregate_only_retention") is not True:
            errors.append("aggregate_retention_invalid")
        if result.get("candidate_layers") != list(protocol.CANDIDATE_LAYERS) or lock.get("candidate_layers") != list(protocol.CANDIDATE_LAYERS):
            errors.append("candidate_layer_binding_mismatch")
        if result.get("fixed_position") != protocol.FIXED_POSITION:
            errors.append("position_binding_mismatch")
        if result.get("measured_splits") != ["fit", "tune"] or lock.get("measured_splits") != ["fit", "tune"]:
            errors.append("split_order_invalid")
        if lock.get("assessment_effects_locked") is not True or lock.get("prediction_lock_before_assessment") is not True or lock.get("assessment_opened") is not False:
            errors.append("assessment_lock_invalid")
        if result.get("assessment_opened") is not False or result.get("assessment_effects_present") is not False:
            errors.append("assessment_should_be_closed")
        if result.get("panel_manifest_sha256") != protocol.sha256_file(panel_root.resolve() / "panel-manifest.json") or lock.get("panel_manifest_sha256") != result.get("panel_manifest_sha256"):
            errors.append("panel_binding_mismatch")
        if result.get("qualification_result_sha256") != protocol.sha256_file(qualification_root.resolve() / "qualification-result.json") or lock.get("qualification_result_sha256") != result.get("qualification_result_sha256"):
            errors.append("qualification_binding_mismatch")
        model_manifest = protocol.model_manifest(model_root.resolve())
        if result.get("model_manifest_sha256") != model_manifest["manifest_sha256"] or lock.get("model_manifest_sha256") != result.get("model_manifest_sha256"):
            errors.append("model_binding_mismatch")
        if lock.get("configuration_lock_sha256") != runner._configuration_lock_digest(lock) or result.get("configuration_lock_sha256") != lock.get("configuration_lock_sha256"):
            errors.append("configuration_lock_digest_mismatch")
        if result.get("selection_rule") != "lowest_numeric_candidate_layer_passing_all_tune_gates" or lock.get("selection_rule") != result.get("selection_rule"):
            errors.append("selection_rule_mismatch")
        splits = result.get("splits")
        if not isinstance(splits, dict) or set(splits) != {"fit", "tune"}:
            errors.append("split_result_census_invalid")
        else:
            _check_split(splits["fit"], errors, "fit")
            _check_split(splits["tune"], errors, "tune")
        tune_layers = splits.get("tune", {}).get("layer_summaries", {}) if isinstance(splits, dict) else {}
        recomputed_passing = [layer for layer in protocol.CANDIDATE_LAYERS if isinstance(tune_layers.get(str(layer)), dict) and all(tune_layers[str(layer)].get("reliability", {}).get("gates", {}).values())]
        if result.get("passing_layers") != recomputed_passing:
            errors.append("passing_layer_recomputation_mismatch")
        if result.get("tune_passed") is not bool(recomputed_passing):
            errors.append("tune_pass_aggregate_mismatch")
        selected = result.get("selected_layer")
        if selected != (min(recomputed_passing) if recomputed_passing else None):
            errors.append("selected_layer_rule_mismatch")
        classification = result.get("classification")
        if not recomputed_passing:
            if classification != "TargetLocalizationNoCandidate" or result.get("claim_ceiling") != "LocalDevelopmentV43TargetLocalizationNoCandidate":
                errors.append("no_candidate_disposition_mismatch")
        elif classification != "ReviewRequired" or result.get("claim_ceiling") != "LocalDevelopmentV43TargetLocalizationReviewRequired" or result.get("review_verified") is not False:
            errors.append("review_disposition_mismatch")
        expected_files = {"configuration-lock.json", "localization-result.json"}
        actual_files = {candidate.relative_to(localization_root).as_posix() for candidate in localization_root.rglob("*") if candidate.is_file()}
        if not actual_files <= expected_files | {"validator-receipt.json"} or not expected_files <= actual_files:
            errors.append("output_census_invalid")
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    result_digest = protocol.sha256_file(localization_root / "localization-result.json") if (localization_root / "localization-result.json").is_file() else None
    return _receipt(errors, result_digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("localization_root", type=Path)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"))
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate_with_corpus(args.localization_root, args.panel_root, args.corpus_root, args.qualification_root, args.model, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.localization_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independently validate the aggregate-only V44 measurement result.

State slice: astral-stage0c-qwen36-causal-target-measurement-invariance-v44.
The validator rejects raw prompts, activations, logits, traces, effects, and
predictions from the result root; input custody remains separately bound.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

import protocol_v44 as protocol
import run_measurement_invariance_v44 as runner
import validate_gutenberg_corpus_v44 as corpus_validator
import validate_panel_v44 as panel_validator
import validate_qualification_v44 as qualification_validator


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
        "claim_ceiling": "LocalDevelopmentV44MeasurementInvarianceValidated",
        "classification": "MeasurementInvarianceValidated" if not errors else "MeasurementInvarianceInvalid",
        "valid": not errors,
        "errors": errors,
        "invariance_result_sha256": result_digest,
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


def _check_cell(cell: Any, errors: list[str], label: str) -> None:
    if not isinstance(cell, dict):
        errors.append(f"cell_missing:{label}")
        return
    if not isinstance(cell.get("layer"), int) or cell.get("layer") not in protocol.CANDIDATE_LAYERS:
        errors.append(f"cell_layer_invalid:{label}")
    if cell.get("position") not in protocol.POSITION_NAMES or cell.get("position_offset") != protocol.POSITION_BY_NAME.get(cell.get("position")):
        errors.append(f"cell_position_invalid:{label}")
    if cell.get("family_count") != protocol.FAMILIES_PER_SPLIT or cell.get("document_count") != protocol.DOCUMENTS_PER_SPLIT:
        errors.append(f"cell_census_mismatch:{label}")
    activation = cell.get("activation_only")
    text_only = cell.get("text_only")
    if not isinstance(activation, dict) or set(activation) != set(protocol.WRAPPER_NAMES):
        errors.append(f"activation_invalid:{label}")
    else:
        for wrapper in protocol.WRAPPER_NAMES:
            _check_stats(activation[wrapper], protocol.FAMILIES_PER_SPLIT, errors, f"{label}:activation:{wrapper}")
    if not isinstance(text_only, dict) or set(text_only) != set(protocol.WRAPPER_NAMES):
        errors.append(f"text_invalid:{label}")
    else:
        for wrapper in protocol.WRAPPER_NAMES:
            _check_stats(text_only[wrapper], protocol.FAMILIES_PER_SPLIT, errors, f"{label}:text:{wrapper}")
    controls = cell.get("controls")
    expected_controls = {"exact_copy", "shuffled", "constant", "matched"}
    if not isinstance(controls, dict) or set(controls) != expected_controls:
        errors.append(f"controls_invalid:{label}")
    else:
        for control_name, stats in controls.items():
            _check_stats(stats, protocol.FAMILIES_PER_SPLIT * len(protocol.WRAPPER_NAMES), errors, f"{label}:control:{control_name}")
    for key in ("matched_norm_relative_error_max", "repeat_max_abs_effect_delta"):
        if not _finite(cell.get(key)):
            errors.append(f"control_numeric_invalid:{label}:{key}")
    if cell.get("matched_donor_violations") != 0:
        errors.append(f"matched_donor_violation:{label}")
    if _finite(cell.get("matched_norm_relative_error_max")) and float(cell["matched_norm_relative_error_max"]) > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
        errors.append(f"matched_norm_invalid:{label}")
    reliability = cell.get("reliability")
    expected_gates = {
        "target_effect_non_degenerate", "wrapper_correlation", "wrapper_sign_agreement", "bootstrap_correlation",
        "exact_copy_control", "shuffled_control", "constant_control", "matched_control", "repeatability",
    }
    reliability_keys = (
        "wrapper_correlation", "wrapper_sign_agreement", "bootstrap_correlation_lower_95",
        "wrapper_alpha_effect_std", "wrapper_beta_effect_std", "wrapper_gamma_effect_std", "target_effect_std_min",
    )
    if not isinstance(reliability, dict):
        errors.append(f"reliability_missing:{label}")
        return
    for key in reliability_keys:
        if not _finite(reliability.get(key)):
            errors.append(f"reliability_nonfinite:{label}:{key}")
    pairwise = reliability.get("pairwise")
    expected_pairs = [(left, right) for left, right in itertools.combinations(protocol.WRAPPER_NAMES, 2)]
    if not isinstance(pairwise, list) or len(pairwise) != len(expected_pairs):
        errors.append(f"pairwise_invalid:{label}")
    else:
        for pair, expected_pair in zip(pairwise, expected_pairs):
            if not isinstance(pair, dict) or (pair.get("left_wrapper"), pair.get("right_wrapper")) != expected_pair:
                errors.append(f"pair_binding_invalid:{label}")
                continue
            for key in ("correlation", "sign_agreement", "bootstrap_correlation_lower_95"):
                if not _finite(pair.get(key)):
                    errors.append(f"pair_metric_nonfinite:{label}:{key}")
        if all(isinstance(pair, dict) for pair in pairwise):
            if reliability.get("wrapper_correlation") != min(pair["correlation"] for pair in pairwise):
                errors.append(f"pair_correlation_min_mismatch:{label}")
            if reliability.get("wrapper_sign_agreement") != min(pair["sign_agreement"] for pair in pairwise):
                errors.append(f"pair_sign_min_mismatch:{label}")
            if reliability.get("bootstrap_correlation_lower_95") != min(pair["bootstrap_correlation_lower_95"] for pair in pairwise):
                errors.append(f"pair_bootstrap_min_mismatch:{label}")
    expected_std_min = min(reliability.get("wrapper_alpha_effect_std", float("nan")), reliability.get("wrapper_beta_effect_std", float("nan")), reliability.get("wrapper_gamma_effect_std", float("nan")))
    if _finite(expected_std_min) and reliability.get("target_effect_std_min") != expected_std_min:
        errors.append(f"std_min_mismatch:{label}")
    gates = reliability.get("gates")
    if not isinstance(gates, dict) or set(gates) != expected_gates or any(not isinstance(value, bool) for value in gates.values()):
        errors.append(f"reliability_gates_invalid:{label}")
    elif isinstance(controls, dict):
        expected_gate_values = {
            "target_effect_non_degenerate": reliability["target_effect_std_min"] >= protocol.MIN_TARGET_EFFECT_STD,
            "wrapper_correlation": reliability["wrapper_correlation"] >= protocol.MIN_TARGET_CORRELATION,
            "wrapper_sign_agreement": reliability["wrapper_sign_agreement"] >= protocol.MIN_TARGET_SIGN_AGREEMENT,
            "bootstrap_correlation": reliability["bootstrap_correlation_lower_95"] >= protocol.MIN_BOOTSTRAP_CORRELATION_LOWER,
            "exact_copy_control": controls["exact_copy"]["mean_abs"] <= protocol.MAX_EXACT_COPY_ABS_EFFECT,
            "shuffled_control": abs(controls["shuffled"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
            "constant_control": abs(controls["constant"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
            "matched_control": abs(controls["matched"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
            "repeatability": float(cell["repeat_max_abs_effect_delta"]) <= protocol.MAX_REPEAT_ABS_EFFECT_DELTA,
        }
        if gates != expected_gate_values:
            errors.append(f"reliability_gate_arithmetic_mismatch:{label}")


def validate_with_corpus(measurement_root: Path, panel_root: Path, corpus_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    measurement_root = measurement_root.resolve()
    try:
        protocol.assert_external(measurement_root, repository_root)
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
        result_path = measurement_root / "invariance-result.json"
        lock_path = measurement_root / "configuration-lock.json"
        result = _strict_json(result_path)
        lock = _strict_json(lock_path)
        if not isinstance(result, dict) or not isinstance(lock, dict):
            raise protocol.ProtocolError("measurement documents must be objects")
        errors.extend(_scan_forbidden(result))
        errors.extend(_scan_forbidden(lock))
        for document, label in ((result, "result"), (lock, "lock")):
            if document.get("protocol") != protocol.PROTOCOL_ID or document.get("state_slice") != protocol.STATE_SLICE:
                errors.append(f"{label}_protocol_or_state_slice_mismatch")
        if result.get("aggregate_only_retention") is not True:
            errors.append("aggregate_retention_invalid")
        for document in (result, lock):
            if document.get("candidate_layers") != list(protocol.CANDIDATE_LAYERS) or document.get("position_names") != list(protocol.POSITION_NAMES) or document.get("position_offsets") != list(protocol.POSITION_OFFSETS) or document.get("position_rule") != protocol.FIXED_POSITION_RULE:
                errors.append("target_binding_mismatch")
        if result.get("measured_splits") != ["fit", "tune"] or lock.get("measured_splits") != ["fit", "tune"]:
            errors.append("split_order_invalid")
        if lock.get("assessment_effects_locked") is not True or lock.get("prediction_lock_before_assessment") is not True or lock.get("assessment_opened") is not False:
            errors.append("assessment_lock_invalid")
        if result.get("assessment_opened") is not False or result.get("assessment_effects_present") is not False:
            errors.append("assessment_should_be_closed")
        panel_digest = protocol.sha256_file(panel_root.resolve() / "panel-manifest.json")
        qualification_digest = protocol.sha256_file(qualification_root.resolve() / "qualification-result.json")
        model_manifest = protocol.model_manifest(model_root.resolve())
        for document in (result, lock):
            if document.get("panel_manifest_sha256") != panel_digest or document.get("qualification_result_sha256") != qualification_digest or document.get("model_manifest_sha256") != model_manifest["manifest_sha256"]:
                errors.append("custody_binding_mismatch")
        if lock.get("configuration_lock_sha256") != runner._configuration_lock_digest(lock) or result.get("configuration_lock_sha256") != lock.get("configuration_lock_sha256"):
            errors.append("configuration_lock_digest_mismatch")
        if result.get("selection_rule") != "lowest_numeric_layer_then_final_before_penultimate_passing_all_tune_gates" or lock.get("selection_rule") != result.get("selection_rule"):
            errors.append("selection_rule_mismatch")
        source_sha = result.get("source_sha256")
        if not isinstance(source_sha, dict) or source_sha.get("protocol") != protocol.sha256_file(Path(protocol.__file__).resolve()) or source_sha.get("runner") != protocol.sha256_file(Path(runner.__file__).resolve()):
            errors.append("source_digest_mismatch")
        splits = result.get("splits")
        if not isinstance(splits, dict) or set(splits) != {"fit", "tune"}:
            errors.append("split_result_census_invalid")
        else:
            expected_cells = {f"{layer}:{position}" for layer in protocol.CANDIDATE_LAYERS for position in protocol.POSITION_NAMES}
            for split_name in ("fit", "tune"):
                split = splits.get(split_name)
                if not isinstance(split, dict) or split.get("family_count") != protocol.FAMILIES_PER_SPLIT or split.get("document_count") != protocol.DOCUMENTS_PER_SPLIT:
                    errors.append(f"split_census_mismatch:{split_name}")
                    continue
                cells = split.get("cell_summaries")
                if not isinstance(cells, dict) or set(cells) != expected_cells:
                    errors.append(f"cell_census_invalid:{split_name}")
                    continue
                for cell_key in sorted(expected_cells):
                    _check_cell(cells[cell_key], errors, f"{split_name}:{cell_key}")
        tune_cells = splits.get("tune", {}).get("cell_summaries", {}) if isinstance(splits, dict) else {}
        recomputed_passing = [
            {"layer": layer, "position": position}
            for layer in protocol.CANDIDATE_LAYERS
            for position in protocol.POSITION_NAMES
            if isinstance(tune_cells.get(f"{layer}:{position}"), dict)
            and all(tune_cells[f"{layer}:{position}"].get("reliability", {}).get("gates", {}).values())
        ]
        if result.get("passing_targets") != recomputed_passing or lock.get("passing_targets") != recomputed_passing:
            errors.append("passing_target_recomputation_mismatch")
        selected = recomputed_passing[0] if recomputed_passing else None
        if result.get("selected_target") != selected or lock.get("selected_target") != selected:
            errors.append("selected_target_rule_mismatch")
        if result.get("tune_passed") != bool(recomputed_passing):
            errors.append("tune_pass_aggregate_mismatch")
        if result.get("review_verified") is not False or result.get("assessment_opened") is not False:
            errors.append("review_or_assessment_state_invalid")
        if selected is None:
            if result.get("classification") != "MeasurementInvarianceNoCandidate" or result.get("claim_ceiling") != runner.CLAIM_CEILING_NO_CANDIDATE or result.get("review_required_before_assessment") is not False:
                errors.append("no_candidate_disposition_mismatch")
        elif result.get("classification") != "ReviewRequired" or result.get("claim_ceiling") != runner.CLAIM_CEILING_REVIEW or result.get("review_required_before_assessment") is not True:
            errors.append("review_disposition_mismatch")
        expected_files = {"configuration-lock.json", "invariance-result.json"}
        actual_files = {candidate.relative_to(measurement_root).as_posix() for candidate in measurement_root.rglob("*") if candidate.is_file()}
        if not actual_files <= expected_files | {"validator-receipt.json"} or not expected_files <= actual_files:
            errors.append("output_census_invalid")
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    result_digest = protocol.sha256_file(measurement_root / "invariance-result.json") if (measurement_root / "invariance-result.json").is_file() else None
    return _receipt(errors, result_digest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("measurement_root", type=Path)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"))
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate_with_corpus(args.measurement_root, args.panel_root, args.corpus_root, args.qualification_root, args.model, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.measurement_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

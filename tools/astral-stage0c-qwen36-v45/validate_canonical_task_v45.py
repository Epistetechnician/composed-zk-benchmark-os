#!/usr/bin/env python3
"""Independently validate V45 aggregate-only measurement output.

State slice: astral-stage0c-qwen36-response-anchored-causal-target-v45.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import protocol_v45 as protocol


FORBIDDEN_KEYS = {"prompt", "prompts", "token", "tokens", "activation", "activations", "logit", "logits", "trace", "traces", "per_family", "per-family"}


def _receipt(errors: list[str], digest: str | None, classification: str) -> dict[str, Any]:
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV45CanonicalTaskValidated" if not errors else "LocalDevelopmentV45ValidationFailed",
        "classification": classification if not errors else "CanonicalTaskInvalid",
        "valid": not errors,
        "errors": errors,
        "result_sha256": digest,
        "independent_validation": True,
    }


def _scan_forbidden(value: Any, location: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("_", "-")
            if normalized in FORBIDDEN_KEYS or any(marker in normalized for marker in ("per-family", "raw-activation", "raw-logit")):
                errors.append(f"forbidden_raw_key:{location}.{key}")
            errors.extend(_scan_forbidden(child, f"{location}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_scan_forbidden(child, f"{location}[{index}]"))
    return errors


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _check_summary(value: Any, expected_count: int, errors: list[str], label: str) -> None:
    if not isinstance(value, dict) or value.get("count") != expected_count:
        errors.append(f"summary_shape:{label}")
        return
    for key in ("mean", "std", "mean_abs", "min", "max"):
        if not _finite_number(value.get(key)):
            errors.append(f"summary_numeric:{label}:{key}")


def _check_cell(cell: Any, errors: list[str], label: str, family_count: int) -> None:
    if not isinstance(cell, dict):
        errors.append(f"cell_not_object:{label}")
        return
    if cell.get("family_count") != family_count or cell.get("position") != protocol.POSITION_NAME or cell.get("position_rule") != protocol.POSITION_RULE:
        errors.append(f"cell_binding:{label}")
    _check_summary(cell.get("activation_only"), family_count, errors, f"{label}:activation")
    _check_summary(cell.get("text_only"), family_count, errors, f"{label}:text")
    controls = cell.get("controls")
    if not isinstance(controls, dict) or set(controls) != {"exact_copy", "shuffled", "constant", "matched"}:
        errors.append(f"cell_controls:{label}")
    else:
        for control_name, summary in controls.items():
            _check_summary(summary, family_count, errors, f"{label}:{control_name}")
    reliability = cell.get("reliability")
    gates = reliability.get("gates") if isinstance(reliability, dict) else None
    expected_gates = {"target_effect_non_degenerate", "exact_copy_control", "shuffled_control", "constant_control", "matched_control", "repeatability"}
    if not isinstance(gates, dict) or set(gates) != expected_gates or any(value not in (True, False) for value in gates.values()):
        errors.append(f"cell_gates:{label}")
    if not _finite_number(cell.get("matched_norm_relative_error_max")) or cell.get("matched_donor_violations") != 0 or not _finite_number(cell.get("repeat_max_abs_effect_delta")):
        errors.append(f"cell_diagnostics:{label}")


def validate(measurement_root: Path, panel_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    measurement_root = measurement_root.resolve()
    try:
        for path in (measurement_root, panel_root, qualification_root, model_root):
            protocol.assert_external(path, repository_root)
        result_path = measurement_root / "canonical-task-result.json"
        lock_path = measurement_root / "configuration-lock.json"
        result = protocol.read_json(result_path)
        lock = protocol.read_json(lock_path)
        panel = protocol.read_json(panel_root / "panel-manifest.json")
        qualification = protocol.read_json(qualification_root / "qualification-result.json")
        panel_receipt = protocol.read_json(panel_root / "validator-receipt.json")
        qualification_receipt = protocol.read_json(qualification_root / "validator-receipt.json")
        if not isinstance(result, dict) or not isinstance(lock, dict):
            raise protocol.ProtocolError("result and lock must be objects")
        errors.extend(_scan_forbidden(result))
        errors.extend(_scan_forbidden(lock))
        if result.get("protocol") != protocol.PROTOCOL_ID or lock.get("protocol") != protocol.PROTOCOL_ID:
            errors.append("protocol_mismatch")
        if result.get("state_slice") != protocol.STATE_SLICE or lock.get("state_slice") != protocol.STATE_SLICE:
            errors.append("state_slice_mismatch")
        if panel_receipt.get("valid") is not True or qualification_receipt.get("valid") is not True:
            errors.append("upstream_receipt_invalid")
        if panel_receipt.get("protocol_source_sha256") != protocol.sha256_file(Path(protocol.__file__).resolve()):
            errors.append("panel_protocol_source_digest")
        model_manifest = protocol.model_manifest(model_root)
        expected_panel_digest = protocol.sha256_file(panel_root / "panel-manifest.json")
        expected_qualification_digest = protocol.sha256_file(qualification_root / "qualification-result.json")
        if result.get("panel_manifest_sha256") != expected_panel_digest or lock.get("panel_manifest_sha256") != expected_panel_digest:
            errors.append("panel_digest_binding")
        if result.get("qualification_result_sha256") != expected_qualification_digest or lock.get("qualification_result_sha256") != expected_qualification_digest:
            errors.append("qualification_digest_binding")
        if result.get("model_manifest_sha256") != model_manifest["manifest_sha256"] or lock.get("model_manifest_sha256") != model_manifest["manifest_sha256"]:
            errors.append("model_digest_binding")
        result_sources = result.get("source_sha256")
        runner_source = Path(__file__).with_name("run_canonical_task_v45.py").resolve()
        if not isinstance(result_sources, dict) or result_sources.get("protocol") != protocol.sha256_file(Path(protocol.__file__).resolve()) or result_sources.get("runner") != protocol.sha256_file(runner_source):
            errors.append("result_source_digest_binding")
        if qualification.get("protocol_source_sha256") != protocol.sha256_file(Path(protocol.__file__).resolve()):
            errors.append("qualification_protocol_source_digest")
        if qualification.get("classification") != "InstrumentFeasibility" or not all(qualification.get("gates", {}).values()):
            errors.append("qualification_not_passing")
        if panel.get("protocol") != protocol.PROTOCOL_ID or panel.get("state_slice") != protocol.STATE_SLICE:
            errors.append("panel_binding")
        for value, expected, label in ((result.get("candidate_layers"), list(protocol.CANDIDATE_LAYERS), "candidate_layers"), (result.get("position_name"), protocol.POSITION_NAME, "position_name"), (result.get("position_rule"), protocol.POSITION_RULE, "position_rule"), (result.get("feature_map_id"), protocol.FEATURE_MAP_ID, "feature_map_id"), (result.get("ridge_alphas"), list(protocol.RIDGE_ALPHAS), "ridge_alphas")):
            if value != expected:
                errors.append(f"binding:{label}")
        if result.get("assessment_opened") is not False or result.get("assessment_effects_present") is not False:
            errors.append("assessment_not_closed")
        if result.get("prediction_lock_before_assessment") is not True or lock.get("prediction_lock_before_assessment") is not True:
            errors.append("prediction_lock_missing")
        splits = result.get("splits")
        if not isinstance(splits, dict) or set(splits) != {"fit", "tune"}:
            errors.append("split_shape")
        else:
            for split, expected_count in (("fit", protocol.FAMILIES_PER_SPLIT), ("tune", protocol.FAMILIES_PER_SPLIT)):
                split_result = splits.get(split)
                if not isinstance(split_result, dict) or split_result.get("family_count") != expected_count:
                    errors.append(f"split_count:{split}")
                    continue
                cells = split_result.get("cell_summaries")
                expected_cells = {f"{layer}:{protocol.POSITION_NAME}" for layer in protocol.CANDIDATE_LAYERS}
                if not isinstance(cells, dict) or set(cells) != expected_cells:
                    errors.append(f"cell_keys:{split}")
                    continue
                for cell_key, cell in cells.items():
                    _check_cell(cell, errors, f"{split}:{cell_key}", expected_count)
                if split == "tune":
                    for cell_key, cell in cells.items():
                        predictors = cell.get("predictors") if isinstance(cell, dict) else None
                        if not isinstance(predictors, dict) or set(predictors) != {f"alpha={alpha:g}" for alpha in protocol.RIDGE_ALPHAS}:
                            errors.append(f"predictor_keys:{cell_key}")
                        else:
                            for alpha_key, metrics in predictors.items():
                                if not isinstance(metrics, dict) or not all(_finite_number(metrics.get(key)) for key in ("correlation", "sign_agreement", "bootstrap_correlation_lower_95")):
                                    errors.append(f"predictor_metrics:{cell_key}:{alpha_key}")
                                gates = metrics.get("gates") if isinstance(metrics, dict) else None
                                if not isinstance(gates, dict) or set(gates) != {"prediction_correlation", "prediction_sign_agreement", "bootstrap_correlation"} or any(value not in (True, False) for value in gates.values()):
                                    errors.append(f"predictor_gates:{cell_key}:{alpha_key}")
        passing = result.get("passing_targets")
        selected = result.get("selected_target")
        if not isinstance(passing, list):
            errors.append("passing_targets_shape")
            passing = []
        if selected is not None and selected not in passing:
            errors.append("selected_target_not_passing")
        classification = result.get("classification")
        if classification == "CanonicalTaskNoCandidate" and (passing or selected is not None):
            errors.append("no_candidate_binding")
        if classification == "ReviewRequired" and selected is None:
            errors.append("review_required_without_target")
        expected_files = {"canonical-task-result.json", "configuration-lock.json"}
        actual_files = {candidate.relative_to(measurement_root).as_posix() for candidate in measurement_root.rglob("*") if candidate.is_file()}
        allowed = expected_files | {"validator-receipt.json", "review-receipt.json", "assessment-result.json", "assessment-validator-receipt.json"}
        if not actual_files <= allowed or not expected_files <= actual_files:
            errors.append("output_census_invalid")
        if lock.get("configuration_lock_sha256") != protocol.canonical_digest({key: value for key, value in lock.items() if key != "configuration_lock_sha256"}):
            errors.append("lock_digest_invalid")
        digest = protocol.sha256_file(result_path)
        output_classification = "CanonicalTaskValidated" if classification == "CanonicalTaskNoCandidate" else "CanonicalTaskReviewRequired"
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
        digest = protocol.sha256_file(measurement_root / "canonical-task-result.json") if (measurement_root / "canonical-task-result.json").is_file() else None
        output_classification = "CanonicalTaskInvalid"
    return _receipt(errors, digest, output_classification)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("measurement_root", type=Path)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.measurement_root, args.panel_root, args.qualification_root, args.model, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.measurement_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

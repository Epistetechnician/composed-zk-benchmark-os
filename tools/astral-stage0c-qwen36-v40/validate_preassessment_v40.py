#!/usr/bin/env python3
"""Validate the V40 fit/tune bundle and prediction-lock boundary.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

The validator checks that assessment effects were absent when estimator states
were sealed and that no per-family predictions or raw intermediates were
retained.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import panel_v40 as panel
import protocol_v40 as protocol
import validate_panel_v40 as panel_validator
import validate_qualification_v40 as qualification_validator


def validate(preassessment_root: Path, panel_root: Path, corpus_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    preassessment_root = preassessment_root.resolve()
    try:
        protocol.assert_external(preassessment_root, repository_root)
        panel_receipt = panel_validator.validate(panel_root.resolve(), corpus_root.resolve(), model_root.resolve(), repository_root)
        qualification_receipt = qualification_validator.validate(qualification_root.resolve(), model_root.resolve(), repository_root)
        if not panel_receipt["valid"]:
            errors.append("panel_validation_failed")
        if not qualification_receipt["valid"]:
            errors.append("qualification_validation_failed")
        summary_path = preassessment_root / "fit-tune-summary.json"
        lock_path = preassessment_root / "prediction-lock.json"
        run_path = preassessment_root / "run-manifest.json"
        summary = protocol.read_json(summary_path)
        lock = protocol.read_json(lock_path)
        run = protocol.read_json(run_path)
        if summary.get("protocol") != protocol.PROTOCOL_ID or lock.get("protocol") != protocol.PROTOCOL_ID or run.get("protocol") != protocol.PROTOCOL_ID:
            errors.append("protocol_mismatch")
        if any(value.get("state_slice") != protocol.STATE_SLICE for value in (summary, lock, run)):
            errors.append("state_slice_mismatch")
        if summary.get("classification") != "PreassessmentPredictionLocked":
            errors.append("classification_mismatch")
        if summary.get("claim_ceiling") != "LocalDevelopmentV40PreassessmentPredictionLocked":
            errors.append("claim_ceiling_mismatch")
        for value in (summary, lock, run):
            if value.get("assessment_effects_absent") is not True and value.get("assessment_effects_present") is not False:
                errors.append("assessment_effect_state_invalid")
            if value.get("assessment_effects_measured") is not False:
                errors.append("assessment_effects_measured")
            if value.get("raw_intermediates_retained") is not False or value.get("aggregate_only") is not True:
                errors.append("retention_state_invalid")
        if lock.get("prediction_locked_before_assessment") is not True or run.get("prediction_locked_before_assessment") is not True:
            errors.append("prediction_lock_missing")
        if lock.get("per_family_predictions_retained") is not False or summary.get("per_family_predictions_retained") is not False:
            errors.append("per_family_predictions_present")
        if lock.get("assessment_family_ids") != sorted(lock.get("assessment_family_ids", [])):
            errors.append("assessment_family_order_not_canonical")
        if len(lock.get("assessment_family_ids", [])) != protocol.FAMILIES_PER_SPLIT:
            errors.append("assessment_family_count_mismatch")
        states = lock.get("estimator_states")
        if not isinstance(states, dict) or set(states) != set(protocol.CONTROL_NAMES) - {"matched"}:
            errors.append("estimator_state_names_mismatch")
        else:
            for name, state in states.items():
                if name == "constant":
                    if set(state) != {"target_mean"}:
                        errors.append("constant_state_invalid")
                    continue
                if len(state.get("feature_mean", [])) != protocol.FEATURE_WIDTH or len(state.get("feature_scale", [])) != protocol.FEATURE_WIDTH or len(state.get("coefficients", [])) != protocol.FEATURE_WIDTH:
                    errors.append(f"state_width_mismatch:{name}")
        expected_digests = {
            "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
            "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
            "concept_registry_sha256": protocol.sha256_file(panel_root / "concept-registry.json"),
            "split_manifest_sha256": protocol.sha256_file(panel_root / "split-manifest.json"),
            "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
            "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
        }
        for key, expected in expected_digests.items():
            if lock.get(key) != expected or summary.get(key) != expected or run.get(key) != expected:
                errors.append(f"digest_binding_mismatch:{key}")
        if run.get("prediction_lock_sha256") != protocol.canonical_digest(lock):
            errors.append("prediction_lock_digest_mismatch")
        if run.get("fit_tune_summary_sha256") != protocol.canonical_digest(summary):
            errors.append("summary_digest_mismatch")
        panel_names = summary.get("panels", {})
        if set(panel_names) != set(protocol.CONTROL_NAMES):
            errors.append("summary_panel_names_mismatch")
        for name, panel_summary in panel_names.items():
            if panel_summary.get("fit_count") != protocol.FAMILIES_PER_SPLIT or panel_summary.get("tune_count") != protocol.FAMILIES_PER_SPLIT:
                errors.append(f"summary_count_mismatch:{name}")
        expected_files = {"fit-tune-summary.json", "prediction-lock.json", "run-manifest.json"}
        actual_files = {path.relative_to(preassessment_root).as_posix() for path in preassessment_root.rglob("*") if path.is_file()}
        if not actual_files <= expected_files | {"validator-receipt.json"} or not expected_files <= actual_files:
            errors.append("output_census_mismatch")
    except (OSError, json.JSONDecodeError, protocol.ProtocolError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentV40PreassessmentPredictionLocked",
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
    receipt = validate(args.preassessment_root, args.panel_root, args.corpus_root, args.qualification_root, args.model, args.repository_root)
    if args.write_receipt:
        protocol.write_json(args.preassessment_root / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

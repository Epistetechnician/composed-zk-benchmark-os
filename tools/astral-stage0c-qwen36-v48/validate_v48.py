#!/usr/bin/env python3
"""Independently validate V48 aggregate-only fit/tune results.

State slice: astral-stage0c-cross-view-causal-state-transport-v48.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import protocol_v48 as protocol


ALLOWED_CLASSIFICATIONS = {"DevelopmentNoCandidate", "ReviewRequired"}
FORBIDDEN_EXACT_KEYS = {
    "prompt", "prompts", "token", "tokens", "activation", "activations",
    "logit", "logits", "trace", "traces", "transcript", "pii", "credential",
    "password", "secret",
}
FORBIDDEN_KEY_MARKERS = (
    "raw-activation", "raw_activation", "raw-logit", "raw_logit", "per_family",
    "per-family", "generated_text", "generated-text",
)
ALLOWED_RESULT_KEYS = {
    "protocol", "state_slice", "repeat_index", "classification", "claim_ceiling",
    "aggregate_only_retention", "assessment_opened", "assessment_effects_present",
    "review_required_before_assessment", "review_verified", "prediction_lock_before_assessment",
    "panel_manifest_sha256", "qualification_result_sha256", "model_manifest_sha256",
    "configuration_lock_sha256", "operator", "controls", "selected_alpha", "measured_splits",
    "fit_tune_gates", "fit", "tune", "predictors", "recoverability", "power_simulation",
    "source_sha256",
}
ALLOWED_LOCK_KEYS = {
    "protocol", "state_slice", "repeat_index", "source_layer", "destination_layer",
    "position_name", "position_rule", "alpha", "additional_passes", "feature_map_id",
    "ridge_alphas", "selected_target", "prediction_digests", "measured_splits", "events",
    "panel_manifest_sha256", "qualification_result_sha256", "model_manifest_sha256",
    "assessment_opened", "prediction_lock_before_assessment", "configuration_lock_sha256",
}


def _walk_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            keys.append(str(key).lower())
            keys.extend(_walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.extend(_walk_keys(child))
    return keys


def _validate_one(root: Path, repository_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    root = root.resolve()
    repository_root = repository_root.resolve()
    try:
        protocol.assert_external(root, repository_root)
        result = protocol.read_json(root / "causal-state-transport-result.json")
        lock = protocol.read_json(root / "configuration-lock.json")
        prediction_lock = protocol.read_json(root / "prediction-lock.json")
    except (OSError, ValueError, json.JSONDecodeError, KeyError, protocol.ProtocolError) as exc:
        return {}, {}, [f"load:{type(exc).__name__}:{exc}"]
    if set(result) != ALLOWED_RESULT_KEYS:
        errors.append("result_schema")
    if set(lock) != ALLOWED_LOCK_KEYS:
        errors.append("lock_schema")
    if result.get("protocol") != protocol.PROTOCOL_ID or lock.get("protocol") != protocol.PROTOCOL_ID or prediction_lock.get("protocol") != protocol.PROTOCOL_ID:
        errors.append("protocol_identity")
    if result.get("state_slice") != protocol.STATE_SLICE or lock.get("state_slice") != protocol.STATE_SLICE or prediction_lock.get("state_slice") != protocol.STATE_SLICE:
        errors.append("state_slice_identity")
    if result.get("repeat_index") != lock.get("repeat_index") or result.get("repeat_index") != prediction_lock.get("repeat_index"):
        errors.append("repeat_identity")
    if result.get("classification") not in ALLOWED_CLASSIFICATIONS:
        errors.append("classification")
    if result.get("assessment_opened") is not False or result.get("assessment_effects_present") is not False:
        errors.append("assessment_opened")
    if result.get("review_verified") is not False or lock.get("assessment_opened") is not False or prediction_lock.get("assessment_opened") is not False:
        errors.append("review_or_assessment_state")
    if result.get("aggregate_only_retention") is not True or result.get("prediction_lock_before_assessment") is not True:
        errors.append("retention_or_lock_policy")
    if result.get("panel_manifest_sha256") != lock.get("panel_manifest_sha256") or result.get("qualification_result_sha256") != lock.get("qualification_result_sha256") or result.get("model_manifest_sha256") != lock.get("model_manifest_sha256"):
        errors.append("custody_binding")
    expected_lock_digest = dict(lock)
    expected_lock_digest.pop("configuration_lock_sha256", None)
    if lock.get("configuration_lock_sha256") != protocol.canonical_digest(expected_lock_digest):
        errors.append("configuration_lock_digest")
    if lock.get("prediction_digests") != prediction_lock.get("prediction_digests"):
        errors.append("prediction_lock_digest")
    if prediction_lock.get("tune_effects_generated") is not False:
        errors.append("prediction_lock_order")
    events = lock.get("events")
    if not isinstance(events, list) or [event.get("event") for event in events] != ["fit_effects_generated", "tune_predictions_emitted_and_digested", "tune_effects_generated"]:
        errors.append("event_order")
    if lock.get("selected_target") is not None and result.get("selected_alpha") is None:
        errors.append("selected_target_binding")
    if result.get("classification") == "DevelopmentNoCandidate" and result.get("selected_alpha") is not None:
        errors.append("no_candidate_selection")
    if result.get("classification") == "ReviewRequired" and result.get("review_required_before_assessment") is not True:
        errors.append("review_requirement")
    if result.get("operator") != {
        "source_layer": protocol.SOURCE_LAYER,
        "destination_layer": protocol.DESTINATION_LAYER,
        "position_name": protocol.POSITION_NAME,
        "position_rule": protocol.POSITION_RULE,
        "alpha": protocol.ALPHA,
        "additional_passes": protocol.ADDITIONAL_PASSES,
    }:
        errors.append("operator_contract")
    if result.get("controls") != ["activation_only", "text_only", "input_only", "exact_copy", "shuffled", "constant", "matched", "access_null", "matched_norm"]:
        errors.append("control_contract")
    gates = result.get("fit_tune_gates")
    if not isinstance(gates, dict) or not isinstance(gates.get("all"), bool):
        errors.append("gate_contract")
    if result.get("classification") == "DevelopmentNoCandidate" and gates.get("all") is not False:
        errors.append("negative_gate_classification")
    for key in _walk_keys(result) + _walk_keys(lock) + _walk_keys(prediction_lock):
        if key in FORBIDDEN_EXACT_KEYS or any(marker in key for marker in FORBIDDEN_KEY_MARKERS):
            errors.append(f"forbidden_key:{key}")
    return result, lock, sorted(set(errors))


def validate(root: Path, repository_root: Path, repeat_root: Path | None = None) -> dict[str, Any]:
    result, lock, errors = _validate_one(root, repository_root)
    repeat_summary: dict[str, Any] | None = None
    if repeat_root is not None:
        other_result, other_lock, other_errors = _validate_one(repeat_root, repository_root)
        errors.extend(f"repeat:{error}" for error in other_errors)
        if result and other_result:
            if result.get("repeat_index") == other_result.get("repeat_index"):
                errors.append("repeat_indices_not_distinct")
            for field in ("protocol", "state_slice", "panel_manifest_sha256", "qualification_result_sha256", "model_manifest_sha256", "configuration_lock_sha256"):
                if field in result and field in other_result and field not in {"configuration_lock_sha256"} and result[field] != other_result[field]:
                    errors.append(f"repeat_{field}_mismatch")
            first_mean = result.get("tune", {}).get("lambda_local", {}).get("mean")
            second_mean = other_result.get("tune", {}).get("lambda_local", {}).get("mean")
            if not isinstance(first_mean, (int, float)) or not isinstance(second_mean, (int, float)):
                errors.append("repeat_lambda_summary")
            else:
                repeat_summary = {
                    "repeat_indices": sorted([int(result["repeat_index"]), int(other_result["repeat_index"])]),
                    "lambda_local_means": [float(first_mean), float(second_mean)],
                    "same_lambda_sign": bool(float(first_mean) == 0.0 or float(second_mean) == 0.0 or (float(first_mean) > 0.0) == (float(second_mean) > 0.0)),
                    "assessment_opened": False,
                }
    receipt = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "measurement_root": str(root.resolve()),
        "measurement_result_sha256": protocol.sha256_file(root.resolve() / "causal-state-transport-result.json") if (root.resolve() / "causal-state-transport-result.json").is_file() else None,
        "configuration_lock_sha256": lock.get("configuration_lock_sha256"),
        "repeat_summary": repeat_summary,
        "valid": not errors,
        "errors": sorted(set(errors)),
        "classification": "AggregateOnlyValidated" if not errors else "AggregateOnlyInvalid",
        "claim_ceiling": "LocalDevelopmentV48AggregateOnlyValidated" if not errors else "LocalDevelopmentV48AggregateOnlyValidationFailed",
        "assessment_opened": False,
    }
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("measurement_root", type=Path)
    parser.add_argument("--repeat-root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = validate(args.measurement_root, args.repository_root, args.repeat_root)
        if args.write_receipt:
            protocol.write_json(args.measurement_root.resolve() / "validator-receipt.json", receipt)
    except (OSError, ValueError, json.JSONDecodeError, KeyError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "errors": [f"{type(exc).__name__}:{exc}"]}, indent=2))
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independent V29 aggregate validator.
State slice: astral-calibrated-opaque-causal-channel-v29-validation.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

PROTOCOL = "astral-calibrated-opaque-causal-channel-v29"
CLAIM_CEILING = "LocalDevelopmentCalibratedOpaqueCausalChannel"
CLASSES = {"CalibratedOpaqueCausalChannelUtilityObserved", "CalibratedOpaqueCausalChannelDiagnosticOnly"}

def validate(value: object) -> list[str]:
    if not isinstance(value, dict): return ["result_not_object"]
    errors = []
    if value.get("protocol") != PROTOCOL: errors.append("protocol_mismatch")
    if value.get("claim_ceiling") != CLAIM_CEILING: errors.append("claim_ceiling_mismatch")
    if value.get("classification") not in CLASSES: errors.append("classification_unknown")
    for field, expected in (("model_execution", True), ("network_access", False), ("raw_intermediate_retained", False), ("prediction_locked_before_assessment", True), ("finite", True), ("variance_gate", True)):
        if value.get(field) is not expected: errors.append(f"{field}_failed")
    if not isinstance(value.get("utility_gate"), bool): errors.append("utility_gate_missing_or_non_boolean")
    for field, expected in (("trial_count", 32), ("fit_count", 16), ("tune_count", 8), ("assessment_count", 8), ("full_feature_count", 4), ("opaque_feature_count", 2)):
        if value.get(field) != expected: errors.append(f"{field}_mismatch")
    numeric = ("tune_full_mse", "tune_opaque_mse", "tune_shuffled_mse", "assessment_full_mse", "assessment_opaque_mse", "assessment_shuffled_mse", "assessment_target_variance", "assessment_full_relative_mse", "assessment_opaque_relative_mse", "assessment_shuffled_relative_mse")
    for field in numeric:
        item = value.get(field)
        if not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(float(item)): errors.append(f"{field}_invalid")
    expected_class = "CalibratedOpaqueCausalChannelUtilityObserved" if value.get("utility_gate") is True else "CalibratedOpaqueCausalChannelDiagnosticOnly"
    if value.get("classification") != expected_class: errors.append("classification_gate_mismatch")
    if value.get("assessment_target_variance", 0) < 1e-8: errors.append("target_variance_gate")
    return errors

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("result", type=Path); args = parser.parse_args(argv)
    try: value = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc: print(f"invalid V29 result: {type(exc).__name__}", file=sys.stderr); return 2
    errors = validate(value); print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True)); return 0 if not errors else 2

if __name__ == "__main__": sys.exit(main())

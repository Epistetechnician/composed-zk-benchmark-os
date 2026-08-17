#!/usr/bin/env python3
"""Independent aggregate-only validator for V28.

State slice: astral-opaque-causal-channel-separation-v28-validation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

PROTOCOL = "astral-opaque-causal-channel-separation-v28"
POSITIVE_CLASSIFICATION = "OpaqueCausalChannelSeparationObserved"
NEGATIVE_CLASSIFICATION = "OpaqueCausalChannelOrderingSignalOnly"
CLAIM_CEILING = "LocalDevelopmentOpaqueCausalChannelSeparation"


def validate(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["result_not_object"]
    for field, expected in (("protocol", PROTOCOL), ("claim_ceiling", CLAIM_CEILING)):
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
    if value.get("classification") not in (POSITIVE_CLASSIFICATION, NEGATIVE_CLASSIFICATION):
        errors.append("classification_unknown")
    for field in ("model_execution", "network_access", "raw_intermediate_retained", "prediction_locked_before_assessment", "finite", "variance_gate", "channel_order_gate", "utility_gate", "separation_gate"):
        expected = False if field in ("network_access", "raw_intermediate_retained") else True
        if field in ("utility_gate", "separation_gate"):
            if not isinstance(value.get(field), bool):
                errors.append(f"{field}_missing_or_non_boolean")
        elif value.get(field) is not expected:
            errors.append(f"{field}_failed")
    if value.get("separation_gate") is not value.get("utility_gate"):
        errors.append("separation_utility_mismatch")
    for field, expected in (("trial_count", 16), ("fit_count", 8), ("tune_count", 4), ("assessment_count", 4), ("full_feature_count", 16), ("opaque_feature_count", 4)):
        if value.get(field) != expected:
            errors.append(f"{field}_mismatch")
    numeric = (
        "tune_full_mse", "tune_opaque_mse", "tune_shuffled_mse", "assessment_full_mse",
        "assessment_opaque_mse", "assessment_shuffled_mse", "assessment_target_variance",
        "assessment_full_relative_mse", "assessment_opaque_relative_mse", "assessment_shuffled_relative_mse",
    )
    for field in numeric:
        value_for_field = value.get(field)
        if not isinstance(value_for_field, (int, float)) or isinstance(value_for_field, bool) or not math.isfinite(float(value_for_field)):
            errors.append(f"{field}_invalid")
    if value.get("assessment_full_relative_mse", math.inf) >= value.get("assessment_shuffled_relative_mse", -math.inf):
        errors.append("full_not_better_than_shuffled")
    expected_classification = POSITIVE_CLASSIFICATION if value.get("utility_gate") is True else NEGATIVE_CLASSIFICATION
    if value.get("classification") != expected_classification:
        errors.append("classification_gate_mismatch")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"invalid V28 result: {type(exc).__name__}", file=sys.stderr)
        return 2
    errors = validate(value)
    print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())

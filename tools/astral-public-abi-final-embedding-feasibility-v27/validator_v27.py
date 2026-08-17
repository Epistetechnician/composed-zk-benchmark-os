#!/usr/bin/env python3
"""Independent aggregate-only validator for V27 execution output.

State slice: astral-public-abi-final-embedding-feasibility-v27-execution.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

PROTOCOL = "astral-public-abi-final-embedding-feasibility-v27"
CLASSIFICATION = "PublicAbiFinalEmbeddingInterventionFeasible"
CLAIM_CEILING = "LocalDevelopmentPublicAbiFinalEmbeddingFeasibility"
TOLERANCE = 1e-4
EFFECT_GATE = 1e-4


def validate(value: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["result_not_object"]
    if value.get("protocol") != PROTOCOL:
        errors.append("protocol_mismatch")
    if value.get("claim_ceiling") != CLAIM_CEILING:
        errors.append("claim_ceiling_mismatch")
    if value.get("model_execution") is not True:
        errors.append("model_execution_missing")
    if value.get("network_access") is not False:
        errors.append("network_access_not_false")
    required = (
        "embedding_dim", "layer_count", "prompt_token_count", "token_a", "token_b",
        "clean_zero_max_abs_error", "clean_repeat_max_abs_error",
        "intervention_repeat_max_abs_error", "direct_logit_effect",
    )
    for field in required:
        if field not in value:
            errors.append(f"missing_{field}")
        elif not isinstance(value[field], (int, float)) or isinstance(value[field], bool):
            errors.append(f"non_numeric_{field}")
        elif not math.isfinite(float(value[field])):
            errors.append(f"non_finite_{field}")
    if value.get("classification") != CLASSIFICATION:
        errors.append("classification_not_positive")
    for field in ("parity_gate", "repeatability_gate", "effect_gate", "finite"):
        if value.get(field) is not True:
            errors.append(f"{field}_failed")
    if isinstance(value.get("clean_zero_max_abs_error"), (int, float)) and value["clean_zero_max_abs_error"] > TOLERANCE:
        errors.append("clean_zero_tolerance")
    if isinstance(value.get("clean_repeat_max_abs_error"), (int, float)) and value["clean_repeat_max_abs_error"] > TOLERANCE:
        errors.append("clean_repeat_tolerance")
    if isinstance(value.get("intervention_repeat_max_abs_error"), (int, float)) and value["intervention_repeat_max_abs_error"] > TOLERANCE:
        errors.append("intervention_repeat_tolerance")
    if isinstance(value.get("direct_logit_effect"), (int, float)) and value["direct_logit_effect"] < EFFECT_GATE:
        errors.append("effect_gate_threshold")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"invalid V27 result: {type(exc).__name__}", file=sys.stderr)
        return 2
    errors = validate(value)
    print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())

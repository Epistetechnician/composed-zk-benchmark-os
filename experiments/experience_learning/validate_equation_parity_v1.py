"""Independent validator for equation-parity V1.

State slice: ``oaklab-experience-learning-equation-parity-v1``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys

from .equation_parity_v1 import BOUND_MAX, BOUND_MIN, SCHEMA_VERSION, STATE_SLICE, _canonical, _digest


def validate_result(result: dict) -> list[str]:
    findings: list[str] = []
    if not isinstance(result, dict):
        return ["result must be an object"]
    if result.get("schema_version") != SCHEMA_VERSION:
        findings.append("schema_version mismatch")
    if result.get("state_slice") != STATE_SLICE:
        findings.append("state_slice mismatch")
    try:
        if result.get("result_digest") != _digest(result):
            findings.append("result_digest mismatch")
    except (TypeError, ValueError):
        findings.append("result contains non-canonical or non-finite values")
    if result.get("status") != "PASSED":
        findings.append("parity status is not PASSED")
    if result.get("bounds", {}).get("beta_min") != BOUND_MIN or result.get("bounds", {}).get("beta_max") != BOUND_MAX:
        findings.append("deployed beta bounds mismatch")
    cases = result.get("cases")
    if not isinstance(cases, dict) or set(cases) != {"idbd", "tidbd"}:
        findings.append("IDBD/TIDBD cases missing")
        cases = {}
    for name, case in cases.items():
        if case.get("status") != "passed" or case.get("steps", 0) < 32:
            findings.append(f"{name}: parity case incomplete")
        for key in ("max_abs_diff", "bounded_variant_max_abs_diff"):
            value = case.get(key)
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value > 1e-12:
                findings.append(f"{name}: {key} exceeds tolerance")
        if case.get("bound_hits") != 0:
            findings.append(f"{name}: published-core parity hit deployment bound")
        if case.get("bounds") != [BOUND_MIN, BOUND_MAX]:
            findings.append(f"{name}: case bounds mismatch")
    return findings


def validate_file(path: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        return validate_result(json.load(handle))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m experiments.experience_learning.validate_equation_parity_v1 RESULT.json")
    errors = validate_file(sys.argv[1])
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("VALID")

"""Independent aggregate-only validator for powered guard receipts.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from .acquire_real_data_v1 import validate_manifest
from .plasticity_guard_assessment_v2 import PLAN, PLAN_DIGEST


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"


def _digest(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate(path: Path, custody_root: Path | None = None) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("state_slice") != STATE_SLICE or result.get("plan_digest") != PLAN_DIGEST:
        raise ValueError("powered guard receipt state or plan mismatch")
    actual = _digest({key: value for key, value in result.items() if key != "result_digest"})
    if result.get("result_digest") != actual:
        raise ValueError("powered guard receipt digest mismatch")
    if result.get("plan") != PLAN:
        raise ValueError("powered guard receipt contains a changed plan")
    expected_count = len(PLAN["assessment_cohort_indices"])
    if result.get("assessment_cohort_count") != expected_count:
        raise ValueError("powered guard assessment cohort count mismatch")
    power = result.get("power", {})
    for field in ("normal_approximation_power", "target_power"):
        if not isinstance(power.get(field), (int, float)) or not math.isfinite(float(power[field])):
            raise ValueError(f"invalid power field: {field}")
    if result.get("paired_test", {}).get("n") != expected_count:
        raise ValueError("powered guard paired-test count mismatch")
    if custody_root is not None:
        custody = validate_manifest(custody_root)
        receipt = result.get("custody", {})
        if receipt.get("manifest_sha256") != custody["manifest_sha256"]:
            raise ValueError("powered guard custody manifest mismatch")
    return {"status": "valid", "state_slice": STATE_SLICE, "result_digest": actual,
            "dataset": result.get("dataset"), "assessment_cohort_count": expected_count,
            "strict_gate": result.get("strict_gate")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.receipt, args.root), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

"""Independent validator for a fresh-cohort plasticity-guard receipt.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from .acquire_real_data_v1 import validate_manifest
from .plasticity_guard_assessment_v1 import PLAN, PLAN_DIGEST, STATE_SLICE


def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    expected = result.get("result_digest")
    if expected != _digest({key: value for key, value in result.items() if key != "result_digest"}):
        raise ValueError("plasticity-guard result digest mismatch")
    if result.get("state_slice") != STATE_SLICE or result.get("plan_digest") != PLAN_DIGEST or result.get("plan") != PLAN:
        raise ValueError("plasticity-guard sealed plan mismatch")
    if result.get("strict_gate", {}).get("status") not in {"candidate", "no_candidate"}:
        raise ValueError("plasticity-guard gate status invalid")
    paired = result.get("paired_test", {})
    power = result.get("power", {})
    if not isinstance(paired.get("p_value"), (int, float)) or not math.isfinite(float(paired["p_value"])):
        raise ValueError("plasticity-guard paired p-value invalid")
    if power.get("planned_n") != len(PLAN["assessment_cohort_indices"]):
        raise ValueError("plasticity-guard power sample count mismatch")
    if not isinstance(power.get("normal_approximation_power"), (int, float)) or not 0.0 <= float(power["normal_approximation_power"]) <= 1.0:
        raise ValueError("plasticity-guard power value invalid")
    if power.get("target_met") != (float(power["normal_approximation_power"]) >= PLAN["target_power"]):
        raise ValueError("plasticity-guard power target mismatch")
    custody = result.get("custody", {})
    manifest_status = validate_manifest(args.root)
    if custody.get("manifest_sha256") != manifest_status["manifest_sha256"]:
        raise ValueError("plasticity-guard custody manifest mismatch")
    manifest = json.loads((args.root / "manifest.json").read_text(encoding="utf-8"))
    record = next((item for item in manifest["datasets"] if item["name"] == result.get("dataset")), None)
    if record is None or custody.get("derived_sha256") != record["derived_sha256"] or custody.get("rows") != record["rows"]:
        raise ValueError("plasticity-guard derived custody mismatch")
    if result.get("assessment_cohort_count") != len(PLAN["assessment_cohort_indices"]):
        raise ValueError("plasticity-guard cohort count mismatch")
    print(json.dumps({"status": "valid", "result_digest": expected, "dataset": result["dataset"]}, sort_keys=True))


if __name__ == "__main__":
    main()

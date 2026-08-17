#!/usr/bin/env python3
"""Independent validator for the V26 actor-custody preflight result.

State slice: astral-causal-channel-separation-v26-execution-preflight.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROTOCOL_ID = "astral-causal-channel-separation-v26"
STATE_SLICE = "astral-causal-channel-separation-v26-execution-preflight"
CLAIM_CEILING = "LocalDevelopmentCausalChannelSeparationDesignOnly"
NO_FRESH_ACTOR = "NoFreshActor"
READY = "ReadyForInstrumentQualification"


def validate(result: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return ["result_not_object"]
    expected = {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_execution": False,
        "network_access": False,
        "assessment_opened": False,
    }
    for key, value in expected.items():
        if result.get(key) != value:
            errors.append(f"{key}_mismatch")
    classification = result.get("classification")
    if classification not in {NO_FRESH_ACTOR, READY}:
        errors.append("unknown_classification")
    candidates = result.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates_not_array")
        candidates = []
    eligible_count = result.get("eligible_actor_count")
    actual_eligible = sum(1 for item in candidates if isinstance(item, dict) and item.get("eligible") is True)
    if eligible_count != actual_eligible:
        errors.append("eligible_count_mismatch")
    if classification == NO_FRESH_ACTOR and actual_eligible != 0:
        errors.append("no_fresh_actor_with_eligible_candidate")
    if classification == READY and actual_eligible != 1:
        errors.append("ready_without_unique_candidate")
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            errors.append(f"candidate_{index}_not_object")
            continue
        for key in ("model_dir", "config", "eligible", "weights_present", "reasons"):
            if key not in item:
                errors.append(f"candidate_{index}_missing_{key}")
        if not isinstance(item.get("reasons"), list):
            errors.append(f"candidate_{index}_reasons_not_array")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args(argv)
    try:
        result = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"invalid preflight JSON: {type(exc).__name__}", file=sys.stderr)
        return 2
    errors = validate(result)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, sort_keys=True))
        return 2
    print(json.dumps({"valid": True, "classification": result["classification"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

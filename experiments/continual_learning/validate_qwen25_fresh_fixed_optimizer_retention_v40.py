#!/usr/bin/env python3
"""Independent V40 retention validator over the V38 validation seam."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import validate_qwen25_fixed_optimizer_retention_v38 as v38_validator
from experiments.continual_learning.qwen25_fresh_fixed_optimizer_retention_v40 import (
    CLAIM_CEILING,
    FIXED_OPTIMIZER_SEED,
    MODEL_DEFAULT,
    PROTOCOL,
    SOURCE_STATE_SLICE,
    STATE_SLICE,
    TASK_SEEDS,
)


def validate(case_root: Path, source_case: Path, model: Path, expected_task_seed: int) -> dict:
    if expected_task_seed not in TASK_SEEDS:
        raise ValueError("task seed outside fixed V40 retention set")
    originals = {
        "CLAIM_CEILING": v38_validator.CLAIM_CEILING,
        "FIXED_OPTIMIZER_SEED": v38_validator.FIXED_OPTIMIZER_SEED,
        "PROTOCOL": v38_validator.PROTOCOL,
        "SOURCE_STATE_SLICE": v38_validator.SOURCE_STATE_SLICE,
        "STATE_SLICE": v38_validator.STATE_SLICE,
    }
    v38_validator.CLAIM_CEILING = CLAIM_CEILING
    v38_validator.FIXED_OPTIMIZER_SEED = FIXED_OPTIMIZER_SEED
    v38_validator.PROTOCOL = PROTOCOL
    v38_validator.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    v38_validator.STATE_SLICE = STATE_SLICE
    try:
        return v38_validator.validate(case_root.resolve(), source_case.resolve(), model, expected_task_seed)
    finally:
        for key, value in originals.items():
            setattr(v38_validator, key, value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--source-case", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--expected-task-seed", type=int, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.case_root, args.source_case, args.model, args.expected_task_seed), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

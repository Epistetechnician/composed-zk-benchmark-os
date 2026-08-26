#!/usr/bin/env python3
"""Independent validator for one V41 task-order retention case."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import validate_qwen25_fixed_optimizer_retention_v38 as base_validator
from experiments.continual_learning.qwen25_fresh_fixed_optimizer_acquisition_v40 import MODEL_DEFAULT, TASK_SEEDS
from experiments.continual_learning.qwen25_fresh_fixed_optimizer_order_retention_v41 import (
    CLAIM_CEILING,
    FIXED_OPTIMIZER_SEED,
    ORDERS,
    PROTOCOL,
    SOURCE_STATE_SLICE,
    STATE_SLICE,
    order_code,
)


def validate(case_root: Path, source_case: Path, model: Path, expected_task_seed: int, expected_order: tuple[int, ...]) -> dict:
    if expected_task_seed not in TASK_SEEDS:
        raise ValueError("task seed outside fixed V41 set")
    if expected_order not in ORDERS:
        raise ValueError("order outside fixed V41 set")
    originals = {
        "CLAIM_CEILING": base_validator.CLAIM_CEILING,
        "FIXED_OPTIMIZER_SEED": base_validator.FIXED_OPTIMIZER_SEED,
        "ORDER": base_validator.ORDER,
        "PROTOCOL": base_validator.PROTOCOL,
        "SOURCE_STATE_SLICE": base_validator.SOURCE_STATE_SLICE,
        "STATE_SLICE": base_validator.STATE_SLICE,
    }
    base_validator.CLAIM_CEILING = CLAIM_CEILING
    base_validator.FIXED_OPTIMIZER_SEED = FIXED_OPTIMIZER_SEED
    base_validator.ORDER = list(expected_order)
    base_validator.PROTOCOL = PROTOCOL
    base_validator.SOURCE_STATE_SLICE = SOURCE_STATE_SLICE
    base_validator.STATE_SLICE = STATE_SLICE
    try:
        result = base_validator.validate(case_root.resolve(), source_case.resolve(), model, expected_task_seed)
    finally:
        for key, value in originals.items():
            setattr(base_validator, key, value)
    config = json.loads((case_root / "config.json").read_text(encoding="utf8"))
    if config.get("replication_order") != list(expected_order):
        raise ValueError("V41 replication order binding drift")
    result["replication_order"] = order_code(expected_order)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--source-case", type=Path, required=True)
    parser.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    parser.add_argument("--expected-task-seed", type=int, required=True)
    parser.add_argument("--expected-order", required=True)
    args = parser.parse_args()
    try:
        order = tuple(int(value) for value in args.expected_order)
        print(json.dumps(validate(args.case_root, args.source_case, args.model, args.expected_task_seed, order), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

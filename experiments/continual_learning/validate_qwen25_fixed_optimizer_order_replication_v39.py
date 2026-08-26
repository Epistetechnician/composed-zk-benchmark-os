#!/usr/bin/env python3
"""Independent validator for one V39 order-replication case."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import validate_qwen25_fixed_optimizer_retention_v38 as v38_validator
from experiments.continual_learning.qwen25_fixed_optimizer_order_replication_v39 import (
    CLAIM_CEILING,
    ORDERS,
    PROTOCOL,
    STATE_SLICE,
    order_code,
)


def validate(case_root: Path, source_case: Path, model: Path, expected_task_seed: int, expected_order: tuple[int, ...]) -> dict:
    if expected_order not in ORDERS:
        raise ValueError("V39 expected order is outside the frozen set")
    config = json.loads((case_root / "config.json").read_text(encoding="utf8"))
    result = json.loads((case_root / "result.json").read_text(encoding="utf8"))
    if config["state_slice"] != STATE_SLICE or result["state_slice"] != STATE_SLICE:
        raise ValueError("V39 state slice drift")
    if config["protocol"] != PROTOCOL or result["protocol"] != PROTOCOL:
        raise ValueError("V39 protocol drift")
    if config["replication_order"] != list(expected_order) or result["replication_order"] != list(expected_order):
        raise ValueError("V39 order binding drift")
    v38_validator.STATE_SLICE = STATE_SLICE
    v38_validator.PROTOCOL = PROTOCOL
    v38_validator.ORDER = expected_order
    v38_validator.CLAIM_CEILING = CLAIM_CEILING
    validation = v38_validator.validate(case_root, source_case, model, expected_task_seed)
    validation.update({"order": order_code(expected_order), "claim_ceiling": CLAIM_CEILING, "protocol": PROTOCOL, "state_slice": STATE_SLICE})
    return validation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_root", type=Path)
    parser.add_argument("--source-case", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--expected-task-seed", type=int, required=True)
    parser.add_argument("--expected-order", required=True)
    args = parser.parse_args()
    order = tuple(int(value) for value in args.expected_order)
    print(json.dumps(validate(args.case_root.resolve(), args.source_case.resolve(), args.model, args.expected_task_seed, order), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

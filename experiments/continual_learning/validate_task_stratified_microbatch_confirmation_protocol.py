#!/usr/bin/env python3
"""Independent validator for the V28 confirmation pure-data plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning.task_stratified_microbatch_confirmation_protocol import validate_plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_plan(json.loads(args.plan.resolve().read_text())), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

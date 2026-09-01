"""CLI for the sealed fresh-cohort plasticity-guard assessment.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .plasticity_guard_assessment_v1 import run_custody_assessment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_custody_assessment(args.root, args.dataset)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(result["result_digest"])


if __name__ == "__main__":
    main()

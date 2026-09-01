"""CLI for the real-panel all-baseline matrix.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .real_benchmark_v1 import run_custody


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--dataset", action="append", dest="datasets")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_custody(args.root, args.datasets)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(result["result_digest"])


if __name__ == "__main__":
    main()

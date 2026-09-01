"""CLI for digest-bound backend parity on a custodied real panel.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backends import BACKEND_NAMES, run_custody_backend_parity


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--backend", action="append", dest="backends")
    parser.add_argument("--learning-rate", type=float, default=0.00001)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = run_custody_backend_parity(
        args.root, args.dataset, tuple(args.backends or BACKEND_NAMES), args.learning_rate, args.threshold
    )
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        Path(args.output).write_text(encoded, encoding="utf-8")
    print(result["result_digest"])


if __name__ == "__main__":
    main()

"""CLI for the bounded selective-credit qualification.

State slice: ``oaklab-experience-learning-selective-credit-v1``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .selective_credit_qualification_v1 import run_qualification, write_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int)
    args = parser.parse_args()
    result = run_qualification(steps=args.steps)
    write_result(result, args.output)
    print(result["result_digest"])


if __name__ == "__main__":
    main()

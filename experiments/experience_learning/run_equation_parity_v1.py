"""CLI for equation parity V1.

State slice: ``oaklab-experience-learning-equation-parity-v1``.
"""

from __future__ import annotations

import argparse

from .equation_parity_v1 import run_parity, write_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run_parity()
    write_result(result, args.output)
    print(result["result_digest"])


if __name__ == "__main__":
    main()

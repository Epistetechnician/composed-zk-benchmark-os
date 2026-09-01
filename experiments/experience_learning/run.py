"""CLI entry point for the Oak Lab experience-learning baseline benchmark."""

from __future__ import annotations

import argparse

from .benchmark import ALGORITHM_IDS, STREAMS, run_benchmark, write_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--stream", action="append", choices=sorted(STREAMS))
    parser.add_argument("--algorithm", action="append", choices=ALGORITHM_IDS)
    args = parser.parse_args()
    result = run_benchmark(args.stream, args.steps, algorithms=args.algorithm or ALGORITHM_IDS)
    write_result(result, args.output)
    print(result["result_digest"])


if __name__ == "__main__":
    main()

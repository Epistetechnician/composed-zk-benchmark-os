"""CLI for the sealed V2 multi-seed benchmark."""

from __future__ import annotations

import argparse

from .benchmark import ALGORITHM_IDS
from .benchmark_v2 import DEFAULT_SEED_OFFSETS, run_multiseed, write_result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--steps", type=int, default=256)
    parser.add_argument("--stream", action="append", dest="streams")
    parser.add_argument("--algorithm", action="append", dest="algorithms")
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    args = parser.parse_args()
    result = run_multiseed(
        stream_names=args.streams,
        steps=args.steps,
        seed_offsets=tuple(args.seeds or DEFAULT_SEED_OFFSETS),
        algorithms=tuple(args.algorithms) if args.algorithms else ALGORITHM_IDS,
        include_controls=True,
    )
    write_result(result, args.output)
    print(result["result_digest"])


if __name__ == "__main__":
    main()

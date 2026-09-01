"""CLI for the fresh-seed replication/sensitivity campaign.

State slice: ``oaklab-experience-learning-replication-sensitivity-v1``.
"""

from __future__ import annotations

import argparse

from .replication_sensitivity_v1 import (
    DEFAULT_SEED_OFFSETS, DEFAULT_STEPS, STREAM_NAMES, SURVIVING_ALGORITHMS,
    run_campaign, write_result,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--stream", action="append", dest="streams")
    parser.add_argument("--algorithm", action="append", dest="algorithms")
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    args = parser.parse_args()
    result = run_campaign(
        stream_names=tuple(args.streams or STREAM_NAMES),
        steps=args.steps,
        seed_offsets=tuple(args.seeds or DEFAULT_SEED_OFFSETS),
        algorithms=tuple(args.algorithms) if args.algorithms else SURVIVING_ALGORITHMS,
    )
    write_result(result, args.output)
    print(result["result_digest"])


if __name__ == "__main__":
    main()

"""Deterministic replay for replication/sensitivity V1.

State slice: ``oaklab-experience-learning-replication-sensitivity-v1``.
"""

from __future__ import annotations

import argparse
import json

from .replication_sensitivity_v1 import run_campaign
from .validate_replication_sensitivity_v1 import _canonical


def replay(path: str) -> bool:
    with open(path, encoding="utf-8") as handle:
        expected = json.load(handle)
    actual = run_campaign(
        stream_names=tuple(expected["stream_names"]),
        steps=int(expected["steps"]),
        seed_offsets=tuple(expected["seed_offsets"]),
        algorithms=tuple(expected["algorithm_names"]),
        include_controls=True,
    )
    return _canonical(actual) == _canonical(expected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    args = parser.parse_args()
    if not replay(args.result):
        raise SystemExit("REPLAY_MISMATCH")
    print("REPLAY_VALID")

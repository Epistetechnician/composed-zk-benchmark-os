"""Independent deterministic replay check for V2 aggregate results."""

from __future__ import annotations

import argparse
import json

from .benchmark_v2 import run_multiseed
from .validate_v2 import _canonical


def replay(path: str) -> bool:
    with open(path, encoding="utf-8") as handle:
        expected = json.load(handle)
    actual = run_multiseed(
        stream_names=expected["stream_names"], steps=int(expected["steps"]),
        seed_offsets=expected["seed_offsets"], algorithms=expected["algorithm_names"],
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

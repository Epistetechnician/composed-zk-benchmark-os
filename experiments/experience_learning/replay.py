"""Deterministic independent replay check for benchmark result files."""

from __future__ import annotations

import argparse
import json

from .benchmark import _canonical_for_digest, run_benchmark


def replay(path: str) -> bool:
    with open(path, encoding="utf-8") as handle:
        expected = json.load(handle)
    stream_names = expected["stream_names"]
    algorithms = expected["algorithm_names"]
    lengths = {name: record["n_experiences"] for name, record in expected["streams"].items()}
    seed_offset = int(expected.get("seed_offset", 0))
    if len(set(lengths.values())) == 1:
        actual = run_benchmark(stream_names, steps=next(iter(lengths.values())),
                               seed_offset=seed_offset, algorithms=algorithms)
        return actual.get("result_digest") == expected.get("result_digest")
    # Default V1 includes a 512-step long-horizon stream while the other
    # streams default to 256. Replay each stream independently and compare its
    # canonical aggregate record, preserving the result-level digest contract.
    for name, length in lengths.items():
        actual = run_benchmark([name], steps=length, seed_offset=seed_offset, algorithms=algorithms)
        if _canonical_for_digest(actual["streams"][name]) != _canonical_for_digest(expected["streams"][name]):
            return False
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    args = parser.parse_args()
    if not replay(args.result):
        raise SystemExit("REPLAY_MISMATCH")
    print("REPLAY_VALID")

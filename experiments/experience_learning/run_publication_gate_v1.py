"""CLI for the strict multi-stream publication gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .publication_gate_v1 import evaluate, read_results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", action="append", type=Path, required=True)
    parser.add_argument("--energy", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(read_results(args.result), args.energy)
    result["result_digest"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(result["result_digest"])


if __name__ == "__main__":
    main()

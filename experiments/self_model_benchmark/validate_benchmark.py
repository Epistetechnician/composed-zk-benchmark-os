"""Independently recompute and validate a self-model benchmark result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark_execution_gate import require_public_execution_source
from .protocol import BenchmarkProtocolError, evaluate, load_input, validate_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    try:
        result = json.loads(Path(args.result).read_text(encoding="utf-8"))
        manifest, trials = load_input(args.input)
        require_public_execution_source(manifest)
        expected = evaluate(manifest, trials)
        errors = validate_result(result, expected)
    except (OSError, json.JSONDecodeError, BenchmarkProtocolError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, sort_keys=True))
        return 2
    print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

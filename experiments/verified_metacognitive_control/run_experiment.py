#!/usr/bin/env python3
"""Run the paired metacognitive-control aggregate evaluation."""

from __future__ import annotations

import argparse
import json
import sys

from .protocol import ProtocolError, evaluate, load_input, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="manifest-plus-trial JSONL")
    parser.add_argument("--output", required=True, help="aggregate result JSON")
    args = parser.parse_args()
    try:
        result = evaluate(load_input(args.input))
    except (OSError, ProtocolError, json.JSONDecodeError) as exc:
        print(f"protocol_error: {exc}", file=sys.stderr)
        return 2
    write_json(args.output, result)
    print(json.dumps({"classification": result["classification"], "decision": result["decision"], "result_digest": result["result_digest"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

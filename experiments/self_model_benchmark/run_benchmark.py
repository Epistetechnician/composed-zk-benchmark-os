"""Run the aggregate-only self-model benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .protocol import BenchmarkProtocolError, evaluate, load_input


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        manifest, trials = load_input(args.input)
        result = evaluate(manifest, trials)
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, BenchmarkProtocolError) as exc:
        print(f"self_model_benchmark_error: {exc}")
        return 2
    print(json.dumps({"classification": result["classification"], "decision": result["decision"], "result_digest": result["result_digest"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

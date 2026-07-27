#!/usr/bin/env python3
"""Canonicalize JSON before V24 admin or reviewer signing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from review_auth import write_canonical


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("canonical output already exists")
    value = json.loads(args.input.read_text())
    digest = write_canonical(args.output, value)
    print(json.dumps({"output": str(args.output), "sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

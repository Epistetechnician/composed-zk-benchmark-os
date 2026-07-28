#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from release_v2 import replay_release


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Replay an immutable Astral-RGS V27-R1 release without mutating it."
    )
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--native-python", type=Path, required=True)
    args = parser.parse_args()
    report = replay_release(
        release_root=args.release,
        output_path=args.output,
        native_python=args.native_python,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

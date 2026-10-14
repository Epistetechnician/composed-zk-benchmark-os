from __future__ import annotations

import argparse
import json
from pathlib import Path

from v28r6 import validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a V28R6 legacy batch-8 endurance preflight")
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.artifact_root.resolve())
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

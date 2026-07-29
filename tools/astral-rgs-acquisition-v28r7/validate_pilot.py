from __future__ import annotations

import argparse
import json
from pathlib import Path

from v28r7 import validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a V28R7 single-cell acquisition pilot")
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.artifact_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Parse repository Python sources without creating bytecode artifacts."""

from __future__ import annotations

import ast
import json
from pathlib import Path


STATE_SLICE = "repo-package-manager-contract-v1"
ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / "experiments", ROOT / "tools")


def source_paths() -> list[Path]:
    return sorted(
        path
        for root in SOURCE_ROOTS
        if root.exists()
        for path in root.rglob("*.py")
        if ".venv" not in path.parts and "__pycache__" not in path.parts
    )


def main() -> int:
    paths = source_paths()
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    print(json.dumps({"state_slice": STATE_SLICE, "python_sources": len(paths)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

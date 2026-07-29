from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("astral_v29_validator", HERE / "v29.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("V29 validator module is unavailable")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_exclusive(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()
    with path.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a V29 positive-control artifact")
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = MODULE.validate_artifact(args.artifact_root.resolve())
    write_exclusive(args.output, report)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

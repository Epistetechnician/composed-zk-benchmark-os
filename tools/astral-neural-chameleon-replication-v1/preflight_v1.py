#!/usr/bin/env python3
"""Run the V1 Neural Chameleon artifact-custody preflight.

State slice: astral-neural-chameleon-replication-v1-preflight.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from protocol_v1 import inspect


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", required=True, type=Path)
    args = parser.parse_args(argv)
    result = inspect(args.artifact_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["classification"] == "ReadyForInstrumentQualification" else 2


if __name__ == "__main__":
    sys.exit(main())

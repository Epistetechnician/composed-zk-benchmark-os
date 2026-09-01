#!/usr/bin/env python3
"""Independently validate V46 qualification custody and gates.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any

import protocol_v46 as protocol


V45_SOURCE = Path(__file__).resolve().parents[1] / "astral-stage0c-qwen36-v45"
sys.path.insert(0, str(V45_SOURCE))
import validate_qualification_v45 as validator_engine  # noqa: E402


def validate(qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    validator_engine.protocol = protocol
    receipt = validator_engine.validate(qualification_root, model_root, repository_root)
    receipt["protocol"] = protocol.PROTOCOL_ID
    receipt["state_slice"] = protocol.STATE_SLICE
    receipt["claim_ceiling"] = "LocalDevelopmentV46QualificationValidated" if receipt["valid"] else "LocalDevelopmentV46ValidationFailed"
    receipt["classification"] = "QualificationValidated" if receipt["valid"] else "QualificationInvalid"
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qualification_root", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.qualification_root, args.model, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.qualification_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

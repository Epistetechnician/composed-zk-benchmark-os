#!/usr/bin/env python3
"""Independently validate V46 corpus custody.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import protocol_v46 as protocol


V45_SOURCE = Path(__file__).resolve().parents[1] / "astral-stage0c-qwen36-v45"
sys.path.insert(0, str(V45_SOURCE))
import validate_gutenberg_corpus_v45 as validator_engine  # noqa: E402


def validate(corpus_root: Path, repository_root: Path) -> dict[str, Any]:
    validator_engine.protocol = protocol
    receipt = validator_engine.validate(corpus_root, repository_root)
    receipt["protocol"] = protocol.PROTOCOL_ID
    receipt["state_slice"] = protocol.STATE_SLICE
    receipt["claim_ceiling"] = "LocalDevelopmentV46FreshCorpusValidated" if receipt["valid"] else "LocalDevelopmentV46ValidationFailed"
    receipt["classification"] = "FreshCorpusValidated" if receipt["valid"] else "CorpusInvalid"
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_root", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.corpus_root, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.corpus_root.resolve() / "validator-receipt.json", receipt)
    import json
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

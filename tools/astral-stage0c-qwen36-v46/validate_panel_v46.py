#!/usr/bin/env python3
"""Independently validate the sealed V46 panel.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import protocol_v46 as protocol


V45_SOURCE = Path(__file__).resolve().parents[1] / "astral-stage0c-qwen36-v45"
sys.path.insert(0, str(V45_SOURCE))
import validate_panel_v45 as validator_engine  # noqa: E402
import panel_v45 as panel_engine  # noqa: E402


ORIGINAL_BUILD_REGISTRY = panel_engine.build_registry


def _registry(corpus_root: Path, tokenizer: object) -> list[dict[str, object]]:
    registry = ORIGINAL_BUILD_REGISTRY(corpus_root, tokenizer)
    for family in registry:
        family["family_id"] = str(family["family_id"]).replace("v45-", "v46-", 1)
    return registry


def validate(panel_root: Path, corpus_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    validator_engine.protocol = protocol
    panel_engine.protocol = protocol
    panel_engine.build_registry = _registry
    receipt = validator_engine.validate(panel_root, corpus_root, model_root, repository_root)
    receipt["protocol"] = protocol.PROTOCOL_ID
    receipt["state_slice"] = protocol.STATE_SLICE
    receipt["claim_ceiling"] = "LocalDevelopmentV46PanelSealed" if receipt["valid"] else "LocalDevelopmentV46ValidationFailed"
    receipt["classification"] = "PanelSealedForAnswerAlignedTask" if receipt["valid"] else "PanelInvalid"
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("panel_root", type=Path)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.panel_root, args.corpus_root, args.model, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.panel_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Independently validate an external Project Gutenberg corpus bundle.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This validator recomputes the corpus manifest, document hashes, RDF identity,
UTF-8 boundaries, split census, selection binding, and external-root boundary.
It never calls Project Gutenberg and never opens scientific assessment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_v39 as corpus


def validate(root: Path, repository_root: Path) -> dict[str, Any]:
    root = root.resolve()
    errors = corpus.manifest_errors(root, repository_root.resolve())
    try:
        manifest_bytes = (root / "corpus-manifest.json").read_bytes()
        manifest_digest = corpus.sha256_bytes(manifest_bytes)
    except OSError:
        manifest_digest = None
    receipt = {
        "protocol": corpus.protocol.PROTOCOL_ID,
        "state_slice": corpus.protocol.STATE_SLICE,
        "claim_ceiling": corpus.CORPUS_CLAIM_CEILING,
        "valid": not errors,
        "classification": "ExternalCorpusCustodyValid" if not errors else "ExternalCorpusInvalid",
        "corpus_manifest_sha256": manifest_digest,
        "errors": errors,
    }
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_root", type=Path)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = validate(args.corpus_root, args.repository_root)
    except (OSError, corpus.CorpusError, json.JSONDecodeError) as exc:
        receipt = {
            "protocol": corpus.protocol.PROTOCOL_ID,
            "state_slice": corpus.protocol.STATE_SLICE,
            "claim_ceiling": corpus.CORPUS_CLAIM_CEILING,
            "valid": False,
            "classification": "ExternalCorpusInvalid",
            "corpus_manifest_sha256": None,
            "errors": [f"validator_error:{type(exc).__name__}:{exc}"],
        }
    if args.write_receipt:
        receipt_path = args.corpus_root.resolve() / "validator-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

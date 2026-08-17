#!/usr/bin/env python3
"""Inspect a local llama.cpp public header without loading a model.

State slice: astral-causal-channel-separation-v26-runtime-adapter-preflight.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PROTOCOL_ID = "astral-causal-channel-separation-v26"
STATE_SLICE = "astral-causal-channel-separation-v26-runtime-adapter-preflight"
INSUFFICIENT = "RuntimeSurfaceInsufficientForV26"
READY = "RuntimeSurfaceCandidateForV26"

REQUIRED_PUBLIC_SYMBOLS = (
    "llama_decode",
    "llama_get_embeddings",
    "llama_set_adapter_cvec",
)
PER_LAYER_CAPTURE_MARKERS = (
    "llama_get_embeddings_layer",
    "llama_get_hidden_state_layer",
    "llama_capture_residual_layer",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_header(path: Path) -> dict:
    result = {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "header": str(path),
        "header_sha256": None,
        "required_public_symbols": {},
        "per_layer_capture_markers": {},
        "model_execution": False,
        "network_access": False,
        "assessment_opened": False,
        "classification": INSUFFICIENT,
        "reasons": [],
    }
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        result["reasons"].append(f"header_unreadable:{type(exc).__name__}")
        return result
    result["header_sha256"] = sha256_file(path)
    result["required_public_symbols"] = {
        marker: marker in text for marker in REQUIRED_PUBLIC_SYMBOLS
    }
    result["per_layer_capture_markers"] = {
        marker: marker in text for marker in PER_LAYER_CAPTURE_MARKERS
    }
    missing = [
        marker for marker, present in result["required_public_symbols"].items()
        if not present
    ]
    if missing:
        result["reasons"].append(f"missing_public_symbols:{','.join(missing)}")
    if not any(result["per_layer_capture_markers"].values()):
        result["reasons"].append("no_public_per_layer_residual_capture")
    if not result["reasons"]:
        result["classification"] = READY
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--header",
        type=Path,
        default=Path("/opt/homebrew/Cellar/llama.cpp/10050/include/llama.h"),
    )
    args = parser.parse_args(argv)
    result = inspect_header(args.header)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["classification"] == READY else 2


if __name__ == "__main__":
    sys.exit(main())

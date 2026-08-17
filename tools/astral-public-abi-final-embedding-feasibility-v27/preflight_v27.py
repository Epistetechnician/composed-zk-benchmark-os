#!/usr/bin/env python3
"""No-model public-ABI preflight for V27.

State slice: astral-public-abi-final-embedding-feasibility-v27-preflight.
This module loads a shared library only to resolve public symbols. It does not
load a GGUF, initialize a model, run a forward pass, or use the network.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import sys
from pathlib import Path

PROTOCOL = "astral-public-abi-final-embedding-feasibility-v27"
STATE_SLICE = "astral-public-abi-final-embedding-feasibility-v27-preflight"
READY = "ReadyForExecutionAuthorization"
STOP = "PublicAbiPreflightFailed"
REQUIRED_SYMBOLS = (
    "llama_backend_init",
    "llama_backend_free",
    "llama_model_default_params",
    "llama_model_load_from_file",
    "llama_model_free",
    "llama_init_from_model",
    "llama_free",
    "llama_model_get_vocab",
    "llama_model_n_embd",
    "llama_model_n_layer",
    "llama_batch_init",
    "llama_batch_free",
    "llama_tokenize",
    "llama_decode",
    "llama_get_embeddings_ith",
    "llama_get_logits_ith",
    "llama_set_adapter_cvec",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_header(path: Path) -> dict:
    result = {"path": str(path), "exists": path.is_file(), "sha256": None, "declarations": {}}
    if not path.is_file():
        return result
    result["sha256"] = sha256_file(path)
    text = path.read_text(encoding="utf-8")
    result["declarations"] = {symbol: symbol in text for symbol in REQUIRED_SYMBOLS}
    return result


def inspect_library(path: Path) -> dict:
    result = {"path": str(path), "exists": path.is_file(), "sha256": None, "symbols": {}, "load_error": None}
    if not path.is_file():
        return result
    result["sha256"] = sha256_file(path)
    try:
        library = ctypes.CDLL(str(path))
    except OSError as exc:
        result["load_error"] = f"{type(exc).__name__}:{exc}"
        return result
    result["symbols"] = {
        symbol: hasattr(library, symbol) for symbol in REQUIRED_SYMBOLS
    }
    return result


def preflight(header: Path, library: Path, actor: Path) -> dict:
    header_result = inspect_header(header)
    library_result = inspect_library(library)
    reasons: list[str] = []
    if not header_result["exists"]:
        reasons.append("header_missing")
    if not library_result["exists"]:
        reasons.append("library_missing")
    if library_result["load_error"] is not None:
        reasons.append("library_load_failed")
    missing_declarations = [name for name, present in header_result["declarations"].items() if not present]
    missing_symbols = [name for name, present in library_result["symbols"].items() if not present]
    if missing_declarations:
        reasons.append("header_missing_symbols:" + ",".join(missing_declarations))
    if missing_symbols:
        reasons.append("library_missing_symbols:" + ",".join(missing_symbols))
    if not actor.is_file() or actor.is_symlink():
        reasons.append("actor_not_regular_local_file")
    actor_sha = sha256_file(actor) if actor.is_file() and not actor.is_symlink() else None
    return {
        "protocol": PROTOCOL,
        "state_slice": STATE_SLICE,
        "classification": READY if not reasons else STOP,
        "header": header_result,
        "library": library_result,
        "actor": {"path": str(actor), "sha256": actor_sha, "regular_local_file": actor.is_file() and not actor.is_symlink()},
        "reasons": reasons,
        "model_loaded": False,
        "model_execution": False,
        "network_access": False,
        "assessment_opened": False,
        "claim_ceiling": "LocalDevelopmentPublicAbiFinalEmbeddingFeasibility",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--header", type=Path, default=Path("/opt/homebrew/Cellar/llama.cpp/10050/include/llama.h"))
    parser.add_argument("--library", type=Path, default=Path("/opt/homebrew/Cellar/llama.cpp/10050/lib/libllama.0.0.10050.dylib"))
    parser.add_argument("--actor", type=Path, default=Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf"))
    args = parser.parse_args(argv)
    result = preflight(args.header, args.library, args.actor)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["classification"] == READY else 2


if __name__ == "__main__":
    sys.exit(main())

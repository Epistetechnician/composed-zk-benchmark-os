#!/usr/bin/env python3
"""No-model V28 custody and public-ABI preflight.

State slice: astral-opaque-causal-channel-separation-v28-preflight.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import sys
from pathlib import Path

PROTOCOL = "astral-opaque-causal-channel-separation-v28"
STATE_SLICE = "astral-opaque-causal-channel-separation-v28-preflight"
READY = "ReadyForExecutionAuthorization"
STOP = "OpaqueCausalChannelSeparationPreflightFailed"
REQUIRED_SYMBOLS = (
    "llama_backend_init", "llama_backend_free", "llama_model_default_params",
    "llama_model_load_from_file", "llama_model_free", "llama_init_from_model",
    "llama_free", "llama_model_get_vocab", "llama_model_n_embd", "llama_model_n_layer",
    "llama_batch_init", "llama_batch_free", "llama_tokenize", "llama_decode",
    "llama_get_embeddings_ith", "llama_get_logits_ith", "llama_set_adapter_cvec",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(path: Path, symbols: bool = False) -> dict:
    result = {"path": str(path), "exists": path.is_file(), "sha256": None}
    if not path.is_file():
        return result
    result["sha256"] = sha256_file(path)
    if symbols:
        try:
            library = ctypes.CDLL(str(path))
            result["symbols"] = {symbol: hasattr(library, symbol) for symbol in REQUIRED_SYMBOLS}
            result["load_error"] = None
        except OSError as exc:
            result["symbols"] = {}
            result["load_error"] = f"{type(exc).__name__}:{exc}"
    return result


def preflight(header: Path, library: Path, actor: Path) -> dict:
    header_result = inspect(header)
    if header_result["exists"]:
        text = header.read_text(encoding="utf-8")
        header_result["declarations"] = {symbol: symbol in text for symbol in REQUIRED_SYMBOLS}
    else:
        header_result["declarations"] = {}
    library_result = inspect(library, symbols=True)
    reasons: list[str] = []
    if not header_result["exists"]:
        reasons.append("header_missing")
    if not library_result["exists"]:
        reasons.append("library_missing")
    if library_result.get("load_error") is not None:
        reasons.append("library_load_failed")
    if any(not present for present in header_result["declarations"].values()):
        reasons.append("header_symbol_missing")
    if any(not present for present in library_result.get("symbols", {}).values()):
        reasons.append("library_symbol_missing")
    regular = actor.is_file() and not actor.is_symlink()
    if not regular:
        reasons.append("actor_not_regular_local_file")
    return {
        "protocol": PROTOCOL,
        "state_slice": STATE_SLICE,
        "classification": READY if not reasons else STOP,
        "header": header_result,
        "library": library_result,
        "actor": {"path": str(actor), "sha256": sha256_file(actor) if regular else None, "regular_local_file": regular},
        "fresh_protocol": True,
        "v27_artifact_reused": False,
        "model_loaded": False,
        "model_execution": False,
        "network_access": False,
        "assessment_opened": False,
        "claim_ceiling": "LocalDevelopmentOpaqueCausalChannelSeparation",
        "reasons": reasons,
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

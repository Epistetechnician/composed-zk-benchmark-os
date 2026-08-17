#!/usr/bin/env python3
"""No-model V29 custody and public-ABI preflight.
State slice: astral-calibrated-opaque-causal-channel-v29-preflight.
"""
from __future__ import annotations
import argparse, ctypes, hashlib, json, sys
from pathlib import Path

PROTOCOL = "astral-calibrated-opaque-causal-channel-v29"
SYMBOLS = ("llama_backend_init", "llama_backend_free", "llama_model_default_params", "llama_model_load_from_file", "llama_model_free", "llama_init_from_model", "llama_free", "llama_model_get_vocab", "llama_model_n_embd", "llama_model_n_layer", "llama_batch_init", "llama_batch_free", "llama_tokenize", "llama_decode", "llama_get_embeddings_ith", "llama_get_logits_ith", "llama_set_adapter_cvec")

def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024): value.update(chunk)
    return value.hexdigest()

def preflight(header: Path, library: Path, actor: Path) -> dict:
    reasons = []; header_exists = header.is_file(); library_exists = library.is_file(); regular = actor.is_file() and not actor.is_symlink()
    if not header_exists: reasons.append("header_missing")
    if not library_exists: reasons.append("library_missing")
    if not regular: reasons.append("actor_not_regular_local_file")
    declarations = {}
    if header_exists: declarations = {symbol: symbol in header.read_text(encoding="utf-8") for symbol in SYMBOLS}
    symbols = {}; load_error = None
    if library_exists:
        try: symbols = {symbol: hasattr(ctypes.CDLL(str(library)), symbol) for symbol in SYMBOLS}
        except OSError as exc: load_error = f"{type(exc).__name__}:{exc}"; reasons.append("library_load_failed")
    if any(not value for value in declarations.values()): reasons.append("header_symbol_missing")
    if any(not value for value in symbols.values()): reasons.append("library_symbol_missing")
    return {"protocol": PROTOCOL, "state_slice": "astral-calibrated-opaque-causal-channel-v29-preflight", "classification": "ReadyForExecutionAuthorization" if not reasons else "CalibratedOpaqueCausalChannelPreflightFailed", "header": {"path": str(header), "exists": header_exists, "sha256": digest(header) if header_exists else None, "declarations": declarations}, "library": {"path": str(library), "exists": library_exists, "sha256": digest(library) if library_exists else None, "symbols": symbols, "load_error": load_error}, "actor": {"path": str(actor), "regular_local_file": regular, "sha256": digest(actor) if regular else None}, "model_loaded": False, "model_execution": False, "network_access": False, "assessment_opened": False, "fresh_protocol": True, "prior_result_reused": False, "claim_ceiling": "LocalDevelopmentCalibratedOpaqueCausalChannel", "reasons": reasons}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--header", type=Path, default=Path("/opt/homebrew/Cellar/llama.cpp/10050/include/llama.h")); parser.add_argument("--library", type=Path, default=Path("/opt/homebrew/Cellar/llama.cpp/10050/lib/libllama.0.0.10050.dylib")); parser.add_argument("--actor", type=Path, default=Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf")); args = parser.parse_args(argv)
    result = preflight(args.header, args.library, args.actor); print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["classification"] == "ReadyForExecutionAuthorization" else 2

if __name__ == "__main__": sys.exit(main())

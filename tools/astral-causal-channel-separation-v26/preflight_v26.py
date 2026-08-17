#!/usr/bin/env python3
"""Offline V26 actor-custody preflight.

State slice: astral-causal-channel-separation-v26-execution-preflight.

This module does not import MLX, load weights, contact a provider, or execute a
model. It only inventories local MLX-style model directories and fails closed
when no actor is both instrumentable and fresh relative to V22-V25.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROTOCOL_ID = "astral-causal-channel-separation-v26"
CLAIM_CEILING = "LocalDevelopmentCausalChannelSeparationDesignOnly"
NO_FRESH_ACTOR = "NoFreshActor"
READY = "ReadyForInstrumentQualification"

DEFAULT_ROOTS = (
    Path("/Users/shaanp/.lmstudio/models/mlx-community"),
    Path("/Users/shaanp/.lmstudio/models/mlx_lm_lora"),
)

RESERVED_ACTOR_PATHS = {
    Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit").resolve(): "V22",
    Path("/Users/shaanp/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit").resolve(): "V23",
    Path("/Users/shaanp/.lmstudio/models/mlx_lm_lora/mesh-brain-nemotron-3-nano-4b").resolve(): "V25",
}

RESERVED_MODEL_SIGNATURES = {
    ("qwen2", "Qwen2ForCausalLM"): "V22",
    ("llama", "LlamaForCausalLM"): "V23",
    ("nemotron_h", ""): "V25",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _read_config(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"malformed_config:{type(exc).__name__}"
    if not isinstance(value, dict):
        return None, "malformed_config:top_level_not_object"
    return value, None


def _signature(config: dict[str, Any]) -> tuple[str, str]:
    architectures = config.get("architectures", [])
    architecture = architectures[0] if isinstance(architectures, list) and architectures else ""
    return str(config.get("model_type", "")), str(architecture)


def _candidate(model_dir: Path, config_path: Path) -> dict[str, Any]:
    config, error = _read_config(config_path)
    record: dict[str, Any] = {
        "model_dir": str(model_dir),
        "config": str(config_path),
        "config_sha256": sha256_file(config_path) if config_path.is_file() else None,
        "weights_present": any(model_dir.glob("*.safetensors")),
        "eligible": False,
        "reasons": [],
    }
    if error is not None:
        record["reasons"].append(error)
        return record
    assert config is not None
    model_type, architecture = _signature(config)
    record["model_type"] = model_type
    record["architecture"] = architecture
    if not record["weights_present"]:
        record["reasons"].append("no_safetensors_weights")
    if model_dir.resolve() in RESERVED_ACTOR_PATHS:
        record["reasons"].append(f"reserved_actor:{RESERVED_ACTOR_PATHS[model_dir.resolve()]}")
    reserved_phase = RESERVED_MODEL_SIGNATURES.get((model_type, architecture))
    if reserved_phase is not None:
        record["reasons"].append(f"reserved_signature:{reserved_phase}")
    if not record["reasons"]:
        record["eligible"] = True
    return record


def inventory(roots: tuple[Path, ...]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    scanned_roots: list[str] = []
    for root in roots:
        root = root.resolve()
        if not root.is_dir() or root.is_symlink():
            continue
        scanned_roots.append(str(root))
        for config_path in sorted(root.rglob("config.json")):
            model_dir = config_path.parent
            if model_dir.is_symlink():
                candidates.append({
                    "model_dir": str(model_dir),
                    "config": str(config_path),
                    "config_sha256": None,
                    "weights_present": False,
                    "eligible": False,
                    "reasons": ["symlinked_model_dir"],
                })
                continue
            candidates.append(_candidate(model_dir, config_path))
    eligible = [item for item in candidates if item["eligible"]]
    classification = READY if len(eligible) == 1 else NO_FRESH_ACTOR
    reasons: list[str]
    if not scanned_roots:
        reasons = ["no_model_roots_found"]
    elif not eligible:
        reasons = ["no_distinct_instrumentable_actor"]
    else:
        reasons = ["ambiguous_fresh_actor_inventory"]
    return {
        "protocol": PROTOCOL_ID,
        "state_slice": "astral-causal-channel-separation-v26-execution-preflight",
        "claim_ceiling": CLAIM_CEILING,
        "classification": classification,
        "scanned_roots": scanned_roots,
        "candidates": candidates,
        "eligible_actor_count": len(eligible),
        "reasons": reasons,
        "model_execution": False,
        "network_access": False,
        "assessment_opened": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", type=Path, dest="roots")
    args = parser.parse_args(argv)
    roots = tuple(args.roots) if args.roots else DEFAULT_ROOTS
    result = inventory(roots)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["classification"] == READY else 2


if __name__ == "__main__":
    sys.exit(main())

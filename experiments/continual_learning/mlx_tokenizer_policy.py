"""Fail-closed tokenizer policy for cached MLX model directories.

State slice: continual-learning-runtime-execution-v22.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STATE_SLICE = "continual-learning-runtime-execution-v22"
POLICY_VERSION = "mlx-tokenizer-policy-v1"
FIX_MISTRAL_REGEX_MODEL_TYPES = frozenset({"nemotron_h"})


def model_type_from_config(model_path: Path) -> str:
    """Read the declared model type without loading code or model weights."""

    config_path = model_path.resolve() / "config.json"
    if not config_path.is_file() or config_path.is_symlink():
        raise ValueError(f"model config is missing or unsafe: {config_path}")
    try:
        config: Any = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"model config is unreadable: {config_path}") from exc
    if not isinstance(config, dict):
        raise ValueError(f"model config must be an object: {config_path}")
    model_type = config.get("model_type")
    if not isinstance(model_type, str) or not model_type:
        raise ValueError(f"model config has no declared model_type: {config_path}")
    return model_type


def tokenizer_policy_for_model(model_path: Path) -> dict[str, Any]:
    """Return the deterministic tokenizer policy bound to model metadata."""

    model_type = model_type_from_config(model_path)
    return {
        "policy_version": POLICY_VERSION,
        "model_type": model_type,
        "fix_mistral_regex": model_type in FIX_MISTRAL_REGEX_MODEL_TYPES,
    }


def tokenizer_config_from_policy(policy: dict[str, Any]) -> dict[str, Any]:
    """Translate a validated policy receipt into MLX-LM tokenizer kwargs."""

    if policy.get("policy_version") != POLICY_VERSION:
        raise ValueError("unsupported tokenizer policy version")
    model_type = policy.get("model_type")
    expected_fix = model_type in FIX_MISTRAL_REGEX_MODEL_TYPES
    if not isinstance(model_type, str) or policy.get("fix_mistral_regex") is not expected_fix:
        raise ValueError("tokenizer policy does not match the declared model type")
    return {"fix_mistral_regex": True} if expected_fix else {}

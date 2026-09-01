"""Exact Gemma 3 1B native Python module registry.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
"""

from __future__ import annotations

from typing import Any

import protocol_v2 as protocol


ATTENTION_SEQUENCE = (
    "q_proj",
    "k_proj",
    "v_proj",
    "q_norm",
    "k_norm",
    "o_proj",
)
MLP_SEQUENCE = (
    "gate_proj",
    "act_fn",
    "up_proj",
    "down_proj",
)
def expected_input_paths() -> tuple[str, ...]:
    paths = ["model.embed_tokens", "model.rotary_emb", "model.rotary_emb_local"]
    for layer in range(protocol.LAYER_COUNT):
        prefix = f"model.layers.{layer}"
        paths.append(prefix)
        paths.append(f"{prefix}.input_layernorm")
        paths.append(f"{prefix}.self_attn")
        paths.extend(f"{prefix}.self_attn.{name}" for name in ATTENTION_SEQUENCE)
        paths.append(f"{prefix}.post_attention_layernorm")
        paths.append(f"{prefix}.pre_feedforward_layernorm")
        paths.append(f"{prefix}.mlp")
        paths.extend(f"{prefix}.mlp.{name}" for name in MLP_SEQUENCE)
        paths.append(f"{prefix}.post_feedforward_layernorm")
    paths.extend(("model.norm", "lm_head"))
    return tuple(paths)


def expected_output_paths() -> tuple[str, ...]:
    paths = ["model.embed_tokens", "model.rotary_emb", "model.rotary_emb_local"]
    for layer in range(protocol.LAYER_COUNT):
        prefix = f"model.layers.{layer}"
        paths.append(f"{prefix}.input_layernorm")
        paths.extend(f"{prefix}.self_attn.{name}" for name in ATTENTION_SEQUENCE)
        paths.append(f"{prefix}.self_attn")
        paths.append(f"{prefix}.post_attention_layernorm")
        paths.append(f"{prefix}.pre_feedforward_layernorm")
        paths.extend(f"{prefix}.mlp.{name}" for name in MLP_SEQUENCE)
        paths.append(f"{prefix}.mlp")
        paths.append(f"{prefix}.post_feedforward_layernorm")
        paths.append(prefix)
    paths.extend(("model.norm", "lm_head"))
    return tuple(paths)


def attention_paths() -> tuple[str, ...]:
    return tuple(f"model.layers.{layer}.self_attn" for layer in range(protocol.LAYER_COUNT))


def validate_model(model: Any) -> dict[str, Any]:
    modules = dict(model.named_modules())
    input_calls = expected_input_paths()
    required = tuple(dict.fromkeys(input_calls))
    missing = [path for path in required if path not in modules]
    extra_layers = [name for name in modules if name.startswith("model.layers.") and name.count(".") == 2 and name not in required]
    config = model.config
    errors = []
    if missing:
        errors.append(f"missing_modules:{len(missing)}")
    if extra_layers:
        errors.append(f"unexpected_layers:{len(extra_layers)}")
    if getattr(config, "num_hidden_layers", None) != protocol.LAYER_COUNT:
        errors.append("layer_count")
    if getattr(config, "hidden_size", None) != protocol.HIDDEN_WIDTH:
        errors.append("hidden_width")
    if getattr(config, "model_type", None) != "gemma3_text":
        errors.append("model_type")
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "hook_paths": list(required),
        "module_input_paths": list(input_calls),
        "module_output_paths": list(expected_output_paths()),
        "attention_paths": list(attention_paths()),
        "module_registry_sha256": protocol.digest_json(
            {"inputs": list(required), "outputs": list(expected_output_paths())}
        ),
        "valid": not errors,
        "errors": errors,
    }
    if errors:
        raise protocol.ProtocolError("model registry mismatch: " + ",".join(errors))
    return value

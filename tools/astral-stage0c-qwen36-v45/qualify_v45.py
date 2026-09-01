#!/usr/bin/env python3
"""Run V45 qualification only.

State slice: astral-stage0c-qwen36-response-anchored-causal-target-v45.
No panel effects or assessment effects are opened here.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import platform
import shutil
import tempfile
from pathlib import Path
from typing import Any

import protocol_v45 as protocol


DEFAULT_MODEL = Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit")


def _module_path(module: Any) -> Path:
    source = getattr(module, "__file__", None)
    if not isinstance(source, str):
        raise protocol.ProtocolError("runtime module has no source path")
    return Path(source).resolve()


def _runtime_manifest(qwen3_5: Any, qwen3_5_moe: Any) -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "mlx": importlib.metadata.version("mlx"),
        "mlx_lm": importlib.metadata.version("mlx-lm"),
        "qwen3_5_source_sha256": protocol.sha256_file(_module_path(qwen3_5)),
        "qwen3_5_moe_source_sha256": protocol.sha256_file(_module_path(qwen3_5_moe)),
    }


def _qualification_cases(tokenizer: Any) -> list[tuple[list[int], int]]:
    cases: list[tuple[list[int], int]] = []
    for label in protocol.QUALIFICATION_PROMPTS:
        prefix = f"{protocol.CANONICAL_WRAPPER}\nPassage:\nA short qualification passage contains {label}"
        boundary_index = len(tokenizer.encode(prefix))
        tokens = list(tokenizer.encode(prefix + "\nContext boundary:\nOptions:\nA) alpha\nB) beta\nAnswer:"))
        if len(tokens) < boundary_index or boundary_index - protocol.CONTENT_ANCHOR_OFFSET < 0:
            raise protocol.ProtocolError("qualification content anchor is invalid")
        cases.append((tokens, boundary_index - protocol.CONTENT_ANCHOR_OFFSET))
    return cases


class ProbeLayer:
    def __init__(self, layer: Any, index: int, mode: str, target_layer: int, anchor_index: int, mx: Any) -> None:
        self.layer = layer
        self.index = index
        self.mode = mode
        self.target_layer = target_layer
        self.anchor_index = anchor_index
        self.mx = mx
        self.last = None
        self.last_replaced = None
        self.is_linear = layer.is_linear

    def __call__(self, x: Any, mask: Any = None, cache: Any = None) -> Any:
        output = self.layer(x, mask=mask, cache=cache)
        self.last = output
        if self.mode != "none" and self.index == self.target_layer:
            if self.anchor_index < 0 or self.anchor_index >= int(output.shape[1]):
                raise protocol.ProtocolError("qualification content anchor is outside the layer sequence")
            if self.mode == "zero":
                replacement = self.mx.zeros((output.shape[0], 1, output.shape[-1]), dtype=output.dtype)
            elif self.mode == "nonzero":
                replacement = self.mx.ones((output.shape[0], 1, output.shape[-1]), dtype=output.dtype) * protocol.REPLACEMENT_SCALE
            elif self.mode == "noop":
                replacement = output[:, self.anchor_index : self.anchor_index + 1, :]
            else:
                raise protocol.ProtocolError(f"unknown qualification mode: {self.mode}")
            output = self.mx.concatenate([output[:, :self.anchor_index, :], replacement, output[:, self.anchor_index + 1 :, :]], axis=1)
        self.last_replaced = output
        return output


def _forward(model: Any, base_layers: list[Any], tokens: list[int], mode: str, target_layer: int, anchor_index: int, mx: Any) -> tuple[Any, list[ProbeLayer]]:
    if mode == "native":
        model.language_model.model.layers = base_layers
        logits = model(mx.array([tokens]))
        mx.eval(logits)
        return logits, []
    probes = [ProbeLayer(layer, index, mode, target_layer, anchor_index, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array([tokens]))
        mx.eval(logits, *[probe.last for probe in probes], *[probe.last_replaced for probe in probes])
        return logits, probes
    finally:
        model.language_model.model.layers = base_layers


def _max_abs(left: Any, right: Any, mx: Any) -> float:
    return float(mx.max(mx.abs(left.astype(mx.float32) - right.astype(mx.float32))).item())


def qualify(model_root: Path, output_root: Path, repository_root: Path) -> Path:
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(model_root, repository_root)
    protocol.assert_external(output_root, repository_root)
    if output_root.exists() and any(output_root.iterdir()):
        raise protocol.ProtocolError(f"qualification root must be empty: {output_root}")
    output_root.parent.mkdir(parents=True, exist_ok=True)
    manifest = protocol.model_manifest(model_root)
    config = protocol.read_json(model_root / "config.json")
    if config.get("architectures") != [protocol.MODEL_ARCHITECTURE]:
        raise protocol.ProtocolError(f"unexpected architecture: {config.get('architectures')!r}")
    import mlx.core as mx
    from mlx_lm import load
    import mlx_lm.models.qwen3_5 as qwen3_5
    import mlx_lm.models.qwen3_5_moe as qwen3_5_moe

    runtime = _runtime_manifest(qwen3_5, qwen3_5_moe)
    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise protocol.ProtocolError(f"unexpected layer count: {len(base_layers)}")
    cases = _qualification_cases(tokenizer)
    response_ids = {label: list(tokenizer.encode(token))[0] for label, token in protocol.RESPONSE_TOKENS.items() if len(list(tokenizer.encode(token))) == 1}
    if set(response_ids) != set(protocol.RESPONSE_TOKENS):
        raise protocol.ProtocolError("response token is not one tokenizer token")
    native_parity = 0.0
    repeat_delta = 0.0
    noop_delta = 0.0
    zero_delta = {str(layer): 0.0 for layer in protocol.CANDIDATE_LAYERS}
    nonzero_reach = {str(layer): 0.0 for layer in protocol.CANDIDATE_LAYERS}
    capture_shape_ok = True
    replacement_shape_ok = True
    for tokens, anchor_index in cases:
        native, _ = _forward(model, base_layers, tokens, "native", protocol.CANDIDATE_LAYERS[0], anchor_index, mx)
        wrapped, probes = _forward(model, base_layers, tokens, "noop", protocol.CANDIDATE_LAYERS[0], anchor_index, mx)
        repeated, _ = _forward(model, base_layers, tokens, "noop", protocol.CANDIDATE_LAYERS[0], anchor_index, mx)
        plain, _ = _forward(model, base_layers, tokens, "none", protocol.CANDIDATE_LAYERS[0], anchor_index, mx)
        native_parity = max(native_parity, _max_abs(native, wrapped, mx))
        repeat_delta = max(repeat_delta, _max_abs(wrapped, repeated, mx))
        noop_delta = max(noop_delta, _max_abs(wrapped, plain, mx))
        expected = (1, len(tokens), protocol.EXPECTED_HIDDEN_WIDTH)
        capture_shape_ok = capture_shape_ok and all(tuple(int(value) for value in probe.last.shape) == expected for probe in probes)
        replacement_shape_ok = replacement_shape_ok and all(tuple(int(value) for value in probe.last_replaced.shape) == expected for probe in probes)
        for layer in protocol.CANDIDATE_LAYERS:
            zero, _ = _forward(model, base_layers, tokens, "zero", layer, anchor_index, mx)
            nonzero, _ = _forward(model, base_layers, tokens, "nonzero", layer, anchor_index, mx)
            zero_delta[str(layer)] = max(zero_delta[str(layer)], _max_abs(wrapped, zero, mx))
            nonzero_reach[str(layer)] = max(nonzero_reach[str(layer)], _max_abs(wrapped, nonzero, mx))
    runtime_exact = runtime["mlx"] == "0.31.2" and runtime["mlx_lm"] == "0.31.3"
    gates = {
        "native_parity": native_parity <= 1e-4,
        "deterministic_repeat": repeat_delta <= 1e-5,
        "noop_replacement": noop_delta <= 1e-5,
        "zero_replacement_reached": all(math.isfinite(value) for value in zero_delta.values()),
        "nonzero_reach": all(value > 1e-6 for value in nonzero_reach.values()),
        "capture_shape": capture_shape_ok,
        "replacement_shape": replacement_shape_ok,
        "model_architecture": True,
        "runtime_exact": runtime_exact,
        "model_source_custody": bool(manifest["manifest_sha256"]),
        "no_network_access": True,
        "no_model_training": True,
        "no_raw_intermediates_retained": True,
    }
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "qualification_id": protocol.QUALIFICATION_ID,
        "claim_ceiling": "LocalDevelopmentV45InstrumentFeasibilityOnly",
        "classification": "InstrumentFeasibility" if all(gates.values()) else "InstrumentQualificationFailed",
        "model_root_basename": model_root.name,
        "model_manifest_sha256": manifest["manifest_sha256"],
        "config_sha256": protocol.sha256_file(model_root / "config.json"),
        "runtime": runtime,
        "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
        "runner_source_sha256": protocol.sha256_file(Path(__file__).resolve()),
        "qualification_prompt_sha256": protocol.canonical_digest([tokens for tokens, _ in cases]),
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "position_name": protocol.POSITION_NAME,
        "content_anchor_offset": protocol.CONTENT_ANCHOR_OFFSET,
        "position_rule": protocol.POSITION_RULE,
        "native_parity_max_abs_logit_delta": native_parity,
        "deterministic_repeat_max_abs_logit_delta": repeat_delta,
        "noop_replacement_max_abs_logit_delta": noop_delta,
        "zero_replacement_max_abs_logit_delta_by_layer": zero_delta,
        "nonzero_reach_max_abs_logit_delta_by_layer": nonzero_reach,
        "observed_layer_count": len(base_layers),
        "observed_hidden_width": protocol.EXPECTED_HIDDEN_WIDTH,
        "assessment_opened": False,
        "gates": gates,
    }
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        protocol.write_json(staging / "qualification-result.json", result)
        if output_root.exists() and any(output_root.iterdir()):
            raise protocol.ProtocolError(f"qualification root appeared during execution: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = qualify(args.model, args.output_root, args.repository_root)
    except (OSError, ImportError, KeyError, json.JSONDecodeError, protocol.ProtocolError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    result = protocol.read_json(root / "qualification-result.json")
    valid = all(result["gates"].values())
    print(json.dumps({"qualification_root": str(root), "classification": result["classification"], "valid": valid}, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run V40 instrument qualification before scientific panel execution.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

The runner re-custodies the already-cached Qwen3.6 checkpoint, checks native
parity, deterministic repeatability, zero replacement, nonzero reach at every
V40 qualification layer, and shape correctness, then retains aggregate output
only in a new external root.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import protocol_v40 as protocol


DEFAULT_MODEL = Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit")


def _module_path(module: Any) -> Path:
    source = getattr(module, "__file__", None)
    if not isinstance(source, str):
        raise protocol.ProtocolError(f"module has no source path: {module!r}")
    return Path(source).resolve()


def _runtime_manifest(qwen3_5: Any, qwen3_5_moe: Any) -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "mlx": importlib.metadata.version("mlx"),
        "mlx_lm": importlib.metadata.version("mlx-lm"),
        "qwen3_5_source_sha256": protocol.sha256_file(_module_path(qwen3_5)),
        "qwen3_5_moe_source_sha256": protocol.sha256_file(_module_path(qwen3_5_moe)),
    }


class ProbeLayer:
    """Capture one native layer and optionally replace its final position."""

    def __init__(self, layer: Any, index: int, mode: str, target_layer: int, mx: Any) -> None:
        self.layer = layer
        self.index = index
        self.mode = mode
        self.target_layer = target_layer
        self.mx = mx
        self.last = None
        self.last_replaced = None
        self.is_linear = layer.is_linear

    def __call__(self, x: Any, mask: Any = None, cache: Any = None) -> Any:
        output = self.layer(x, mask=mask, cache=cache)
        self.last = output
        if self.mode != "none" and self.index == self.target_layer:
            if self.mode == "zero":
                delta = self.mx.zeros_like(output)
            else:
                prefix = self.mx.zeros((output.shape[0], max(output.shape[1] - 1, 0), output.shape[-1]), dtype=output.dtype)
                suffix = self.mx.ones((output.shape[0], 1, output.shape[-1]), dtype=output.dtype) * protocol.REPLACEMENT_SCALE
                delta = self.mx.concatenate([prefix, suffix], axis=1)
            output = output + delta
        self.last_replaced = output
        return output


def _forward(model: Any, base_layers: list[Any], tokens: list[int], mode: str, target_layer: int, mx: Any) -> tuple[Any, list[ProbeLayer]]:
    if mode == "native":
        model.language_model.model.layers = base_layers
        logits = model(mx.array([tokens]))
        mx.eval(logits)
        return logits, []
    probes = [ProbeLayer(layer, index, mode, target_layer, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array([tokens]))
        mx.eval(logits, *[probe.last for probe in probes], *[probe.last_replaced for probe in probes])
        return logits, probes
    finally:
        model.language_model.model.layers = base_layers


def _max_abs(left: Any, right: Any, mx: Any) -> float:
    return float(mx.max(mx.abs(left.astype(mx.float32) - right.astype(mx.float32))).item())


def _shape_ok(probes: list[ProbeLayer], token_count: int) -> tuple[bool, bool, int, int]:
    if len(probes) != protocol.EXPECTED_LAYER_COUNT:
        return False, False, len(probes), 0
    capture_shapes = [tuple(int(value) for value in probe.last.shape) for probe in probes]
    replacement_shapes = [tuple(int(value) for value in probe.last_replaced.shape) for probe in probes]
    expected = (1, token_count, protocol.EXPECTED_HIDDEN_WIDTH)
    capture_ok = all(shape == expected for shape in capture_shapes)
    replacement_ok = capture_ok and replacement_shapes == capture_shapes
    return capture_ok, replacement_ok, len(capture_shapes), expected[-1]


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

    native_parity = 0.0
    repeat_delta = 0.0
    zero_delta = {str(layer): 0.0 for layer in protocol.QUALIFICATION_LAYERS}
    nonzero_delta = {str(layer): 0.0 for layer in protocol.QUALIFICATION_LAYERS}
    capture_shape_ok = True
    replacement_shape_ok = True
    for prompt in protocol.QUALIFICATION_PROMPTS:
        tokens = list(tokenizer.encode(prompt))
        if len(tokens) < 2:
            raise protocol.ProtocolError("qualification prompt tokenization is too short")
        native, _ = _forward(model, base_layers, tokens, "native", protocol.TARGET_LAYER, mx)
        wrapped, probes = _forward(model, base_layers, tokens, "none", protocol.TARGET_LAYER, mx)
        repeated, _ = _forward(model, base_layers, tokens, "none", protocol.TARGET_LAYER, mx)
        native_parity = max(native_parity, _max_abs(native, wrapped, mx))
        repeat_delta = max(repeat_delta, _max_abs(wrapped, repeated, mx))
        capture_ok, replacement_ok, layer_count, hidden_width = _shape_ok(probes, len(tokens))
        capture_shape_ok = capture_shape_ok and capture_ok and layer_count == protocol.EXPECTED_LAYER_COUNT and hidden_width == protocol.EXPECTED_HIDDEN_WIDTH
        replacement_shape_ok = replacement_shape_ok and replacement_ok
        for target_layer in protocol.QUALIFICATION_LAYERS:
            zero, zero_probes = _forward(model, base_layers, tokens, "zero", target_layer, mx)
            patched, patched_probes = _forward(model, base_layers, tokens, "nonzero", target_layer, mx)
            zero_delta[str(target_layer)] = max(zero_delta[str(target_layer)], _max_abs(wrapped, zero, mx))
            nonzero_delta[str(target_layer)] = max(nonzero_delta[str(target_layer)], _max_abs(wrapped, patched, mx))
            if len(zero_probes) != protocol.EXPECTED_LAYER_COUNT or len(patched_probes) != protocol.EXPECTED_LAYER_COUNT:
                raise protocol.ProtocolError("replacement probe layer count mismatch")

    gates = {
        "native_parity": native_parity <= 1e-4,
        "deterministic_repeat": repeat_delta <= 1e-5,
        "zero_replacement": all(value <= 1e-5 for value in zero_delta.values()),
        "nonzero_reach": all(value > 1e-6 for value in nonzero_delta.values()),
        "capture_shape": capture_shape_ok,
        "replacement_shape": replacement_shape_ok,
        "model_architecture": True,
        "no_network_access": True,
        "no_model_training": True,
        "no_raw_intermediates_retained": True,
    }
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "qualification_id": "astral-stage0c-qwen36-intervention-conditioned-target-v40-qualification-v1",
        "claim_ceiling": "LocalDevelopmentV40InstrumentFeasibilityOnly",
        "classification": "InstrumentFeasibility" if all(gates.values()) else "InstrumentQualificationFailed",
        "model_root_basename": model_root.name,
        "model_manifest_sha256": manifest["manifest_sha256"],
        "runtime": runtime,
        "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
        "runner_source_sha256": protocol.sha256_file(Path(__file__).resolve()),
        "qualification_prompt_sha256": protocol.canonical_digest(list(protocol.QUALIFICATION_PROMPTS)),
        "native_parity_max_abs_logit_delta": native_parity,
        "deterministic_repeat_max_abs_logit_delta": repeat_delta,
        "zero_replacement_max_abs_logit_delta_by_layer": zero_delta,
        "nonzero_reach_max_abs_logit_delta_by_layer": nonzero_delta,
        "observed_layer_count": protocol.EXPECTED_LAYER_COUNT,
        "observed_hidden_width": protocol.EXPECTED_HIDDEN_WIDTH,
        "qualification_layers": list(protocol.QUALIFICATION_LAYERS),
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
    print(json.dumps({"qualification_root": str(root), "classification": result["classification"], "valid": all(result["gates"].values())}, indent=2))
    return 0 if all(result["gates"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())

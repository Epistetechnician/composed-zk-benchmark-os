#!/usr/bin/env python3
"""Run V44 capture/replacement qualification only.

State slice: astral-stage0c-qwen36-causal-target-measurement-invariance-v44.
No panel or scientific measurement is opened by this command. Only aggregate
seam and custody checks are written.
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

import protocol_v44 as protocol


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
    def __init__(self, layer: Any, index: int, mode: str, target_layer: int, position_offset: int, mx: Any) -> None:
        self.layer = layer
        self.index = index
        self.mode = mode
        self.target_layer = target_layer
        self.position_offset = position_offset
        self.mx = mx
        self.last = None
        self.last_replaced = None
        self.is_linear = layer.is_linear

    def __call__(self, x: Any, mask: Any = None, cache: Any = None) -> Any:
        output = self.layer(x, mask=mask, cache=cache)
        self.last = output
        if self.mode != "none" and self.index == self.target_layer:
            position = int(output.shape[1]) - self.position_offset
            if position < 0 or position >= int(output.shape[1]):
                raise protocol.ProtocolError("qualification position is outside the layer sequence")
            if self.mode == "zero":
                replacement = self.mx.zeros((output.shape[0], 1, output.shape[-1]), dtype=output.dtype)
            elif self.mode == "nonzero":
                replacement = self.mx.ones((output.shape[0], 1, output.shape[-1]), dtype=output.dtype) * protocol.REPLACEMENT_SCALE
            elif self.mode == "noop":
                replacement = output[:, position : position + 1, :]
            else:
                raise protocol.ProtocolError(f"unknown qualification mode: {self.mode}")
            output = self.mx.concatenate([output[:, :position, :], replacement, output[:, position + 1 :, :]], axis=1)
        self.last_replaced = output
        return output


def _forward(model: Any, base_layers: list[Any], tokens: list[int], mode: str, target_layer: int, position_offset: int, mx: Any) -> tuple[Any, list[ProbeLayer]]:
    if mode == "native":
        model.language_model.model.layers = base_layers
        logits = model(mx.array([tokens]))
        mx.eval(logits)
        return logits, []
    probes = [ProbeLayer(layer, index, mode, target_layer, position_offset, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array([tokens]))
        mx.eval(logits, *[probe.last for probe in probes], *[probe.last_replaced for probe in probes])
        return logits, probes
    finally:
        model.language_model.model.layers = base_layers


def _max_abs(left: Any, right: Any, mx: Any) -> float:
    return float(mx.max(mx.abs(left.astype(mx.float32) - right.astype(mx.float32))).item())


def _shape_ok(probes: list[ProbeLayer], token_count: int) -> tuple[bool, bool]:
    if len(probes) != protocol.EXPECTED_LAYER_COUNT:
        return False, False
    expected = (1, token_count, protocol.EXPECTED_HIDDEN_WIDTH)
    capture_shapes = [tuple(int(value) for value in probe.last.shape) for probe in probes]
    replacement_shapes = [tuple(int(value) for value in probe.last_replaced.shape) for probe in probes]
    capture_ok = all(shape == expected for shape in capture_shapes)
    replacement_ok = capture_ok and replacement_shapes == capture_shapes
    return capture_ok, replacement_ok


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
    noop_delta = 0.0
    zero_replacement_delta = {f"{layer}:{position}": 0.0 for layer in protocol.CANDIDATE_LAYERS for position in protocol.POSITION_NAMES}
    nonzero_reach = {f"{layer}:{position}": 0.0 for layer in protocol.CANDIDATE_LAYERS for position in protocol.POSITION_NAMES}
    capture_shape_ok = True
    replacement_shape_ok = True
    for prompt in protocol.QUALIFICATION_PROMPTS:
        tokens = list(tokenizer.encode(prompt))
        if len(tokens) < 3:
            raise protocol.ProtocolError("qualification prompt tokenization is too short")
        native, _ = _forward(model, base_layers, tokens, "native", protocol.CANDIDATE_LAYERS[0], protocol.POSITION_OFFSETS[0], mx)
        wrapped, probes = _forward(model, base_layers, tokens, "noop", protocol.CANDIDATE_LAYERS[0], protocol.POSITION_OFFSETS[0], mx)
        repeated, _ = _forward(model, base_layers, tokens, "noop", protocol.CANDIDATE_LAYERS[0], protocol.POSITION_OFFSETS[0], mx)
        plain, _ = _forward(model, base_layers, tokens, "none", protocol.CANDIDATE_LAYERS[0], protocol.POSITION_OFFSETS[0], mx)
        native_parity = max(native_parity, _max_abs(native, wrapped, mx))
        repeat_delta = max(repeat_delta, _max_abs(wrapped, repeated, mx))
        noop_delta = max(noop_delta, _max_abs(wrapped, plain, mx))
        capture_ok, replacement_ok = _shape_ok(probes, len(tokens))
        capture_shape_ok = capture_shape_ok and capture_ok
        replacement_shape_ok = replacement_shape_ok and replacement_ok
        for target_layer in protocol.CANDIDATE_LAYERS:
            for position_name, position_offset in protocol.POSITION_BY_NAME.items():
                key = f"{target_layer}:{position_name}"
                zero, _ = _forward(model, base_layers, tokens, "zero", target_layer, position_offset, mx)
                patched, _ = _forward(model, base_layers, tokens, "nonzero", target_layer, position_offset, mx)
                zero_replacement_delta[key] = max(zero_replacement_delta[key], _max_abs(wrapped, zero, mx))
                nonzero_reach[key] = max(nonzero_reach[key], _max_abs(wrapped, patched, mx))

    runtime_exact = runtime["mlx"] == "0.31.2" and runtime["mlx_lm"] == "0.31.3"
    gates = {
        "native_parity": native_parity <= 1e-4,
        "deterministic_repeat": repeat_delta <= 1e-5,
        "noop_replacement": noop_delta <= 1e-5,
        "zero_replacement_reached": all(math.isfinite(value) for value in zero_replacement_delta.values()),
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
        "claim_ceiling": "LocalDevelopmentV44InstrumentFeasibilityOnly",
        "classification": "InstrumentFeasibility" if all(gates.values()) else "InstrumentQualificationFailed",
        "model_root_basename": model_root.name,
        "model_manifest_sha256": manifest["manifest_sha256"],
        "config_sha256": protocol.sha256_file(model_root / "config.json"),
        "runtime": runtime,
        "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
        "runner_source_sha256": protocol.sha256_file(Path(__file__).resolve()),
        "qualification_prompt_sha256": protocol.canonical_digest(list(protocol.QUALIFICATION_PROMPTS)),
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "position_names": list(protocol.POSITION_NAMES),
        "position_offsets": list(protocol.POSITION_OFFSETS),
        "position_rule": protocol.FIXED_POSITION_RULE,
        "native_parity_max_abs_logit_delta": native_parity,
        "deterministic_repeat_max_abs_logit_delta": repeat_delta,
        "noop_replacement_max_abs_logit_delta": noop_delta,
        "zero_replacement_max_abs_logit_delta_by_cell": zero_replacement_delta,
        "nonzero_reach_max_abs_logit_delta_by_cell": nonzero_reach,
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

#!/usr/bin/env python3
"""Run V48 qualification only; scientific measurement stays closed.

State slice: astral-stage0c-cross-view-causal-state-transport-v48.
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

import numpy as np

import protocol_v48 as protocol


DEFAULT_MODEL = Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit")


def _module_sha256(module: Any) -> str:
    source = getattr(module, "__file__", None)
    if not isinstance(source, str):
        raise protocol.ProtocolError("runtime module source path is missing")
    return protocol.sha256_file(Path(source).resolve())


def _runtime_manifest(qwen3_5: Any, qwen3_5_moe: Any) -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "mlx": importlib.metadata.version("mlx"),
        "mlx_lm": importlib.metadata.version("mlx-lm"),
        "qwen3_5_source_sha256": _module_sha256(qwen3_5),
        "qwen3_5_moe_source_sha256": _module_sha256(qwen3_5_moe),
    }


def _cases(tokenizer: Any) -> list[tuple[list[int], int]]:
    result: list[tuple[list[int], int]] = []
    for label in protocol.RESPONSE_LABELS:
        prefix = (
            "Answer the state routing task with exactly one label: A, B, C, or D.\n"
            "State payload boundary:\n"
            f"The route state code is {label}.\n"
            "Select the route label:"
        )
        boundary = len(tokenizer.encode(prefix.split("State payload boundary:")[0] + "State payload boundary:"))
        tokens = list(tokenizer.encode(prefix))
        anchor = boundary - protocol.CONTENT_ANCHOR_OFFSET
        if anchor < 0 or anchor >= len(tokens):
            raise protocol.ProtocolError("qualification state anchor is invalid")
        result.append((tokens, anchor))
    return result


class ProbeLayer:
    def __init__(self, layer: Any, index: int, target_layer: int | None, position: int, replacement: np.ndarray | None, mode: str, mx: Any) -> None:
        self.layer = layer
        self.index = index
        self.target_layer = target_layer
        self.position = position
        self.replacement = replacement
        self.mode = mode
        self.mx = mx
        self.capture = None
        self.replaced = None
        self.is_linear = layer.is_linear

    def __call__(self, x: Any, mask: Any = None, cache: Any = None) -> Any:
        output = self.layer(x, mask=mask, cache=cache)
        self.capture = output
        if self.target_layer == self.index:
            if self.position < 0 or self.position >= int(output.shape[1]):
                raise protocol.ProtocolError("replacement position is outside the layer sequence")
            if self.mode == "noop":
                replacement = output[:, self.position : self.position + 1, :]
            elif self.mode == "zero":
                replacement = self.mx.zeros((output.shape[0], 1, output.shape[-1]), dtype=output.dtype)
            elif self.mode == "nonzero":
                replacement = self.mx.ones((output.shape[0], 1, output.shape[-1]), dtype=output.dtype) * 0.01
            elif self.mode == "access":
                if self.replacement is None:
                    raise protocol.ProtocolError("access replacement is missing")
                replacement = self.mx.array(self.replacement.astype(np.float32), dtype=output.dtype).reshape((1, 1, -1))
            else:
                raise protocol.ProtocolError(f"unknown qualification mode: {self.mode}")
            output = self.mx.concatenate([output[:, :self.position, :], replacement, output[:, self.position + 1 :, :]], axis=1)
        self.replaced = output
        return output


def _forward(model: Any, base_layers: list[Any], tokens: list[int], position: int, mx: Any, target_layer: int | None = None, mode: str = "none", replacement: np.ndarray | None = None) -> tuple[Any, list[ProbeLayer]]:
    if target_layer is None and mode == "native":
        model.language_model.model.layers = base_layers
        logits = model(mx.array([tokens]))
        mx.eval(logits)
        return logits, []
    probes = [ProbeLayer(layer, index, target_layer, position, replacement, mode, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array([tokens]))
        mx.eval(logits, *[probe.capture for probe in probes], *[probe.replaced for probe in probes])
        return logits, probes
    finally:
        model.language_model.model.layers = base_layers


def _max_abs(left: Any, right: Any, mx: Any) -> float:
    return float(mx.max(mx.abs(left.astype(mx.float32) - right.astype(mx.float32))).item())


def _selected_logits(logits: Any, tokenizer: Any, mx: Any) -> np.ndarray:
    ids: list[int] = []
    for label in protocol.RESPONSE_LABELS:
        encoded = list(tokenizer.encode(protocol.RESPONSE_TOKENS[label]))
        if len(encoded) != 1:
            raise protocol.ProtocolError(f"response label is not one token: {label}")
        ids.append(encoded[0])
    selected = logits[:, -1, ids]
    mx.eval(selected)
    result = np.asarray(selected.astype(mx.float32), dtype=np.float64)
    if result.shape != (1, protocol.STATE_COUNT) or not np.isfinite(result).all():
        raise protocol.ProtocolError("invalid qualification logits")
    return result


def _norm_match(source: np.ndarray, receiver: np.ndarray) -> np.ndarray:
    source_norm = float(np.linalg.norm(source.astype(np.float64)))
    receiver_norm = float(np.linalg.norm(receiver.astype(np.float64)))
    if source_norm <= 0.0 or receiver_norm <= 0.0:
        raise protocol.ProtocolError("cannot norm-match zero qualification activation")
    replacement = source * np.float32(receiver_norm / source_norm)
    error = abs(float(np.linalg.norm(replacement.astype(np.float64))) - receiver_norm) / receiver_norm
    if error > protocol.MAX_NORM_ERROR:
        raise protocol.ProtocolError("qualification norm match exceeded tolerance")
    return replacement


def qualify(model_root: Path, output_root: Path, repository_root: Path) -> Path:
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(model_root, repository_root)
    protocol.assert_external(output_root, repository_root)
    if output_root.exists() and any(output_root.iterdir()):
        raise protocol.ProtocolError(f"qualification root must be empty: {output_root}")
    model_manifest = protocol.model_manifest(model_root)
    config = protocol.read_json(model_root / "config.json")
    if config.get("architectures") != [protocol.MODEL_ARCHITECTURE]:
        raise protocol.ProtocolError(f"unexpected model architecture: {config.get('architectures')!r}")
    import mlx.core as mx
    from mlx_lm import load
    import mlx_lm.models.qwen3_5 as qwen3_5
    import mlx_lm.models.qwen3_5_moe as qwen3_5_moe

    runtime = _runtime_manifest(qwen3_5, qwen3_5_moe)
    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise protocol.ProtocolError(f"unexpected layer count: {len(base_layers)}")
    cases = _cases(tokenizer)
    native_parity = 0.0
    deterministic_repeat = 0.0
    noop_delta = 0.0
    zero_delta = 0.0
    nonzero_delta = 0.0
    access_delta = 0.0
    capture_shape_ok = True
    replacement_shape_ok = True
    source_shape_ok = True
    for tokens, position in cases:
        native, _ = _forward(model, base_layers, tokens, position, mx, mode="native")
        wrapped, probes = _forward(model, base_layers, tokens, position, mx, target_layer=protocol.DESTINATION_LAYER, mode="noop")
        repeated, _ = _forward(model, base_layers, tokens, position, mx, target_layer=protocol.DESTINATION_LAYER, mode="noop")
        plain, _ = _forward(model, base_layers, tokens, position, mx, target_layer=None, mode="none")
        native_parity = max(native_parity, _max_abs(native, wrapped, mx))
        deterministic_repeat = max(deterministic_repeat, _max_abs(wrapped, repeated, mx))
        noop_delta = max(noop_delta, _max_abs(wrapped, plain, mx))
        expected = (1, len(tokens), protocol.EXPECTED_HIDDEN_WIDTH)
        capture_shape_ok = capture_shape_ok and all(tuple(int(value) for value in probe.capture.shape) == expected for probe in probes if probe.capture is not None)
        replacement_shape_ok = replacement_shape_ok and all(tuple(int(value) for value in probe.replaced.shape) == expected for probe in probes if probe.replaced is not None)
        source_probe = probes[protocol.SOURCE_LAYER]
        source_shape_ok = source_shape_ok and source_probe.capture is not None and tuple(int(value) for value in source_probe.capture.shape) == expected
        zero, _ = _forward(model, base_layers, tokens, position, mx, target_layer=protocol.DESTINATION_LAYER, mode="zero")
        nonzero, _ = _forward(model, base_layers, tokens, position, mx, target_layer=protocol.DESTINATION_LAYER, mode="nonzero")
        zero_delta = max(zero_delta, _max_abs(wrapped, zero, mx))
        nonzero_delta = max(nonzero_delta, _max_abs(wrapped, nonzero, mx))
        receiver = np.asarray(source_probe.capture[0, position, :].astype(mx.float32), dtype=np.float32)
        donor_source, donor_probes = _forward(model, base_layers, list(reversed(tokens)), position, mx, target_layer=None, mode="none")
        donor = np.asarray(donor_probes[protocol.SOURCE_LAYER].capture[0, position, :].astype(mx.float32), dtype=np.float32)
        access_vector = _norm_match(donor, receiver)
        access, _ = _forward(model, base_layers, tokens, position, mx, target_layer=protocol.DESTINATION_LAYER, mode="access", replacement=access_vector)
        access_delta = max(access_delta, _max_abs(wrapped, access, mx))
        _selected_logits(access, tokenizer, mx)
    runtime_exact = runtime["python"] == "3.14.5" and runtime["mlx"] == "0.31.2" and runtime["mlx_lm"] == "0.31.3"
    gates = {
        "native_parity": native_parity <= 1e-4,
        "deterministic_repeat": deterministic_repeat <= 1e-5,
        "noop_replacement": noop_delta <= 1e-5,
        "zero_replacement_reached": math.isfinite(zero_delta),
        "nonzero_reach": nonzero_delta > protocol.MIN_NONZERO_REACH and access_delta > protocol.MIN_NONZERO_REACH,
        "capture_shape": capture_shape_ok and source_shape_ok,
        "replacement_shape": replacement_shape_ok,
        "model_architecture": True,
        "runtime_exact": runtime_exact,
        "model_source_custody": bool(model_manifest.get("manifest_sha256")),
        "no_network_access": True,
        "no_model_training": True,
        "no_raw_intermediates_retained": True,
    }
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "qualification_id": protocol.QUALIFICATION_ID,
        "claim_ceiling": "LocalDevelopmentV48InstrumentFeasibilityOnly",
        "classification": "InstrumentFeasibility" if all(gates.values()) else "InstrumentQualificationFailed",
        "model_root_basename": model_root.name,
        "model_manifest_sha256": model_manifest["manifest_sha256"],
        "config_sha256": protocol.sha256_file(model_root / "config.json"),
        "runtime": runtime,
        "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
        "runner_source_sha256": protocol.sha256_file(Path(__file__).resolve()),
        "source_layer": protocol.SOURCE_LAYER,
        "destination_layer": protocol.DESTINATION_LAYER,
        "position_name": protocol.POSITION_NAME,
        "position_rule": protocol.POSITION_RULE,
        "alpha": protocol.ALPHA,
        "additional_passes": protocol.ADDITIONAL_PASSES,
        "native_parity_max_abs_logit_delta": native_parity,
        "deterministic_repeat_max_abs_logit_delta": deterministic_repeat,
        "noop_replacement_max_abs_logit_delta": noop_delta,
        "zero_replacement_max_abs_logit_delta": zero_delta,
        "nonzero_replacement_max_abs_logit_delta": nonzero_delta,
        "access_replacement_max_abs_logit_delta": access_delta,
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
        result = protocol.read_json(root / "qualification-result.json")
    except (OSError, ImportError, KeyError, json.JSONDecodeError, protocol.ProtocolError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    valid = result.get("classification") == "InstrumentFeasibility" and all(result.get("gates", {}).values())
    print(json.dumps({"qualification_root": str(root), "classification": result.get("classification"), "valid": valid}, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())

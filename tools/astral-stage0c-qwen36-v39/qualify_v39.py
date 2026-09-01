#!/usr/bin/env python3
"""Run only the V39 Qwen3.6 instrument qualification.

State slice: astral-stage0c-qwen36-layer-effect-v39.

The runner never reads a scientific corpus and never opens an assessment.  It
retains one aggregate qualification result outside the repository.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import protocol_v39 as protocol


DEFAULT_MODEL = Path(
    "/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"
)


def _module_path(module: Any) -> Path:
    path = getattr(module, "__file__", None)
    if not isinstance(path, str):
        raise RuntimeError(f"module has no source path: {module!r}")
    return Path(path).resolve()


def _runtime_manifest(qwen3_5: Any, qwen3_5_moe: Any) -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "mlx": importlib.metadata.version("mlx"),
        "mlx_lm": importlib.metadata.version("mlx-lm"),
        "qwen3_5_source_sha256": protocol.sha256_file(_module_path(qwen3_5)),
        "qwen3_5_moe_source_sha256": protocol.sha256_file(_module_path(qwen3_5_moe)),
    }


class ProbeLayer:
    """Wrap one native layer, retaining only shape and aggregate calculations."""

    def __init__(self, layer: Any, index: int, mode: str, mx: Any) -> None:
        self.layer = layer
        self.index = index
        self.mode = mode
        self.mx = mx
        self.last = None
        self.last_replaced = None
        self.is_linear = layer.is_linear

    def __call__(self, x: Any, mask: Any = None, cache: Any = None) -> Any:
        output = self.layer(x, mask=mask, cache=cache)
        self.last = output
        if self.mode != "none" and self.index == protocol.TARGET_LAYER:
            width = output.shape[-1]
            prefix = self.mx.zeros(
                (output.shape[0], max(output.shape[1] - 1, 0), width),
                dtype=output.dtype,
            )
            suffix = (
                self.mx.ones((output.shape[0], 1, width), dtype=output.dtype)
                * protocol.REPLACEMENT_SCALE
            )
            delta = self.mx.concatenate([prefix, suffix], axis=1)
            if self.mode == "zero":
                delta = self.mx.zeros_like(delta)
            output = output + delta
        self.last_replaced = output
        return output


def _attach(model: Any, base_layers: list[Any], mode: str, mx: Any) -> list[ProbeLayer]:
    probes = [ProbeLayer(layer, index, mode, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    return probes


def _forward(
    model: Any,
    base_layers: list[Any],
    tokens: list[int],
    mode: str,
    mx: Any,
) -> tuple[Any, list[ProbeLayer]]:
    if mode == "native":
        model.language_model.model.layers = base_layers
        logits = model(mx.array([tokens]))
        mx.eval(logits)
        return logits, []
    probes = _attach(model, base_layers, mode, mx)
    logits = model(mx.array([tokens]))
    mx.eval(logits, *[probe.last for probe in probes], *[probe.last_replaced for probe in probes])
    return logits, probes


def _max_abs(left: Any, right: Any, mx: Any) -> float:
    return float(mx.max(mx.abs(left.astype(mx.float32) - right.astype(mx.float32))).item())


def _shape_ok(probes: list[ProbeLayer], token_count: int) -> tuple[bool, bool, int, int]:
    if len(probes) != protocol.EXPECTED_LAYER_COUNT:
        return False, False, len(probes), 0
    capture_shapes = [tuple(int(value) for value in probe.last.shape) for probe in probes]
    replacement_shapes = [tuple(int(value) for value in probe.last_replaced.shape) for probe in probes]
    capture_ok = all(
        shape == (1, token_count, protocol.EXPECTED_HIDDEN_WIDTH)
        for shape in capture_shapes
    )
    replacement_ok = capture_ok and replacement_shapes == capture_shapes
    return (
        capture_ok,
        replacement_ok,
        len(capture_shapes),
        capture_shapes[0][-1] if capture_shapes else 0,
    )


def run_qualification(model_root: Path, output_root: Path) -> dict[str, Any]:
    repository_root = Path(__file__).resolve().parents[2]
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    protocol.assert_external(model_root, repository_root)
    protocol.assert_external(output_root, repository_root)
    if output_root.exists() and any(output_root.iterdir()):
        raise ValueError(f"qualification output root must be empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    manifest = protocol.model_manifest(model_root)
    config = json.loads((model_root / "config.json").read_text(encoding="utf-8"))
    architectures = config.get("architectures")
    if architectures != [protocol.MODEL_ARCHITECTURE]:
        raise ValueError(f"unexpected model architecture: {architectures!r}")

    import mlx.core as mx
    from mlx_lm import load
    import mlx_lm.models.qwen3_5 as qwen3_5
    import mlx_lm.models.qwen3_5_moe as qwen3_5_moe

    runtime = _runtime_manifest(qwen3_5, qwen3_5_moe)
    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise ValueError(f"unexpected layer count: {len(base_layers)}")

    native_parity = 0.0
    repeat_delta = 0.0
    zero_delta = 0.0
    nonzero_delta = 0.0
    capture_shape_ok = True
    replacement_shape_ok = True
    observed_layer_count = 0
    observed_hidden_width = 0

    for prompt in protocol.QUALIFICATION_PROMPTS:
        tokens = tokenizer.encode(prompt)
        if len(tokens) < 2:
            raise ValueError("qualification tokenizer produced too few tokens")
        native, _ = _forward(model, base_layers, tokens, "native", mx)
        wrapped, probes = _forward(model, base_layers, tokens, "none", mx)
        repeated, _ = _forward(model, base_layers, tokens, "none", mx)
        zero, zero_probes = _forward(model, base_layers, tokens, "zero", mx)
        patched, patched_probes = _forward(model, base_layers, tokens, "nonzero", mx)
        native_parity = max(native_parity, _max_abs(native, wrapped, mx))
        repeat_delta = max(repeat_delta, _max_abs(wrapped, repeated, mx))
        zero_delta = max(zero_delta, _max_abs(wrapped, zero, mx))
        nonzero_delta = max(nonzero_delta, _max_abs(wrapped, patched, mx))
        capture_ok, replacement_ok, layer_count, hidden_width = _shape_ok(probes, len(tokens))
        capture_shape_ok = capture_shape_ok and capture_ok
        replacement_shape_ok = replacement_shape_ok and replacement_ok
        observed_layer_count = max(observed_layer_count, layer_count)
        observed_hidden_width = max(observed_hidden_width, hidden_width)
        if len(zero_probes) != protocol.EXPECTED_LAYER_COUNT or len(patched_probes) != protocol.EXPECTED_LAYER_COUNT:
            capture_shape_ok = False
            replacement_shape_ok = False

    result: dict[str, Any] = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": protocol.QUALIFICATION_CLAIM_CEILING,
        "classification": "InstrumentQualificationFailed",
        "model_id": model_root.name,
        "model_architecture": protocol.MODEL_ARCHITECTURE,
        "model_root": str(model_root),
        "model_manifest_sha256": manifest["manifest_sha256"],
        "model_file_count": manifest["file_count"],
        "runtime": runtime,
        "source": {
            "runner_sha256": protocol.sha256_file(Path(__file__).resolve()),
            "protocol_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
        },
        "prompt_count": len(protocol.QUALIFICATION_PROMPTS),
        "prompt_registry_sha256": protocol.QUALIFICATION_PROMPT_DIGEST,
        "layer_count": observed_layer_count,
        "hidden_width_observed": observed_hidden_width,
        "target_layer": protocol.TARGET_LAYER,
        "capture_shape_ok": capture_shape_ok,
        "replacement_shape_ok": replacement_shape_ok,
        "native_parity_max_abs_logit_delta": native_parity,
        "baseline_repeat_max_abs_logit_delta": repeat_delta,
        "zero_replacement_max_abs_logit_delta": zero_delta,
        "nonzero_replacement_max_abs_logit_delta": nonzero_delta,
        "assessment_opened": False,
        "prediction_locked_before_assessment": False,
        "scientific_assessment": False,
        "model_loaded": True,
        "model_training": False,
        "network_access": False,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "stage_0c": False,
        "stage_1": False,
        "accepted_evidence": False,
        "reasons": [],
    }
    reasons = protocol.qualification_gate_errors(result)
    result["classification"] = "InstrumentQualificationPassed" if not reasons else "InstrumentQualificationFailed"
    result["reasons"] = reasons
    output_path = output_root / "qualification-result.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run_qualification(args.model, args.output_root)
    except Exception as exc:
        print(json.dumps({"classification": "InstrumentQualificationFailed", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["classification"] == "InstrumentQualificationPassed" else 2


if __name__ == "__main__":
    raise SystemExit(main())

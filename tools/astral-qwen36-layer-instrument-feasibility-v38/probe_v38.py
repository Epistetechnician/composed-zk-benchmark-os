#!/usr/bin/env python3
"""Bounded Qwen3.6 layer-instrument feasibility probe.

State slice: astral-qwen36-layer-instrument-feasibility-v38.

This runner performs only deterministic repeat, zero-intervention, and one
synthetic nonzero layer replacement. It emits aggregate metrics to stdout and
does not retain prompts, logits, hidden states, traces, credentials, or PII.
It does not open an assessment or authorize a scientific Astral run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import mlx.core as mx
import mlx.nn as nn
from mlx_lm import load
import mlx_lm.models.qwen3_5 as qwen3_5
import mlx_lm.models.qwen3_5_moe as qwen3_5_moe


STATE_SLICE = "astral-qwen36-layer-instrument-feasibility-v38"
CLAIM_CEILING = "LocalDevelopmentInstrumentFeasibilityOnly"
DEFAULT_MODEL = Path(
    "/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"
)
PROMPT = "A neutral arithmetic check: 2 + 2 ="
TARGET_LAYER = 19
SCALE = 0.01


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def model_manifest(model_path: Path) -> dict[str, Any]:
    files = []
    for path in sorted(
        candidate
        for candidate in model_path.rglob("*")
        if candidate.is_file() and not candidate.is_symlink()
    ):
        files.append(
            {
                "path": path.relative_to(model_path).as_posix(),
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if not files:
        raise ValueError(f"model directory has no regular files: {model_path}")
    manifest = {"model_id": model_path.name, "files": files}
    return {"manifest": manifest, "manifest_sha256": digest(manifest)}


class ProbeLayer(nn.Module):
    """Capture one layer output and optionally replace the final position."""

    def __init__(self, layer: nn.Module, index: int, mode: str) -> None:
        super().__init__()
        self.layer = layer
        self.index = index
        self.mode = mode
        self.last = None
        self.is_linear = layer.is_linear

    def __call__(self, x, mask=None, cache=None):
        output = self.layer(x, mask=mask, cache=cache)
        self.last = output
        if self.mode != "none" and self.index == TARGET_LAYER:
            width = output.shape[-1]
            prefix = mx.zeros(
                (output.shape[0], max(output.shape[1] - 1, 0), width),
                dtype=output.dtype,
            )
            suffix = mx.ones((output.shape[0], 1, width), dtype=output.dtype) * SCALE
            delta = mx.concatenate([prefix, suffix], axis=1)
            if self.mode == "zero":
                delta = mx.zeros_like(delta)
            output = output + delta
        return output


def runtime_manifest() -> dict[str, Any]:
    return {
        "mlx": importlib.metadata.version("mlx"),
        "mlx_lm": importlib.metadata.version("mlx-lm"),
        "qwen3_5_source_sha256": sha256_file(Path(qwen3_5.__file__)),
        "qwen3_5_moe_source_sha256": sha256_file(Path(qwen3_5_moe.__file__)),
    }


def attach(model, base_layers, mode: str) -> list[ProbeLayer]:
    probes = [ProbeLayer(layer, index, mode) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    return probes


def run(model, base_layers, tokens: list[int], mode: str):
    probes = attach(model, base_layers, mode)
    logits = model(mx.array([tokens]))
    mx.eval(logits, *[probe.last for probe in probes])
    norms = [
        float(mx.sqrt(mx.sum(probe.last.astype(mx.float32) ** 2)).item())
        for probe in probes
    ]
    return logits, norms, probes


def max_abs(left, right) -> float:
    return float(mx.max(mx.abs(left.astype(mx.float32) - right.astype(mx.float32))).item())


def run_probe(model_path: Path) -> dict[str, Any]:
    model_path = model_path.resolve()
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")

    manifest = model_manifest(model_path)
    runtime = runtime_manifest()
    model, tokenizer = load(str(model_path), lazy=False)
    tokens = tokenizer.encode(PROMPT)
    if len(tokens) < 2:
        raise ValueError("tokenizer produced too few tokens")

    base_layers = list(model.language_model.model.layers)
    baseline, baseline_norms, baseline_probes = run(model, base_layers, tokens, "none")
    repeat, repeat_norms, _ = run(model, base_layers, tokens, "none")
    zero, _, _ = run(model, base_layers, tokens, "zero")
    patched, patched_norms, _ = run(model, base_layers, tokens, "nonzero")

    return {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_id": model_path.name,
        "model_manifest_sha256": manifest["manifest_sha256"],
        "runtime": runtime,
        "prompt_sha256": hashlib.sha256(PROMPT.encode("utf-8")).hexdigest(),
        "token_count": len(tokens),
        "layer_count": len(baseline_norms),
        "hidden_width_observed": int(baseline_probes[0].last.shape[-1]),
        "target_layer": TARGET_LAYER,
        "baseline_repeat_max_abs_logit_delta": max_abs(baseline, repeat),
        "zero_intervention_max_abs_logit_delta": max_abs(baseline, zero),
        "nonzero_intervention_max_abs_logit_delta": max_abs(baseline, patched),
        "layer_norm_repeat_max_abs_delta": max(
            abs(left - right) for left, right in zip(baseline_norms, repeat_norms)
        ),
        "target_layer_norm": baseline_norms[TARGET_LAYER],
        "target_layer_norm_after_nonzero": patched_norms[TARGET_LAYER],
        "assessment_opened": False,
        "training": False,
        "network_access": False,
        "raw_trace_retained": False,
        "scientific_assessment": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(json.dumps(run_probe(args.model), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Local-only live bridge for the Astral Model Observatory prototype.

State slice: astral-research-progress-app-live-local-adapter.

This process loads only the already-cached local nemotron_h checkpoint through
the repository's V25 all-layer capture seam. It serves the latest capture over
loopback and never contacts a provider, downloads a model, trains, or writes
research artifacts.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
V25_PATH = ROOT / "tools" / "astral-telemetry-probe-v25" / "v25.py"
RUNTIME_LAYOUT_PATH = ROOT / "tools" / "astral-telemetry-probe-v25" / "run_canonical_suite.py"
CACHE_ROOT = Path("/Users/shaanp/.cache/uv/archive-v0")
SITE_PACKAGES = Path("/Users/shaanp/.hermes/hermes-agent/venv/lib/python3.11/site-packages")
TORCH_STUB = Path("/tmp/astral_torch_import_stub/torch.py")
PYTHON_PATH = Path("/opt/homebrew/bin/python3.13")
MODEL_PATH = Path("/Users/shaanp/.lmstudio/models/mlx_lm_lora/mesh-brain-nemotron-3-nano-4b")
DEFAULT_PROMPTS = (
    "The next token is",
    "A system can be described as",
    "The current state is",
)


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def ensure_runtime() -> None:
    """Re-exec with the cached MLX ABI before importing native extensions."""
    layout_module = import_path("astral_live_runtime_layout", RUNTIME_LAYOUT_PATH)
    layout = layout_module.discover_layout(CACHE_ROOT, SITE_PACKAGES, TORCH_STUB, PYTHON_PATH)
    environment = layout_module.build_env(layout)
    environment["ASTRAL_LIVE_RUNTIME_READY"] = "1"
    interpreter = layout.python.resolve()
    if os.environ.get("ASTRAL_LIVE_RUNTIME_READY") != "1" or Path(sys.executable).resolve() != interpreter:
        os.execve(str(interpreter), [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]], environment)


ensure_runtime()

import numpy as np  # noqa: E402


V25 = import_path("astral_live_v25", V25_PATH)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def normalized(values: list[float]) -> list[float]:
    logs = np.log1p(np.asarray(values, dtype=np.float64))
    low = float(np.min(logs))
    high = float(np.max(logs))
    if high <= low:
        return [0.5 for _value in values]
    return [clamp((float(value) - low) / (high - low)) for value in logs]


def distribution_entropy(vector: np.ndarray) -> float:
    weights = np.abs(vector.astype(np.float64))
    total = float(weights.sum())
    if total <= 0:
        return 0.0
    probabilities = weights / total
    entropy = float(-(probabilities * np.log(probabilities + 1e-12)).sum())
    return clamp(entropy / math.log(max(2, len(probabilities))))


def node_features(vector: np.ndarray) -> list[float]:
    segments = np.array_split(np.abs(vector.astype(np.float32)), 6)
    norms = [float(np.linalg.norm(segment)) for segment in segments]
    peak = max(norms) if norms else 1.0
    return [clamp(0.18 + (value / max(peak, 1e-8)) * 0.82) for value in norms]


def make_sample(
    runner: Any,
    tick: int,
    prompt: str,
    previous: dict[int, np.ndarray] | None,
    run_id: str,
) -> tuple[dict[str, Any], dict[int, np.ndarray]]:
    logits, captures = runner._forward(prompt, capture=True)
    ordered = [(int(layer), np.asarray(vector, dtype=np.float32)) for layer, vector in sorted(captures.items())]
    raw_norms = [float(np.linalg.norm(vector)) for _layer, vector in ordered]
    energies = normalized(raw_norms)
    layers: list[dict[str, Any]] = []
    for (layer, vector), energy in zip(ordered, energies):
        current_norm = max(float(np.linalg.norm(vector)), 1e-8)
        previous_vector = previous.get(layer) if previous else None
        delta = 0.0 if previous_vector is None else clamp(float(np.linalg.norm(vector - previous_vector)) / current_norm)
        layers.append({
            "layer": layer + 1,
            "energy": energy,
            "entropy": distribution_entropy(vector),
            "sparsity": clamp(float(np.mean(np.abs(vector) < 1e-3))),
            "delta": delta,
            "nodes": node_features(vector),
            "raw_residual_norm": current_norm,
        })
    active = max(layers, key=lambda layer: layer["energy"])
    sample = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tick": tick,
        "token": int(np.argmax(logits)),
        "model_id": "nemotron_h / mesh-brain-nemotron-3-nano-4b",
        "run_id": run_id,
        "layers": layers,
        "activeLayer": active["layer"],
        "phase": {
            "id": "runtime",
            "label": "Runtime forward pass",
            "short": "RUN",
            "tone": "acid",
            "note": "A local model execution is producing residual telemetry.",
            "claim": "Telemetry only; no sleep semantics.",
        },
        "metrics": {
            "residualEnergy": active["energy"],
            "attentionEntropy": active["entropy"],
            "activationSparsity": active["sparsity"],
            "interventionDelta": None,
            "selfModelCoherence": None,
            "actorObserverDivergence": None,
            "retrospectionProxy": None,
            "counterfactualConsistency": None,
        },
        "metricSemantics": {
            "attentionEntropy": "residual_distribution_entropy",
            "interventionDelta": "temporal_residual_delta",
            "selfModelCoherence": "not-captured",
            "actorObserverDivergence": "not-captured",
            "retrospectionProxy": "not-captured",
            "counterfactualConsistency": "not-captured",
        },
        "events": [
            "native forward completed",
            f"{len(layers)} final-position residuals captured",
            f"prompt lane: {prompt}",
            "no intervention applied",
        ],
        "source": "live",
        "provenance": {
            "kind": "local_model_forward",
            "model_path": str(MODEL_PATH),
            "capture_tool": "tools/astral-telemetry-probe-v25/v25.py",
            "capture_mode": "all-layer-final-position",
            "capture_dtype": "float16",
            "network_access": False,
            "training": False,
        },
    }
    return sample, {layer: vector.copy() for layer, vector in ordered}


class LiveState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.sample: dict[str, Any] | None = None
        self.error: str | None = None
        self.started_at = datetime.now(timezone.utc).isoformat()


class Handler(BaseHTTPRequestHandler):
    state: LiveState

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:4173")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            with self.state.lock:
                self._write_json(200, {"status": "ok" if self.state.sample else "starting", "error": self.state.error})
            return
        if self.path == "/sample":
            with self.state.lock:
                sample = self.state.sample
                error = self.state.error
            if sample is None:
                self._write_json(503, {"status": "starting", "error": error or "first model capture not ready"})
            else:
                self._write_json(200, sample)
            return
        self._write_json(404, {"status": "not_found"})

    def log_message(self, _format: str, *_args: Any) -> None:
        return


def produce(state: LiveState, runner: Any, prompts: tuple[str, ...], interval: float, run_id: str) -> None:
    previous: dict[int, np.ndarray] | None = None
    tick = 0
    while True:
        prompt = prompts[tick % len(prompts)]
        try:
            sample, previous = make_sample(runner, tick, prompt, previous, run_id)
            with state.lock:
                state.sample = sample
                state.error = None
            tick += 1
        except Exception as error:  # pragma: no cover - exercised by local runtime failures
            with state.lock:
                state.error = f"{type(error).__name__}: {error}"
        time.sleep(max(0.25, interval))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4174)
    parser.add_argument("--interval", type=float, default=1.5)
    parser.add_argument("--prompt", action="append", dest="prompts")
    args = parser.parse_args()
    prompts = tuple(args.prompts or DEFAULT_PROMPTS)
    runner = V25.TelemetryRunner()
    state = LiveState()
    run_id = f"live-{int(time.time())}"
    producer = threading.Thread(target=produce, args=(state, runner, prompts, args.interval, run_id), daemon=True)
    producer.start()
    Handler.state = state
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(json.dumps({"status": "listening", "url": f"http://127.0.0.1:{args.port}", "run_id": run_id, "layers": 42}, sort_keys=True), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())

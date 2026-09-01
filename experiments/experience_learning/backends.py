"""Backend-parity runner for the batch-one experience learner.

State slice: ``oaklab-experience-learning-benchmark-v2``.

The contract intentionally fixes one linear SGD update and varies only the
execution backend. Dense CPU and sparse CPU are always available; CUDA is
available only when a CUDA device is present; event-driven uses the declared
feature threshold. Unavailable hardware is reported, never silently emulated.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .acquire_real_data_v1 import validate_manifest
from .custody import load_custodied_jsonl
from .types import Experience, StepStats


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"
BACKEND_NAMES = ("dense_cpu", "sparse_cpu", "gpu", "event_driven")


@dataclass(frozen=True)
class BackendStatus:
    name: str
    available: bool
    reason: str


def backend_statuses() -> tuple[BackendStatus, ...]:
    statuses = [
        BackendStatus("dense_cpu", True, "NumPy host execution"),
        BackendStatus("sparse_cpu", True, "NumPy host execution over declared active coordinates"),
    ]
    try:
        import torch  # type: ignore[import-not-found]

        cuda = bool(torch.cuda.is_available())
    except Exception as error:  # pragma: no cover - dependency is environment-specific
        statuses.append(BackendStatus("gpu", False, f"CUDA dependency unavailable: {type(error).__name__}"))
    else:
        statuses.append(BackendStatus("gpu", cuda, "CUDA device available" if cuda else "CUDA device unavailable"))
    statuses.append(BackendStatus("event_driven", True, "thresholded sparse host execution"))
    return tuple(statuses)


def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class BackendLinearLearner:
    """One-step linear SGD learner with explicit backend semantics."""

    def __init__(self, dimensions: int, backend: str, learning_rate: float = 0.03, threshold: float = 0.5):
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        if backend not in BACKEND_NAMES:
            raise ValueError(f"unknown backend: {backend}")
        status = next(item for item in backend_statuses() if item.name == backend)
        if not status.available:
            raise RuntimeError(f"backend unavailable: {backend}: {status.reason}")
        if not math.isfinite(learning_rate) or learning_rate <= 0:
            raise ValueError("learning_rate must be positive and finite")
        self.dimensions = dimensions
        self.backend = backend
        self.learning_rate = learning_rate
        self.threshold = threshold
        self.weights = self._zeros(dimensions)
        self.bias = self._scalar(0.0)
        self.samples_seen = self.updates = self.gradient_units = self.active_synaptic_ops = 0
        self.event_count = 0

    def _zeros(self, dimensions: int):
        if self.backend == "gpu":
            import torch  # type: ignore[import-not-found]

            return torch.zeros(dimensions, device="cuda", dtype=torch.float64)
        import numpy as np  # type: ignore[import-not-found]

        return np.zeros(dimensions, dtype=np.float64)

    def _scalar(self, value: float):
        if self.backend == "gpu":
            import torch  # type: ignore[import-not-found]

            return torch.tensor(value, device="cuda", dtype=torch.float64)
        return float(value)

    def _active(self, item: Experience) -> tuple[int, ...]:
        if self.backend == "dense_cpu" or self.backend == "gpu":
            return tuple(range(self.dimensions))
        if self.backend == "event_driven":
            return tuple(index for index, value in enumerate(item.features) if abs(value) >= self.threshold)
        indices = tuple(sorted(set(item.event_indices)))
        if any(index >= self.dimensions for index in indices):
            raise ValueError("sparse event index exceeds feature dimension")
        return indices

    def predict(self, features: Sequence[float], active: Sequence[int] | None = None) -> float:
        indices = tuple(active) if active is not None else tuple(range(self.dimensions))
        if self.backend == "gpu":
            import torch  # type: ignore[import-not-found]

            feature_tensor = torch.tensor([features[index] for index in indices], device="cuda", dtype=torch.float64)
            index_tensor = torch.tensor(indices, device="cuda", dtype=torch.long)
            return float((self.bias + torch.dot(self.weights[index_tensor], feature_tensor)).item())
        return float(self.bias + sum(float(self.weights[index]) * features[index] for index in indices))

    def observe(self, item: Experience) -> StepStats:
        active = self._active(item)
        prediction = self.predict(item.features, active)
        error = prediction - item.target
        if self.backend == "gpu":
            import torch  # type: ignore[import-not-found]

            index_tensor = torch.tensor(active, device="cuda", dtype=torch.long)
            feature_tensor = torch.tensor([item.features[index] for index in active], device="cuda", dtype=torch.float64)
            self.weights[index_tensor] -= self.learning_rate * error * feature_tensor
            self.bias -= self.learning_rate * error
        else:
            for index in active:
                self.weights[index] -= self.learning_rate * error * item.features[index]
            self.bias -= self.learning_rate * error
        self.samples_seen += 1
        self.updates += 1
        self.gradient_units += len(active) + 1
        self.active_synaptic_ops += len(active) + 1
        self.event_count += len(item.event_indices)
        model_bytes = (self.dimensions + 1) * 8
        state_bytes = model_bytes
        return StepStats(
            prediction, 0.5 * error * error, True, 1, self.samples_seen,
            self.gradient_units, self.event_count, self.active_synaptic_ops, 0,
            model_bytes, state_bytes,
        )

    def _weights_list(self) -> list[float]:
        if self.backend == "gpu":
            return [float(value) for value in self.weights.detach().cpu().tolist()]
        return [float(value) for value in self.weights.tolist()]

    def snapshot(self) -> dict:
        bias = float(self.bias.item()) if self.backend == "gpu" else float(self.bias)
        return {
            "state_slice": STATE_SLICE,
            "backend": self.backend,
            "dimensions": self.dimensions,
            "learning_rate": self.learning_rate,
            "threshold": self.threshold,
            "weights": self._weights_list(),
            "bias": bias,
            "samples_seen": self.samples_seen,
            "updates": self.updates,
            "gradient_units": self.gradient_units,
            "active_synaptic_ops": self.active_synaptic_ops,
            "event_count": self.event_count,
        }

    def digest(self) -> str:
        return _digest(self.snapshot())

    def parameter_digest(self) -> str:
        """Digest only learned parameters so backend parity can be checked."""
        return _digest({"dimensions": self.dimensions, "weights": self._weights_list(),
                        "bias": float(self.bias.item()) if self.backend == "gpu" else float(self.bias)})


def run_backend_parity(
    experiences: Sequence[Experience],
    backends: Sequence[str] = BACKEND_NAMES,
    learning_rate: float = 0.00001,
    threshold: float = 0.5,
) -> dict:
    """Run identical ordered experiences through requested backend arms."""
    if not experiences:
        raise ValueError("backend parity requires at least one experience")
    requested = tuple(backends)
    unknown = sorted(set(requested) - set(BACKEND_NAMES))
    if unknown:
        raise ValueError(f"unknown backends: {unknown}")
    dimensions = len(experiences[0].features)
    outputs = {}
    statuses = {status.name: status for status in backend_statuses()}
    for name in requested:
        status = statuses[name]
        if not status.available:
            outputs[name] = {"status": "unavailable", "reason": status.reason}
            continue
        learner = BackendLinearLearner(dimensions, name, learning_rate, threshold)
        losses = []
        predictions = []
        for item in experiences:
            stats = learner.observe(item)
            if not math.isfinite(stats.prediction) or not math.isfinite(stats.loss):
                raise FloatingPointError(f"backend diverged on {name}; choose a finite fixed learning rate")
            losses.append(stats.loss)
            predictions.append(stats.prediction)
        outputs[name] = {
            "status": "executed",
            "backend": name,
            "steps": len(experiences),
            "mean_loss": sum(losses) / len(losses),
            "final_prediction": predictions[-1],
            "updates": learner.updates,
            "gradient_units": learner.gradient_units,
            "active_synaptic_ops": learner.active_synaptic_ops,
            "event_count": learner.event_count,
            "state_bytes": (dimensions + 1) * 8,
            "final_state_digest": learner.digest(),
            "parameter_digest": learner.parameter_digest(),
        }
    payload = {
        "schema_version": "oaklab.experience-learning.backend-parity.v1",
        "state_slice": STATE_SLICE,
        "protocol": "one ordered experience per observe; backend changes only execution representation",
        "dimensions": dimensions,
        "steps": len(experiences),
        "learning_rate": learning_rate,
        "threshold": threshold,
        "backends": outputs,
    }
    payload["result_digest"] = _digest(payload)
    return payload


def run_custody_backend_parity(
    root: str,
    dataset: str,
    backends: Sequence[str] = BACKEND_NAMES,
    learning_rate: float = 0.00001,
    threshold: float = 0.5,
) -> dict:
    """Load a manifest-bound derived panel and execute backend parity."""
    root_path = Path(root)
    custody_status = validate_manifest(root_path)
    manifest_path = root_path / "manifest.json"
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    record = next((item for item in manifest["datasets"] if item["name"] == dataset), None)
    if record is None:
        raise ValueError(f"dataset is not in custody manifest: {dataset}")
    path = str(root_path / record["derived_file"])
    experiences, _ = load_custodied_jsonl(path, record["kind"], record["derived_sha256"])
    result = run_backend_parity(experiences, backends, learning_rate, threshold)
    result["custody"] = {
        "dataset": dataset,
        "derived_sha256": record["derived_sha256"],
        "rows": len(experiences),
        "manifest_sha256": custody_status["manifest_sha256"],
    }
    result["result_digest"] = _digest({key: value for key, value in result.items() if key != "result_digest"})
    return result


def validate_backend_result(result: dict) -> dict:
    """Validate aggregate parity receipt without rerunning a backend."""
    expected = result.get("result_digest")
    actual = _digest({key: value for key, value in result.items() if key != "result_digest"})
    if expected != actual:
        raise ValueError("backend parity result digest mismatch")
    if result.get("state_slice") != STATE_SLICE:
        raise ValueError("backend parity state slice mismatch")
    if result.get("schema_version") != "oaklab.experience-learning.backend-parity.v1":
        raise ValueError("backend parity schema mismatch")
    for name, record in result.get("backends", {}).items():
        if record.get("status") == "executed":
            required = {"steps", "mean_loss", "updates", "active_synaptic_ops", "parameter_digest"}
            if not required <= set(record):
                raise ValueError(f"backend receipt missing fields: {name}")
            if record["steps"] != result["steps"] or record["updates"] != result["steps"]:
                raise ValueError(f"backend step accounting mismatch: {name}")
        elif record.get("status") != "unavailable":
            raise ValueError(f"unknown backend receipt status: {name}")
    return {"status": "valid", "result_digest": actual, "backends": sorted(result.get("backends", {}))}

"""Online learner baselines for the Oak Lab experience-stream benchmark.

All learners consume one :class:`Experience` at a time. Mini-batch learners
buffer only when their explicitly configured batch size is greater than one;
the strict batch-one arms never buffer or replay.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import time
from typing import List, Sequence

from .types import Experience, StepStats


def _dot(weights: Sequence[float], features: Sequence[float]) -> float:
    return sum(w * x for w, x in zip(weights, features))


class OnlineLearner:
    """Small common interface used by the benchmark and independent validator."""

    batch_size = 1
    allows_replay = False
    event_driven = False

    def predict(self, features: Sequence[float]) -> float:
        raise NotImplementedError

    def observe(self, experience: Experience) -> StepStats:
        raise NotImplementedError

    def flush(self) -> int:
        return 0

    def snapshot(self) -> dict:
        raise NotImplementedError

    def restore(self, snapshot: dict) -> None:
        raise NotImplementedError

    def digest(self) -> str:
        encoded = json.dumps(self.snapshot(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


class SGDLearner(OnlineLearner):
    def __init__(self, dimensions: int, learning_rate: float = 0.03, batch_size: int = 1):
        if batch_size not in (1, 32, 128):
            raise ValueError("batch_size must be one of 1, 32, 128")
        self.dimensions = dimensions
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.weights = [0.0] * dimensions
        self.bias = 0.0
        self.pending: List[Experience] = []
        self.samples_seen = self.updates = self.gradient_units = 0
        self.replay_examples = self.event_count = self.active_synaptic_ops = 0
        self.rollback_count = 0

    def predict(self, features: Sequence[float]) -> float:
        return self.bias + _dot(self.weights, features)

    def _apply_batch(self, batch: Sequence[Experience]) -> None:
        if not batch:
            return
        grad_w = [0.0] * self.dimensions
        grad_b = 0.0
        for item in batch:
            error = self.predict(item.features) - item.target
            for i, x in enumerate(item.features):
                grad_w[i] += error * x
            grad_b += error
        scale = 1.0 / len(batch)
        for i in range(self.dimensions):
            self.weights[i] -= self.learning_rate * grad_w[i] * scale
        self.bias -= self.learning_rate * grad_b * scale
        self.updates += 1
        self.gradient_units += len(batch) * (self.dimensions + 1)
        self.active_synaptic_ops += len(batch) * (self.dimensions + 1)

    def _stats(self, item: Experience, prediction: float, before: int, updated: bool,
               replay_examples: int = 0) -> StepStats:
        return StepStats(prediction, 0.5 * (prediction - item.target) ** 2, updated,
                         self.updates - before, self.samples_seen, self.gradient_units,
                         self.event_count, self.active_synaptic_ops, replay_examples,
                         (self.dimensions + 1) * 8, (len(self.weights) + 8) * 8,
                         self.rollback_count)

    def observe(self, experience: Experience) -> StepStats:
        started = time.perf_counter_ns()
        prediction = self.predict(experience.features)
        before = self.updates
        self.samples_seen += 1
        self.event_count += len(experience.event_indices)
        self.pending.append(experience)
        if len(self.pending) >= self.batch_size:
            batch = tuple(self.pending)
            self.pending.clear()
            self._apply_batch(batch)
        stats = self._stats(experience, prediction, before, self.updates > before)
        _ = time.perf_counter_ns() - started  # latency is measured by the runner, not persisted here.
        return stats

    def flush(self) -> int:
        if not self.pending:
            return 0
        pending = tuple(self.pending)
        self.pending.clear()
        self._apply_batch(pending)
        return len(pending)

    def snapshot(self) -> dict:
        return {"kind": "sgd", "dimensions": self.dimensions, "learning_rate": self.learning_rate,
                "batch_size": self.batch_size, "weights": list(self.weights), "bias": self.bias,
                "samples_seen": self.samples_seen, "updates": self.updates,
                "gradient_units": self.gradient_units, "replay_examples": self.replay_examples}

    def restore(self, snapshot: dict) -> None:
        self.weights = list(snapshot["weights"])
        self.bias = float(snapshot["bias"])
        self.samples_seen = int(snapshot["samples_seen"])
        self.updates = int(snapshot["updates"])
        self.gradient_units = int(snapshot["gradient_units"])


class AdamLearner(SGDLearner):
    def __init__(self, dimensions: int, learning_rate: float = 0.01, batch_size: int = 1,
                 beta1: float = 0.9, beta2: float = 0.999, epsilon: float = 1e-8):
        super().__init__(dimensions, learning_rate, batch_size)
        self.beta1, self.beta2, self.epsilon = beta1, beta2, epsilon
        self.m = [0.0] * dimensions + [0.0]
        self.v = [0.0] * dimensions + [0.0]
        self.t = 0

    def _apply_batch(self, batch: Sequence[Experience]) -> None:
        if not batch:
            return
        grad = [0.0] * (self.dimensions + 1)
        for item in batch:
            error = self.predict(item.features) - item.target
            for i, x in enumerate(item.features):
                grad[i] += error * x / len(batch)
            grad[-1] += error / len(batch)
        self.t += 1
        for i, value in enumerate(grad):
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * value
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * value * value
            m_hat = self.m[i] / (1 - self.beta1 ** self.t)
            v_hat = self.v[i] / (1 - self.beta2 ** self.t)
            update = self.learning_rate * m_hat / (math.sqrt(v_hat) + self.epsilon)
            if i < self.dimensions:
                self.weights[i] -= update
            else:
                self.bias -= update
        self.updates += 1
        self.gradient_units += len(batch) * (self.dimensions + 1)
        self.active_synaptic_ops += len(batch) * (self.dimensions + 1)

    def snapshot(self) -> dict:
        data = super().snapshot()
        data.update({"kind": "adam", "m": list(self.m), "v": list(self.v), "t": self.t})
        return data


class IDBDLearner(OnlineLearner):
    """Linear IDBD with bounded log step sizes and a bias coordinate."""

    def __init__(self, dimensions: int, meta_step: float = 0.01, initial_step: float = 0.03):
        self.dimensions, self.meta_step = dimensions, meta_step
        self.weights = [0.0] * dimensions
        self.beta = [math.log(initial_step)] * dimensions
        self.h = [0.0] * dimensions
        self.samples_seen = self.updates = self.gradient_units = 0
        self.event_count = self.active_synaptic_ops = self.replay_examples = 0

    def predict(self, features: Sequence[float]) -> float:
        return _dot(self.weights, features)

    def observe(self, experience: Experience) -> StepStats:
        prediction = self.predict(experience.features)
        error = experience.target - prediction
        before = self.updates
        for i, x in enumerate(experience.features):
            g = error * x
            self.beta[i] += self.meta_step * g * self.h[i]
            self.beta[i] = max(-8.0, min(1.0, self.beta[i]))
            alpha = math.exp(self.beta[i])
            self.weights[i] += alpha * g
            self.h[i] = max(0.0, self.h[i] * (1.0 - alpha * x * x)) + alpha * g
        self.samples_seen += 1
        self.updates += 1
        self.gradient_units += self.dimensions
        self.active_synaptic_ops += self.dimensions
        self.event_count += len(experience.event_indices)
        return StepStats(prediction, 0.5 * error * error, self.updates > before, 1,
                         self.samples_seen, self.gradient_units, self.event_count,
                         self.active_synaptic_ops, 0, self.dimensions * 8, self.dimensions * 16)

    def snapshot(self) -> dict:
        return {"kind": "idbd", "dimensions": self.dimensions, "weights": list(self.weights),
                "beta": list(self.beta), "h": list(self.h), "samples_seen": self.samples_seen,
                "updates": self.updates}

    def restore(self, snapshot: dict) -> None:
        self.weights, self.beta, self.h = list(snapshot["weights"]), list(snapshot["beta"]), list(snapshot["h"])
        self.samples_seen, self.updates = int(snapshot["samples_seen"]), int(snapshot["updates"])


class NetworkIDBDLearner(OnlineLearner):
    """Clearly defined nonlinear extension: diagonal IDBD on a ReLU MLP.

    Each weight receives its own bounded log step size. The eligibility-like
    trace is a first-order local trace of the output gradient, not a claim of
    exact equivalence to a published Network-IDBD algorithm.
    """

    def __init__(self, dimensions: int, hidden_size: int = 8, meta_step: float = 0.002,
                 initial_step: float = 0.01):
        self.dimensions, self.hidden_size, self.meta_step = dimensions, hidden_size, meta_step
        # Small deterministic nonzero initialization keeps the nonlinear path
        # reachable while remaining reproducible and seed-free.
        self.w1 = [[0.02 * (1 if (j + i) % 2 else -1) for i in range(dimensions)] for j in range(hidden_size)]
        self.b1 = [0.0] * hidden_size
        self.w2 = [0.02 * (1 if j % 2 else -1) for j in range(hidden_size)]
        self.b2 = 0.0
        count = hidden_size * dimensions + hidden_size + hidden_size + 1
        self.beta = [math.log(initial_step)] * count
        self.h = [0.0] * count
        self.samples_seen = self.updates = self.gradient_units = self.event_count = 0
        self.active_synaptic_ops = 0

    def _forward(self, features: Sequence[float]):
        pre = [self.b1[j] + _dot(self.w1[j], features) for j in range(self.hidden_size)]
        hidden = [max(0.0, z) for z in pre]
        return pre, hidden, self.b2 + _dot(self.w2, hidden)

    def predict(self, features: Sequence[float]) -> float:
        return self._forward(features)[2]

    def observe(self, experience: Experience) -> StepStats:
        pre, hidden, prediction = self._forward(experience.features)
        error = experience.target - prediction
        grads = []
        for j in range(self.hidden_size):
            grads.extend(error * self.w2[j] * (1.0 if pre[j] > 0 else 0.0) * x for x in experience.features)
        grads.extend(error * self.w2[j] * (1.0 if pre[j] > 0 else 0.0) for j in range(self.hidden_size))
        grads.extend(error * h for h in hidden)
        grads.append(error)
        params = []
        for row in self.w1:
            params.extend(row)
        params.extend(self.b1)
        params.extend(self.w2)
        params.append(self.b2)
        for i, (param, grad) in enumerate(zip(params, grads)):
            alpha = math.exp(max(-10.0, min(-1.0, self.beta[i])))
            self.h[i] = 0.9 * self.h[i] + alpha * grad
            self.beta[i] = max(-10.0, min(-1.0, self.beta[i] + self.meta_step * grad * self.h[i]))
            params[i] = param + alpha * grad
        offset = 0
        for j in range(self.hidden_size):
            self.w1[j] = params[offset:offset + self.dimensions]; offset += self.dimensions
        self.b1 = params[offset:offset + self.hidden_size]; offset += self.hidden_size
        self.w2 = params[offset:offset + self.hidden_size]; offset += self.hidden_size
        self.b2 = params[offset]
        self.samples_seen += 1; self.updates += 1; self.gradient_units += len(params)
        self.active_synaptic_ops += len(params)
        self.event_count += len(experience.event_indices)
        return StepStats(prediction, 0.5 * error * error, True, 1, self.samples_seen,
                         self.gradient_units, self.event_count, self.active_synaptic_ops, 0,
                         len(params) * 8, len(params) * 16)

    def snapshot(self) -> dict:
        return {"kind": "networkidbd", "dimensions": self.dimensions, "hidden_size": self.hidden_size,
                "w1": copy.deepcopy(self.w1), "b1": list(self.b1), "w2": list(self.w2), "b2": self.b2,
                "beta": list(self.beta), "h": list(self.h), "samples_seen": self.samples_seen,
                "updates": self.updates}

    def restore(self, snapshot: dict) -> None:
        self.w1, self.b1, self.w2, self.b2 = copy.deepcopy(snapshot["w1"]), list(snapshot["b1"]), list(snapshot["w2"]), float(snapshot["b2"])
        self.beta, self.h = list(snapshot["beta"]), list(snapshot["h"])
        self.samples_seen, self.updates = int(snapshot["samples_seen"]), int(snapshot["updates"])


class TIDBDLearner(OnlineLearner):
    """TD(0) prediction with per-feature adaptive step sizes."""

    def __init__(self, dimensions: int, gamma: float = 0.9, meta_step: float = 0.01,
                 initial_step: float = 0.03, trace_decay: float = 0.8):
        self.dimensions, self.gamma, self.meta_step, self.trace_decay = dimensions, gamma, meta_step, trace_decay
        self.weights = [0.0] * dimensions
        self.beta = [math.log(initial_step)] * dimensions
        self.h = [0.0] * dimensions
        self.e = [0.0] * dimensions
        self.samples_seen = self.updates = self.gradient_units = self.event_count = 0
        self.active_synaptic_ops = 0

    def predict(self, features: Sequence[float]) -> float:
        return _dot(self.weights, features)

    def observe(self, experience: Experience) -> StepStats:
        prediction = self.predict(experience.features)
        next_value = 0.0 if experience.done or experience.next_features is None else self.predict(experience.next_features)
        td_error = experience.reward + self.gamma * next_value - prediction
        for i, x in enumerate(experience.features):
            self.beta[i] += self.meta_step * td_error * x * self.h[i]
            self.beta[i] = max(-8.0, min(1.0, self.beta[i]))
            alpha = math.exp(self.beta[i])
            self.e[i] = self.gamma * self.trace_decay * self.e[i] + x
            self.weights[i] += alpha * td_error * self.e[i]
            self.h[i] = max(0.0, self.h[i] * (1.0 - alpha * x * self.e[i])) + alpha * td_error * self.e[i]
        if experience.done:
            self.e = [0.0] * self.dimensions
        self.samples_seen += 1; self.updates += 1; self.gradient_units += self.dimensions
        self.active_synaptic_ops += self.dimensions
        self.event_count += len(experience.event_indices)
        return StepStats(prediction, 0.5 * td_error * td_error, True, 1, self.samples_seen,
                         self.gradient_units, self.event_count, self.active_synaptic_ops, 0,
                         self.dimensions * 8, self.dimensions * 32)

    def snapshot(self) -> dict:
        return {"kind": "tidbd", "dimensions": self.dimensions, "weights": list(self.weights),
                "beta": list(self.beta), "h": list(self.h), "e": list(self.e),
                "samples_seen": self.samples_seen, "updates": self.updates}

    def restore(self, snapshot: dict) -> None:
        self.weights, self.beta, self.h, self.e = list(snapshot["weights"]), list(snapshot["beta"]), list(snapshot["h"]), list(snapshot["e"])
        self.samples_seen, self.updates = int(snapshot["samples_seen"]), int(snapshot["updates"])


class ReplayLearner(OnlineLearner):
    """Explicit replay arm; replay is never implicit in strict batch-one arms."""

    allows_replay = True

    def __init__(self, dimensions: int, capacity: int = 64, replay_ratio: int = 1,
                 learning_rate: float = 0.03):
        self.base = SGDLearner(dimensions, learning_rate, batch_size=1)
        self.capacity, self.replay_ratio = capacity, replay_ratio
        self.buffer: List[Experience] = []
        self.samples_seen = 0

    @property
    def updates(self): return self.base.updates
    @property
    def replay_examples(self): return self.base.replay_examples

    def predict(self, features: Sequence[float]) -> float:
        return self.base.predict(features)

    def observe(self, experience: Experience) -> StepStats:
        stats = self.base.observe(experience)
        self.samples_seen += 1
        replayed = 0
        if self.buffer:
            for old in self.buffer[-self.replay_ratio:]:
                self.base.observe(old)
                replayed += 1
        self.base.replay_examples += replayed
        self.buffer.append(experience)
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)
        return StepStats(stats.prediction, stats.loss, True, 1 + replayed,
                         self.samples_seen, self.base.gradient_units, self.base.event_count,
                         self.base.active_synaptic_ops, self.base.replay_examples,
                         stats.model_bytes, stats.state_bytes, stats.rollback_count)

    def flush(self): return self.base.flush()
    def snapshot(self): return {"kind": "replay", "capacity": self.capacity, "replay_ratio": self.replay_ratio,
                               "base": self.base.snapshot(), "buffer_size": len(self.buffer)}
    def restore(self, snapshot): self.base.restore(snapshot["base"])


class EWCLearner(SGDLearner):
    """Diagonal EWC penalty with explicit task-boundary consolidation."""

    def __init__(self, dimensions: int, learning_rate: float = 0.03, ewc_lambda: float = 2.0):
        super().__init__(dimensions, learning_rate, batch_size=1)
        self.ewc_lambda = ewc_lambda
        self.reference = list(self.weights) + [self.bias]
        self.importance = [0.0] * (dimensions + 1)

    def _apply_batch(self, batch: Sequence[Experience]) -> None:
        if not batch: return
        item = batch[-1]
        error = self.predict(item.features) - item.target
        grad = [error * x for x in item.features] + [error]
        for i in range(len(grad)):
            current = self.weights[i] if i < self.dimensions else self.bias
            grad[i] += self.ewc_lambda * self.importance[i] * (current - self.reference[i])
            self.importance[i] = 0.99 * self.importance[i] + 0.01 * (grad[i] * grad[i])
            if i < self.dimensions: self.weights[i] -= self.learning_rate * grad[i]
            else: self.bias -= self.learning_rate * grad[i]
        self.updates += 1; self.gradient_units += len(grad); self.active_synaptic_ops += len(grad)

    def mark_task_boundary(self) -> None:
        self.reference = list(self.weights) + [self.bias]
        self.importance = [max(value, 1e-8) for value in self.importance]

    def snapshot(self):
        data = super().snapshot(); data.update({"kind": "ewc", "reference": list(self.reference), "importance": list(self.importance)})
        return data


class PlasticityGuardLearner(SGDLearner):
    """Bounded plasticity guard: attenuate updates after surprises, recover on safe loss."""

    def __init__(self, dimensions: int, learning_rate: float = 0.03, guard_floor: float = 0.2,
                 recovery: float = 0.02, surprise_threshold: float = 1.0):
        super().__init__(dimensions, learning_rate, batch_size=1)
        self.guard_floor, self.recovery, self.surprise_threshold = guard_floor, recovery, surprise_threshold
        self.plasticity = 1.0

    def observe(self, experience: Experience) -> StepStats:
        prediction = self.predict(experience.features)
        loss = 0.5 * (prediction - experience.target) ** 2
        original = self.learning_rate
        self.learning_rate = original * self.plasticity
        stats = super().observe(experience)
        self.learning_rate = original
        if loss > self.surprise_threshold:
            self.plasticity = max(self.guard_floor, self.plasticity * 0.9)
        else:
            self.plasticity = min(1.0, self.plasticity + self.recovery)
        return stats

    def snapshot(self):
        data = super().snapshot(); data.update({"kind": "plasticity_guard", "plasticity": self.plasticity})
        return data


class EventDrivenLearner(SGDLearner):
    """Software sparse simulator: only event-active coordinates update."""

    event_driven = True

    def __init__(self, dimensions: int, learning_rate: float = 0.03, threshold: float = 0.5):
        super().__init__(dimensions, learning_rate, batch_size=1)
        self.threshold = threshold

    def _apply_batch(self, batch: Sequence[Experience]) -> None:
        if not batch: return
        item = batch[-1]
        active = [i for i, value in enumerate(item.features) if abs(value) >= self.threshold]
        error = self.predict(item.features) - item.target
        for i in active:
            self.weights[i] -= self.learning_rate * error * item.features[i]
        if active:
            self.bias -= self.learning_rate * error
            self.active_synaptic_ops += len(active) + 1
            self.updates += 1
        self.gradient_units += len(active) + 1

    def snapshot(self):
        data = super().snapshot(); data.update({"kind": "event_driven", "threshold": self.threshold})
        return data

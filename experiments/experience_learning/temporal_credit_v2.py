"""Scalar temporal-utility selective credit for Oak Lab.

State slice: ``oaklab-experience-learning-selective-credit-v2``.

This is a new theory after V1's failure.  It avoids V1's per-parameter delta
memory and does not interpret uncertainty as evidence of harm.  A scalar
online utility signal is updated from the observed sequential loss change;
the next update is throttled only when the upper confidence bound of that
signal is below zero.  This is an operational predictive-utility estimand,
not a causal counterfactual claim.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Sequence

from .learners import OnlineLearner, _dot
from .types import Experience, StepStats


STATE_SLICE = "oaklab-experience-learning-selective-credit-v2"


class TemporalUtilityGateLearner(OnlineLearner):
    """Batch-one SGD with a scalar delayed utility gate.

    Let ``ell_t`` be the pre-update loss on item ``t``.  After observing item
    ``t``, the utility statistic is ``U_t = ell_(t-1) - ell_t``.  A full update
    is used unless ``mean(U) + k*std(U) < 0`` after warm-up, in which case the
    fixed minimum gate is used.  The rule therefore preserves updates while
    utility is uncertain and reacts only to confidently harmful sequences.
    """

    batch_size = 1
    allows_replay = False
    event_driven = False

    def __init__(
        self,
        dimensions: int,
        learning_rate: float = 0.03,
        utility_decay: float = 0.8,
        variance_decay: float = 0.9,
        confidence_k: float = 0.75,
        min_gate: float = 0.1,
        warmup: int = 8,
    ):
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        if learning_rate <= 0 or not 0 < utility_decay < 1 or not 0 < variance_decay < 1:
            raise ValueError("invalid learning or decay parameter")
        if confidence_k < 0 or not 0 <= min_gate <= 1 or warmup < 0:
            raise ValueError("invalid confidence, gate, or warmup parameter")
        self.dimensions = dimensions
        self.learning_rate = float(learning_rate)
        self.utility_decay = float(utility_decay)
        self.variance_decay = float(variance_decay)
        self.confidence_k = float(confidence_k)
        self.min_gate = float(min_gate)
        self.warmup = int(warmup)
        self.weights = [0.0] * dimensions
        self.bias = 0.0
        self.utility_mean = 0.0
        self.utility_second = 0.0
        self.previous_loss: float | None = None
        self.samples_seen = 0
        self.updates = 0
        self.gated_updates = 0
        self.event_count = 0
        self.active_synaptic_ops = 0

    def predict(self, features: Sequence[float]) -> float:
        return self.bias + _dot(self.weights, features)

    def _record_utility(self, loss: float) -> None:
        if self.previous_loss is None:
            return
        utility = self.previous_loss - loss
        self.utility_mean = self.utility_decay * self.utility_mean + (1.0 - self.utility_decay) * utility
        self.utility_second = self.variance_decay * self.utility_second + (1.0 - self.variance_decay) * utility * utility

    def _gate(self) -> float:
        if self.samples_seen < self.warmup:
            return 1.0
        variance = max(0.0, self.utility_second - self.utility_mean ** 2)
        upper_bound = self.utility_mean + self.confidence_k * math.sqrt(variance + 1e-12)
        if upper_bound >= 0.0:
            return 1.0
        self.gated_updates += 1
        return self.min_gate

    def observe(self, experience: Experience) -> StepStats:
        prediction = self.predict(experience.features)
        loss = 0.5 * (prediction - experience.target) ** 2
        self._record_utility(loss)
        gate = self._gate()
        error = prediction - experience.target
        for index, value in enumerate(experience.features):
            self.weights[index] -= self.learning_rate * gate * error * value
        self.bias -= self.learning_rate * gate * error
        self.previous_loss = loss
        self.samples_seen += 1
        self.updates += 1
        self.event_count += len(experience.event_indices)
        self.active_synaptic_ops += self.dimensions + 1
        model_bytes = (self.dimensions + 1) * 8
        state_bytes = (self.dimensions + 6) * 8
        return StepStats(
            prediction=prediction,
            loss=loss,
            updated=True,
            updates=1,
            samples_seen=self.samples_seen,
            gradient_units=self.dimensions + 1,
            event_count=self.event_count,
            active_synaptic_ops=self.active_synaptic_ops,
            replay_examples=0,
            model_bytes=model_bytes,
            state_bytes=state_bytes,
        )

    def snapshot(self) -> dict:
        return {
            "kind": "temporal_utility_gate",
            "state_slice": STATE_SLICE,
            "dimensions": self.dimensions,
            "learning_rate": self.learning_rate,
            "utility_decay": self.utility_decay,
            "variance_decay": self.variance_decay,
            "confidence_k": self.confidence_k,
            "min_gate": self.min_gate,
            "warmup": self.warmup,
            "weights": list(self.weights),
            "bias": self.bias,
            "utility_mean": self.utility_mean,
            "utility_second": self.utility_second,
            "previous_loss": self.previous_loss,
            "samples_seen": self.samples_seen,
            "updates": self.updates,
            "gated_updates": self.gated_updates,
        }

    def restore(self, snapshot: dict) -> None:
        if snapshot.get("state_slice") != STATE_SLICE:
            raise ValueError("snapshot state slice mismatch")
        self.weights = list(snapshot["weights"])
        self.bias = float(snapshot["bias"])
        self.utility_mean = float(snapshot["utility_mean"])
        self.utility_second = float(snapshot["utility_second"])
        previous_loss = snapshot.get("previous_loss")
        self.previous_loss = None if previous_loss is None else float(previous_loss)
        self.samples_seen = int(snapshot["samples_seen"])
        self.updates = int(snapshot["updates"])
        self.gated_updates = int(snapshot["gated_updates"])

    def digest(self) -> str:
        encoded = json.dumps(self.snapshot(), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        return hashlib.sha256(encoded).hexdigest()

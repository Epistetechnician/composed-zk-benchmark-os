"""Delayed predictive-utility selective credit for the Oak Lab lane.

State slice: ``oaklab-experience-learning-selective-credit-v1``.

The mechanism is deliberately different from the closed plasticity guard.  It
does not reject an update because the current error is surprising.  Instead it
scores the *previous* update by its one-step downstream loss reduction and
uses a lower confidence bound on that score to gate the next update.  Only the
current ``Experience`` is presented to ``observe``; the learner retains one
parameter-delta vector, not a replay buffer or an accumulated gradient.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Sequence

from .learners import OnlineLearner, _dot
from .types import Experience, StepStats


STATE_SLICE = "oaklab-experience-learning-selective-credit-v1"


class PredictiveUtilityCreditLearner(OnlineLearner):
    """Linear batch-one learner with a delayed, per-coordinate credit gate.

    For item ``t`` the learner first evaluates whether the update made on
    item ``t-1`` improved the loss on item ``t``.  The counterfactual prediction
    is reconstructed from the retained previous delta, so no prior example is
    retained.  The next update is scaled by a lower confidence bound of the
    exponentially tracked utility.  The first ``warmup`` items are ungated.
    """

    batch_size = 1
    allows_replay = False
    event_driven = False

    def __init__(
        self,
        dimensions: int,
        learning_rate: float = 0.03,
        utility_decay: float = 0.9,
        variance_decay: float = 0.9,
        confidence_k: float = 0.5,
        min_gate: float = 0.05,
        warmup: int = 4,
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
        self.credit_mean = [0.0] * (dimensions + 1)
        self.credit_second = [0.0] * (dimensions + 1)
        self.previous_delta = [0.0] * (dimensions + 1)
        self.pending_delta = False
        self.samples_seen = 0
        self.updates = 0
        self.gated_coordinates = 0
        self.event_count = 0
        self.active_synaptic_ops = 0

    def predict(self, features: Sequence[float]) -> float:
        return self.bias + _dot(self.weights, features)

    def _record_previous_utility(self, features: Sequence[float], target: float, prediction: float) -> None:
        if not self.pending_delta:
            return
        augmented = tuple(features) + (1.0,)
        no_update_prediction = prediction - _dot(self.previous_delta, augmented)
        current_loss = 0.5 * (prediction - target) ** 2
        no_update_loss = 0.5 * (no_update_prediction - target) ** 2
        utility = no_update_loss - current_loss
        for index, delta in enumerate(self.previous_delta):
            if abs(delta) < 1e-15:
                continue
            mean = self.utility_decay * self.credit_mean[index] + (1.0 - self.utility_decay) * utility
            second = self.variance_decay * self.credit_second[index] + (1.0 - self.variance_decay) * utility * utility
            self.credit_mean[index] = mean
            self.credit_second[index] = second

    def _gate(self, index: int) -> float:
        if self.samples_seen < self.warmup:
            return 1.0
        variance = max(0.0, self.credit_second[index] - self.credit_mean[index] ** 2)
        lower_bound = self.credit_mean[index] - self.confidence_k * math.sqrt(variance + 1e-12)
        if lower_bound > 0.0:
            return 1.0
        self.gated_coordinates += 1
        return self.min_gate

    def observe(self, experience: Experience) -> StepStats:
        prediction = self.predict(experience.features)
        self._record_previous_utility(experience.features, experience.target, prediction)
        error = prediction - experience.target
        gates = [self._gate(index) for index in range(self.dimensions + 1)]
        delta = [-self.learning_rate * gates[index] * error * value
                 for index, value in enumerate(experience.features)]
        delta.append(-self.learning_rate * gates[-1] * error)
        for index, value in enumerate(delta[:-1]):
            self.weights[index] += value
        self.bias += delta[-1]
        self.previous_delta = delta
        self.pending_delta = True
        self.samples_seen += 1
        self.updates += 1
        self.event_count += len(experience.event_indices)
        self.active_synaptic_ops += self.dimensions + 1
        loss = 0.5 * error * error
        model_bytes = (self.dimensions + 1) * 8
        state_bytes = (4 * (self.dimensions + 1) + 8) * 8
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
            "kind": "predictive_utility_credit",
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
            "credit_mean": list(self.credit_mean),
            "credit_second": list(self.credit_second),
            "previous_delta": list(self.previous_delta),
            "pending_delta": self.pending_delta,
            "samples_seen": self.samples_seen,
            "updates": self.updates,
            "gated_coordinates": self.gated_coordinates,
        }

    def restore(self, snapshot: dict) -> None:
        if snapshot.get("state_slice") != STATE_SLICE:
            raise ValueError("snapshot state slice mismatch")
        self.weights = list(snapshot["weights"])
        self.bias = float(snapshot["bias"])
        self.credit_mean = list(snapshot["credit_mean"])
        self.credit_second = list(snapshot["credit_second"])
        self.previous_delta = list(snapshot["previous_delta"])
        self.pending_delta = bool(snapshot["pending_delta"])
        self.samples_seen = int(snapshot["samples_seen"])
        self.updates = int(snapshot["updates"])
        self.gated_coordinates = int(snapshot["gated_coordinates"])

    def digest(self) -> str:
        encoded = json.dumps(self.snapshot(), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        return hashlib.sha256(encoded).hexdigest()

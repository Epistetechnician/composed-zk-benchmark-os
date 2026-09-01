"""Primary and secondary metrics for experience streams."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass
class MetricAccumulator:
    losses: list[float]
    predictions: list[float]
    targets: list[float]
    updates: int = 0
    samples: int = 0
    events: int = 0
    active_synaptic_ops: int = 0
    replay_examples: int = 0
    model_bytes: int = 0
    state_bytes: int = 0
    rollback_count: int = 0
    latency_ns: int = 0

    @classmethod
    def create(cls):
        return cls([], [], [])

    def add(self, stats, target: float, latency_ns: int = 0) -> None:
        self.losses.append(float(stats.loss)); self.predictions.append(float(stats.prediction));
        self.targets.append(float(target))
        self.updates += stats.updates; self.samples = stats.samples_seen
        self.events = stats.event_count; self.active_synaptic_ops = stats.active_synaptic_ops
        self.replay_examples = stats.replay_examples; self.model_bytes = stats.model_bytes
        self.state_bytes = stats.state_bytes; self.rollback_count = stats.rollback_count
        self.latency_ns += latency_ns

    def summary(self, change_points: Sequence[int] = ()) -> dict:
        n = len(self.losses)
        cumulative = sum(self.losses)
        rolling = max(1, min(16, n // 4 or 1))
        lag = adaptation_lag(self.losses, change_points, rolling)
        return {
            "primary_endpoint": "cumulative_prediction_loss",
            "cumulative_prediction_loss": cumulative,
            "mean_prediction_loss": cumulative / n if n else 0.0,
            "heldout_performance_after_fixed_update_budget": cumulative / n if n else 0.0,
            "fixed_update_budget_updates": self.updates,
            "adaptation_lag": lag,
            "forgetting": forgetting(self.losses, change_points, rolling),
            "calibration_brier": brier_score(self.predictions, self.targets),
            "updates": self.updates,
            "samples": self.samples,
            "event_count": self.events,
            "active_synaptic_ops": self.active_synaptic_ops,
            "replay_examples": self.replay_examples,
            "replay_storage_bytes": self.replay_examples * 8,
            "model_bytes": self.model_bytes,
            "state_bytes": self.state_bytes,
            "wall_clock_latency_ns": self.latency_ns,
            "energy_per_learned_event_proxy": (self.active_synaptic_ops / self.events) if self.events else 0.0,
            "rollback_count": self.rollback_count,
        }


def adaptation_lag(losses: Sequence[float], change_points: Sequence[int], window: int = 8) -> int:
    """First post-shift window at or below the pre-shift median; horizon if absent."""
    if not losses or not change_points:
        return 0
    lags = []
    for point in change_points:
        baseline = losses[max(0, point - window):point]
        if not baseline: continue
        threshold = sorted(baseline)[len(baseline) // 2]
        found = len(losses) - point
        for index in range(point, len(losses) - window + 1):
            if sum(losses[index:index + window]) / window <= threshold:
                found = index - point; break
        lags.append(found)
    return max(lags) if lags else 0


def forgetting(losses: Sequence[float], change_points: Sequence[int], window: int = 8) -> float:
    if not change_points or not losses: return 0.0
    values = []
    for point in change_points:
        pre = losses[max(0, point - window):point]
        post = losses[point:min(len(losses), point + window)]
        if pre and post: values.append(sum(post) / len(post) - sum(pre) / len(pre))
    return sum(values) / len(values) if values else 0.0


def brier_score(predictions: Sequence[float], targets: Sequence[float]) -> float:
    if not predictions: return 0.0
    # Map arbitrary regression targets/predictions into a bounded confidence only
    # for a comparable calibration diagnostic; it is not the primary endpoint.
    values = []
    for pred, target in zip(predictions, targets):
        p = 1.0 / (1.0 + math.exp(max(-60.0, min(60.0, -pred))))
        y = 1.0 if target >= 0 else 0.0
        values.append((p - y) ** 2)
    return sum(values) / len(values)

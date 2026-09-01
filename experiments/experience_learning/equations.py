"""Reference one-step equations for exact IDBD/TIDBD parity checks.

These functions intentionally contain no learner imports. They are small
independent oracles used to validate the state transition implemented by
``learners.py``.
"""

from __future__ import annotations

import math
from typing import Sequence


def _dot(weights: Sequence[float], features: Sequence[float]) -> float:
    return sum(w * x for w, x in zip(weights, features))


def _bound(value: float, lower: float | None, upper: float | None) -> float:
    if lower is not None:
        value = max(lower, value)
    if upper is not None:
        value = min(upper, value)
    return value


def idbd_reference_step(weights, beta, h, features, target, meta_step=0.01,
                        beta_min=-8.0, beta_max=1.0):
    weights, beta, h = list(weights), list(beta), list(h)
    delta = target - _dot(weights, features)
    for i, x in enumerate(features):
        beta[i] = _bound(beta[i] + meta_step * delta * x * h[i], beta_min, beta_max)
        alpha = math.exp(beta[i])
        weights[i] += alpha * delta * x
        h[i] = max(0.0, h[i] * (1.0 - alpha * x * x)) + alpha * delta * x
    return weights, beta, h


def idbd_published_step(weights, beta, h, features, target, meta_step=0.01):
    """One unbounded IDBD step from Sutton's published pseudocode.

    The deployed learner uses the separately declared ``[-8, 1]`` beta
    stabilization bounds. Keeping this unbounded oracle explicit prevents an
    implementation convenience from being mistaken for part of the paper's
    core algorithm.
    """
    return idbd_reference_step(weights, beta, h, features, target,
                               meta_step=meta_step, beta_min=None, beta_max=None)


def tidbd_reference_step(weights, beta, h, eligibility, features, reward,
                         next_features, done, gamma=0.9, trace_decay=0.8,
                         meta_step=0.01, beta_min=-8.0, beta_max=1.0):
    weights, beta, h, eligibility = list(weights), list(beta), list(h), list(eligibility)
    prediction = _dot(weights, features)
    next_value = 0.0 if done or next_features is None else _dot(weights, next_features)
    delta = reward + gamma * next_value - prediction
    for i, x in enumerate(features):
        beta[i] = _bound(beta[i] + meta_step * delta * x * h[i], beta_min, beta_max)
        alpha = math.exp(beta[i])
        eligibility[i] = gamma * trace_decay * eligibility[i] + x
        weights[i] += alpha * delta * eligibility[i]
        h[i] = max(0.0, h[i] * (1.0 - alpha * x * eligibility[i])) + alpha * delta * eligibility[i]
    if done:
        eligibility = [0.0] * len(eligibility)
    return weights, beta, h, eligibility


def tidbd_published_step(weights, beta, h, eligibility, features, reward,
                         next_features, done, gamma=0.9, trace_decay=0.8,
                         meta_step=0.01):
    """One unbounded TIDBD(λ) step from Algorithm 1 of the paper."""
    return tidbd_reference_step(weights, beta, h, eligibility, features, reward,
                                next_features, done, gamma=gamma,
                                trace_decay=trace_decay, meta_step=meta_step,
                                beta_min=None, beta_max=None)

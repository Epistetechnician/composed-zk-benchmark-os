"""Shared immutable protocol types for the experience-learning lane."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Experience:
    """One and only one item presented to an online learner."""

    step: int
    features: Tuple[float, ...]
    target: float
    reward: float = 0.0
    next_features: Optional[Tuple[float, ...]] = None
    done: bool = True
    task_id: int = 0
    event_indices: Tuple[int, ...] = ()
    source_id: str = ""


@dataclass(frozen=True)
class StepStats:
    prediction: float
    loss: float
    updated: bool
    updates: int
    samples_seen: int
    gradient_units: int
    event_count: int
    active_synaptic_ops: int
    replay_examples: int
    model_bytes: int
    state_bytes: int
    rollback_count: int = 0

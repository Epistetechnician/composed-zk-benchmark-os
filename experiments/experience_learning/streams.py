"""Deterministic, future-safe experience streams.

The ``NoisyMNISTLike`` and ``EventCameraLike`` generators are synthetic local
fixtures, not downloads or claims of the real datasets. Every stream exposes
which features are learnable so a benchmark can measure learnable versus
unlearnable correlation directly.
"""

from __future__ import annotations

import random
from typing import Iterator, Sequence

from .types import Experience


def _normal(rng: random.Random, scale: float) -> float:
    return rng.gauss(0.0, scale) if scale else 0.0


class SparseNoisyStream:
    """Sparse regression with one predictable coordinate and distractors."""

    def __init__(self, steps: int = 256, seed: int = 7, dimensions: int = 16,
                 predictable_index: int = 0, noise: float = 0.25,
                 sparsity: float = 0.15):
        if dimensions < 2 or not 0 <= predictable_index < dimensions:
            raise ValueError("invalid dimensions or predictable_index")
        self.steps, self.seed, self.dimensions = steps, seed, dimensions
        self.predictable_feature_indices = (predictable_index,)
        self.noise, self.sparsity = noise, sparsity

    def __iter__(self) -> Iterator[Experience]:
        rng = random.Random(self.seed)
        p = self.predictable_feature_indices[0]
        for step in range(self.steps):
            values = [0.0] * self.dimensions
            active = []
            for index in range(self.dimensions):
                if rng.random() < self.sparsity or index == p:
                    values[index] = float(rng.choice((-1, 1)))
                    active.append(index)
            target = 1.5 * values[p] + _normal(rng, self.noise)
            yield Experience(step, tuple(values), target,
                             event_indices=tuple(active), source_id=f"sparse:{step}")


class NonstationaryFeatureStream:
    """Feature relevance switches at fixed, declared task boundaries."""

    def __init__(self, steps: int = 256, seed: int = 11, dimensions: int = 8,
                 switch_at: int | None = None, noise: float = 0.1):
        self.steps, self.seed, self.dimensions = steps, seed, dimensions
        self.switch_at = switch_at if switch_at is not None else steps // 2
        self.noise = noise
        self.predictable_feature_indices = (0, 1)

    def __iter__(self) -> Iterator[Experience]:
        rng = random.Random(self.seed)
        for step in range(self.steps):
            x = [rng.uniform(-1.0, 1.0) for _ in range(self.dimensions)]
            task = 0 if step < self.switch_at else 1
            target = (2.0 * x[0] if task == 0 else -2.0 * x[1]) + _normal(rng, self.noise)
            yield Experience(step, tuple(x), target, task_id=task,
                             event_indices=tuple(range(self.dimensions)), source_id=f"nonstationary:{step}")


class DriftingTargetStream:
    """Continuous target drift without changing the feature distribution."""

    def __init__(self, steps: int = 256, seed: int = 13, dimensions: int = 6,
                 drift_per_step: float = 0.01, noise: float = 0.1):
        self.steps, self.seed, self.dimensions = steps, seed, dimensions
        self.drift_per_step, self.noise = drift_per_step, noise
        self.predictable_feature_indices = (0, 1)

    def __iter__(self) -> Iterator[Experience]:
        rng = random.Random(self.seed)
        for step in range(self.steps):
            x = [rng.uniform(-1.0, 1.0) for _ in range(self.dimensions)]
            coefficient = 1.0 + self.drift_per_step * step
            target = coefficient * x[0] - 0.75 * x[1] + _normal(rng, self.noise)
            yield Experience(step, tuple(x), target, task_id=step // max(1, self.steps // 4),
                             event_indices=tuple(range(self.dimensions)), source_id=f"drift:{step}")


class DelayedRewardStream:
    """One-state delayed-reward TD stream with explicit next observations."""

    def __init__(self, episodes: int = 32, horizon: int = 8, seed: int = 17,
                 reward_delay: int = 3, gamma: float = 0.9):
        self.episodes, self.horizon, self.seed = episodes, horizon, seed
        self.reward_delay, self.gamma = reward_delay, gamma
        self.predictable_feature_indices = (0,)

    def __iter__(self) -> Iterator[Experience]:
        rng = random.Random(self.seed)
        step = 0
        for episode in range(self.episodes):
            # Fixed-state features make the TD target independently checkable.
            features = (1.0,)
            for t in range(self.horizon):
                done = t == self.horizon - 1
                reward = 1.0 if t == self.reward_delay else 0.0
                yield Experience(step, features, reward, reward=reward,
                                 next_features=None if done else features,
                                 done=done, task_id=episode,
                                 event_indices=(0,), source_id=f"td:{episode}:{t}")
                step += 1
            # Independent episode marker prevents accidental state carry-over in clients.
            _ = rng.random()


class NoisyMNISTLikeStream:
    """Synthetic 28x28 digit-like stream with distractor pixels.

    This deliberately does not download or represent the MNIST dataset. The
    central 3x3 pattern is learnable; noise and distractors are unlearnable.
    """

    def __init__(self, steps: int = 256, seed: int = 19, noise_pixels: int = 40):
        self.steps, self.seed, self.noise_pixels = steps, seed, noise_pixels
        self.dimensions = 28 * 28
        self.predictable_feature_indices = tuple(13 * 28 + 13 + i for i in (0, 1, 28, 29))

    def __iter__(self) -> Iterator[Experience]:
        rng = random.Random(self.seed)
        for step in range(self.steps):
            label = step % 2
            x = [0.0] * self.dimensions
            if label:
                for i in self.predictable_feature_indices:
                    x[i] = 1.0
            else:
                x[self.predictable_feature_indices[0]] = -1.0
            for _ in range(self.noise_pixels):
                x[rng.randrange(self.dimensions)] += rng.choice((-1.0, 1.0))
            target = float(1 if label else -1) + _normal(rng, 0.2)
            active = tuple(i for i, value in enumerate(x) if value)
            yield Experience(step, tuple(x), target, task_id=label,
                             event_indices=active, source_id=f"noisy-mnist-like:{step}")


class NoisyMNISTArrayStream:
    """No-download adapter for caller-supplied flattened MNIST arrays."""

    def __init__(self, images: Sequence[Sequence[float]], labels: Sequence[int],
                 seed: int = 31, noise_pixels: int = 40):
        if len(images) != len(labels) or not images:
            raise ValueError("images and labels must be non-empty and aligned")
        self.images, self.labels, self.seed, self.noise_pixels = images, labels, seed, noise_pixels
        self.dimensions = len(images[0])
        if self.dimensions == 0 or any(len(image) != self.dimensions for image in images):
            raise ValueError("all images must have equal nonzero flattened length")
        self.steps = len(images)
        self.predictable_feature_indices = tuple(range(min(4, self.dimensions)))

    def __iter__(self) -> Iterator[Experience]:
        rng = random.Random(self.seed)
        for step, (image, label) in enumerate(zip(self.images, self.labels)):
            x = [float(value) for value in image]
            for _ in range(self.noise_pixels):
                x[rng.randrange(self.dimensions)] += rng.choice((-1.0, 1.0))
            active = tuple(i for i, value in enumerate(x) if value)
            yield Experience(step, tuple(x), float(1 if int(label) else -1), task_id=int(label),
                             event_indices=active, source_id=f"noisy-mnist-array:{step}")


class EventCameraLikeStream:
    """Synthetic sparse polarity events, represented as a feature vector."""

    def __init__(self, steps: int = 256, seed: int = 23, dimensions: int = 64,
                 events_per_step: int = 3):
        self.steps, self.seed, self.dimensions = steps, seed, dimensions
        self.events_per_step = events_per_step
        self.predictable_feature_indices = (0, 1)

    def __iter__(self) -> Iterator[Experience]:
        rng = random.Random(self.seed)
        for step in range(self.steps):
            active = sorted({rng.randrange(self.dimensions) for _ in range(self.events_per_step)})
            values = [0.0] * self.dimensions
            for i in active:
                values[i] = float(rng.choice((-1, 1)))
            # Add a weak learnable polarity channel plus sparse unlearnable events.
            values[0] = 1.0 if step % 2 else -1.0
            if 0 not in active:
                active.append(0)
            target = values[0] + _normal(rng, 0.15)
            yield Experience(step, tuple(values), target,
                             event_indices=tuple(sorted(set(active))), source_id=f"event-camera-like:{step}")


class LongHorizonStream:
    """Composed long stream with shifts, drift, and delayed targets."""

    def __init__(self, steps: int = 512, seed: int = 29):
        self.steps, self.seed = steps, seed
        self.predictable_feature_indices = (0, 1)

    def __iter__(self) -> Iterator[Experience]:
        rng = random.Random(self.seed)
        for step in range(self.steps):
            x = [rng.uniform(-1.0, 1.0) for _ in range(8)]
            phase = (step // 128) % 2
            coefficient = 1.0 + 0.005 * step
            target = coefficient * (x[0] if phase == 0 else x[1]) + _normal(rng, 0.25)
            next_x = tuple(x) if step % 7 else tuple(rng.uniform(-1.0, 1.0) for _ in x)
            yield Experience(step, tuple(x), target, next_features=next_x,
                             done=step == self.steps - 1, task_id=phase,
                             event_indices=tuple(range(len(x))), source_id=f"long:{step}")


STREAMS = {
    "sparse_noisy": SparseNoisyStream,
    "nonstationary": NonstationaryFeatureStream,
    "drifting": DriftingTargetStream,
    "delayed_reward": DelayedRewardStream,
    "noisy_mnist_like": NoisyMNISTLikeStream,
    "event_camera_like": EventCameraLikeStream,
    "long_horizon": LongHorizonStream,
}

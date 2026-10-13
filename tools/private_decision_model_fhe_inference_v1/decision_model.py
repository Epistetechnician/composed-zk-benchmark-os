"""Synthetic linear scorer for the private-decision FHE inference V1 slice.

State slice: private-decision-model-fhe-inference-v1.
All examples are generated locally from fixed seeds. No user data is read.
"""

from __future__ import annotations

import hashlib

import numpy as np

STATE_SLICE = "private-decision-model-fhe-inference-v1"
SEED = 20260930
FEATURE_COUNT = 6
OPTIONS_PER_REQUEST = 4
TRAIN_ROWS = 128
CALIBRATION_REQUESTS = 12
EVALUATION_REQUESTS = 8
FEATURE_LOW = -8
FEATURE_HIGH_EXCLUSIVE = 9

_SYNTHETIC_TARGET_WEIGHTS = np.asarray([2, -3, 1, 4, -2, 3], dtype=np.int64)
_SYNTHETIC_TARGET_BIAS = 5


def fit_synthetic_scorer() -> tuple[np.ndarray, int]:
    """Fit integer coefficients using only a deterministic synthetic sample."""
    generator = np.random.default_rng(SEED)
    features = generator.integers(
        FEATURE_LOW,
        FEATURE_HIGH_EXCLUSIVE,
        size=(TRAIN_ROWS, FEATURE_COUNT),
        dtype=np.int64,
    )
    outcomes = features @ _SYNTHETIC_TARGET_WEIGHTS + _SYNTHETIC_TARGET_BIAS
    design = np.column_stack((features, np.ones(TRAIN_ROWS, dtype=np.int64)))
    fitted, *_ = np.linalg.lstsq(design, outcomes, rcond=None)
    coefficients = np.rint(fitted).astype(np.int64)
    weights = coefficients[:-1]
    bias = int(coefficients[-1])

    if not np.array_equal(weights, _SYNTHETIC_TARGET_WEIGHTS):
        raise RuntimeError("synthetic fit did not recover the frozen coefficient fixture")
    if bias != _SYNTHETIC_TARGET_BIAS:
        raise RuntimeError("synthetic fit did not recover the frozen bias fixture")
    return weights, bias


MODEL_WEIGHTS, MODEL_BIAS = fit_synthetic_scorer()


def option_scores(features: np.ndarray) -> np.ndarray:
    """Return four signed integer scores; compile this function with FHE."""
    return features @ MODEL_WEIGHTS + MODEL_BIAS


def _requests(seed_offset: int, count: int) -> np.ndarray:
    generator = np.random.default_rng(SEED + seed_offset)
    return generator.integers(
        FEATURE_LOW,
        FEATURE_HIGH_EXCLUSIVE,
        size=(count, OPTIONS_PER_REQUEST, FEATURE_COUNT),
        dtype=np.int64,
    )


def synthetic_calibration_requests() -> np.ndarray:
    """Return the disjoint synthetic input set used only for FHE compilation."""
    return _requests(1, CALIBRATION_REQUESTS)


def synthetic_evaluation_requests() -> np.ndarray:
    """Return a separate deterministic synthetic option-ranking fixture."""
    return _requests(2, EVALUATION_REQUESTS)


def validate_request_batch(requests: np.ndarray, expected_count: int | None = None) -> None:
    """Fail closed on shapes, types, or ranges outside the frozen circuit."""
    if not isinstance(requests, np.ndarray) or requests.dtype != np.int64:
        raise ValueError("feature batch must be an int64 NumPy array")
    if requests.ndim != 3 or requests.shape[1:] != (OPTIONS_PER_REQUEST, FEATURE_COUNT):
        raise ValueError("feature batch must have the frozen (requests, 4, 6) shape")
    if requests.shape[0] == 0 or (
        expected_count is not None and requests.shape[0] != expected_count
    ):
        raise ValueError("feature batch has an unexpected request count")
    if np.any(requests < FEATURE_LOW) or np.any(requests >= FEATURE_HIGH_EXCLUSIVE):
        raise ValueError("feature batch exceeds the frozen signed-integer range")


def synthetic_fixture_sha256() -> str:
    """Digest seeds, fitted model, and generated arrays without retaining them."""
    digest = hashlib.sha256()
    digest.update(f"{STATE_SLICE}:{SEED}:train={TRAIN_ROWS}".encode("ascii"))
    digest.update(MODEL_WEIGHTS.tobytes())
    digest.update(np.asarray([MODEL_BIAS], dtype=np.int64).tobytes())
    digest.update(synthetic_calibration_requests().tobytes())
    digest.update(synthetic_evaluation_requests().tobytes())
    return digest.hexdigest()

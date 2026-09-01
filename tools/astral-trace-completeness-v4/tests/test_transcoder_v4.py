"""State slice: astral-trace-completeness-gemma3-end-to-end-v4."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import transcoder_v4 as transcoder


def test_pooled_global_centered_nmse_uses_one_global_denominator():
    stats = [
        {"sum_squared_error": 1.0, "target_sum": 0.0, "target_squared_sum": 2.0, "coordinate_count": 2},
        {"sum_squared_error": 3.0, "target_sum": 2.0, "target_squared_sum": 2.0, "coordinate_count": 2},
    ]
    assert transcoder.pooled_global_centered_nmse(stats) == 4.0 / 3.0


def test_feature_vector_cosine_compares_precomputed_features():
    import torch

    assert transcoder.feature_vector_cosine(torch.tensor([1.0, 0.0]), torch.tensor([1.0, 0.0])) == 1.0

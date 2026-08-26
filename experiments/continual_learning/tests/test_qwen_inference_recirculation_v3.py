from __future__ import annotations

from experiments.continual_learning.qwen_inference_recirculation_v3 import (
    ALPHAS,
    candidate_configs_v3,
)


def test_alpha_grid_is_paper_aligned_and_explicit():
    configs = candidate_configs_v3(24)
    assert len(configs) == 16
    assert tuple(sorted({config.alpha for config in configs})) == ALPHAS
    assert {(config.source_layer, config.destination_layer) for config in configs} == {
        (7, 2),
        (9, 3),
        (11, 4),
        (12, 5),
    }


def test_alpha_grid_is_layer_bounded():
    configs = candidate_configs_v3(10)
    assert len(configs) == 8
    assert all(config.source_layer < 10 for config in configs)

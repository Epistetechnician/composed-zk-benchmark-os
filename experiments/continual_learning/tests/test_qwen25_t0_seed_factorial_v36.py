from __future__ import annotations

import pytest

from experiments.continual_learning.qwen25_t0_seed_factorial_v36 import (
    FAILING_TASK_SEED,
    FIXED_OPTIMIZER_SEED,
    MODEL_DEFAULT,
    SEEDS,
    _arm_cells,
    raw_text_training_command,
    run_campaign,
)


def test_v36_arms_change_one_seed_factor():
    assert _arm_cells("optimizer_seed_arm") == tuple((FAILING_TASK_SEED, seed) for seed in SEEDS)
    assert _arm_cells("task_seed_arm") == tuple((seed, FIXED_OPTIMIZER_SEED) for seed in SEEDS)
    assert len(set(_arm_cells("optimizer_seed_arm"))) == 3
    assert len(set(_arm_cells("task_seed_arm"))) == 3


def test_v36_training_command_keeps_raw_text_boundary():
    command = raw_text_training_command(SEEDS[0], SEEDS[1], SEEDS[2], SEEDS[0])
    assert "--mask-prompt" not in command


def test_v36_campaign_refuses_immutable_root(tmp_path):
    root = tmp_path / "campaign"
    root.mkdir()
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        run_campaign(root, MODEL_DEFAULT)

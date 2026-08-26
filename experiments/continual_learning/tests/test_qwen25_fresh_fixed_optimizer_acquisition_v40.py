from __future__ import annotations

import pytest

from experiments.continual_learning import qwen25_fresh_fixed_optimizer_acquisition_v40 as v40


def test_v40_freezes_fresh_task_seeds_and_inherits_the_v37_training_contract():
    assert v40.TASK_SEEDS == (20260859, 20260860, 20260861)
    assert v40.FIXED_OPTIMIZER_SEED == 20260856
    assert v40.ORDER == (0, 1, 2, 3)
    assert v40.ITERS == 160
    assert v40.UPDATE_BUDGET == 32


def test_v40_case_rejects_task_seed_drift_without_mutation(tmp_path):
    with pytest.raises(ValueError, match="task seed"):
        v40.run_case(tmp_path / "case", v40.MODEL_DEFAULT, 20260858)
    assert not (tmp_path / "case").exists()


def test_v40_campaign_rejects_existing_immutable_root(tmp_path):
    root = tmp_path / "campaign"
    root.mkdir()
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        v40.run_campaign(root, v40.MODEL_DEFAULT)

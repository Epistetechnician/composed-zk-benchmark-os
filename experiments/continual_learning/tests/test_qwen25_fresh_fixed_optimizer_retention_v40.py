from __future__ import annotations

import pytest

from experiments.continual_learning import qwen25_fresh_fixed_optimizer_retention_v40 as v40


def test_v40_retention_binds_only_the_fresh_eligible_acquisition_source():
    assert v40.TASK_SEEDS == (20260859, 20260860, 20260861)
    assert v40.SOURCE_STATE_SLICE == "continual-learning-qwen25-fresh-fixed-optimizer-acquisition-v40"
    assert v40.REPLAY_CAPACITY == 24
    assert v40.RECOVERY_ITERS == 20


def test_v40_retention_case_rejects_task_seed_drift_without_mutation(tmp_path):
    with pytest.raises(ValueError, match="task seed"):
        v40.run_case(tmp_path / "case", tmp_path / "source", v40.MODEL_DEFAULT, 20260858)
    assert not (tmp_path / "case").exists()


def test_v40_retention_campaign_rejects_existing_immutable_root(tmp_path):
    root = tmp_path / "campaign"
    root.mkdir()
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        v40.run_campaign(root, v40.MODEL_DEFAULT, v40.SOURCE_ARTIFACT_ROOT)

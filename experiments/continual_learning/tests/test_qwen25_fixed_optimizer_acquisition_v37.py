from __future__ import annotations

import pytest

from experiments.continual_learning import qwen25_fixed_optimizer_acquisition_v37 as v37


def test_v37_freezes_first_declared_optimizer_seed_and_task_seed_set():
    assert v37.FIXED_OPTIMIZER_SEED == 20260856
    assert v37.TASK_SEEDS == (20260856, 20260857, 20260858)
    assert v37.ORDER == (0, 1, 2, 3)
    assert v37.ITERS == 160
    assert v37.UPDATE_BUDGET == 32


def test_v37_fixed_optimizer_seed_offsets_are_explicit_in_audit_contract():
    assert v37.FIXED_OPTIMIZER_SEED + 0 == 20260856
    assert v37.FIXED_OPTIMIZER_SEED + 3 == 20260859


def test_v37_case_rejects_task_seed_drift_without_mutation(tmp_path):
    with pytest.raises(ValueError, match="task seed"):
        v37.run_case(tmp_path / "case", v37.MODEL_DEFAULT, 999)
    assert not (tmp_path / "case").exists()


def test_v37_campaign_rejects_existing_immutable_root(tmp_path):
    root = tmp_path / "campaign"
    root.mkdir()
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        v37.run_campaign(root, v37.MODEL_DEFAULT)

from __future__ import annotations

import pytest

from experiments.continual_learning import qwen25_fresh_fixed_optimizer_order_retention_v41 as v41


def test_v41_freezes_fresh_seeds_and_noncanonical_orders():
    assert v41.TASK_SEEDS == (20260859, 20260860, 20260861)
    assert v41.ORDERS == ((0, 2, 1, 3), (0, 3, 1, 2), (0, 1, 3, 2))
    assert v41.FIXED_OPTIMIZER_SEED == 20260856


def test_v41_case_rejects_order_drift_without_mutation(tmp_path):
    with pytest.raises(ValueError, match="order"):
        v41.run_case(tmp_path / "case", tmp_path / "source", v41.MODEL_DEFAULT, 20260859, (0, 1, 2, 3))
    assert not (tmp_path / "case").exists()


def test_v41_campaign_rejects_existing_immutable_root(tmp_path):
    root = tmp_path / "campaign"
    root.mkdir()
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        v41.run_campaign(root, v41.MODEL_DEFAULT, v41.SOURCE_ARTIFACT_ROOT)

from __future__ import annotations

import pytest

from experiments.continual_learning import qwen25_second_model_replication_v44 as v44


def test_v44_freezes_second_model_units_and_budgets():
    assert v44.STATE_SLICE == "continual-learning-qwen25-second-model-replication-v44"
    assert v44.PROTOCOL == "v44-qwen25-second-model-replication-v1"
    assert v44.MODEL_DEFAULT.name == "Llama-3.2-1B-Instruct-4bit"
    assert v44.PARENT_MODEL.name == "Qwen2.5-0.5B-Instruct-4bit"
    assert v44.TASK_SEEDS == (20260862, 20260863, 20260864)
    assert v44.ORDERS == ((1, 0, 2, 3), (1, 2, 0, 3), (1, 3, 0, 2))
    assert v44.FIXED_OPTIMIZER_SEED == 20260856
    assert v44.ITERS == 160
    assert v44.UPDATE_BUDGET == 32
    assert v44.REPLAY_CAPACITY == 24
    assert v44.RECOVERY_ITERS == 20


def test_v44_orders_are_disjoint_from_prior_v41_orders():
    prior_orders = {(0, 2, 1, 3), (0, 3, 1, 2), (0, 1, 3, 2)}
    assert set(v44.ORDERS).isdisjoint(prior_orders)
    assert all(order[0] == 1 for order in v44.ORDERS)


def test_v44_case_names_bind_phase_seed_order_and_optimizer():
    assert v44._case_name("acquisition", 20260862) == (
        "task-seed-20260862-order-0123-fixed-opt-20260856"
    )
    assert v44._case_name("retention", 20260862) == (
        "task-seed-20260862-order-0123-fixed-opt-20260856"
    )
    assert v44._case_name("order_retention", 20260862, (1, 2, 0, 3)) == (
        "task-seed-20260862-order-1203-fixed-opt-20260856"
    )


def test_v44_refuses_repository_or_existing_artifact_roots(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        v44._ensure_external_new_root(v44.REPO_ROOT / "forbidden-v44")
    existing = tmp_path / "existing-v44"
    existing.mkdir()
    with pytest.raises(FileExistsError, match="refusing overwrite"):
        v44._ensure_external_new_root(existing)

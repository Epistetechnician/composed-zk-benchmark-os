from __future__ import annotations

from experiments.continual_learning.qwen25_fixed_optimizer_order_replication_v39 import (
    ORDERS,
    TASK_SEEDS,
    case_name,
    order_code,
)


def test_v39_freezes_three_noncanonical_orders():
    assert ORDERS == ((0, 2, 1, 3), (0, 3, 1, 2), (0, 1, 3, 2))
    assert all(order[0] == 0 and sorted(order) == [0, 1, 2, 3] for order in ORDERS)


def test_v39_crosses_every_seed_with_every_order():
    assert len(TASK_SEEDS) * len(ORDERS) == 9


def test_v39_case_identity_contains_seed_and_order():
    assert order_code((0, 3, 1, 2)) == "0312"
    assert case_name(20260857, (0, 3, 1, 2)) == "task-seed-20260857-order-0312-fixed-opt-20260856"

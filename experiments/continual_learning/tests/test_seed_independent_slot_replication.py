from experiments.continual_learning.seed_independent_slot_replication_cell_preflight import (
    OPTIMIZER_STATE_POLICY,
    SLOT_INITIALIZATION_POLICY,
    SLOT_SEED_BASE,
    STATE_SLICE,
    fixed_slot_seed,
)
from experiments.continual_learning.seed_independent_slot_replication_matrix_preflight import ORDERS, SEEDS


def test_v22_uses_the_frozen_v20_seed_order_matrix():
    assert SEEDS == (20260811, 20260812, 20260813)
    assert ORDERS == ((0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2))


def test_v22_slot_state_is_task_keyed_not_experiment_seed_keyed():
    assert STATE_SLICE == "continual-learning-protocol-v22-seed-independent-init-replication-cell"
    assert SLOT_INITIALIZATION_POLICY == "task_keyed_fixed_seed_v1"
    assert OPTIMIZER_STATE_POLICY == "fresh_zero_state_task_keyed_seed_v1"
    assert [fixed_slot_seed(task_id) for task_id in range(4)] == [SLOT_SEED_BASE + task_id for task_id in range(4)]
    assert fixed_slot_seed(0) != 20260811

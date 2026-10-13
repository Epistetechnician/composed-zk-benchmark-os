from experiments.continual_learning.compact_routing_replication_matrix_preflight import ORDERS, SEEDS, STATE_SLICE


def test_v20_matrix_has_three_fresh_seeds_and_orders():
    assert STATE_SLICE == "continual-learning-protocol-v20-compact-routing-replication"
    assert len(SEEDS) == 3
    assert len(ORDERS) == 3
    assert all(order[0] == 0 and sorted(order) == [0, 1, 2, 3] for order in ORDERS)


def test_v20_matrix_cells_are_unique():
    assert len({(seed, order) for seed in SEEDS for order in ORDERS}) == 9

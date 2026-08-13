from experiments.continual_learning import replay_anchored_temporal_replication_protocol as protocol


def test_replication_matrix_excludes_only_the_two_v29_anchor_cells():
    plan = protocol.build_matrix_plan()
    assert plan["replication_cell_count"] == 7
    assert len(plan["anchor_cells"]) == 2
    assert plan["gates"]["matrix_identity_exact"] is True
    assert plan["gates"]["fresh_cells_exclude_anchors"] is True


def test_replication_cell_plan_is_valid_for_a_fresh_cell():
    seed, order = protocol.REPLICATION_CELLS[0]
    original = (protocol.DATA_SEED, protocol.PREFLIGHT_ORDER)
    protocol.DATA_SEED = seed
    protocol.PREFLIGHT_ORDER = order
    try:
        plan = protocol.build_plan()
        assert protocol.validate_plan(plan)["valid"] is True
        assert plan["replication_cell"] == {"seed": seed, "order": list(order)}
    finally:
        protocol.DATA_SEED, protocol.PREFLIGHT_ORDER = original

from experiments.continual_learning import shared_global_update_stream_replication_protocol as protocol


def test_v27_has_eight_fresh_cells_and_one_excluded_anchor():
    plan = protocol.build_plan()
    assert plan["replication_cell_count"] == 8
    assert plan["anchor"]["execution_kind"] == "development_anchor_not_rerun"
    identities = {(cell["seed"], tuple(cell["order"])) for cell in plan["replication_cells"]}
    assert (20260812, (0, 1, 2, 3)) not in identities
    assert len(identities) == 8


def test_v27_preserves_v26_budgets_and_closes_authority_gates():
    plan = protocol.build_plan()
    assert plan["total_examples_per_cell"] == 128
    assert plan["total_optimizer_steps_per_cell"] == 640
    assert plan["gates"]["same_seed_order_matrix_as_v26"] is True
    assert plan["h100_authorized"] is False
    assert plan["breakthrough_claim_eligible"] is False

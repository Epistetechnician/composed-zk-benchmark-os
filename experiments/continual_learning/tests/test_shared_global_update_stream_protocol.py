from experiments.continual_learning import shared_global_update_stream_protocol as protocol
from experiments.continual_learning import shared_global_update_stream_preflight as preflight


def test_v26_changes_update_stream_boundary_only():
    plan = protocol.build_plan()
    assert plan["changed_protocol_variable"] == "shared_global_update_stream_v1"
    assert plan["fixed_preflight_seed"] == 20260812
    assert plan["initialization_policy"] == "global_data_seed_before_model_load_and_after_load_before_lora_v1"
    assert plan["data_order_policy"] == "single_global_rng_stream_no_per_task_reseed_v1"
    assert plan["model_training_authorized"] is False
    assert plan["h100_authorized"] is False


def test_v26_preserves_v24_matrix_and_budget_contract():
    plan = protocol.build_plan()
    assert len(plan["cells"]) == 9
    assert plan["total_examples_per_cell"] == 128
    assert plan["total_optimizer_steps_per_cell"] == 640
    assert plan["gates"]["same_seed_and_order_as_v24"] is True
    assert plan["gates"]["one_shared_optimizer_state"] is True


def test_v26_materializes_every_update_to_the_frozen_row_budget():
    facts = [object()] * 8
    assert len(preflight.materialize_update_facts(facts)) == 32
    assert len(preflight.materialize_update_facts([object()] * 16)) == 32

from experiments.continual_learning import shared_adapter_reference_initialization_protocol as protocol


def test_v25_changes_only_shared_adapter_initialization():
    plan = protocol.build_plan()
    assert plan["adapter_initialization_seed"] == 20260811
    assert plan["adapter_initialization_policy"] == "fixed_reference_seed_post_model_load_from_prior_successful_family_v1"
    assert plan["changed_protocol_variable"] == "shared_adapter_reference_initialization_v1"
    assert plan["model_training_authorized"] is False
    assert plan["h100_authorized"] is False


def test_v25_preserves_v24_cell_and_budget_contract():
    plan = protocol.build_plan()
    assert len(plan["cells"]) == 9
    assert plan["total_examples_per_cell"] == 128
    assert plan["total_optimizer_steps_per_cell"] == 640
    assert plan["gates"]["only_initialization_changed_from_v24"] is True

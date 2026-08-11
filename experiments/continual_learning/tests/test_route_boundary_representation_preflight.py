from experiments.continual_learning.route_boundary_representation_preflight import (
    STATE_SLICE,
    route_bound_prompt_for,
)


def test_v18_repeats_task_route_at_answer_boundary_without_raw_pair():
    fact = type("Fact", (), {"task_token": "T2", "residue": 3, "label": "A"})()
    prompt = route_bound_prompt_for(fact)
    assert prompt.endswith("Task route binding: T2.\nAnswer:")
    assert "Compose " not in prompt


def test_v18_state_slice_is_local_representation_pilot():
    assert STATE_SLICE == "continual-learning-protocol-v18-route-boundary-representation"

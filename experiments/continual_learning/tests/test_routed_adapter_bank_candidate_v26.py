from experiments.continual_learning.routed_adapter_bank_candidate_v26 import (
    STATE_SLICE,
    route_bound_prompt_for,
)


def test_v26_route_binding_is_at_answer_boundary_and_raw_pair_is_absent():
    class Fact:
        task_token = "T2"
        residue = 3

    prompt = route_bound_prompt_for(Fact())
    assert prompt.endswith("Task route binding: T2.\nAnswer:")
    assert "Compose " not in prompt


def test_v26_state_slice_is_candidate_bounded():
    assert STATE_SLICE == "continual-learning-candidate-task-routed-adapter-bank-v26"

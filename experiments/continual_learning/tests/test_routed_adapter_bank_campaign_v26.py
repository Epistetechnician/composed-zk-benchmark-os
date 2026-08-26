from experiments.continual_learning.run_routed_adapter_bank_campaign_v26 import CASES, STATE_SLICE


def test_v26_campaign_has_three_preregistered_fresh_cases():
    assert len(CASES) == 3
    assert len({seed for seed, _ in CASES}) == 3
    assert all(order.startswith("0,") for _, order in CASES)


def test_v26_campaign_state_slice_is_stable():
    assert STATE_SLICE == "continual-learning-candidate-task-routed-adapter-bank-v26"

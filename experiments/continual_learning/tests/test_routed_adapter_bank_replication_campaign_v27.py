from experiments.continual_learning.run_routed_adapter_bank_replication_v27 import CASES, STATE_SLICE


def test_v27_campaign_has_three_fresh_preregistered_cases():
    assert len(CASES) == 3
    assert len({seed for seed, _ in CASES}) == 3
    assert all(order.startswith("0,") for _, order in CASES)
    assert len({order for _, order in CASES}) == 3


def test_v27_campaign_state_slice_is_stable():
    assert STATE_SLICE == "continual-learning-replication-task-routed-adapter-bank-v27"

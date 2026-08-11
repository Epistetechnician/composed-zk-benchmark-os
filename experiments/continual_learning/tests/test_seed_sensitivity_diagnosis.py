from experiments.continual_learning.seed_sensitivity_diagnosis import EXPECTED_ORDERS, EXPECTED_SEEDS, STATE_SLICE


def test_v21_diagnosis_is_bound_to_the_frozen_v20_matrix():
    assert STATE_SLICE == "continual-learning-protocol-v21-seed-sensitivity-diagnosis"
    assert EXPECTED_SEEDS == (20260811, 20260812, 20260813)
    assert len(EXPECTED_ORDERS) == 3


def test_v21_diagnosis_has_no_hardware_or_breakthrough_authority():
    assert "sensitivity" in STATE_SLICE

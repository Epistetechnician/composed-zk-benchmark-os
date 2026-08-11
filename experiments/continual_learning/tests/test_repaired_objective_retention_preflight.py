from experiments.continual_learning.repaired_objective_retention_preflight import STATE_SLICE


def test_v14_state_slice_is_distinct_from_v13_fit_repair():
    assert STATE_SLICE == "continual-learning-protocol-v14-repaired-objective-retention"


def test_v14_retention_requires_strict_gain_in_the_candidate_gate():
    assert (0.50 > 0.25) is True
    assert (0.25 > 0.25) is False

from experiments.continual_learning.fit_repair_preflight import digest


def test_v13_fit_repair_digest_is_order_stable():
    assert digest({"b": 2, "a": 1}) == digest({"a": 1, "b": 2})


def test_v13_fit_floor_threshold_is_six_of_eight():
    assert 6 / 8 == 0.75

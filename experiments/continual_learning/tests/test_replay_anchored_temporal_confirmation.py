from experiments.continual_learning import replay_anchored_temporal_confirmation_preflight as preflight
from experiments.continual_learning import replay_anchored_temporal_confirmation_protocol as protocol


def test_confirmation_targets_the_other_frozen_v27_tie_cell():
    plan = protocol.build_plan()
    assert plan["preflight_seed"] == 20260812
    assert plan["preflight_order"] == [0, 2, 3, 1]
    assert plan["confirmation_of_state_slice"] == "continual-learning-protocol-v29-replay-anchored-temporal-microbatch"
    assert plan["gates"]["confirms_other_v27_20260812_tie_cell"] is True


def test_confirmation_preserves_v29_temporal_policy_and_budget():
    plan = protocol.build_plan()
    assert plan["batch_policy"] == "replay_anchored_oldest_first_temporal_microbatch_v1"
    assert plan["total_examples_per_arm"] == 128
    assert plan["total_optimizer_steps_per_arm"] == 640
    assert plan["h100_authorized"] is False
    assert preflight.STATE_SLICE.endswith("-confirmation-preflight")

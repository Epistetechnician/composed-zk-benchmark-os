from experiments.continual_learning import task_stratified_microbatch_confirmation_preflight as preflight
from experiments.continual_learning import task_stratified_microbatch_confirmation_protocol as protocol


def test_confirmation_targets_the_second_v27_tie_cell():
    plan = protocol.build_plan()
    assert plan["preflight_seed"] == 20260812
    assert plan["preflight_order"] == [0, 3, 1, 2]
    assert plan["confirmation_of_state_slice"] == "continual-learning-protocol-v28-task-stratified-microbatch"
    assert plan["gates"]["confirms_second_v27_tie_cell"] is True


def test_confirmation_preserves_v28_batch_and_authority_boundaries():
    plan = protocol.build_plan()
    assert plan["batch_policy"] == "task_stratified_round_robin_microbatch_v1"
    assert plan["total_examples_per_arm"] == 128
    assert plan["total_optimizer_steps_per_arm"] == 640
    assert plan["h100_authorized"] is False
    assert preflight.STATE_SLICE.endswith("-confirmation-preflight")

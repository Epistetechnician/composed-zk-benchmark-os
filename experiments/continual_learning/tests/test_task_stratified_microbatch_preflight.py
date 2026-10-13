from experiments.continual_learning import task_stratified_microbatch_preflight as preflight


def test_v28_preflight_state_slice_is_distinct():
    assert preflight.STATE_SLICE == "continual-learning-protocol-v28-task-stratified-microbatch-preflight"

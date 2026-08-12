from experiments.continual_learning import shared_adapter_task_keyed_optimizer_state_preflight as preflight


def test_v24_preflight_keeps_shared_parameter_surface():
    assert preflight.STATE_SLICE.endswith("-preflight")
    assert preflight.SHARED_ADAPTER_LAYERS == 8
    assert preflight.SOURCE_STATE_SLICE == "continual-learning-protocol-v24-shared-adapter-task-keyed-optimizer-state"


def test_v24_preflight_keeps_fixed_training_budget():
    assert preflight.BATCH_SIZE == 2
    assert preflight.ADAMW_LEARNING_RATE == 0.0001
    assert preflight.MAX_SEQUENCE_LENGTH == 192

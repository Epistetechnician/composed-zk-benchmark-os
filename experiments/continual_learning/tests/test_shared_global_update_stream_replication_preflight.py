from experiments.continual_learning import shared_global_update_stream_replication_preflight as preflight


def test_v27_cell_state_slice_is_distinct_from_v26():
    assert preflight.STATE_SLICE != "continual-learning-protocol-v26-shared-global-update-stream-preflight"
    assert preflight.CELL_STATE_SLICE.startswith(preflight.STATE_SLICE)

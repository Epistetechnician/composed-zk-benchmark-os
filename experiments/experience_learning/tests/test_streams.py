from experiments.experience_learning.streams import (
    EventCameraLikeStream, NoisyMNISTArrayStream, NoisyMNISTLikeStream, NonstationaryFeatureStream, SparseNoisyStream,
)


def test_streams_are_deterministic_and_expose_learnable_coordinates():
    first = list(SparseNoisyStream(12, seed=3))
    second = list(SparseNoisyStream(12, seed=3))
    assert first == second
    assert first[0].source_id == "sparse:0"
    assert SparseNoisyStream().predictable_feature_indices == (0,)


def test_nonstationary_stream_declares_task_shift_without_future_leakage():
    items = list(NonstationaryFeatureStream(10, seed=4, switch_at=5))
    assert [item.task_id for item in items] == [0] * 5 + [1] * 5
    assert [item.step for item in items] == list(range(10))


def test_synthetic_noisy_mnist_and_event_streams_are_sparse():
    mnist = list(NoisyMNISTLikeStream(3, seed=4, noise_pixels=2))
    events = list(EventCameraLikeStream(3, seed=4, events_per_step=2))
    assert len(mnist[0].features) == 784
    assert all(item.event_indices for item in mnist + events)
    assert max(map(len, [item.event_indices for item in events])) <= 3


def test_noisy_mnist_array_adapter_preserves_caller_order():
    items = list(NoisyMNISTArrayStream([[0.0, 1.0], [1.0, 0.0]], [0, 1], seed=2, noise_pixels=0))
    assert [item.step for item in items] == [0, 1]
    assert [item.target for item in items] == [-1.0, 1.0]

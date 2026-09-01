import math

from experiments.experience_learning.learners import (
    AdamLearner, EWCLearner, EventDrivenLearner, IDBDLearner,
    NetworkIDBDLearner, PlasticityGuardLearner, ReplayLearner, SGDLearner, TIDBDLearner,
)
from experiments.experience_learning.streams import DelayedRewardStream, SparseNoisyStream


def test_sgd_and_adam_batch_sizes_are_explicit_and_flush_remainders():
    items = list(SparseNoisyStream(33, seed=8))
    for cls in (SGDLearner, AdamLearner):
        for batch_size in (1, 32, 128):
            learner = cls(len(items[0].features), batch_size=batch_size)
            for item in items: learner.observe(item)
            assert learner.samples_seen == 33
            flushed = learner.flush()
            assert flushed == (1 if batch_size == 32 else 33 if batch_size == 128 else 0)
            assert learner.updates == (33 if batch_size == 1 else 2 if batch_size == 32 else 1)


def test_idbd_adapts_a_predictable_coordinate():
    items = list(SparseNoisyStream(200, seed=2, dimensions=4, noise=0.0, sparsity=0.0))
    learner = IDBDLearner(4)
    for item in items: learner.observe(item)
    assert learner.weights[0] > 0.8
    assert all(math.isfinite(x) for x in learner.beta)


def test_networkidbd_is_a_finite_nonlinear_extension():
    learner = NetworkIDBDLearner(2, hidden_size=4)
    for step in range(200):
        x = (1.0 if step % 2 else -1.0, 1.0 if (step // 2) % 2 else -1.0)
        target = 1.0 if x[0] * x[1] > 0 else -1.0
        from experiments.experience_learning.types import Experience
        learner.observe(Experience(step, x, target, event_indices=(0, 1)))
    assert learner.updates == 200
    assert all(math.isfinite(value) for value in learner.w2 + [learner.b2])


def test_tidbd_updates_delayed_reward_prediction():
    learner = TIDBDLearner(1, gamma=0.9)
    for _ in range(100):
        for item in DelayedRewardStream(1, horizon=4, reward_delay=0): learner.observe(item)
    assert learner.weights[0] > 0.1
    assert all(math.isfinite(x) for x in learner.beta)


def test_replay_is_explicit_and_ewc_has_boundary_state():
    items = list(SparseNoisyStream(5, seed=5, dimensions=3))
    replay = ReplayLearner(3)
    for item in items: replay.observe(item)
    assert replay.replay_examples >= 4
    ewc = EWCLearner(3)
    for item in items[:2]: ewc.observe(item)
    before = tuple(ewc.reference)
    ewc.mark_task_boundary()
    assert tuple(ewc.reference) != before


def test_guard_is_bounded_and_event_driven_counts_only_active_synapses():
    items = list(SparseNoisyStream(10, seed=6, dimensions=5, sparsity=0.0))
    guard = PlasticityGuardLearner(5)
    event = EventDrivenLearner(5, threshold=0.5)
    for item in items:
        guard.observe(item); event.observe(item)
    assert guard.guard_floor <= guard.plasticity <= 1.0
    assert event.active_synaptic_ops > 0
    assert event.active_synaptic_ops <= event.gradient_units

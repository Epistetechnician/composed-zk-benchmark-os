from experiments.experience_learning.learners import AdamLearner, NetworkIDBDLearner, TIDBDLearner
from experiments.experience_learning.types import Experience


def test_adam_counts_active_synaptic_operations():
    learner = AdamLearner(3, learning_rate=0.001, batch_size=1)
    stats = learner.observe(Experience(0, (1.0, 0.0, 0.0), 1.0, event_indices=(0,)))
    assert stats.active_synaptic_ops == 4
    assert learner.active_synaptic_ops == 4


def test_nonlinear_and_td_learners_return_operation_counters():
    network = NetworkIDBDLearner(2, hidden_size=2)
    network_stats = network.observe(Experience(0, (1.0, 0.0), 1.0, event_indices=(0,)))
    assert network_stats.active_synaptic_ops == network.active_synaptic_ops > 0
    td = TIDBDLearner(2)
    td_stats = td.observe(Experience(0, (1.0, 0.0), 1.0, reward=1.0,
                                     next_features=(1.0, 0.0), done=False,
                                     event_indices=(0,)))
    assert td_stats.active_synaptic_ops == td.active_synaptic_ops > 0

from experiments.experience_learning.equations import idbd_reference_step, tidbd_reference_step
from experiments.experience_learning.learners import IDBDLearner, TIDBDLearner
from experiments.experience_learning.types import Experience
import pytest


def test_idbd_matches_independent_reference_one_step():
    item = Experience(0, (0.5, -1.0), 0.7, event_indices=(0, 1))
    learner = IDBDLearner(2, meta_step=0.01, initial_step=0.03)
    expected = idbd_reference_step(learner.weights, learner.beta, learner.h, item.features, item.target)
    learner.observe(item)
    assert learner.weights == expected[0]
    assert learner.beta == expected[1]
    assert learner.h == expected[2]


def test_tidbd_matches_independent_semigradient_reference_one_step():
    item = Experience(0, (1.0, 0.5), 0.0, reward=0.4, next_features=(0.25, 1.0), done=False,
                      event_indices=(0, 1))
    learner = TIDBDLearner(2, gamma=0.9, trace_decay=0.8, meta_step=0.01, initial_step=0.03)
    expected = tidbd_reference_step(learner.weights, learner.beta, learner.h, learner.e,
                                    item.features, item.reward, item.next_features, item.done)
    learner.observe(item)
    assert learner.weights == expected[0]
    assert learner.beta == expected[1]
    assert learner.h == expected[2]
    assert learner.e == expected[3]


def test_idbd_reference_has_published_one_step_values():
    weights, beta, h = idbd_reference_step([0.0], [0.0], [0.0], [1.0], 1.0,
                                           meta_step=0.1)
    assert weights == pytest.approx([1.0])
    assert beta == pytest.approx([0.0])
    assert h == pytest.approx([1.0])


def test_tidbd_reference_has_td_error_and_trace_values():
    weights, beta, h, eligibility = tidbd_reference_step(
        [0.0], [0.0], [0.0], [0.0], [1.0], 1.0, [0.0], True,
        gamma=0.9, trace_decay=0.8, meta_step=0.1)
    assert weights == pytest.approx([1.0])
    assert beta == pytest.approx([0.0])
    assert h == pytest.approx([1.0])
    assert eligibility == [0.0]

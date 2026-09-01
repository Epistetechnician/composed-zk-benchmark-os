from experiments.experience_learning.controls import RunningMeanLearner, evaluate_control
from experiments.experience_learning.types import Experience


def test_noise_floor_is_causal():
    learner = RunningMeanLearner()
    first = learner.observe(Experience(0, (1.0,), 4.0))
    second = learner.observe(Experience(1, (1.0,), 4.0))
    assert first.prediction == 0.0
    assert second.prediction == 4.0


def test_oracle_control_runs_on_predictable_projection():
    result = evaluate_control("sparse_noisy", 24, 0, "oracle_feature_sgd_b1", {"sgd_b1": {"learning_rate": 0.03}})
    assert result["status"] == "executed"
    assert result["assessment_metrics"]["mean_loss"] >= 0.0
    assert result["assessment_metrics"]["updates"] > 0

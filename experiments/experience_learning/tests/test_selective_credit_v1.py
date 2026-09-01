from experiments.experience_learning.selective_credit_qualification_v1 import (
    PLAN, PLAN_DIGEST, run_qualification,
)
from experiments.experience_learning.selective_credit_v1 import (
    STATE_SLICE, PredictiveUtilityCreditLearner,
)
from experiments.experience_learning.types import Experience


def test_predictive_utility_gate_is_batch_one_and_restorable():
    learner = PredictiveUtilityCreditLearner(2, warmup=1, min_gate=0.0)
    first = learner.observe(Experience(0, (1.0, 0.0), 1.0, event_indices=(0,)))
    second = learner.observe(Experience(1, (1.0, 0.0), 1.0, event_indices=(0,)))
    assert first.updated and second.updated
    assert learner.batch_size == 1
    assert learner.allows_replay is False
    assert learner.snapshot()["state_slice"] == STATE_SLICE
    restored = PredictiveUtilityCreditLearner(2, warmup=1, min_gate=0.0)
    restored.restore(learner.snapshot())
    assert restored.digest() == learner.digest()


def test_small_qualification_is_sealed_and_deterministic():
    first = run_qualification(["sparse_noisy", "nonstationary"], steps=24)
    second = run_qualification(["sparse_noisy", "nonstationary"], steps=24)
    assert first["plan_digest"] == PLAN_DIGEST
    assert first["plan"] == PLAN
    assert first["execution"]["synthetic_only"] is True
    assert first["execution"]["hardware_energy"] == "not_run"
    assert first["result_digest"] == second["result_digest"]

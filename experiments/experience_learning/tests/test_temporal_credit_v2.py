from experiments.experience_learning.temporal_credit_v2 import (
    STATE_SLICE, TemporalUtilityGateLearner,
)
from experiments.experience_learning.temporal_credit_qualification_v2 import (
    PLAN, PLAN_DIGEST, run_qualification,
)
from experiments.experience_learning.types import Experience


def test_temporal_credit_uses_scalar_state_and_restores():
    learner = TemporalUtilityGateLearner(2, warmup=1)
    first = learner.observe(Experience(0, (1.0, 0.0), 1.0, event_indices=(0,)))
    second = learner.observe(Experience(1, (1.0, 0.0), 1.0, event_indices=(0,)))
    assert first.updated and second.updated
    assert learner.batch_size == 1
    assert learner.allows_replay is False
    assert second.state_bytes <= second.model_bytes + 8 * 7
    snapshot = learner.snapshot()
    assert snapshot["state_slice"] == STATE_SLICE
    restored = TemporalUtilityGateLearner(2, warmup=1)
    restored.restore(snapshot)
    assert restored.digest() == learner.digest()


def test_v2_qualification_is_fresh_and_deterministic():
    first = run_qualification(["sparse_noisy", "nonstationary"], steps=24)
    second = run_qualification(["sparse_noisy", "nonstationary"], steps=24)
    assert first["plan_digest"] == PLAN_DIGEST
    assert first["plan"] == PLAN
    assert first["execution"]["seed_offsets"] == [10, 11, 12, 13, 14]
    assert first["execution"]["real_stream_execution"] == "sealed_pending_review"
    assert first["result_digest"] == second["result_digest"]

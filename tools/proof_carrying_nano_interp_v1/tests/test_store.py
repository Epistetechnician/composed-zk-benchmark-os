"""Store behavior for the proof-carrying nano interpretability V1 slice."""

import pytest

from tools.proof_carrying_nano_interp_v1.proof import ProofAttempt
from tools.proof_carrying_nano_interp_v1.runtime import FeatureDetectorNano, ToyHostSlice
from tools.proof_carrying_nano_interp_v1.store import ConcurrentStore, StoreError


def _action(*, activation: tuple[int, int], timestamp: str):
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = FeatureDetectorNano(
        identity="feature-detector-v1",
        feature_id="feature-0",
        feature_index=0,
        threshold=2,
    ).attach(host, layer=1, site="residual")
    trace = host.capture(
        prompt="alpha",
        activation=activation,
        seed=7,
        layer=1,
        site="residual",
    )
    return attachment.run(trace, timestamp=timestamp)


def test_store_commits_immutable_action_and_checked_proof(tmp_path):
    action = _action(activation=(3, 1), timestamp="2026-09-16T12:00:00Z")
    proof = ProofAttempt.checked(
        action_digest=action.action_digest,
        theorem_name="action_feature_0_exact",
        statement="featureActivation [3, 1] 0 = 3",
        source="theorem action_feature_0_exact : featureActivation [3, 1] 0 = 3 := by rfl",
        checker="lean-kernel",
        checker_version="4.30.0",
    )

    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        assert store.commit_action(action) == action.action_digest
        assert store.commit_action(action) == action.action_digest
        assert store.commit_proof(proof) == proof.proof_digest
        proven = store.query_proven_claims(layer=1, feature_id="feature-0")

    assert len(proven) == 1
    assert proven[0]["action_digest"] == action.action_digest
    assert proven[0]["proof"]["status"] == "checked"

    altered = action.to_dict()
    altered["outputs"] = {"detected": False, "feature_value": 3}
    with pytest.raises(StoreError, match="action digest mismatch"):
        ConcurrentStore.assert_action_digest(altered)

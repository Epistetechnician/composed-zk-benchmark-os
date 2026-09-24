"""Store behavior for the proof-carrying nano interpretability V1 slice."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from tools.proof_carrying_nano_interp_v1.proof import LeanProofEngine, ProofAttempt
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
    proof = LeanProofEngine().attempt(action)
    assert proof.status == "checked", proof.diagnostics

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


def test_store_records_failed_attempts_but_excludes_them_from_proven_claims(tmp_path):
    action = _action(activation=(3, 1), timestamp="2026-09-16T12:00:00Z")
    proof = ProofAttempt.create(
        action_digest=action.action_digest,
        status="failed",
        theorem_name="action_feature_0_exact",
        statement="featureActivation [3, 1] 0 = 3",
        source="theorem action_feature_0_exact : False := by sorry",
        checker="lean-kernel",
        checker_version="4.30.0",
        diagnostics=("declaration uses sorry",),
    )

    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        store.commit_action(action)
        store.commit_proof(proof)
        assert store.query_proven_claims() == []
        assert store.list_proof_attempts(action_digest=action.action_digest)[0]["status"] == "failed"


def test_store_detects_contradictory_checked_claims(tmp_path):
    first = _action(activation=(3, 1), timestamp="2026-09-16T12:00:00Z")
    second = _action(activation=(1, 1), timestamp="2026-09-16T12:00:01Z")
    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        for action in (first, second):
            store.commit_action(action)
            store.commit_proof(LeanProofEngine().attempt(action))
        conflicts = store.detect_conflicts()

    assert len(conflicts) == 1
    assert conflicts[0]["status"] == "conflict"
    assert conflicts[0]["values"] == [1, 3]


def test_store_allows_concurrent_action_appends(tmp_path):
    actions = [_action(activation=(index, 1), timestamp=f"2026-09-16T12:00:{index:02d}Z") for index in range(12)]
    store = ConcurrentStore(tmp_path / "store.sqlite3")
    with ThreadPoolExecutor(max_workers=4) as pool:
        committed = list(pool.map(store.commit_action, actions))

    assert sorted(committed) == sorted(action.action_digest for action in actions)
    assert store.action_count() == len(actions)


def test_store_rejects_forged_checked_status(tmp_path):
    action = _action(activation=(3, 1), timestamp="2026-09-16T12:00:00Z")
    forged = ProofAttempt.checked(
        action_digest=action.action_digest,
        theorem_name="fake_theorem",
        statement="False",
        source="theorem fake_theorem : False := by sorry",
        checker="lean-kernel",
        checker_version="4.30.0",
    )

    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        store.commit_action(action)
        with pytest.raises(StoreError, match="checked proof failed kernel recheck"):
            store.commit_proof(forged)


def test_run_and_record_persists_every_action_with_a_proof_attempt(tmp_path):
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = FeatureDetectorNano(
        identity="feature-detector-v1",
        feature_id="feature-0",
        feature_index=0,
        threshold=2,
    ).attach(host, layer=1, site="residual")
    trace = host.capture(
        prompt="alpha",
        activation=(3, 1),
        seed=7,
        layer=1,
        site="residual",
    )

    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        action, proof = attachment.run_and_record(
            trace,
            store=store,
            timestamp="2026-09-16T12:00:00Z",
        )
        attempts = store.list_proof_attempts(action_digest=action.action_digest)

    assert proof.status == "checked", proof.diagnostics
    assert len(attempts) == 1
    assert attempts[0]["action_digest"] == action.action_digest


def test_store_integrity_check_rejects_tampered_action_payload(tmp_path):
    action = _action(activation=(3, 1), timestamp="2026-09-16T12:00:00Z")
    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        store.commit_action(action)
        with sqlite3.connect(tmp_path / "store.sqlite3") as connection:
            connection.execute(
                "UPDATE actions SET payload = ? WHERE action_digest = ?",
                (b"{\"tampered\":true}", action.action_digest),
            )
        with pytest.raises(StoreError, match="action digest mismatch"):
            store.validate_integrity(recheck_checked=False)

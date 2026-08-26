from dataclasses import replace

import pytest

from experiments.continual_learning.update_governance import (
    STATE_SLICE,
    CanaryReport,
    UpdateLedger,
    SafetyReport,
    UpdateCandidate,
    UtilityReport,
    evaluate_candidate,
    validate_bundle,
)


def valid_candidate() -> UpdateCandidate:
    return UpdateCandidate(
        candidate_id="candidate-1",
        tenant_id="tenant-a",
        parent_model_id="model-0",
        parent_model_digest="0" * 64,
        candidate_model_id="model-1",
        candidate_model_digest="1" * 64,
        update_data_digest="2" * 64,
        source_event_ids=("event-1", "event-2"),
        source_tenant_ids=("tenant-a", "tenant-a"),
        consent_scope="tenant-training-opt-in-v1",
        safety=SafetyReport(
            baseline_jailbreak_milli=10,
            candidate_jailbreak_milli=10,
            baseline_backdoor_milli=0,
            candidate_backdoor_milli=0,
            baseline_persona_drift_milli=5,
            candidate_persona_drift_milli=5,
            unknown_count=0,
        ),
        utility=UtilityReport(
            baseline_utility_milli=800,
            candidate_utility_milli=810,
        ),
        canary=CanaryReport(sample_count=100, failure_count=0, unknown_count=0),
    )


def test_valid_candidate_is_canary_eligible():
    decision = evaluate_candidate(valid_candidate())

    assert STATE_SLICE == "continual-learning-update-governance-v1"
    assert decision.status == "canary_eligible"
    assert decision.reasons == ()


def test_cross_tenant_source_is_quarantined():
    candidate = replace(valid_candidate(), source_tenant_ids=("tenant-a", "tenant-b"))

    decision = evaluate_candidate(candidate)

    assert decision.status == "quarantined"
    assert "cross_tenant_source" in decision.reasons


def test_blank_model_identity_is_quarantined():
    candidate = replace(valid_candidate(), candidate_model_id=" ")

    decision = evaluate_candidate(candidate)

    assert decision.status == "quarantined"
    assert "candidate_model_id_missing" in decision.reasons


def test_safety_unknown_or_regression_is_quarantined():
    candidate = valid_candidate()
    candidate = replace(
        candidate,
        safety=replace(
            candidate.safety,
            candidate_jailbreak_milli=11,
            unknown_count=1,
        ),
    )

    decision = evaluate_candidate(candidate)

    assert decision.status == "quarantined"
    assert "jailbreak_regression" in decision.reasons
    assert "safety_unknown" in decision.reasons


def test_failed_canary_is_quarantined_and_cannot_promote():
    candidate = replace(
        valid_candidate(),
        canary=CanaryReport(sample_count=100, failure_count=1, unknown_count=0),
    )
    ledger = UpdateLedger(
        tenant_id="tenant-a",
        initial_model_id="model-0",
        initial_model_digest="0" * 64,
    )

    decision = ledger.submit(candidate)

    assert decision.status == "quarantined"
    assert "canary_failure_rate" in decision.reasons
    with pytest.raises(ValueError, match="candidate_not_canary_eligible"):
        ledger.promote(candidate.candidate_id)


def test_ledger_promotes_only_a_canary_eligible_candidate():
    ledger = UpdateLedger(
        tenant_id="tenant-a",
        initial_model_id="model-0",
        initial_model_digest="0" * 64,
    )

    decision = ledger.submit(valid_candidate())
    promoted = ledger.promote("candidate-1")

    assert decision.status == "canary_eligible"
    assert promoted.kind == "promoted"
    assert ledger.head().model_id == "model-1"
    assert [event.kind for event in ledger.events()] == [
        "baseline",
        "canary_eligible",
        "promoted",
    ]


def test_rollback_appends_history_and_restores_prior_promoted_snapshot():
    ledger = UpdateLedger(
        tenant_id="tenant-a",
        initial_model_id="model-0",
        initial_model_digest="0" * 64,
    )
    ledger.submit(valid_candidate())
    ledger.promote("candidate-1")
    second = replace(
        valid_candidate(),
        candidate_id="candidate-2",
        parent_model_id="model-1",
        parent_model_digest="1" * 64,
        candidate_model_id="model-2",
        candidate_model_digest="3" * 64,
    )
    ledger.submit(second)
    ledger.promote("candidate-2")
    history_before_rollback = ledger.events()

    rollback = ledger.rollback("1" * 64, "candidate safety regression")

    assert rollback.kind == "rollback"
    assert ledger.head().model_id == "model-1"
    assert ledger.events()[: len(history_before_rollback)] == history_before_rollback
    ledger.validate_chain()


def test_stale_canary_candidate_cannot_promote_after_head_changes():
    ledger = UpdateLedger(
        tenant_id="tenant-a",
        initial_model_id="model-0",
        initial_model_digest="0" * 64,
    )
    ledger.submit(valid_candidate())
    stale = replace(
        valid_candidate(),
        candidate_id="candidate-stale",
        candidate_model_id="model-stale",
        candidate_model_digest="3" * 64,
    )
    ledger.submit(stale)
    ledger.promote("candidate-1")

    with pytest.raises(ValueError, match="parent_head_mismatch"):
        ledger.promote("candidate-stale")

    assert ledger.head().model_id == "model-1"
    assert ledger.events()[-1].kind == "quarantined"


def test_candidate_manifest_digest_binds_update_identity_and_source_scope():
    candidate = valid_candidate()

    original_digest = candidate.manifest_digest()
    changed_digest = replace(candidate, update_data_digest="4" * 64).manifest_digest()

    assert len(original_digest) == 64
    assert original_digest == candidate.manifest_digest()
    assert changed_digest != original_digest


def test_exported_bundle_is_independently_readback_validated():
    ledger = UpdateLedger(
        tenant_id="tenant-a",
        initial_model_id="model-0",
        initial_model_digest="0" * 64,
    )
    ledger.submit(valid_candidate())
    ledger.promote("candidate-1")

    bundle = ledger.export_bundle()

    assert validate_bundle(bundle) is None
    assert bundle["state_slice"] == "continual-learning-update-governance-v1"


def test_exported_bundle_rejects_payload_drift():
    ledger = UpdateLedger(
        tenant_id="tenant-a",
        initial_model_id="model-0",
        initial_model_digest="0" * 64,
    )
    ledger.submit(valid_candidate())
    bundle = ledger.export_bundle()
    bundle["events"][1]["reason"] = "tampered"

    with pytest.raises(ValueError, match="bundle_digest_mismatch"):
        validate_bundle(bundle)


def test_bundle_head_remains_current_after_quarantined_promotion_attempt():
    ledger = UpdateLedger(
        tenant_id="tenant-a",
        initial_model_id="model-0",
        initial_model_digest="0" * 64,
    )
    ledger.submit(valid_candidate())
    stale = replace(
        valid_candidate(),
        candidate_id="candidate-stale",
        candidate_model_id="model-stale",
        candidate_model_digest="3" * 64,
    )
    ledger.submit(stale)
    ledger.promote("candidate-1")
    with pytest.raises(ValueError, match="parent_head_mismatch"):
        ledger.promote("candidate-stale")

    validate_bundle(ledger.export_bundle())

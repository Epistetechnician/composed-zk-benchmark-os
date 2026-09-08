use hsai_control_plane::*;
use std::collections::BTreeSet;

fn digest(label: &str) -> Digest {
    Digest::from_text(label)
}

fn evidence(valid_until: u64) -> EvidenceBinding {
    EvidenceBinding::validated(
        digest("artifact"),
        "independent-validator",
        digest("nonclaims"),
        valid_until,
        ClaimLevel::Local,
    )
}

fn policy() -> AdmissionPolicy {
    AdmissionPolicy {
        policy_id: "policy-v1".to_owned(),
        allowed_capabilities: CapabilitySet::new([Capability::Read, Capability::CodeExecution]),
        max_capability_ttl: 100,
        max_spend_units: 50,
        require_independent_evidence: true,
        require_reversible: true,
        forbidden_risks: BTreeSet::from([RiskLabel::DataExfiltration]),
    }
}

fn proposal(policy: &AdmissionPolicy) -> AgentProposal {
    AgentProposal {
        proposal_id: "proposal-1".to_owned(),
        actor_id: "agent-1".to_owned(),
        intent_digest: digest("intent"),
        policy_digest: policy.digest(),
        requested_capabilities: CapabilitySet::new([Capability::Read]),
        max_spend_units: 10,
        proposed_at: 10,
        expires_at: 50,
        nonce: 1,
        reversible: true,
        model_generated: true,
        model_requested_authority: false,
        evidence: Some(evidence(50)),
        risk_labels: BTreeSet::new(),
    }
}

fn accepted_receipt() -> CapabilityReceipt {
    match evaluate_admission(&proposal(&policy()), &policy(), 20, &KillSwitch::Armed) {
        AdmissionDecision::Accepted(receipt) => receipt,
        decision => panic!("expected accepted decision, got {decision:?}"),
    }
}

#[test]
fn accepted_proposal_issues_only_digest_bound_non_authority_receipt() {
    let receipt = accepted_receipt();
    assert!(receipt.is_digest_valid());
    assert!(!receipt.grants_authority());
    assert_eq!(receipt.expires_at(), 50);
    assert_eq!(receipt.capabilities().canonical(), "read");
}

#[test]
fn model_cannot_request_authority_and_unauthorized_capability_is_rejected() {
    let mut candidate = proposal(&policy());
    candidate.model_requested_authority = true;
    candidate.requested_capabilities = CapabilitySet::new([Capability::Secrets]);
    let decision = evaluate_admission(&candidate, &policy(), 20, &KillSwitch::Armed);
    assert!(matches!(decision, AdmissionDecision::Rejected(blockers)
        if blockers.contains(&AdmissionBlocker::ModelRequestedAuthority)
            && blockers.contains(&AdmissionBlocker::CapabilityNotAllowed(Capability::Secrets))));
}

#[test]
fn missing_stale_and_contradictory_evidence_quarantine() {
    let mut missing = proposal(&policy());
    missing.evidence = None;
    assert!(matches!(
        evaluate_admission(&missing, &policy(), 20, &KillSwitch::Armed),
        AdmissionDecision::Quarantined(blockers)
            if blockers == vec![AdmissionBlocker::MissingEvidence]
    ));

    let mut stale = proposal(&policy());
    stale.evidence = Some(evidence(19));
    assert!(matches!(
        evaluate_admission(&stale, &policy(), 20, &KillSwitch::Armed),
        AdmissionDecision::Quarantined(blockers)
            if blockers == vec![AdmissionBlocker::EvidenceStale]
    ));

    let mut contradictory = proposal(&policy());
    let mut bound = evidence(50);
    bound.contradictory = true;
    contradictory.evidence = Some(bound);
    assert!(matches!(
        evaluate_admission(&contradictory, &policy(), 20, &KillSwitch::Armed),
        AdmissionDecision::Quarantined(blockers)
            if blockers == vec![AdmissionBlocker::EvidenceContradictory]
    ));
}

#[test]
fn expired_receipt_kill_switch_and_capability_escalation_fail_closed() {
    let receipt = accepted_receipt();
    let request = ExecutionRequest {
        proposal_digest: receipt.proposal_digest(),
        requested_capabilities: CapabilitySet::new([Capability::Read]),
        spend_units: 1,
        reversible: true,
        nonce: 1,
        now: 50,
    };
    assert!(matches!(
        authorize_execution(&receipt, &request, &KillSwitch::Armed),
        Err(blockers) if blockers == vec![ExecutionBlocker::Expired]
    ));

    let mut escalated = request.clone();
    escalated.now = 20;
    escalated.requested_capabilities = CapabilitySet::new([Capability::CodeExecution]);
    assert!(matches!(
        authorize_execution(&receipt, &escalated, &KillSwitch::Armed),
        Err(blockers) if blockers == vec![ExecutionBlocker::CapabilityEscalation(Capability::CodeExecution)]
    ));

    let mut wrong_nonce = escalated;
    wrong_nonce.requested_capabilities = CapabilitySet::new([Capability::Read]);
    wrong_nonce.nonce = 2;
    assert!(matches!(
        authorize_execution(&receipt, &wrong_nonce, &KillSwitch::Armed),
        Err(blockers) if blockers == vec![ExecutionBlocker::NonceMismatch]
    ));

    let mut live = request;
    live.now = 20;
    assert!(matches!(
        authorize_execution(
            &receipt,
            &live,
            &KillSwitch::Tripped { reason_digest: digest("stop") }
        ),
        Err(blockers) if blockers == vec![ExecutionBlocker::KillSwitchActive]
    ));
}

#[test]
fn monitoring_maps_failure_to_rollback_and_kill_to_shutdown() {
    let receipt = accepted_receipt();
    let rollback = monitor_execution(
        &receipt,
        &MonitorObservation {
            now: 21,
            signal: MonitorSignal::InvariantViolation,
            resource_units_used: 1,
            spend_units_used: 1,
        },
        &KillSwitch::Armed,
    );
    assert_eq!(rollback.disposition, MonitorDisposition::RollbackAndFreeze);
    assert!(!rollback.authority_granted);

    let shutdown = monitor_execution(
        &receipt,
        &MonitorObservation {
            now: 21,
            signal: MonitorSignal::Healthy,
            resource_units_used: 1,
            spend_units_used: 1,
        },
        &KillSwitch::Tripped {
            reason_digest: digest("stop"),
        },
    );
    assert_eq!(shutdown.disposition, MonitorDisposition::Shutdown);
}

#[test]
fn alignment_requires_prediction_lock_independent_review_and_held_out_evidence() {
    let plan = AlignmentPlan {
        plan_id: "mechanistic-v1".to_owned(),
        track: AlignmentTrack::Mechanistic,
        requires_fit_tune_assessment: true,
        requires_prediction_lock: true,
        requires_independent_validator: true,
        requires_held_out: true,
        requires_causal_intervention: true,
        evaluator_independent: true,
    };
    let incomplete = AlignmentEvidence {
        plan_digest: plan.digest(),
        fit_digest: Some(digest("fit")),
        tune_digest: Some(digest("tune")),
        assessment_digest: None,
        prediction_lock_digest: None,
        validator_digest: Some(digest("validator")),
        held_out: false,
        causal_intervention_observed: false,
        evaluator_independent: true,
        model_controls_evaluator: false,
    };
    assert!(matches!(
        evaluate_alignment(&plan, &incomplete),
        AlignmentDecision::Blocked(blockers)
            if blockers.contains(&AlignmentBlocker::MissingAssessment)
                && blockers.contains(&AlignmentBlocker::MissingPredictionLock)
                && blockers.contains(&AlignmentBlocker::HeldOutRequired)
                && blockers.contains(&AlignmentBlocker::CausalInterventionRequired)
    ));

    let complete = AlignmentEvidence {
        assessment_digest: Some(digest("assessment")),
        prediction_lock_digest: Some(digest("lock")),
        held_out: true,
        causal_intervention_observed: true,
        ..incomplete
    };
    assert!(matches!(
        evaluate_alignment(&plan, &complete),
        AlignmentDecision::LocalCandidate { .. }
    ));
}

#[test]
fn learning_update_is_shadow_only_and_cannot_change_protected_surfaces() {
    let base = digest("base");
    let valid = LearningUpdateProposal {
        update_id: "update-1".to_owned(),
        immutable_base_digest: base.clone(),
        candidate_digest: digest("candidate"),
        trajectory_digest: digest("trajectory"),
        prediction_lock_digest: Some(digest("lock")),
        independent_evaluation_digest: Some(digest("eval")),
        rollback_target_digest: Some(base),
        requested_surfaces: BTreeSet::from([UpdateSurface::ModelAdapter]),
        shadow_mode: true,
        requested_promotion: false,
        resource_budget_units: 1,
    };
    assert!(matches!(
        evaluate_learning_update(&valid),
        LearningDecision::ShadowOnly {
            promotion_allowed: false,
            ..
        }
    ));

    let mut forbidden = valid;
    forbidden.requested_surfaces = BTreeSet::from([UpdateSurface::Evaluator]);
    assert!(matches!(
        evaluate_learning_update(&forbidden),
        LearningDecision::Blocked(blockers)
            if blockers.contains(&UpdateBlocker::ProtectedSurface(UpdateSurface::Evaluator))
    ));
}

#[test]
fn compute_market_match_creates_unexecuted_hyperliquid_settlement_intent() {
    let job = ComputeJobRequest {
        job_id: "job-1".to_owned(),
        program_digest: digest("program"),
        input_commitment: digest("input"),
        route: ComputeRoute::ProofMarket,
        required_capabilities: CapabilitySet::new([Capability::CodeExecution]),
        minimum_confidentiality: ConfidentialityTier::TransportEncrypted,
        minimum_verifiability: VerifiabilityTier::ZkProof,
        max_price_units: 100,
        deadline: 200,
    };
    let offer = ComputeOffer {
        offer_id: "offer-1".to_owned(),
        job_id: "job-1".to_owned(),
        provider_id: "provider-1".to_owned(),
        offered_capabilities: CapabilitySet::new([Capability::CodeExecution]),
        confidentiality: ConfidentialityTier::TransportEncrypted,
        verifiability: VerifiabilityTier::ZkProof,
        price_units: 10,
        completion_deadline: 100,
        result_digest: Some(digest("result")),
        proof_digest: Some(digest("proof")),
    };
    let matched = match_compute_job(&job, &offer).expect("valid market match");
    assert_eq!(matched.settlement.rail, SettlementRail::Hyperliquid);
    assert!(!matched.settlement.executed);
    assert!(!matched.proof_verified);
    assert!(!matched.authority_granted);
}

#[test]
fn replay_guard_is_strict_and_rejected_nonce_does_not_advance_it() {
    let guard = ReplayGuard::new(1);
    let unchanged = guard
        .consume(2)
        .expect_err("out-of-order nonce must reject");
    assert_eq!(
        unchanged,
        ReplayBlocker::UnexpectedNonce {
            expected: 1,
            received: 2,
        }
    );
    assert_eq!(guard.next_nonce(), 1);
    let advanced = guard.consume(1).expect("first nonce is accepted");
    assert_eq!(advanced.next_nonce(), 2);
}

#[test]
fn state_machine_has_no_direct_proposal_to_execution_or_frozen_to_execution_edge() {
    assert_eq!(
        transition_state(ControlState::Proposal, StateTransition::Admit),
        Ok(ControlState::Admitted)
    );
    assert!(transition_state(ControlState::Proposal, StateTransition::BeginExecution).is_err());
    assert!(transition_state(ControlState::Frozen, StateTransition::BeginExecution).is_err());
    assert_eq!(
        transition_state(ControlState::Executing, StateTransition::Rollback),
        Ok(ControlState::RolledBack)
    );
}

#[test]
fn replay_journal_is_append_only_and_caller_owned() {
    let journal = ReplayJournal::new(1);
    let admitted = journal
        .append(
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            1,
            JournalState::Authorized,
        )
        .expect("first journal entry");
    assert!(journal.entries().is_empty());
    assert_eq!(admitted.entries().len(), 1);
    assert_eq!(admitted.entries()[0].sequence_number(), 1);
    assert!(admitted.validate().is_empty());

    let rejected = admitted.append(
        digest("proposal"),
        digest("receipt"),
        digest("permit"),
        1,
        JournalState::Completed,
    );
    assert_eq!(
        rejected,
        Err(JournalBlocker::UnexpectedNonce {
            expected: 2,
            received: 1,
        })
    );
    assert_eq!(admitted.next_nonce(), 2);
}

#[test]
fn replay_journal_checked_tip_rejects_stale_snapshot_without_mutation() {
    let empty = ReplayJournal::new(1);
    let first = empty
        .append_if_tip(
            None,
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            1,
            JournalState::Authorized,
        )
        .expect("first journal entry");
    let second = first
        .append_if_tip(
            first.tip_digest(),
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            2,
            JournalState::Completed,
        )
        .expect("second journal entry");

    assert_eq!(
        first.append_if_tip(
            first.tip_digest(),
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            2,
            JournalState::Completed,
        ),
        Ok(second.clone())
    );
    assert_eq!(
        first.append_if_tip(
            second.tip_digest(),
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            2,
            JournalState::Completed,
        ),
        Err(JournalBlocker::TipMismatch)
    );
    assert_eq!(first.entries().len(), 1);
}

#[test]
fn file_store_round_trips_and_recovers_an_interrupted_temp_write() {
    let path = std::env::temp_dir().join(format!(
        "hsai-control-plane-journal-storage-roundtrip-{}.json",
        digest("storage-roundtrip").to_hex()
    ));
    let temporary_path = path.with_extension("json.tmp");
    let _ = std::fs::remove_file(&path);
    let _ = std::fs::remove_file(&temporary_path);

    let journal = ReplayJournal::new(1)
        .append(
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            1,
            JournalState::Authorized,
        )
        .expect("journal entry");
    let encoded = serde_json::to_vec(&journal).expect("journal encodes");
    std::fs::write(&temporary_path, encoded).expect("temporary journal writes");

    let store = ReplayJournalFileStore::new(&path).expect("valid storage path");
    assert_eq!(store.read().expect("temporary journal recovers"), journal);
    assert!(!temporary_path.exists());

    let persisted = store.read().expect("journal round trips");
    assert_eq!(persisted.tip_digest(), journal.tip_digest());
    let _ = std::fs::remove_file(&path);
}

#[test]
fn file_store_checked_replace_rejects_stale_tip_without_overwriting() {
    let path = std::env::temp_dir().join(format!(
        "hsai-control-plane-journal-storage-cas-{}.json",
        digest("storage-cas").to_hex()
    ));
    let _ = std::fs::remove_file(&path);
    let _ = std::fs::remove_file(path.with_extension("json.tmp"));

    let first = ReplayJournal::new(1)
        .append(
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            1,
            JournalState::Authorized,
        )
        .expect("journal entry");
    let store = ReplayJournalFileStore::new(&path).expect("valid storage path");
    store.initialize(&first).expect("journal initializes");
    let second = first
        .append(
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            2,
            JournalState::Completed,
        )
        .expect("journal entry");
    store
        .replace_if_tip(first.tip_digest(), &second)
        .expect("current tip accepts replacement");

    let stale = ReplayJournal::new(1)
        .append(
            digest("other-proposal"),
            digest("other-receipt"),
            digest("other-permit"),
            1,
            JournalState::Authorized,
        )
        .expect("journal entry");
    assert!(matches!(
        store.replace_if_tip(first.tip_digest(), &stale),
        Err(JournalStorageError::TipMismatch { .. })
    ));
    assert_eq!(store.read().expect("journal remains readable"), second);
    let _ = std::fs::remove_file(&path);
}

#[test]
fn file_store_append_if_tip_persists_and_rejects_a_stale_snapshot() {
    let path = std::env::temp_dir().join(format!(
        "hsai-control-plane-journal-storage-append-{}.json",
        digest("storage-append").to_hex()
    ));
    let _ = std::fs::remove_file(&path);
    let _ = std::fs::remove_file(path.with_extension("json.tmp"));

    let store = ReplayJournalFileStore::new(&path).expect("valid storage path");
    let empty = ReplayJournal::new(1);
    store.initialize(&empty).expect("empty journal initializes");
    let first = store
        .append_if_tip(
            None,
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            1,
            JournalState::Authorized,
        )
        .expect("first append persists");
    assert_eq!(store.read().expect("first append reads back"), first);

    assert!(matches!(
        store.append_if_tip(
            None,
            digest("other-proposal"),
            digest("other-receipt"),
            digest("other-permit"),
            2,
            JournalState::Completed,
        ),
        Err(JournalStorageError::JournalAppendRejected(
            JournalBlocker::TipMismatch
        ))
    ));
    assert_eq!(store.read().expect("stale append leaves journal"), first);
    let _ = std::fs::remove_file(&path);
}

#[test]
fn file_store_rejects_noncanonical_and_invalid_snapshots() {
    let path = std::env::temp_dir().join(format!(
        "hsai-control-plane-journal-storage-invalid-{}.json",
        digest("storage-invalid").to_hex()
    ));
    let _ = std::fs::remove_file(&path);
    let _ = std::fs::remove_file(path.with_extension("json.tmp"));

    let store = ReplayJournalFileStore::new(&path).expect("valid storage path");
    let empty = ReplayJournal::new(1);
    let canonical = serde_json::to_vec(&empty).expect("empty journal encodes");
    let mut noncanonical = Vec::with_capacity(canonical.len() + 1);
    noncanonical.push(b' ');
    noncanonical.extend_from_slice(&canonical);
    std::fs::write(&path, noncanonical).expect("noncanonical journal writes");
    assert_eq!(store.read(), Err(JournalStorageError::NonCanonicalBytes));

    let invalid = serde_json::json!({
        "first_nonce": 0,
        "next_nonce": 0,
        "entries": []
    });
    let invalid_bytes = serde_json::to_vec(&invalid).expect("invalid journal encodes");
    std::fs::write(&path, invalid_bytes).expect("invalid journal writes");
    assert_eq!(store.read(), Err(JournalStorageError::InvalidJournal));

    let _ = std::fs::remove_file(&path);
}

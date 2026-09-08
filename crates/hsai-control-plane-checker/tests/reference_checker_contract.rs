use hsai_control_plane::*;
use hsai_control_plane_checker::*;
use serde_json::json;
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
        allowed_capabilities: CapabilitySet::new([Capability::Read]),
        max_capability_ttl: 100,
        max_spend_units: 50,
        require_independent_evidence: true,
        require_reversible: true,
        forbidden_risks: BTreeSet::new(),
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

fn receipt() -> CapabilityReceipt {
    match evaluate_admission(&proposal(&policy()), &policy(), 20, &KillSwitch::Armed) {
        AdmissionDecision::Accepted(receipt) => receipt,
        decision => panic!("expected accepted decision, got {decision:?}"),
    }
}

#[test]
fn checker_accepts_valid_receipt_and_rejects_serialized_tampering() {
    let valid = receipt();
    assert!(check_receipt(&valid).is_empty());

    let mut encoded = serde_json::to_value(&valid).expect("receipt serializes");
    encoded["expires_at"] = json!(0);
    let tampered: CapabilityReceipt = serde_json::from_value(encoded).expect("receipt decodes");
    let violations = check_receipt(&tampered);
    assert!(violations.contains(&CheckerViolation::ReceiptDigestInvalid));
    assert!(violations.contains(&CheckerViolation::ReceiptValidityWindowInvalid));
}

#[test]
fn checker_recomputes_monitor_and_shadow_update_invariants() {
    let receipt = receipt();
    let observation = MonitorObservation {
        now: 21,
        signal: MonitorSignal::InvariantViolation,
        resource_units_used: 1,
        spend_units_used: 1,
    };
    let monitor = monitor_execution(&receipt, &observation, &KillSwitch::Armed);
    assert!(
        check_monitor_decision(&receipt, &observation, &KillSwitch::Armed, &monitor).is_empty()
    );

    let mut forged_monitor = monitor;
    forged_monitor.authority_granted = true;
    assert!(
        check_monitor_decision(&receipt, &observation, &KillSwitch::Armed, &forged_monitor)
            .contains(&CheckerViolation::MonitorGrantsAuthority)
    );

    let update = LearningUpdateProposal {
        update_id: "update-1".to_owned(),
        immutable_base_digest: digest("base"),
        candidate_digest: digest("candidate"),
        trajectory_digest: digest("trajectory"),
        prediction_lock_digest: Some(digest("lock")),
        independent_evaluation_digest: Some(digest("eval")),
        rollback_target_digest: Some(digest("base")),
        requested_surfaces: BTreeSet::from([UpdateSurface::ModelAdapter]),
        shadow_mode: true,
        requested_promotion: false,
        resource_budget_units: 1,
    };
    let decision = evaluate_learning_update(&update);
    assert!(check_learning_decision(&decision).is_empty());
}

#[test]
fn checker_recomputes_market_bindings_and_detects_authority_or_settlement_drift() {
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
    assert!(check_compute_match(&job, &offer, &matched).is_empty());

    let mut forged = matched;
    forged.authority_granted = true;
    forged.settlement.executed = true;
    let violations = check_compute_match(&job, &offer, &forged);
    assert!(violations.contains(&CheckerViolation::MarketGrantsAuthority));
    assert!(violations.contains(&CheckerViolation::MarketSettlementExecuted));
}

#[test]
fn checker_rejects_empty_failure_records_and_accepts_nonempty_failures() {
    assert_eq!(
        check_admission_decision(&AdmissionDecision::Rejected(Vec::new())),
        vec![CheckerViolation::EmptyBlockerList]
    );
    assert!(check_admission_decision(&AdmissionDecision::Rejected(vec![
        AdmissionBlocker::KillSwitchActive,
    ]))
    .is_empty());

    assert_eq!(
        check_alignment_decision(&AlignmentDecision::Blocked(Vec::new())),
        vec![CheckerViolation::EmptyBlockerList]
    );
}

#[test]
fn checker_recomputes_replay_journal_chain() {
    let journal = ReplayJournal::new(7)
        .append(
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            7,
            JournalState::Authorized,
        )
        .expect("journal entry")
        .append(
            digest("proposal"),
            digest("receipt"),
            digest("permit"),
            8,
            JournalState::Completed,
        )
        .expect("journal entry");
    assert!(check_replay_journal(&journal).is_empty());

    let mut encoded = serde_json::to_value(&journal).expect("journal serializes");
    encoded["entries"][1]["nonce"] = json!(99);
    let tampered: ReplayJournal = serde_json::from_value(encoded).expect("journal decodes");
    let violations = check_replay_journal(&tampered);
    assert!(violations.contains(&CheckerViolation::JournalNonceMismatch));
    assert!(violations.contains(&CheckerViolation::JournalEntryDigestInvalid));
}

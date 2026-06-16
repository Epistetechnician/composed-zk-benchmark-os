use zkbench_core::{
    build_default_evidence_acceptance_policy, guard_claim_boundary_escalation,
    review_evidence_append_proposal, validate_evidence_acceptance_policy, ClaimBoundary,
    EvidenceAcceptanceBlockingReason, EvidenceAcceptancePolicy, EvidenceReviewChecklist,
    EvidenceReviewDecisionKind, EvidenceReviewerRole,
};

fn proposal() -> zkbench_core::EvidenceAppendProposal {
    zkbench_core::deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse")
}

fn decision(
    proposal: &zkbench_core::EvidenceAppendProposal,
) -> zkbench_core::EvidenceReviewDecision {
    review_evidence_append_proposal(
        proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build")
}

#[test]
fn default_acceptance_policy_validates() {
    let policy = build_default_evidence_acceptance_policy();
    let validation = validate_evidence_acceptance_policy(&policy);

    assert!(validation.valid, "{:?}", validation.issues);
}

#[test]
fn policy_accepts_reviewed_candidate_only_proposal() {
    let proposal = proposal();
    let decision = decision(&proposal);
    let policy = build_default_evidence_acceptance_policy();

    let validation = policy.validate_proposal_for_candidate(
        &proposal,
        &decision,
        ClaimBoundary::Level0DesignNote,
    );

    assert!(validation.valid, "{:?}", validation.issues);
}

#[test]
fn policy_blocks_level2_actual_evidence() {
    let proposal = proposal();
    let decision = decision(&proposal);
    let policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();

    let validation = policy.validate_proposal_for_candidate(
        &proposal,
        &decision,
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
    );

    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.blocking_reason == EvidenceAcceptanceBlockingReason::Level2ActualEvidenceBlocked
    }));
}

#[test]
fn escalation_guard_requires_explicit_level1_local_policy() {
    let blocked = guard_claim_boundary_escalation(
        ClaimBoundary::Level0DesignNote,
        ClaimBoundary::Level1LocalReplay,
        false,
    );
    assert!(blocked.is_err());

    let allowed = guard_claim_boundary_escalation(
        ClaimBoundary::Level0DesignNote,
        ClaimBoundary::Level1LocalReplay,
        true,
    )
    .expect("explicit local-only policy should allow Level1 candidate boundary");
    assert!(allowed.allowed);
}

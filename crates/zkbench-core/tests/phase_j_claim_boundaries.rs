use zkbench_core::{
    create_evidence_append_preview, create_evidence_record_candidate,
    guard_claim_boundary_escalation, review_evidence_append_proposal,
    validate_evidence_append_preview, validate_evidence_record_candidate, ClaimBoundary,
    EvidenceAcceptancePolicy, EvidenceAppendPreviewStatus, EvidenceClass, EvidenceReviewChecklist,
    EvidenceReviewDecisionKind, EvidenceReviewerRole,
};

fn candidate() -> zkbench_core::EvidenceRecordCandidate {
    let proposal = zkbench_core::deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse");
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build");
    let policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();

    create_evidence_record_candidate(&policy, &proposal, &decision)
        .expect("reviewed candidate should build")
}

#[test]
fn claim_boundary_ordering_remains_monotonic() {
    assert!(ClaimBoundary::Level0DesignNote < ClaimBoundary::Level1LocalReplay);
    assert!(ClaimBoundary::Level1LocalReplay < ClaimBoundary::Level2ReproducibleBenchmarkArtifact);
    assert_eq!(
        ClaimBoundary::Level1LocalReplay.to_string(),
        "Level1LocalReplay"
    );
}

#[test]
fn phase_j_blocks_level2_escalation() {
    let result = guard_claim_boundary_escalation(
        ClaimBoundary::Level1LocalReplay,
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
        true,
    );

    assert!(result.is_err());
}

#[test]
fn candidates_cannot_be_level2_or_formal_evidence() {
    let mut candidate = candidate();
    candidate.proposed_evidence_class = EvidenceClass::MachineCheckedScopedProof;
    candidate.proposed_claim_boundary = ClaimBoundary::Level5MachineCheckedScopedProof;
    candidate.claims_formal_evidence = true;

    let validation = validate_evidence_record_candidate(&candidate);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("Level2+") || issue.message.contains("claim flags")));
}

#[test]
fn append_preview_stays_level0_and_preview_only() {
    let preview =
        create_evidence_append_preview(&candidate(), None).expect("append preview should build");

    assert_eq!(preview.status, EvidenceAppendPreviewStatus::PreviewOnly);
    assert_eq!(preview.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(validate_evidence_append_preview(&preview).valid);
}

use zkbench_core::{
    create_evidence_record_candidate, deserialize_evidence_record_candidate_json,
    review_evidence_append_proposal, serialize_evidence_record_candidate_json,
    validate_evidence_record_candidate, ClaimBoundary, EvidenceAcceptancePolicy, EvidenceClass,
    EvidenceRecordCandidate, EvidenceReviewChecklist, EvidenceReviewDecisionKind,
    EvidenceReviewerRole,
};

fn proposal() -> zkbench_core::EvidenceAppendProposal {
    zkbench_core::deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse")
}

fn level1_candidate() -> EvidenceRecordCandidate {
    let proposal = proposal();
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build");
    let policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();

    create_evidence_record_candidate(&policy, &proposal, &decision)
        .expect("reviewed local-only candidate should build")
}

#[test]
fn level1_local_candidate_validates_but_is_not_accepted_evidence() {
    let candidate = level1_candidate();
    let validation = validate_evidence_record_candidate(&candidate);

    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(
        candidate.proposed_evidence_class,
        EvidenceClass::LocalReplay
    );
    assert_eq!(
        candidate.proposed_claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert!(!candidate.is_accepted_evidence());
    assert!(!candidate.is_official_benchmark_evidence());
    assert!(candidate.requires_future_manual_append());
}

#[test]
fn candidate_fixture_roundtrips() {
    let candidate = deserialize_evidence_record_candidate_json(include_str!(
        "fixtures/evidence_record_candidate_level1.json"
    ))
    .expect("candidate fixture should parse");
    let validation = validate_evidence_record_candidate(&candidate);
    assert!(validation.valid, "{:?}", validation.issues);

    let json =
        serialize_evidence_record_candidate_json(&candidate).expect("candidate should serialize");
    let parsed =
        deserialize_evidence_record_candidate_json(&json).expect("candidate should deserialize");
    assert_eq!(candidate, parsed);
}

#[test]
fn candidate_rejects_level2_or_claim_flags() {
    let mut candidate = level1_candidate();
    candidate.proposed_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    candidate.claims_official_benchmark_evidence = true;
    candidate.candidate_metrics_are_score_inputs = true;

    let validation = validate_evidence_record_candidate(&candidate);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.contains("proposed_claim_boundary")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.contains("claim_flags")));
}

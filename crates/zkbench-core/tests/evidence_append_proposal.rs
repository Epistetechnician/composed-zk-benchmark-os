use zkbench_core::{
    create_evidence_append_proposal, deserialize_evidence_append_proposal_json,
    deserialize_external_result_candidate_json, normalize_synthetic_result_candidate,
    validate_evidence_append_proposal, validate_synthetic_result_candidate, ClaimBoundary,
    EvidenceAppendProposalStatus, EvidenceClass, EvidenceLedger, ResultCandidateArtifactResolver,
};

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

#[test]
fn normalized_draft_creates_pending_review_proposal() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    let resolver = resolver();
    let validation = validate_synthetic_result_candidate(&candidate, &resolver);
    let draft = normalize_synthetic_result_candidate(&candidate, &validation, &resolver)
        .expect("valid candidate should normalize");
    let proposal = create_evidence_append_proposal(&draft).expect("proposal should build");

    assert_eq!(proposal.status, EvidenceAppendProposalStatus::PendingReview);
    assert_eq!(proposal.proposed_evidence_class, EvidenceClass::DesignNote);
    assert_eq!(
        proposal.proposed_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!proposal.is_accepted_evidence());
    assert!(validate_evidence_append_proposal(&proposal).valid);
}

#[test]
fn evidence_append_proposal_fixture_validates() {
    let proposal = deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse");
    let validation = validate_evidence_append_proposal(&proposal);

    assert!(validation.valid, "{:?}", validation.issues);
    assert!(!proposal.is_accepted_evidence());
}

#[test]
fn proposal_cannot_claim_accepted_or_level2_evidence() {
    let mut proposal = deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse");
    proposal.claims_accepted_evidence = true;
    proposal.proposed_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;

    let validation = validate_evidence_append_proposal(&proposal);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.contains("claims_accepted_evidence")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.contains("proposed_claim_boundary")));
}

#[test]
fn proposal_workflow_does_not_mutate_evidence_ledger() {
    let proposal = deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse");
    let ledger = EvidenceLedger::new();

    assert!(!proposal.is_accepted_evidence());
    assert_eq!(ledger.entries.len(), 0);
}

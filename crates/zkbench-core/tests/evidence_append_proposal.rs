use zkbench_core::{
    create_evidence_append_proposal, deserialize_evidence_append_proposal_json,
    deserialize_external_result_candidate_json, normalize_synthetic_result_candidate,
    validate_evidence_append_proposal, validate_synthetic_result_candidate, ClaimBoundary,
    EvidenceAppendProposalStatus, EvidenceClass, EvidenceLedger, EvidenceReviewFinding,
    EvidenceReviewFindingSeverity, EvidenceReviewRequirement, ExternalValidationIssueSeverity,
    ResultCandidateArtifactResolver, SyntheticImportValidationIssue,
    SyntheticImportValidationIssueKind,
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

#[test]
fn proposal_validation_reports_all_local_metadata_rejection_paths() {
    let mut proposal = deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse");

    proposal.id = String::new();
    proposal.source_normalized_draft_id = String::new();
    proposal.proposed_evidence_class = EvidenceClass::ReproducibleBenchmarkArtifact;
    proposal.proposed_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    proposal.claims_accepted_evidence = true;
    proposal.proposed_artifact_refs[0].artifact_ref = String::new();
    proposal
        .blocking_issues
        .push(SyntheticImportValidationIssue {
            path: "candidate.notes[0]".to_string(),
            message: "official benchmark evidence claim".to_string(),
            severity: ExternalValidationIssueSeverity::Error,
            kind: SyntheticImportValidationIssueKind::OfficialClaimDetected,
        });
    proposal
        .blocking_issues
        .push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::ClaimBoundaryTooHigh,
            "candidate.claim_boundary",
            "claim boundary too high",
        ));
    proposal
        .notes
        .push("this is official benchmark evidence".to_string());
    proposal
        .proposed_provenance_summary
        .push("formal proof was accepted".to_string());
    proposal
        .reviewer_checklist
        .requirements
        .push(EvidenceReviewRequirement {
            id: "bad_requirement".to_string(),
            description: "contains forbidden wording".to_string(),
            required: true,
            satisfied: false,
            notes: vec!["machine-checked proof exists".to_string()],
        });
    proposal
        .reviewer_checklist
        .findings
        .push(EvidenceReviewFinding {
            id: "bad_finding".to_string(),
            message: "this proves soundness".to_string(),
            severity: EvidenceReviewFindingSeverity::Blocking,
            blocking: true,
        });

    let validation = validate_evidence_append_proposal(&proposal);
    let issue_paths = validation
        .issues
        .iter()
        .map(|issue| issue.path.as_str())
        .collect::<Vec<_>>();

    assert!(!validation.valid);
    for expected in [
        "proposal.id",
        "proposal.source_normalized_draft_id",
        "proposal.proposed_evidence_class",
        "proposal.proposed_claim_boundary",
        "proposal.claims_accepted_evidence",
        "proposal.proposed_artifact_refs[0].artifact_ref",
        "proposal.blocking_issues[0]",
        "proposal.blocking_issues[0].kind",
        "proposal.blocking_issues[1]",
        "proposal.blocking_issues[1].kind",
        "proposal.notes[2]",
        "proposal.proposed_provenance_summary[3]",
        "proposal.reviewer_checklist.requirements[2].notes[0]",
        "proposal.reviewer_checklist.findings[0].message",
    ] {
        assert!(
            issue_paths.contains(&expected),
            "missing expected issue path {expected}; got {issue_paths:?}"
        );
    }
    assert!(validation
        .issues
        .iter()
        .all(|issue| issue.severity == ExternalValidationIssueSeverity::Error));
}

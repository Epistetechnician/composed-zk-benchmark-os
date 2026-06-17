use zkbench_core::{
    create_evidence_append_preview, create_evidence_append_proposal,
    create_evidence_record_candidate, deserialize_evidence_append_preview_json,
    deserialize_external_result_candidate_json, normalize_synthetic_result_candidate,
    review_evidence_append_proposal, serialize_evidence_append_preview_json,
    validate_evidence_append_preview, validate_evidence_append_proposal,
    validate_evidence_record_candidate, validate_synthetic_result_candidate, ClaimBoundary,
    EvidenceAcceptancePolicy, EvidenceAppendPreview, EvidenceAppendPreviewStatus, EvidenceLedger,
    EvidenceRecordCandidateStatus, EvidenceReviewChecklist, EvidenceReviewDecisionKind,
    EvidenceReviewerRole, ResultCandidateArtifactResolver,
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
fn append_preview_does_not_mutate_evidence_ledger() {
    let candidate = candidate();
    let ledger = EvidenceLedger::new();
    let preview =
        create_evidence_append_preview(&candidate, Some(&ledger)).expect("preview should build");

    assert_eq!(ledger.entries.len(), 0);
    assert!(!preview.mutates_ledger());
    assert!(!preview.mutates_evidence_ledger);
    assert!(preview.validation.valid, "{:?}", preview.validation.issues);
    assert_eq!(
        preview
            .transaction_preview
            .projected_ledger_summary
            .entry_count,
        1
    );
}

#[test]
fn proposal_review_candidate_preview_flow_stays_metadata_only() {
    let source = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("source candidate should parse");
    let resolver = ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )]);
    let source_validation = validate_synthetic_result_candidate(&source, &resolver);
    let draft = normalize_synthetic_result_candidate(&source, &source_validation, &resolver)
        .expect("valid source candidate should normalize");
    let proposal = create_evidence_append_proposal(&draft).expect("proposal should build");
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build");
    let policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();
    let candidate = create_evidence_record_candidate(&policy, &proposal, &decision)
        .expect("reviewed candidate should build");
    let ledger = EvidenceLedger::new();
    let preview =
        create_evidence_append_preview(&candidate, Some(&ledger)).expect("preview should build");

    assert!(validate_evidence_append_proposal(&proposal).valid);
    assert!(validate_evidence_record_candidate(&candidate).valid);
    assert!(validate_evidence_append_preview(&preview).valid);
    assert!(!proposal.is_accepted_evidence());
    assert!(!candidate.is_accepted_evidence());
    assert!(!candidate.is_official_benchmark_evidence());
    assert!(candidate.requires_future_manual_append());
    assert_eq!(
        candidate.status,
        EvidenceRecordCandidateStatus::CandidateOnly
    );
    assert_eq!(
        candidate.proposed_claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert_eq!(preview.status, EvidenceAppendPreviewStatus::PreviewOnly);
    assert_eq!(preview.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!preview.mutates_ledger());
    assert!(!preview.mutates_evidence_ledger);
    assert_eq!(ledger.entries.len(), 0);
    assert_eq!(
        preview
            .transaction_preview
            .projected_ledger_summary
            .entry_count,
        1
    );
}

#[test]
fn append_preview_fixture_roundtrips() {
    let preview: EvidenceAppendPreview = deserialize_evidence_append_preview_json(include_str!(
        "fixtures/evidence_append_preview.json"
    ))
    .expect("preview fixture should parse");
    let validation = validate_evidence_append_preview(&preview);
    assert!(validation.valid, "{:?}", validation.issues);

    let json = serialize_evidence_append_preview_json(&preview).expect("preview should serialize");
    let parsed = deserialize_evidence_append_preview_json(&json).expect("preview should parse");
    assert_eq!(preview, parsed);
}

#[test]
fn append_preview_validation_rejects_mutation_flag() {
    let candidate = candidate();
    let mut preview =
        create_evidence_append_preview(&candidate, None).expect("preview should build");
    preview.mutates_evidence_ledger = true;

    let validation = validate_evidence_append_preview(&preview);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.contains("mutates_evidence_ledger")));
}

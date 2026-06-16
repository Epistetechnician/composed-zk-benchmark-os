use zkbench_core::{
    create_evidence_append_preview, create_evidence_record_candidate,
    deserialize_evidence_append_preview_json, review_evidence_append_proposal,
    serialize_evidence_append_preview_json, validate_evidence_append_preview,
    EvidenceAcceptancePolicy, EvidenceAppendPreview, EvidenceLedger, EvidenceReviewChecklist,
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

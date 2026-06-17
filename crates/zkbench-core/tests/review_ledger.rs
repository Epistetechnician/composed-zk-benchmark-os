use zkbench_core::{
    create_evidence_append_preview, create_evidence_record_candidate,
    deserialize_evidence_review_ledger_json, review_evidence_append_proposal,
    serialize_evidence_review_ledger_json, ClaimBoundary, EvidenceAcceptancePolicy,
    EvidenceReviewChecklist, EvidenceReviewDecisionKind, EvidenceReviewLedger,
    EvidenceReviewerRole,
};

fn proposal() -> zkbench_core::EvidenceAppendProposal {
    zkbench_core::deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse")
}

fn reviewed_candidate_preview() -> (
    zkbench_core::EvidenceReviewDecision,
    zkbench_core::EvidenceAppendPreview,
) {
    let proposal = proposal();
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
    let preview = create_evidence_append_preview(&candidate, None).expect("preview should build");

    (decision, preview)
}

#[test]
fn empty_review_ledger_fixture_validates() {
    let ledger =
        deserialize_evidence_review_ledger_json(include_str!("fixtures/review_ledger.json"))
            .expect("review ledger fixture should parse");
    let validation = ledger.validate();

    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(validation.summary.entry_count, 0);
}

#[test]
fn review_ledger_records_decision_and_preview() {
    let (decision, preview) = reviewed_candidate_preview();
    let mut ledger = EvidenceReviewLedger::new("phase_j_review_ledger");

    ledger
        .append_review_decision(decision)
        .expect("decision append should work");
    ledger
        .append_append_preview(preview)
        .expect("preview append should work");

    let validation = ledger.validate();
    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(validation.summary.entry_count, 2);
    assert_eq!(ledger.entries.len(), 2);

    let json = serialize_evidence_review_ledger_json(&ledger).expect("ledger should serialize");
    let parsed = deserialize_evidence_review_ledger_json(&json).expect("ledger should deserialize");
    assert_eq!(ledger, parsed);
}

#[test]
fn review_ledger_rejects_invalid_append_preview_before_append() {
    let (_, mut preview) = reviewed_candidate_preview();
    preview.claim_boundary = ClaimBoundary::Level1LocalReplay;
    let mut ledger = EvidenceReviewLedger::new("phase_j_review_ledger");

    let error = ledger
        .append_append_preview(preview)
        .expect_err("invalid nested append preview should be rejected");

    assert!(error.to_string().contains("append preview invalid"));
    assert!(ledger.entries.is_empty());
    assert_eq!(ledger.summary.entry_count, 0);
}

#[test]
fn review_ledger_detects_stale_cached_summary() {
    let (decision, preview) = reviewed_candidate_preview();
    let mut ledger = EvidenceReviewLedger::new("phase_j_review_ledger");
    ledger
        .append_review_decision(decision)
        .expect("decision append should work");
    ledger
        .append_append_preview(preview)
        .expect("preview append should work");
    ledger.summary.entry_count = 1;

    let validation = ledger.validate();

    assert!(!validation.valid);
    assert_eq!(validation.summary.entry_count, 2);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "ledger.summary"));
}

#[test]
fn review_ledger_rejects_artifact_claim_boundary_elevation() {
    let (decision, _) = reviewed_candidate_preview();
    let mut ledger = EvidenceReviewLedger::new("phase_j_review_ledger");
    ledger
        .append_review_decision(decision)
        .expect("decision append should work");
    ledger.claim_boundary = ClaimBoundary::Level1LocalReplay;

    let validation = ledger.validate();

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "ledger.claim_boundary"));
}

#[test]
fn review_ledger_rejects_forbidden_claim_text_in_notes() {
    let (decision, _) = reviewed_candidate_preview();
    let mut ledger = EvidenceReviewLedger::new("phase_j_review_ledger");
    ledger
        .append_review_decision(decision)
        .expect("decision append should work");
    ledger
        .notes
        .push("this review ledger is official benchmark evidence".to_string());

    let validation = ledger.validate();

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "ledger.notes[2]"));
}

#[test]
fn review_ledger_rejects_forbidden_claim_text_in_entry_notes() {
    let (decision, _) = reviewed_candidate_preview();
    let mut ledger = EvidenceReviewLedger::new("phase_j_review_ledger");
    ledger
        .append_review_decision(decision)
        .expect("decision append should work");
    ledger.entries[0]
        .notes
        .push("this review ledger entry is official benchmark evidence".to_string());

    let validation = ledger.validate();

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "ledger.entries[0].notes[0]"));
}

#[test]
fn review_ledger_detects_digest_tampering() {
    let (decision, _) = reviewed_candidate_preview();
    let mut ledger = EvidenceReviewLedger::new("phase_j_review_ledger");
    ledger
        .append_review_decision(decision)
        .expect("decision append should work");
    if let zkbench_core::EvidenceReviewLedgerEntrySubject::ReviewDecision(decision) =
        &mut ledger.entries[0].subject
    {
        decision.notes.push("tampered review note".to_string());
    }

    let validation = ledger.validate();
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("digest mismatch")));
}

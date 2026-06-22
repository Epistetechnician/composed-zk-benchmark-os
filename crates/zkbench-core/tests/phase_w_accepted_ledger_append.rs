use std::path::Path;

use zkbench_core::{
    apply_accepted_ledger_append_transaction, build_reviewed_promotion_preflight_report,
    compute_artifact_digest_bytes, create_evidence_append_preview,
    create_evidence_record_candidate, required_reviewed_promotion_preflight_non_claims,
    review_evidence_append_proposal, validate_accepted_ledger_append_transaction_request,
    AcceptedLedgerAppendTransactionIssueKind, AcceptedLedgerAppendTransactionRequest,
    AcceptedLedgerAppendTransactionVersion, ArtifactDigest, ArtifactKind, ArtifactRole,
    ClaimBoundary, EvidenceAcceptancePolicy, EvidenceAppendPreviewStatus, EvidenceClass,
    EvidenceLedger, EvidenceReviewChecklist, EvidenceReviewDecisionKind, EvidenceReviewerRole,
    ReviewedPromotionPreflightRequest, ReviewedPromotionPreflightVersion,
};

fn candidate_and_decision() -> (
    zkbench_core::EvidenceRecordCandidate,
    zkbench_core::EvidenceReviewDecision,
) {
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
    let candidate = create_evidence_record_candidate(&policy, &proposal, &decision)
        .expect("reviewed candidate should build");
    (candidate, decision)
}

fn source_digests(candidate: &zkbench_core::EvidenceRecordCandidate) -> Vec<ArtifactDigest> {
    candidate
        .proposed_artifact_refs
        .iter()
        .map(|artifact| artifact.digest.clone())
        .collect()
}

fn valid_preflight_request(ledger: &EvidenceLedger) -> ReviewedPromotionPreflightRequest {
    let (candidate, decision) = candidate_and_decision();
    let append_preview =
        create_evidence_append_preview(&candidate, Some(ledger)).expect("preview should build");
    assert_eq!(
        append_preview.status,
        EvidenceAppendPreviewStatus::PreviewOnly
    );
    let expected_current_ledger_tip = ledger
        .entries
        .last()
        .map(|entry| entry.entry_digest.clone());

    ReviewedPromotionPreflightRequest {
        id: "phase_w_local_preflight_for_append".to_string(),
        version: ReviewedPromotionPreflightVersion::default(),
        source_artifact_digests: source_digests(&candidate),
        candidate,
        append_preview,
        review_decision: decision,
        expected_current_ledger_tip,
        external_replay_provenance: Vec::new(),
        unresolved_quarantine_markers: Vec::new(),
        blocking_markers: Vec::new(),
        requested_evidence_class: EvidenceClass::LocalReplay,
        requested_claim_boundary: ClaimBoundary::Level1LocalReplay,
        populates_score_axes: false,
        official_submission_package_requested: false,
        accepted_evidence_ledger_entry_ids: Vec::new(),
        claim_text: vec!["local reviewed append transaction".to_string()],
        non_claims: required_reviewed_promotion_preflight_non_claims()
            .into_iter()
            .map(str::to_string)
            .collect(),
    }
}

fn valid_transaction() -> (EvidenceLedger, AcceptedLedgerAppendTransactionRequest) {
    let ledger = EvidenceLedger::new();
    let preflight_request = valid_preflight_request(&ledger);
    let preflight_report = build_reviewed_promotion_preflight_report(&preflight_request);
    assert!(
        preflight_report.validation.valid,
        "{:?}",
        preflight_report.validation.issues
    );

    (
        ledger,
        AcceptedLedgerAppendTransactionRequest {
            transaction_id: "accepted_append_tx_local_level1".to_string(),
            version: AcceptedLedgerAppendTransactionVersion::default(),
            target_evidence_ledger_id: "accepted-ledger-local-fixture".to_string(),
            expected_current_ledger_tip: preflight_request.expected_current_ledger_tip.clone(),
            preflight_request,
            preflight_report,
            notes: vec!["local append transaction stays below Level2".to_string()],
        },
    )
}

fn digest(label: &str) -> ArtifactDigest {
    compute_artifact_digest_bytes(
        label.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

#[test]
fn valid_transaction_appends_one_level1_entry_and_reports_bounded_mutation() {
    let (mut ledger, request) = valid_transaction();
    let validation = validate_accepted_ledger_append_transaction_request(&request, &ledger);
    assert!(validation.valid, "{:?}", validation.issues);

    let report = apply_accepted_ledger_append_transaction(&request, &mut ledger)
        .expect("valid local append should apply");
    assert!(report.validation.valid, "{:?}", report.validation.issues);
    assert!(report.mutates_accepted_evidence_ledger);
    assert!(!report.creates_official_submission);
    assert!(!report.populates_score_axes);
    assert_eq!(report.appended_sequence_number, Some(0));
    assert_eq!(
        report.appended_claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert_eq!(report.appended_evidence_class, EvidenceClass::LocalReplay);

    assert_eq!(ledger.entries.len(), 1);
    let entry = &ledger.entries[0];
    assert_eq!(
        entry.evidence_record.claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert_eq!(
        entry.evidence_record.evidence_class,
        EvidenceClass::LocalReplay
    );
    assert_eq!(
        report.appended_entry_digest,
        Some(entry.entry_digest.clone())
    );
    assert!(ledger.validate().valid);
}

#[test]
fn transaction_rejects_stale_ledger_tip_without_mutation() {
    let (mut ledger, mut request) = valid_transaction();
    request.expected_current_ledger_tip = Some(digest("stale"));

    let validation = validate_accepted_ledger_append_transaction_request(&request, &ledger);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == AcceptedLedgerAppendTransactionIssueKind::StaleLedgerTip));

    assert!(apply_accepted_ledger_append_transaction(&request, &mut ledger).is_err());
    assert!(ledger.entries.is_empty());
}

#[test]
fn transaction_rejects_candidate_digest_mismatch_without_mutation() {
    let (mut ledger, mut request) = valid_transaction();
    request
        .preflight_request
        .append_preview
        .proposed_append_entries[0]
        .proposed_record_digest = digest("wrong candidate digest");
    request.preflight_report =
        build_reviewed_promotion_preflight_report(&request.preflight_request);

    let validation = validate_accepted_ledger_append_transaction_request(&request, &ledger);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == AcceptedLedgerAppendTransactionIssueKind::CandidateDigestMismatch
    }));

    assert!(apply_accepted_ledger_append_transaction(&request, &mut ledger).is_err());
    assert!(ledger.entries.is_empty());
}

#[test]
fn transaction_rejects_official_submission_score_axes_and_level2_claims() {
    let (mut ledger, mut request) = valid_transaction();
    request
        .preflight_request
        .official_submission_package_requested = true;
    request.preflight_request.populates_score_axes = true;
    request.preflight_request.candidate.proposed_claim_boundary =
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    request.preflight_request.candidate.proposed_evidence_class =
        EvidenceClass::ReproducibleBenchmarkArtifact;
    request.preflight_report =
        build_reviewed_promotion_preflight_report(&request.preflight_request);

    let validation = validate_accepted_ledger_append_transaction_request(&request, &ledger);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == AcceptedLedgerAppendTransactionIssueKind::OfficialSubmissionAttempted
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == AcceptedLedgerAppendTransactionIssueKind::ScoreAxisPopulationAttempted
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == AcceptedLedgerAppendTransactionIssueKind::ClaimBoundaryTooHigh
    }));

    assert!(apply_accepted_ledger_append_transaction(&request, &mut ledger).is_err());
    assert!(ledger.entries.is_empty());
}

#[test]
fn accepted_append_source_scan_exposes_no_runtime_submission_or_filesystem_surface() {
    let source_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("evidence")
        .join("accepted_append.rs");
    let source = std::fs::read_to_string(source_path).expect("source should read");

    for forbidden in [
        "std::process",
        "Command::new",
        "std::net",
        "TcpStream",
        "reqwest",
        "ureq",
        "std::fs",
        ".save_json(",
        "append_with_policy",
        "submit_to_",
        "http://",
        "https://",
    ] {
        assert!(
            !source.contains(forbidden),
            "accepted append transaction must not expose {forbidden}"
        );
    }
    assert!(source.contains("ledger.append("));
}

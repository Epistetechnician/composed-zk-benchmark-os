use zkbench_core::{
    apply_accepted_ledger_append_transaction, build_evidence_record_from_transaction,
    build_reviewed_promotion_preflight_report, compute_artifact_digest_bytes,
    create_evidence_append_preview, create_evidence_record_candidate,
    required_reviewed_promotion_preflight_non_claims, review_evidence_append_proposal,
    validate_accepted_ledger_append_transaction_request, AcceptedLedgerAppendTransactionIssueKind,
    AcceptedLedgerAppendTransactionRequest, AcceptedLedgerAppendTransactionVersion, ArtifactDigest,
    ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceAcceptancePolicy,
    EvidenceAppendPreviewStatus, EvidenceClass, EvidenceLedger, EvidenceReviewChecklist,
    EvidenceReviewDecisionKind, EvidenceReviewerRole, ReviewedPromotionPreflightRequest,
    ReviewedPromotionPreflightVersion,
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
        id: "phase_201_local_preflight_for_append".to_string(),
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
            transaction_id: "phase_201_accepted_append_tx_local_level1".to_string(),
            version: AcceptedLedgerAppendTransactionVersion::default(),
            target_evidence_ledger_id: "phase-201-accepted-ledger-local-fixture".to_string(),
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

fn issue_kinds(
    request: &AcceptedLedgerAppendTransactionRequest,
    ledger: &EvidenceLedger,
) -> Vec<AcceptedLedgerAppendTransactionIssueKind> {
    validate_accepted_ledger_append_transaction_request(request, ledger)
        .issues
        .into_iter()
        .map(|issue| issue.kind)
        .collect()
}

#[test]
fn transaction_reports_empty_identities_invalid_ledger_and_tampered_report_flags() {
    let (mut ledger, mut request) = valid_transaction();
    let seed_record =
        build_evidence_record_from_transaction(&request).expect("seed record should build");
    ledger
        .append(seed_record)
        .expect("seed append should succeed");
    ledger.summary.entry_count = 99;

    request.transaction_id = "   ".to_string();
    request.target_evidence_ledger_id.clear();
    request.preflight_request.non_claims.clear();
    request.preflight_report.validation.valid = false;
    request.preflight_report.mutates_accepted_evidence_ledger = true;

    let kinds = issue_kinds(&request, &ledger);
    assert!(kinds.contains(&AcceptedLedgerAppendTransactionIssueKind::EmptyIdentity));
    assert!(kinds.contains(&AcceptedLedgerAppendTransactionIssueKind::InvalidLedger));
    assert!(kinds.contains(&AcceptedLedgerAppendTransactionIssueKind::InvalidPreflight));
    assert!(kinds.contains(&AcceptedLedgerAppendTransactionIssueKind::PreflightReportMismatch));
}

#[test]
fn transaction_rejects_preview_source_and_single_entry_drift() {
    let (ledger, mut request) = valid_transaction();
    request.preflight_request.append_preview.source_candidate_id =
        "phase_201_wrong_candidate".to_string();
    request
        .preflight_request
        .append_preview
        .proposed_append_entries
        .clear();

    let kinds = issue_kinds(&request, &ledger);
    assert!(
        kinds
            .iter()
            .filter(
                |kind| **kind == AcceptedLedgerAppendTransactionIssueKind::CandidatePreviewMismatch
            )
            .count()
            >= 2
    );
}

#[test]
fn transaction_rejects_preview_entry_metadata_drift() {
    let (ledger, mut request) = valid_transaction();
    let entry = &mut request
        .preflight_request
        .append_preview
        .proposed_append_entries[0];
    entry.candidate_id = "phase_201_wrong_entry_candidate".to_string();
    entry.proposed_evidence_class = EvidenceClass::DesignNote;
    entry.proposed_claim_boundary = ClaimBoundary::Level0DesignNote;

    let kinds = issue_kinds(&request, &ledger);
    assert!(
        kinds
            .iter()
            .filter(
                |kind| **kind == AcceptedLedgerAppendTransactionIssueKind::CandidatePreviewMismatch
            )
            .count()
            >= 3
    );
}

#[test]
fn transaction_rejects_missing_source_digests_and_record_conversion_fails() {
    let (ledger, mut request) = valid_transaction();
    request.preflight_request.source_artifact_digests.clear();
    request.preflight_report =
        build_reviewed_promotion_preflight_report(&request.preflight_request);

    let kinds = issue_kinds(&request, &ledger);
    assert!(kinds.contains(&AcceptedLedgerAppendTransactionIssueKind::MissingArtifactDigest));

    let error = build_evidence_record_from_transaction(&request)
        .expect_err("missing source digest should reject record construction");
    assert!(error
        .to_string()
        .contains("at least one source artifact digest"));
}

#[test]
fn transaction_rejects_forbidden_free_text_notes() {
    let (ledger, mut request) = valid_transaction();
    request
        .notes
        .push("verified benchmark result is not permitted here".to_string());

    let kinds = issue_kinds(&request, &ledger);
    assert!(kinds.contains(&AcceptedLedgerAppendTransactionIssueKind::ForbiddenClaimText));
}

#[test]
fn post_append_validation_rejects_forbidden_transaction_id_record_note() {
    let (mut ledger, mut request) = valid_transaction();
    request.transaction_id = "verified benchmark result".to_string();

    let error = apply_accepted_ledger_append_transaction(&request, &mut ledger)
        .expect_err("post-append ledger validation should reject forbidden record note");
    assert!(error.to_string().contains("post_validation"));
    assert_eq!(ledger.entries.len(), 1);
    assert!(!ledger.validate().valid);
}

#[test]
fn transaction_reports_all_current_tip_mismatch_paths() {
    let (ledger, mut request) = valid_transaction();
    request.expected_current_ledger_tip = Some(digest("request stale tip"));
    request.preflight_request.expected_current_ledger_tip = Some(digest("preflight stale tip"));
    request
        .preflight_request
        .append_preview
        .transaction_preview
        .current_ledger_digest = Some(digest("preview stale tip"));

    let kinds = issue_kinds(&request, &ledger);
    assert_eq!(
        kinds
            .iter()
            .filter(|kind| **kind == AcceptedLedgerAppendTransactionIssueKind::StaleLedgerTip)
            .count(),
        3
    );
}

use std::path::Path;

use zkbench_core::{
    apply_accepted_ledger_append_transaction,
    apply_materialized_accepted_ledger_append_transaction,
    build_reviewed_promotion_preflight_report, compute_artifact_digest_bytes,
    create_evidence_append_preview, create_evidence_record_candidate,
    required_reviewed_promotion_preflight_non_claims, review_evidence_append_proposal,
    validate_accepted_ledger_append_transaction_request, AcceptedLedgerAppendTransactionIssueKind,
    AcceptedLedgerAppendTransactionRequest, AcceptedLedgerAppendTransactionVersion, ArtifactDigest,
    ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceAcceptancePolicy,
    EvidenceAppendPreviewStatus, EvidenceClass, EvidenceLedger, EvidenceReviewChecklist,
    EvidenceReviewDecisionKind, EvidenceReviewerRole, MaterializedAcceptedLedgerAppendRequest,
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

fn transaction_for_ledger(ledger: &EvidenceLedger) -> AcceptedLedgerAppendTransactionRequest {
    let preflight_request = valid_preflight_request(ledger);
    let preflight_report = build_reviewed_promotion_preflight_report(&preflight_request);
    assert!(
        preflight_report.validation.valid,
        "{:?}",
        preflight_report.validation.issues
    );

    AcceptedLedgerAppendTransactionRequest {
        transaction_id: format!("accepted_append_tx_local_level1_{}", ledger.entries.len()),
        version: AcceptedLedgerAppendTransactionVersion::default(),
        target_evidence_ledger_id: "accepted-ledger-local-fixture".to_string(),
        expected_current_ledger_tip: preflight_request.expected_current_ledger_tip.clone(),
        preflight_request,
        preflight_report,
        notes: vec!["local append transaction stays below Level2".to_string()],
    }
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
fn materialized_transaction_creates_and_then_appends_local_ledger_json() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let (_, first_transaction) = valid_transaction();
    let first_request = MaterializedAcceptedLedgerAppendRequest {
        ledger_path: ledger_path.clone(),
        create_if_missing: true,
        transaction: first_transaction,
    };

    let first_report = apply_materialized_accepted_ledger_append_transaction(&first_request)
        .expect("first materialized append should create ledger");
    assert_eq!(first_report.appended_sequence_number, Some(0));
    let first_ledger = EvidenceLedger::load_json(&ledger_path).expect("ledger should load");
    assert_eq!(first_ledger.entries.len(), 1);
    assert!(first_ledger.validate().valid);

    let second_transaction = transaction_for_ledger(&first_ledger);
    let second_request = MaterializedAcceptedLedgerAppendRequest {
        ledger_path: ledger_path.clone(),
        create_if_missing: false,
        transaction: second_transaction,
    };
    let second_report = apply_materialized_accepted_ledger_append_transaction(&second_request)
        .expect("second materialized append should extend ledger");
    assert_eq!(second_report.appended_sequence_number, Some(1));
    let second_ledger = EvidenceLedger::load_json(&ledger_path).expect("ledger should reload");
    assert_eq!(second_ledger.entries.len(), 2);
    assert!(second_ledger.validate().valid);
}

#[test]
fn materialized_transaction_rejects_missing_file_without_create() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("missing-ledger.json");
    let (_, transaction) = valid_transaction();
    let request = MaterializedAcceptedLedgerAppendRequest {
        ledger_path: ledger_path.clone(),
        create_if_missing: false,
        transaction,
    };

    let error = apply_materialized_accepted_ledger_append_transaction(&request)
        .expect_err("missing ledger without create should reject");
    assert!(error.to_string().contains("create_if_missing is false"));
    assert!(!ledger_path.exists());
}

#[test]
fn materialized_transaction_rejects_missing_parent_directory() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let (_, transaction) = valid_transaction();
    let request = MaterializedAcceptedLedgerAppendRequest {
        ledger_path: dir.path().join("missing").join("accepted-ledger.json"),
        create_if_missing: true,
        transaction,
    };

    let error = apply_materialized_accepted_ledger_append_transaction(&request)
        .expect_err("missing parent directory should reject");
    assert!(error.to_string().contains("parent directory must exist"));
}

#[test]
fn materialized_transaction_rejects_directory_target() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger-directory");
    std::fs::create_dir(&ledger_path).expect("directory target should create");
    let (_, transaction) = valid_transaction();
    let request = MaterializedAcceptedLedgerAppendRequest {
        ledger_path,
        create_if_missing: false,
        transaction,
    };

    let error = apply_materialized_accepted_ledger_append_transaction(&request)
        .expect_err("directory target should reject");
    assert!(error.to_string().contains("must be a JSON file"));
}

#[test]
fn materialized_transaction_rejects_invalid_existing_ledger_json() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    std::fs::write(&ledger_path, b"{").expect("invalid ledger bytes should write");
    let (_, transaction) = valid_transaction();
    let request = MaterializedAcceptedLedgerAppendRequest {
        ledger_path: ledger_path.clone(),
        create_if_missing: false,
        transaction,
    };

    apply_materialized_accepted_ledger_append_transaction(&request)
        .expect_err("invalid existing ledger JSON should reject");
    assert_eq!(
        std::fs::read(&ledger_path).expect("invalid ledger should remain"),
        b"{"
    );
}

#[cfg(unix)]
#[test]
fn materialized_transaction_rejects_symlink_target() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let real_path = dir.path().join("real-ledger.json");
    let symlink_path = dir.path().join("accepted-ledger.json");
    std::fs::write(&real_path, b"{").expect("real target should write");
    std::os::unix::fs::symlink(&real_path, &symlink_path).expect("symlink should create");
    let (_, transaction) = valid_transaction();
    let request = MaterializedAcceptedLedgerAppendRequest {
        ledger_path: symlink_path,
        create_if_missing: false,
        transaction,
    };

    let error = apply_materialized_accepted_ledger_append_transaction(&request)
        .expect_err("symlink ledger path should reject");
    assert!(error.to_string().contains("must not be a symlink"));
}

#[test]
fn materialized_transaction_rejects_stale_existing_ledger_without_repair() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let mut existing_ledger = EvidenceLedger::new();
    let (_, first_transaction) = valid_transaction();
    apply_accepted_ledger_append_transaction(&first_transaction, &mut existing_ledger)
        .expect("seed append should work");
    existing_ledger
        .save_json(&ledger_path)
        .expect("seed ledger should save");

    let (_, stale_transaction) = valid_transaction();
    let request = MaterializedAcceptedLedgerAppendRequest {
        ledger_path: ledger_path.clone(),
        create_if_missing: false,
        transaction: stale_transaction,
    };

    let error = apply_materialized_accepted_ledger_append_transaction(&request)
        .expect_err("stale transaction should reject existing ledger");
    assert!(error.to_string().contains("StaleLedgerTip"));
    let reloaded = EvidenceLedger::load_json(&ledger_path).expect("ledger should still load");
    assert_eq!(reloaded, existing_ledger);
}

#[test]
fn materialized_transaction_rejects_parent_directory_path_components() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let (_, transaction) = valid_transaction();
    let request = MaterializedAcceptedLedgerAppendRequest {
        ledger_path: dir.path().join("nested").join("..").join("ledger.json"),
        create_if_missing: true,
        transaction,
    };

    let error = apply_materialized_accepted_ledger_append_transaction(&request)
        .expect_err("parent-directory component should reject");
    assert!(error.to_string().contains("parent-directory components"));
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

#[test]
fn materialized_accepted_append_source_scan_exposes_no_runtime_or_submission_surface() {
    let source_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("evidence")
        .join("accepted_append_output.rs");
    let source = std::fs::read_to_string(source_path).expect("source should read");

    for forbidden in [
        "std::process",
        "Command::new",
        "std::net",
        "TcpStream",
        "reqwest",
        "ureq",
        "submit_to_",
        "http://",
        "https://",
    ] {
        assert!(
            !source.contains(forbidden),
            "materialized accepted append must not expose {forbidden}"
        );
    }
    assert!(source.contains("EvidenceLedger::load_json"));
    assert!(source.contains("ledger.save_json"));
}

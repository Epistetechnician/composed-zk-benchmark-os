use std::path::{Path, PathBuf};

use zkbench_core::{
    apply_materialized_accepted_ledger_append_transaction,
    build_reviewed_promotion_preflight_report, create_evidence_append_preview,
    create_evidence_record_candidate, required_reviewed_promotion_preflight_non_claims,
    review_evidence_append_proposal, AcceptedLedgerAppendTransactionRequest,
    AcceptedLedgerAppendTransactionVersion, ArtifactDigest, ClaimBoundary,
    EvidenceAcceptancePolicy, EvidenceAppendPreviewStatus, EvidenceClass, EvidenceLedger,
    EvidenceReviewChecklist, EvidenceReviewDecisionKind, EvidenceReviewerRole,
    MaterializedAcceptedLedgerAppendRequest, ReviewedPromotionPreflightRequest,
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

fn preflight_request(ledger: &EvidenceLedger) -> ReviewedPromotionPreflightRequest {
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
        id: "phase_184_local_preflight_for_append".to_string(),
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

fn transaction_for_ledger(ledger: &EvidenceLedger) -> AcceptedLedgerAppendTransactionRequest {
    let preflight_request = preflight_request(ledger);
    let preflight_report = build_reviewed_promotion_preflight_report(&preflight_request);
    assert!(
        preflight_report.validation.valid,
        "{:?}",
        preflight_report.validation.issues
    );

    AcceptedLedgerAppendTransactionRequest {
        transaction_id: format!("phase_184_accepted_append_tx_{}", ledger.entries.len()),
        version: AcceptedLedgerAppendTransactionVersion::default(),
        target_evidence_ledger_id: "accepted-ledger-local-fixture".to_string(),
        expected_current_ledger_tip: preflight_request.expected_current_ledger_tip.clone(),
        preflight_request,
        preflight_report,
        notes: vec!["local append transaction stays below Level2".to_string()],
    }
}

fn request_for_path(
    ledger_path: PathBuf,
    create_if_missing: bool,
) -> MaterializedAcceptedLedgerAppendRequest {
    MaterializedAcceptedLedgerAppendRequest {
        ledger_path,
        create_if_missing,
        transaction: transaction_for_ledger(&EvidenceLedger::new()),
    }
}

#[test]
fn materialized_append_rejects_empty_and_bare_relative_paths_without_writing() {
    let empty = request_for_path(PathBuf::new(), true);
    let empty_error = apply_materialized_accepted_ledger_append_transaction(&empty)
        .expect_err("empty materialized ledger path should reject");
    assert!(empty_error.to_string().contains("must be non-empty"));

    let bare_relative_path = PathBuf::from("phase-184-accepted-ledger.json");
    assert!(!bare_relative_path.exists());
    let bare_relative = request_for_path(bare_relative_path.clone(), true);
    let bare_error = apply_materialized_accepted_ledger_append_transaction(&bare_relative)
        .expect_err("bare relative path has no existing parent directory");
    assert!(bare_error.to_string().contains("parent directory"));
    assert!(!bare_relative_path.exists());
}

#[test]
fn materialized_append_rejects_root_path_without_writing() {
    let root = request_for_path(PathBuf::from("/"), true);
    let error = apply_materialized_accepted_ledger_append_transaction(&root)
        .expect_err("root path has no materializable ledger parent");

    assert!(error
        .to_string()
        .contains("accepted ledger path must have a parent directory"));
}

#[test]
fn materialized_append_rejects_parseable_invalid_existing_ledger_without_repair() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let mut invalid_ledger = EvidenceLedger::new();
    invalid_ledger
        .notes
        .push("this is official benchmark evidence".to_string());
    assert!(!invalid_ledger.validate().valid);
    invalid_ledger
        .save_json(&ledger_path)
        .expect("parseable invalid ledger should save");

    let request = request_for_path(ledger_path.clone(), false);
    let error = apply_materialized_accepted_ledger_append_transaction(&request)
        .expect_err("parseable invalid ledger should reject before append");
    assert!(error
        .to_string()
        .contains("existing accepted ledger is invalid"));

    let reloaded =
        EvidenceLedger::load_json(&ledger_path).expect("invalid ledger remains readable");
    assert_eq!(reloaded, invalid_ledger);
}

#[test]
fn materialized_append_replaces_stale_temp_file_during_atomic_write() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let temp_path = dir.path().join(".accepted-ledger.json.tmp");
    std::fs::write(&temp_path, "stale temp bytes").expect("stale temp should write");

    let request = request_for_path(ledger_path.clone(), true);
    let report = apply_materialized_accepted_ledger_append_transaction(&request)
        .expect("stale temp should be removed before atomic write");
    assert_eq!(report.appended_sequence_number, Some(0));
    assert!(!temp_path.exists());
    let ledger = EvidenceLedger::load_json(&ledger_path).expect("ledger should load");
    assert_eq!(ledger.entries.len(), 1);
    assert!(ledger.validate().valid);
}

#[cfg(unix)]
#[test]
fn materialized_append_rejects_symlink_parent_directory() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let real_parent = dir.path().join("real-parent");
    let symlink_parent = dir.path().join("symlink-parent");
    std::fs::create_dir(&real_parent).expect("real parent should create");
    std::os::unix::fs::symlink(&real_parent, &symlink_parent)
        .expect("parent symlink should create");

    let request = request_for_path(symlink_parent.join("accepted-ledger.json"), true);
    let error = apply_materialized_accepted_ledger_append_transaction(&request)
        .expect_err("symlink parent should reject before write");
    assert!(error.to_string().contains("must not be a symlink"));
    assert!(!real_parent.join("accepted-ledger.json").exists());
}

#[test]
fn materialized_append_source_scan_keeps_atomic_json_only_boundary_visible() {
    let source_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("evidence")
        .join("accepted_append_output.rs");
    let source = std::fs::read_to_string(source_path).expect("source should read");

    for required in [
        "validate_ledger_path(&request.ledger_path)?",
        "load_or_create_ledger",
        "write_ledger_atomically",
        "fs::remove_file(&temp_path)",
        "ledger.save_json(&temp_path)?",
        "fs::rename(&temp_path, path)",
        "reject_symlink(parent)?",
    ] {
        assert!(
            source.contains(required),
            "materialized append output should expose {required}"
        );
    }
}

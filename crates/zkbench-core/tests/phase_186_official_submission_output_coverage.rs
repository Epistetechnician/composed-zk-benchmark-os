use std::{
    fs,
    path::{Path, PathBuf},
};

use zkbench_core::{
    apply_accepted_ledger_append_transaction, build_reviewed_promotion_preflight_report,
    compute_artifact_digest_bytes, create_evidence_append_preview,
    create_evidence_record_candidate, read_official_submission_package_outputs,
    required_reviewed_promotion_preflight_non_claims, review_evidence_append_proposal,
    validate_accepted_ledger_append_transaction_request, write_official_submission_package_outputs,
    AcceptedLedgerAppendTransactionRequest, AcceptedLedgerAppendTransactionVersion, ArtifactDigest,
    ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceAcceptancePolicy,
    EvidenceAppendPreviewStatus, EvidenceClass, EvidenceLedger, EvidenceReviewChecklist,
    EvidenceReviewDecisionKind, EvidenceReviewerRole, OfficialSubmissionPackageMetadata,
    OfficialSubmissionPackageOutputRequest, OfficialSubmissionPackageOutputValidationReport,
    OfficialSubmissionPackageVersion, ReviewedPromotionPreflightRequest,
    ReviewedPromotionPreflightVersion, OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH,
    OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH, OFFICIAL_SUBMISSION_PACKAGE_METADATA_DIGEST_PATH,
    OFFICIAL_SUBMISSION_PACKAGE_METADATA_PATH, OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH,
    OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH,
};

fn digest(label: &str) -> ArtifactDigest {
    compute_artifact_digest_bytes(
        label.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

fn source_digests(candidate: &zkbench_core::EvidenceRecordCandidate) -> Vec<ArtifactDigest> {
    candidate
        .proposed_artifact_refs
        .iter()
        .map(|artifact| artifact.digest.clone())
        .collect()
}

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

fn reviewed_preflight_request() -> ReviewedPromotionPreflightRequest {
    let (candidate, decision) = candidate_and_decision();
    let ledger = EvidenceLedger::new();
    let append_preview =
        create_evidence_append_preview(&candidate, Some(&ledger)).expect("preview should build");
    assert_eq!(
        append_preview.status,
        EvidenceAppendPreviewStatus::PreviewOnly
    );

    ReviewedPromotionPreflightRequest {
        id: "phase_186_seed_preflight".to_string(),
        version: ReviewedPromotionPreflightVersion::default(),
        source_artifact_digests: source_digests(&candidate),
        candidate,
        append_preview,
        review_decision: decision,
        expected_current_ledger_tip: None,
        external_replay_provenance: Vec::new(),
        unresolved_quarantine_markers: Vec::new(),
        blocking_markers: Vec::new(),
        requested_evidence_class: EvidenceClass::LocalReplay,
        requested_claim_boundary: ClaimBoundary::Level1LocalReplay,
        populates_score_axes: false,
        official_submission_package_requested: false,
        accepted_evidence_ledger_entry_ids: Vec::new(),
        claim_text: vec!["metadata-only local continuation preflight".to_string()],
        non_claims: required_reviewed_promotion_preflight_non_claims()
            .into_iter()
            .map(str::to_string)
            .collect(),
    }
}

fn accepted_ledger_and_package() -> (EvidenceLedger, OfficialSubmissionPackageMetadata) {
    let mut ledger = EvidenceLedger::new();
    let preflight_request = reviewed_preflight_request();
    let preflight_report = build_reviewed_promotion_preflight_report(&preflight_request);
    assert!(
        preflight_report.validation.valid,
        "{:?}",
        preflight_report.validation.issues
    );
    let transaction = AcceptedLedgerAppendTransactionRequest {
        transaction_id: "phase_186_submission_package_seed_append".to_string(),
        version: AcceptedLedgerAppendTransactionVersion::default(),
        target_evidence_ledger_id: "accepted-ledger-local-fixture".to_string(),
        expected_current_ledger_tip: None,
        preflight_request,
        preflight_report,
        notes: vec!["local append transaction stays below Level2".to_string()],
    };
    let validation = validate_accepted_ledger_append_transaction_request(&transaction, &ledger);
    assert!(validation.valid, "{:?}", validation.issues);
    apply_accepted_ledger_append_transaction(&transaction, &mut ledger)
        .expect("seed accepted ledger append should work");

    let accepted_id = ledger.entries[0].entry_digest.hex_digest.clone();
    let package = OfficialSubmissionPackageMetadata {
        package_id: "phase_186_local_submission_package".to_string(),
        version: OfficialSubmissionPackageVersion::default(),
        benchmark_suite_id: "zkbench-local-suite".to_string(),
        backend_id: "external-backend-fixture".to_string(),
        backend_version: "0.0.0-fixture".to_string(),
        source_pack_ids: vec!["pack_local_fixture".to_string()],
        external_replay_environment_provenance: vec![
            "environment provenance digest declared by reviewed evidence".to_string(),
        ],
        artifact_digests: vec![digest("submission artifact")],
        accepted_evidence_ledger_entry_ids: vec![accepted_id],
        review_decision_ids: vec!["review_decision_fixture".to_string()],
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        non_claims: required_reviewed_promotion_preflight_non_claims()
            .into_iter()
            .map(str::to_string)
            .collect(),
        reproduction_instructions: vec!["reproduce from declared package inputs".to_string()],
        known_limitations: vec!["scope is limited to reviewed entry ids".to_string()],
        submits_to_official_endpoint: false,
    };
    (ledger, package)
}

fn write_accepted_ledger(path: &Path) -> (EvidenceLedger, OfficialSubmissionPackageMetadata) {
    let (ledger, package) = accepted_ledger_and_package();
    ledger.save_json(path).expect("accepted ledger should save");
    (ledger, package)
}

fn request(
    output_root: PathBuf,
    accepted_ledger_path: PathBuf,
    package: OfficialSubmissionPackageMetadata,
    overwrite: bool,
) -> OfficialSubmissionPackageOutputRequest {
    OfficialSubmissionPackageOutputRequest {
        output_root,
        accepted_ledger_path,
        package,
        protected_paths: Vec::new(),
        overwrite,
    }
}

fn write_package_output(dir: &tempfile::TempDir) -> (PathBuf, OfficialSubmissionPackageMetadata) {
    let ledger_path = dir.path().join("accepted-ledger.json");
    let output_root = dir.path().join("package-output");
    let (_, package) = write_accepted_ledger(&ledger_path);
    write_official_submission_package_outputs(&request(
        output_root.clone(),
        ledger_path,
        package.clone(),
        false,
    ))
    .expect("package output should write");
    (output_root, package)
}

fn write_file_with_digest(
    output_root: &Path,
    relative_path: &str,
    digest_path: &str,
    bytes: &[u8],
) {
    let file_digest =
        compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report));
    fs::write(output_root.join(relative_path), bytes).expect("declared file should update");
    fs::write(
        output_root.join(digest_path),
        format!("{}\n", file_digest.hex_digest).as_bytes(),
    )
    .expect("digest sidecar should update");
}

fn validation_report(output_root: &Path) -> OfficialSubmissionPackageOutputValidationReport {
    let bytes = fs::read(output_root.join(OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH))
        .expect("validation report should read");
    serde_json::from_slice(&bytes).expect("validation report should parse")
}

fn write_validation_report(
    output_root: &Path,
    report: &OfficialSubmissionPackageOutputValidationReport,
) {
    let bytes = serde_json::to_vec_pretty(report).expect("validation report should serialize");
    write_file_with_digest(
        output_root,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH,
        &bytes,
    );
}

#[test]
fn official_submission_output_rejects_output_root_shape_preconditions() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let (_, package) = write_accepted_ledger(&ledger_path);

    let empty_root = request(PathBuf::new(), ledger_path.clone(), package.clone(), false);
    let empty_error = write_official_submission_package_outputs(&empty_root)
        .expect_err("empty output root should reject");
    assert!(empty_error
        .to_string()
        .contains("output root must be non-empty"));

    let parent_root = request(
        dir.path().join("child/../package-output"),
        ledger_path.clone(),
        package.clone(),
        false,
    );
    let parent_error = write_official_submission_package_outputs(&parent_root)
        .expect_err("parent-directory output root should reject");
    assert!(parent_error
        .to_string()
        .contains("output root must not contain parent-directory components"));

    let protected_parent = OfficialSubmissionPackageOutputRequest {
        output_root: dir.path().join("package-output"),
        accepted_ledger_path: ledger_path.clone(),
        package: package.clone(),
        protected_paths: vec![dir.path().join("safe/../protected")],
        overwrite: false,
    };
    let protected_error = write_official_submission_package_outputs(&protected_parent)
        .expect_err("parent-directory protected path should reject");
    assert!(protected_error
        .to_string()
        .contains("protected path must not contain parent-directory components"));

    let output_file = dir.path().join("package-output-file");
    fs::write(&output_file, b"not a directory").expect("output file should write");
    let file_error = write_official_submission_package_outputs(&request(
        output_file,
        ledger_path.clone(),
        package.clone(),
        false,
    ))
    .expect_err("existing output file should reject");
    assert!(file_error
        .to_string()
        .contains("output root is an existing file"));

    let non_empty_root = dir.path().join("non-empty-package-output");
    fs::create_dir_all(&non_empty_root).expect("output root should create");
    fs::write(non_empty_root.join("placeholder.txt"), b"occupied")
        .expect("placeholder should write");
    let overwrite_error = write_official_submission_package_outputs(&request(
        non_empty_root,
        ledger_path,
        package,
        false,
    ))
    .expect_err("non-empty output root without overwrite should reject");
    assert!(overwrite_error
        .to_string()
        .contains("explicit overwrite is required"));
}

#[test]
fn official_submission_output_rejects_accepted_ledger_path_edges() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let (ledger, package) = write_accepted_ledger(&ledger_path);

    let ledger_dir = dir.path().join("accepted-ledger-dir");
    fs::create_dir_all(&ledger_dir).expect("ledger dir should create");
    let dir_error = write_official_submission_package_outputs(&request(
        dir.path().join("package-output-ledger-dir"),
        ledger_dir,
        package.clone(),
        false,
    ))
    .expect_err("accepted ledger directory should reject");
    assert!(dir_error
        .to_string()
        .contains("accepted ledger path must be a JSON file, not a directory"));

    let parent_ledger_error = write_official_submission_package_outputs(&request(
        dir.path().join("package-output-parent-ledger"),
        dir.path().join("ledger-parent/../accepted-ledger.json"),
        package.clone(),
        false,
    ))
    .expect_err("accepted ledger parent-directory path should reject");
    assert!(parent_ledger_error
        .to_string()
        .contains("accepted ledger path must not contain parent-directory components"));

    let invalid_ledger_path = dir.path().join("invalid-accepted-ledger.json");
    let mut invalid_ledger = ledger;
    invalid_ledger
        .notes
        .push("this is official benchmark evidence".to_string());
    assert!(!invalid_ledger.validate().valid);
    invalid_ledger
        .save_json(&invalid_ledger_path)
        .expect("invalid ledger should save");
    let invalid_error = write_official_submission_package_outputs(&request(
        dir.path().join("package-output-invalid-ledger"),
        invalid_ledger_path,
        package,
        false,
    ))
    .expect_err("parseable invalid accepted ledger should reject");
    assert!(invalid_error
        .to_string()
        .contains("accepted ledger is invalid"));
}

#[test]
fn official_submission_readback_rejects_digest_consistent_semantic_drift() {
    let markdown_dir = tempfile::tempdir().expect("tempdir should be available");
    let (markdown_root, _) = write_package_output(&markdown_dir);
    write_file_with_digest(
        &markdown_root,
        OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH,
        b"# Changed package markdown\n",
    );
    let markdown_error = read_official_submission_package_outputs(&markdown_root, &[])
        .expect_err("digest-consistent markdown drift should reject");
    assert!(markdown_error
        .to_string()
        .contains("package Markdown does not match package metadata"));

    let package_id_dir = tempfile::tempdir().expect("tempdir should be available");
    let (package_id_root, _) = write_package_output(&package_id_dir);
    let mut report = validation_report(&package_id_root);
    report.package_id = "different-package-id".to_string();
    write_validation_report(&package_id_root, &report);
    let package_id_error = read_official_submission_package_outputs(&package_id_root, &[])
        .expect_err("validation report package id drift should reject");
    assert!(package_id_error
        .to_string()
        .contains("validation report package id does not match package metadata"));

    let side_effect_dir = tempfile::tempdir().expect("tempdir should be available");
    let (side_effect_root, _) = write_package_output(&side_effect_dir);
    let mut report = validation_report(&side_effect_root);
    report.creates_official_submission = true;
    write_validation_report(&side_effect_root, &report);
    let side_effect_error = read_official_submission_package_outputs(&side_effect_root, &[])
        .expect_err("validation report side effect claim should reject");
    assert!(side_effect_error
        .to_string()
        .contains("external submission or score-axis side effect"));
}

#[test]
fn official_submission_readback_rejects_non_utf8_declared_files() {
    let metadata_dir = tempfile::tempdir().expect("tempdir should be available");
    let (metadata_root, _) = write_package_output(&metadata_dir);
    write_file_with_digest(
        &metadata_root,
        OFFICIAL_SUBMISSION_PACKAGE_METADATA_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_METADATA_DIGEST_PATH,
        b"\xff",
    );
    let metadata_error = read_official_submission_package_outputs(&metadata_root, &[])
        .expect_err("non-UTF8 metadata should reject");
    assert!(metadata_error
        .to_string()
        .contains("package metadata JSON is not UTF-8"));

    let markdown_dir = tempfile::tempdir().expect("tempdir should be available");
    let (markdown_root, _) = write_package_output(&markdown_dir);
    write_file_with_digest(
        &markdown_root,
        OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH,
        b"\xff",
    );
    let markdown_error = read_official_submission_package_outputs(&markdown_root, &[])
        .expect_err("non-UTF8 markdown should reject");
    assert!(markdown_error
        .to_string()
        .contains("package Markdown is not UTF-8"));

    let validation_dir = tempfile::tempdir().expect("tempdir should be available");
    let (validation_root, _) = write_package_output(&validation_dir);
    write_file_with_digest(
        &validation_root,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH,
        b"\xff",
    );
    let validation_error = read_official_submission_package_outputs(&validation_root, &[])
        .expect_err("non-UTF8 validation report should reject");
    assert!(validation_error
        .to_string()
        .contains("validation report JSON is not UTF-8"));
}

#[test]
fn official_submission_readback_rejects_directory_and_missing_declared_files() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let file_root = dir.path().join("not-a-directory");
    fs::write(&file_root, b"plain file").expect("file root should write");
    let file_root_error = read_official_submission_package_outputs(&file_root, &[])
        .expect_err("file output root should reject on read");
    assert!(file_root_error
        .to_string()
        .contains("output root must be a directory"));

    let missing_dir = tempfile::tempdir().expect("tempdir should be available");
    let (missing_root, _) = write_package_output(&missing_dir);
    fs::remove_file(missing_root.join(OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH))
        .expect("validation report should remove");
    let missing_error = read_official_submission_package_outputs(&missing_root, &[])
        .expect_err("missing declared validation report should reject");
    assert!(missing_error.to_string().contains("No such file"));
}

#[cfg(unix)]
#[test]
fn official_submission_readback_rejects_symlink_roots_and_declared_files() {
    use std::os::unix::fs::symlink;

    let root_dir = tempfile::tempdir().expect("tempdir should be available");
    let (real_root, _) = write_package_output(&root_dir);
    let symlink_root = root_dir.path().join("package-output-link");
    symlink(&real_root, &symlink_root).expect("output root symlink should create");
    let root_error = read_official_submission_package_outputs(&symlink_root, &[])
        .expect_err("symlink output root should reject");
    assert!(root_error.to_string().contains("must not be a symlink"));

    let file_dir = tempfile::tempdir().expect("tempdir should be available");
    let (file_root, _) = write_package_output(&file_dir);
    let real_markdown = file_dir.path().join("real-markdown.md");
    fs::write(&real_markdown, b"# Link target\n").expect("real markdown should write");
    fs::remove_file(file_root.join(OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH))
        .expect("package markdown should remove");
    symlink(
        &real_markdown,
        file_root.join(OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH),
    )
    .expect("declared file symlink should create");
    let file_error = read_official_submission_package_outputs(&file_root, &[])
        .expect_err("declared symlink file should reject");
    assert!(file_error.to_string().contains("must not be a symlink"));
}

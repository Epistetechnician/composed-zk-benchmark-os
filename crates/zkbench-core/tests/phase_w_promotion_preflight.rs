use std::path::Path;

use zkbench_core::{
    apply_accepted_ledger_append_transaction, build_reviewed_promotion_preflight_report,
    compute_artifact_digest_bytes, compute_official_submission_package_metadata_digest,
    compute_reviewed_promotion_preflight_report_digest, create_evidence_append_preview,
    create_evidence_record_candidate, deserialize_official_submission_package_metadata_json,
    deserialize_reviewed_promotion_preflight_report_json, read_official_submission_package_outputs,
    render_official_submission_package_markdown, render_reviewed_promotion_preflight_markdown,
    required_reviewed_promotion_preflight_non_claims, review_evidence_append_proposal,
    serialize_official_submission_package_metadata_json,
    serialize_reviewed_promotion_preflight_report_json,
    validate_accepted_ledger_append_transaction_request,
    validate_official_submission_package_metadata, validate_reviewed_promotion_preflight_request,
    write_official_submission_package_outputs, AcceptedLedgerAppendTransactionRequest,
    AcceptedLedgerAppendTransactionVersion, ArtifactDigest, ArtifactKind, ArtifactRole,
    ClaimBoundary, EvidenceAcceptancePolicy, EvidenceAppendPreviewStatus, EvidenceClass,
    EvidenceLedger, EvidenceReviewChecklist, EvidenceReviewDecisionKind, EvidenceReviewerRole,
    OfficialSubmissionPackageIssueKind, OfficialSubmissionPackageMetadata,
    OfficialSubmissionPackageOutputRequest, OfficialSubmissionPackageVersion,
    ReviewedPromotionPreflightIssueKind, ReviewedPromotionPreflightRequest,
    ReviewedPromotionPreflightVersion, OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH,
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

fn valid_request() -> ReviewedPromotionPreflightRequest {
    let (candidate, decision) = candidate_and_decision();
    let ledger = EvidenceLedger::new();
    let append_preview =
        create_evidence_append_preview(&candidate, Some(&ledger)).expect("preview should build");
    assert_eq!(
        append_preview.status,
        EvidenceAppendPreviewStatus::PreviewOnly
    );

    ReviewedPromotionPreflightRequest {
        id: "phase_w_local_preflight".to_string(),
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

fn digest(label: &str) -> ArtifactDigest {
    compute_artifact_digest_bytes(
        label.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )
}

fn valid_append_transaction() -> (EvidenceLedger, AcceptedLedgerAppendTransactionRequest) {
    let ledger = EvidenceLedger::new();
    let preflight_request = valid_request();
    let preflight_report = build_reviewed_promotion_preflight_report(&preflight_request);
    assert!(
        preflight_report.validation.valid,
        "{:?}",
        preflight_report.validation.issues
    );
    let request = AcceptedLedgerAppendTransactionRequest {
        transaction_id: "phase_w_submission_package_seed_append".to_string(),
        version: AcceptedLedgerAppendTransactionVersion::default(),
        target_evidence_ledger_id: "accepted-ledger-local-fixture".to_string(),
        expected_current_ledger_tip: preflight_request.expected_current_ledger_tip.clone(),
        preflight_request,
        preflight_report,
        notes: vec!["local append transaction stays below Level2".to_string()],
    };
    let validation = validate_accepted_ledger_append_transaction_request(&request, &ledger);
    assert!(validation.valid, "{:?}", validation.issues);
    (ledger, request)
}

fn accepted_ledger_and_package() -> (EvidenceLedger, OfficialSubmissionPackageMetadata) {
    let (mut ledger, transaction) = valid_append_transaction();
    apply_accepted_ledger_append_transaction(&transaction, &mut ledger)
        .expect("seed accepted ledger append should work");
    let accepted_id = ledger.entries[0].entry_digest.hex_digest.clone();
    let package = OfficialSubmissionPackageMetadata {
        package_id: "phase_w_local_submission_package".to_string(),
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

#[test]
fn promotion_preflight_report_is_metadata_only_and_deterministic() {
    let request = valid_request();
    let validation = validate_reviewed_promotion_preflight_request(&request);
    assert!(validation.valid, "{:?}", validation.issues);

    let report = build_reviewed_promotion_preflight_report(&request);
    assert!(report.validation.valid, "{:?}", report.validation.issues);
    assert!(!report.mutates_accepted_evidence_ledger);
    assert!(!report.creates_official_submission);
    assert!(!report.populates_score_axes);
    assert_eq!(report.claim_boundary, ClaimBoundary::Level0DesignNote);

    let first_digest =
        compute_reviewed_promotion_preflight_report_digest(&report).expect("digest should build");
    let second_digest =
        compute_reviewed_promotion_preflight_report_digest(&report).expect("digest should rebuild");
    assert_eq!(first_digest, second_digest);

    let json = serialize_reviewed_promotion_preflight_report_json(&report)
        .expect("report should serialize");
    let parsed =
        deserialize_reviewed_promotion_preflight_report_json(&json).expect("report should parse");
    assert_eq!(report, parsed);

    let markdown =
        render_reviewed_promotion_preflight_markdown(&report).expect("markdown should render");
    assert!(markdown.contains("Accepted Evidence Ledger mutation: `false`"));
    assert!(markdown.contains("Official submission created: `false`"));
    assert!(markdown.contains("Promotion preflight reports are not accepted evidence."));
}

#[test]
fn promotion_preflight_rejects_stale_append_preview_tip() {
    let mut request = valid_request();
    request.expected_current_ledger_tip = Some(digest("stale ledger tip"));

    let validation = validate_reviewed_promotion_preflight_request(&request);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == ReviewedPromotionPreflightIssueKind::StaleAppendPreview));
}

#[test]
fn promotion_preflight_rejects_local_only_level2_promotion() {
    let mut request = valid_request();
    request.requested_evidence_class = EvidenceClass::ReproducibleBenchmarkArtifact;
    request.requested_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;

    let validation = validate_reviewed_promotion_preflight_request(&request);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ReviewedPromotionPreflightIssueKind::MissingExternalReplayProvenance
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ReviewedPromotionPreflightIssueKind::LocalOnlyEvidencePromotion
    }));
}

#[test]
fn promotion_preflight_rejects_missing_human_review_and_score_population() {
    let mut request = valid_request();
    request.review_decision.reviewer_role = EvidenceReviewerRole::AutomatedPolicyCheck;
    request.populates_score_axes = true;

    let validation = validate_reviewed_promotion_preflight_request(&request);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ReviewedPromotionPreflightIssueKind::MissingHumanReviewApproval
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ReviewedPromotionPreflightIssueKind::ScoreAxisPopulationWithoutEvidenceClass
    }));
}

#[test]
fn promotion_preflight_rejects_submission_request_before_accepted_evidence() {
    let mut request = valid_request();
    request.official_submission_package_requested = true;

    let validation = validate_reviewed_promotion_preflight_request(&request);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ReviewedPromotionPreflightIssueKind::OfficialSubmissionBeforeAcceptedEvidence
    }));
}

#[test]
fn official_submission_metadata_requires_accepted_evidence_and_remains_inert() {
    let mut package = OfficialSubmissionPackageMetadata {
        package_id: "phase_w_submission_metadata".to_string(),
        version: OfficialSubmissionPackageVersion::default(),
        benchmark_suite_id: "zkbench-local-suite".to_string(),
        backend_id: "external-backend-fixture".to_string(),
        backend_version: "0.0.0-fixture".to_string(),
        source_pack_ids: vec!["pack_local_fixture".to_string()],
        external_replay_environment_provenance: vec![
            "environment provenance digest declared by reviewed evidence".to_string(),
        ],
        artifact_digests: vec![digest("submission artifact")],
        accepted_evidence_ledger_entry_ids: Vec::new(),
        review_decision_ids: vec!["review_decision_fixture".to_string()],
        claim_boundary: ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
        non_claims: required_reviewed_promotion_preflight_non_claims()
            .into_iter()
            .map(str::to_string)
            .collect(),
        reproduction_instructions: vec!["reproduce from declared package inputs".to_string()],
        known_limitations: vec!["scope is limited to reviewed entry ids".to_string()],
        submits_to_official_endpoint: false,
    };

    let missing = validate_official_submission_package_metadata(&package);
    assert!(!missing.valid);
    assert!(missing.issues.iter().any(|issue| {
        issue.kind == OfficialSubmissionPackageIssueKind::MissingAcceptedEvidence
    }));

    package
        .accepted_evidence_ledger_entry_ids
        .push("accepted-ledger-entry-fixture".to_string());
    let validation = validate_official_submission_package_metadata(&package);
    assert!(validation.valid, "{:?}", validation.issues);

    let first_digest = compute_official_submission_package_metadata_digest(&package)
        .expect("package digest should build");
    let second_digest = compute_official_submission_package_metadata_digest(&package)
        .expect("package digest should rebuild");
    assert_eq!(first_digest, second_digest);

    let json = serialize_official_submission_package_metadata_json(&package)
        .expect("package should serialize");
    let parsed =
        deserialize_official_submission_package_metadata_json(&json).expect("package should parse");
    assert_eq!(package, parsed);

    let markdown =
        render_official_submission_package_markdown(&package).expect("markdown should render");
    assert!(markdown.contains("Submitted to official endpoint: `false`"));
    assert!(markdown.contains("accepted-ledger-entry-fixture"));
}

#[test]
fn official_submission_package_outputs_write_read_declared_files_only() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let output_root = dir.path().join("package-output");
    let (ledger, package) = accepted_ledger_and_package();
    ledger
        .save_json(&ledger_path)
        .expect("accepted ledger should save");

    let request = OfficialSubmissionPackageOutputRequest {
        output_root: output_root.clone(),
        accepted_ledger_path: ledger_path.clone(),
        package: package.clone(),
        protected_paths: vec![ledger_path],
        overwrite: false,
    };
    let output =
        write_official_submission_package_outputs(&request).expect("package output should write");
    assert!(!output.validation_report.creates_official_submission);
    assert!(!output.validation_report.submits_to_official_endpoint);
    assert!(!output.validation_report.populates_score_axes);
    assert_eq!(
        output
            .validation_report
            .matched_accepted_evidence_ledger_entry_ids,
        package.accepted_evidence_ledger_entry_ids
    );

    let read = read_official_submission_package_outputs(&output_root, &request.protected_paths)
        .expect("package output should read");
    assert_eq!(output, read);
}

#[test]
fn official_submission_package_outputs_reject_missing_accepted_ledger() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let (_, package) = accepted_ledger_and_package();
    let request = OfficialSubmissionPackageOutputRequest {
        output_root: dir.path().join("package-output"),
        accepted_ledger_path: dir.path().join("missing-ledger.json"),
        package,
        protected_paths: Vec::new(),
        overwrite: false,
    };

    let error = write_official_submission_package_outputs(&request)
        .expect_err("missing accepted ledger should reject");
    assert!(error
        .to_string()
        .contains("accepted ledger file is missing"));
}

#[test]
fn official_submission_package_outputs_reject_absent_accepted_evidence_id() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let (ledger, mut package) = accepted_ledger_and_package();
    ledger
        .save_json(&ledger_path)
        .expect("accepted ledger should save");
    package.accepted_evidence_ledger_entry_ids = vec!["absent-entry".to_string()];
    let request = OfficialSubmissionPackageOutputRequest {
        output_root: dir.path().join("package-output"),
        accepted_ledger_path: ledger_path,
        package,
        protected_paths: Vec::new(),
        overwrite: false,
    };

    let error = write_official_submission_package_outputs(&request)
        .expect_err("absent accepted evidence id should reject");
    assert!(error.to_string().contains("absent from accepted ledger"));
}

#[test]
fn official_submission_package_outputs_reject_external_submission_flag() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let (ledger, mut package) = accepted_ledger_and_package();
    ledger
        .save_json(&ledger_path)
        .expect("accepted ledger should save");
    package.submits_to_official_endpoint = true;
    let request = OfficialSubmissionPackageOutputRequest {
        output_root: dir.path().join("package-output"),
        accepted_ledger_path: ledger_path,
        package,
        protected_paths: Vec::new(),
        overwrite: false,
    };

    let error = write_official_submission_package_outputs(&request)
        .expect_err("external submission flag should reject");
    assert!(error.to_string().contains("ExternalSubmissionAttempted"));
}

#[test]
fn official_submission_package_outputs_reject_protected_overlap() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let (ledger, package) = accepted_ledger_and_package();
    ledger
        .save_json(&ledger_path)
        .expect("accepted ledger should save");
    let request = OfficialSubmissionPackageOutputRequest {
        output_root: dir.path().join("package-output"),
        accepted_ledger_path: ledger_path,
        package,
        protected_paths: vec![dir.path().to_path_buf()],
        overwrite: false,
    };

    let error = write_official_submission_package_outputs(&request)
        .expect_err("protected root overlap should reject");
    assert!(error.to_string().contains("overlaps protected path"));
}

#[test]
fn official_submission_package_outputs_reject_overwrite_package_drift() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let output_root = dir.path().join("package-output");
    let (ledger, package) = accepted_ledger_and_package();
    ledger
        .save_json(&ledger_path)
        .expect("accepted ledger should save");
    let request = OfficialSubmissionPackageOutputRequest {
        output_root: output_root.clone(),
        accepted_ledger_path: ledger_path.clone(),
        package,
        protected_paths: Vec::new(),
        overwrite: false,
    };
    write_official_submission_package_outputs(&request).expect("package output should write");

    let mut drifted_request = request.clone();
    drifted_request.package.review_decision_ids = vec!["different-review-decision".to_string()];
    drifted_request.overwrite = true;

    let error = write_official_submission_package_outputs(&drifted_request)
        .expect_err("overwrite drift should reject");
    assert!(error
        .to_string()
        .contains("does not match supplied package"));
}

#[test]
fn official_submission_package_outputs_reject_stale_digest_and_unexpected_files() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let ledger_path = dir.path().join("accepted-ledger.json");
    let output_root = dir.path().join("package-output");
    let (ledger, package) = accepted_ledger_and_package();
    ledger
        .save_json(&ledger_path)
        .expect("accepted ledger should save");
    let request = OfficialSubmissionPackageOutputRequest {
        output_root: output_root.clone(),
        accepted_ledger_path: ledger_path,
        package,
        protected_paths: Vec::new(),
        overwrite: false,
    };
    let output =
        write_official_submission_package_outputs(&request).expect("package output should write");

    std::fs::write(
        output_root.join(OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH),
        b"stale\n",
    )
    .expect("digest sidecar should tamper");
    let stale = read_official_submission_package_outputs(&output_root, &[])
        .expect_err("stale digest should reject");
    assert!(stale.to_string().contains("digest sidecar"));

    std::fs::write(
        output_root.join(OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH),
        format!("{}\n", output.package_markdown_digest.hex_digest).as_bytes(),
    )
    .expect("digest sidecar should restore");
    std::fs::write(
        output_root.join("official-submission-package/extra.txt"),
        b"extra",
    )
    .expect("extra file should write");
    let unexpected = read_official_submission_package_outputs(&output_root, &[])
        .expect_err("unexpected file should reject");
    assert!(unexpected
        .to_string()
        .contains("unexpected file or directory"));
}

#[test]
fn phase_w_source_scan_exposes_no_mutation_runtime_or_submission_surface() {
    let source_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("evidence")
        .join("promotion_preflight.rs");
    let source = std::fs::read_to_string(source_path).expect("source should read");

    for forbidden in [
        "std::process",
        "Command::new",
        "std::net",
        "TcpStream",
        "reqwest",
        "ureq",
        "EvidenceLedger::append",
        "append_with_policy",
        ".save_json(",
        "submit_to_",
        "http://",
        "https://",
    ] {
        assert!(
            !source.contains(forbidden),
            "Phase W preflight must not expose {forbidden}"
        );
    }
}

#[test]
fn official_submission_output_source_scan_exposes_no_endpoint_runtime_or_credentials() {
    let source_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("evidence")
        .join("official_submission_output.rs");
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
        "std::env::var",
    ] {
        assert!(
            !source.contains(forbidden),
            "official submission output must not expose {forbidden}"
        );
    }
    assert!(source.contains("EvidenceLedger::load_json"));
    assert!(source.contains("submits_to_official_endpoint: false"));
}

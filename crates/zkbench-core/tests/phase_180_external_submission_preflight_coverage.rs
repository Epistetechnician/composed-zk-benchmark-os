use std::{fs, path::Path};

use zkbench_core::{
    apply_accepted_ledger_append_transaction, build_external_replay_submission_preflight_report,
    build_reviewed_promotion_preflight_report, compute_artifact_digest_bytes,
    create_evidence_append_preview, create_evidence_record_candidate,
    deserialize_external_replay_submission_preflight_report_json,
    render_external_replay_submission_preflight_markdown,
    required_external_replay_submission_preflight_non_claims,
    required_reviewed_promotion_preflight_non_claims, review_evidence_append_proposal,
    validate_accepted_ledger_append_transaction_request,
    validate_external_replay_submission_preflight_request, AcceptedLedgerAppendTransactionRequest,
    AcceptedLedgerAppendTransactionVersion, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary, EvidenceAcceptancePolicy, EvidenceAppendPreviewStatus,
    EvidenceClass, EvidenceLedger, EvidenceReviewChecklist, EvidenceReviewDecisionKind,
    EvidenceReviewerRole, ExternalReplayBenchmarkTarget,
    ExternalReplaySubmissionPreflightIssueKind, ExternalReplaySubmissionPreflightRequest,
    ExternalReplaySubmissionPreflightVersion, OfficialSubmissionPackageMetadata,
    OfficialSubmissionPackageOutputRequest, OfficialSubmissionPackageOutputValidationReport,
    OfficialSubmissionPackageVersion, ReviewedPromotionPreflightRequest,
    ReviewedPromotionPreflightVersion, OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH,
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
        id: "phase_180_seed_preflight".to_string(),
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
        transaction_id: "phase_180_submission_package_seed_append".to_string(),
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
        package_id: "phase_180_local_submission_package".to_string(),
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

fn valid_external_replay_submission_preflight_request(
    dir: &tempfile::TempDir,
) -> ExternalReplaySubmissionPreflightRequest {
    let ledger_path = dir.path().join("accepted-ledger.json");
    let package_output_root = dir.path().join("package-output");
    let future_output_root = dir.path().join("external-replay-submission-output");
    let (ledger, package) = accepted_ledger_and_package();
    ledger
        .save_json(&ledger_path)
        .expect("accepted ledger should save");
    let output = zkbench_core::write_official_submission_package_outputs(
        &OfficialSubmissionPackageOutputRequest {
            output_root: package_output_root.clone(),
            accepted_ledger_path: ledger_path.clone(),
            package: package.clone(),
            protected_paths: Vec::new(),
            overwrite: false,
        },
    )
    .expect("package output should write");

    ExternalReplaySubmissionPreflightRequest {
        id: "phase_180_external_submission_preflight".to_string(),
        version: ExternalReplaySubmissionPreflightVersion::default(),
        accepted_ledger_path: ledger_path.clone(),
        package_output_root,
        expected_package_metadata_digest: output.package_metadata_digest,
        expected_validation_report_digest: output.validation_report_digest,
        benchmark_target: ExternalReplayBenchmarkTarget {
            benchmark_suite_id: package.benchmark_suite_id,
            backend_id: package.backend_id,
            backend_version: package.backend_version,
            target_label: "operator-selected-fixture-target".to_string(),
        },
        external_replay_provenance: vec![
            "future external replay provenance digest declared by operator".to_string(),
        ],
        source_artifact_digests: package.artifact_digests,
        operator_acknowledged: true,
        future_output_root,
        protected_paths: vec![ledger_path],
        overwrite: false,
        redaction_policy: vec![
            "retain digests and schemas only; exclude raw credentials, raw tokens, raw requests, raw responses, raw transcripts, and private operator configuration".to_string(),
        ],
        requested_evidence_class: EvidenceClass::ReproducibleBenchmarkArtifact,
        requested_claim_boundary: ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
        populates_score_axes: false,
        official_endpoint_submission_requested: false,
        unresolved_quarantine_markers: Vec::new(),
        blocking_markers: Vec::new(),
        claim_text: vec!["local preflight only; no endpoint submission".to_string()],
        non_claims: required_external_replay_submission_preflight_non_claims()
            .into_iter()
            .map(str::to_string)
            .collect(),
    }
}

fn write_file_with_digest(
    output_root: &Path,
    relative_path: &str,
    digest_path: &str,
    bytes: &[u8],
) {
    let file_digest =
        compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report));
    fs::write(output_root.join(relative_path), bytes).expect("file should update");
    fs::write(
        output_root.join(digest_path),
        format!("{}\n", file_digest.hex_digest).as_bytes(),
    )
    .expect("digest sidecar should update");
}

fn issue_kinds(
    validation: &zkbench_core::ExternalReplaySubmissionPreflightValidation,
) -> Vec<ExternalReplaySubmissionPreflightIssueKind> {
    validation.issues.iter().map(|issue| issue.kind).collect()
}

#[test]
fn preflight_reports_aggregate_request_shape_rejections() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_submission_preflight_request(&dir);
    request.id = "  ".to_string();
    request.benchmark_target.benchmark_suite_id.clear();
    request.benchmark_target.backend_id.clear();
    request.benchmark_target.backend_version.clear();
    request.benchmark_target.target_label.clear();
    request.external_replay_provenance.clear();
    request.source_artifact_digests = vec![ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Unsupported,
        hex_digest: "short".to_string(),
        byte_len: 5,
        kind: Some(ArtifactKind::Other),
        role: Some(ArtifactRole::Report),
    }];
    request.redaction_policy.clear();
    request
        .unresolved_quarantine_markers
        .push("quarantine:raw-output".to_string());
    request
        .blocking_markers
        .push("review:missing-human-signoff".to_string());
    request
        .claim_text
        .push("SOTA leaderboard and production ready claim".to_string());
    request.non_claims.pop();

    let validation = validate_external_replay_submission_preflight_request(&request);
    assert!(!validation.valid);
    let kinds = issue_kinds(&validation);
    assert_eq!(
        kinds
            .iter()
            .filter(|kind| **kind == ExternalReplaySubmissionPreflightIssueKind::EmptyIdentity)
            .count(),
        5
    );
    for expected in [
        ExternalReplaySubmissionPreflightIssueKind::MissingExternalReplayProvenance,
        ExternalReplaySubmissionPreflightIssueKind::MissingSourceArtifactDigest,
        ExternalReplaySubmissionPreflightIssueKind::MissingRedactionPolicy,
        ExternalReplaySubmissionPreflightIssueKind::UnresolvedBlockingMarker,
        ExternalReplaySubmissionPreflightIssueKind::MissingRequiredNonClaim,
        ExternalReplaySubmissionPreflightIssueKind::ForbiddenClaimText,
    ] {
        assert!(
            kinds.contains(&expected),
            "missing {expected:?}: {validation:?}"
        );
    }

    let mut report = build_external_replay_submission_preflight_report(&request);
    report.non_claims.pop();
    let markdown = render_external_replay_submission_preflight_markdown(&report)
        .expect_err("missing report non-claims should fail markdown rendering");
    assert!(markdown.to_string().contains("missing required non-claim"));
}

#[test]
fn preflight_rejects_accepted_ledger_path_variants_without_external_effects() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_submission_preflight_request(&dir);

    request.accepted_ledger_path = dir.path().join("missing-ledger.json");
    let missing = validate_external_replay_submission_preflight_request(&request);
    assert!(issue_kinds(&missing)
        .contains(&ExternalReplaySubmissionPreflightIssueKind::InvalidAcceptedLedger));

    let ledger_dir = dir.path().join("ledger-dir");
    fs::create_dir(&ledger_dir).expect("ledger directory should create");
    request.accepted_ledger_path = ledger_dir;
    let directory = validate_external_replay_submission_preflight_request(&request);
    assert!(issue_kinds(&directory)
        .contains(&ExternalReplaySubmissionPreflightIssueKind::InvalidAcceptedLedger));

    let malformed = dir.path().join("malformed-ledger.json");
    fs::write(&malformed, b"{").expect("malformed ledger should write");
    request.accepted_ledger_path = malformed;
    let malformed_validation = validate_external_replay_submission_preflight_request(&request);
    assert!(issue_kinds(&malformed_validation)
        .contains(&ExternalReplaySubmissionPreflightIssueKind::InvalidAcceptedLedger));

    request.accepted_ledger_path = dir.path().join("nested/../accepted-ledger.json");
    let parent_component = validate_external_replay_submission_preflight_request(&request);
    assert!(parent_component.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::InvalidAcceptedLedger
            && issue.message.contains("parent-directory")
    }));
}

#[test]
fn preflight_rejects_future_output_root_safety_edges() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_submission_preflight_request(&dir);

    request.future_output_root = Path::new("").to_path_buf();
    let empty = validate_external_replay_submission_preflight_request(&request);
    assert!(
        issue_kinds(&empty).contains(&ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot)
    );

    let file_dir = tempfile::tempdir().expect("tempdir should be available");
    request = valid_external_replay_submission_preflight_request(&file_dir);
    request.future_output_root = dir.path().join("future-file");
    fs::write(&request.future_output_root, b"file").expect("future file should write");
    let file_root = validate_external_replay_submission_preflight_request(&request);
    assert!(file_root.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot
            && issue.message.contains("existing file")
    }));

    let non_empty_dir = tempfile::tempdir().expect("tempdir should be available");
    request = valid_external_replay_submission_preflight_request(&non_empty_dir);
    request.future_output_root = dir.path().join("non-empty-output");
    fs::create_dir(&request.future_output_root).expect("future directory should create");
    fs::write(request.future_output_root.join("existing.txt"), b"existing")
        .expect("existing output file should write");
    let non_empty = validate_external_replay_submission_preflight_request(&request);
    assert!(non_empty.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot
            && issue.message.contains("explicit overwrite")
    }));

    request.overwrite = true;
    let overwrite = validate_external_replay_submission_preflight_request(&request);
    assert!(
        !issue_kinds(&overwrite)
            .contains(&ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot),
        "{overwrite:?}"
    );

    let parent_dir = tempfile::tempdir().expect("tempdir should be available");
    request = valid_external_replay_submission_preflight_request(&parent_dir);
    request.future_output_root = dir.path().join("safe/../escape");
    request
        .protected_paths
        .push(dir.path().join("protected/../ledger"));
    let parent_components = validate_external_replay_submission_preflight_request(&request);
    assert_eq!(
        parent_components
            .issues
            .iter()
            .filter(
                |issue| issue.kind == ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot
            )
            .count(),
        1
    );
}

#[test]
fn preflight_rejects_digest_consistent_package_ledger_drift() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_submission_preflight_request(&dir);
    let validation_path = request
        .package_output_root
        .join(OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH);
    let validation_json =
        fs::read_to_string(&validation_path).expect("validation report should read");
    let mut validation_report: OfficialSubmissionPackageOutputValidationReport =
        serde_json::from_str(&validation_json).expect("validation report should parse");
    validation_report.accepted_ledger_path = dir.path().join("different-ledger.json");
    validation_report.accepted_ledger_entry_count += 10;
    validation_report.matched_accepted_evidence_ledger_entry_ids =
        vec!["absent-accepted-evidence-id".to_string()];
    let tampered =
        serde_json::to_string_pretty(&validation_report).expect("validation report should render");
    write_file_with_digest(
        &request.package_output_root,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH,
        tampered.as_bytes(),
    );

    let validation = validate_external_replay_submission_preflight_request(&request);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::PackageDigestMismatch
            && issue.path == "request.expected_validation_report_digest"
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::InvalidPackageOutput
            && issue.path == "request.accepted_ledger_path"
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::InvalidPackageOutput
            && issue.message.contains("accepted ledger count")
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::InvalidPackageOutput
            && issue.message.contains("absent")
    }));
}

#[test]
fn malformed_preflight_report_json_reports_deserialization_context() {
    let error = deserialize_external_replay_submission_preflight_report_json("{")
        .expect_err("malformed preflight report JSON should reject");
    assert!(error
        .to_string()
        .contains("deserialize_external_replay_submission_preflight_report_json"));
}

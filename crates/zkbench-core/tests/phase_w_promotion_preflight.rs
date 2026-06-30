use std::{
    fs,
    path::{Path, PathBuf},
};

use zkbench_core::{
    apply_accepted_ledger_append_transaction, build_external_replay_submission_preflight_report,
    build_reviewed_promotion_preflight_report, compute_artifact_digest_bytes,
    compute_external_replay_submission_preflight_report_digest,
    compute_official_submission_package_metadata_digest,
    compute_reviewed_promotion_preflight_report_digest, create_evidence_append_preview,
    create_evidence_record_candidate, deserialize_external_replay_submission_preflight_report_json,
    deserialize_official_submission_package_metadata_json,
    deserialize_reviewed_promotion_preflight_report_json,
    read_external_replay_submission_preflight_outputs, read_official_submission_package_outputs,
    render_external_replay_submission_preflight_markdown,
    render_official_submission_package_markdown, render_reviewed_promotion_preflight_markdown,
    required_reviewed_promotion_preflight_non_claims, review_evidence_append_proposal,
    serialize_external_replay_submission_preflight_report_json,
    serialize_official_submission_package_metadata_json,
    serialize_reviewed_promotion_preflight_report_json,
    validate_accepted_ledger_append_transaction_request,
    validate_external_replay_submission_preflight_request,
    validate_official_submission_package_metadata, validate_reviewed_promotion_preflight_request,
    write_external_replay_submission_preflight_outputs, write_official_submission_package_outputs,
    AcceptedLedgerAppendTransactionRequest, AcceptedLedgerAppendTransactionVersion, ArtifactDigest,
    ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceAcceptancePolicy,
    EvidenceAppendPreviewStatus, EvidenceClass, EvidenceLedger, EvidenceReviewChecklist,
    EvidenceReviewDecisionKind, EvidenceReviewDecisionStatus, EvidenceReviewerRole,
    ExternalReplayBenchmarkTarget, ExternalReplaySubmissionPreflightIssueKind,
    ExternalReplaySubmissionPreflightOutputRequest, ExternalReplaySubmissionPreflightRequest,
    ExternalReplaySubmissionPreflightVersion, OfficialSubmissionPackageIssueKind,
    OfficialSubmissionPackageMetadata, OfficialSubmissionPackageOutputRequest,
    OfficialSubmissionPackageVersion, ReviewedPromotionPreflightIssueKind,
    ReviewedPromotionPreflightRequest, ReviewedPromotionPreflightVersion,
    EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
    EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
    EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH, EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH,
    EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH,
    EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_PATH,
    EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH,
    EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_PATH,
    EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH, EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH,
    EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH,
    EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_PATH,
    OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH,
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

fn write_external_preflight_file_with_digest(
    output_root: &Path,
    relative_path: &str,
    digest_path: &str,
    bytes: &[u8],
) {
    let file_digest =
        compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report));
    fs::write(output_root.join(relative_path), bytes).expect("materialized file should tamper");
    fs::write(
        output_root.join(digest_path),
        format!("{}\n", file_digest.hex_digest).as_bytes(),
    )
    .expect("digest sidecar should update");
}

fn external_preflight_non_claims_markdown(non_claims: &[String]) -> String {
    let mut markdown = "# External Replay Submission Preflight Non-Claims\n\n".to_string();
    for non_claim in non_claims {
        markdown.push_str("- ");
        markdown.push_str(non_claim);
        markdown.push('\n');
    }
    markdown
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
    let output =
        write_official_submission_package_outputs(&OfficialSubmissionPackageOutputRequest {
            output_root: package_output_root.clone(),
            accepted_ledger_path: ledger_path.clone(),
            package: package.clone(),
            protected_paths: Vec::new(),
            overwrite: false,
        })
        .expect("package output should write");

    ExternalReplaySubmissionPreflightRequest {
        id: "phase_w_external_submission_preflight".to_string(),
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
        non_claims: zkbench_core::required_external_replay_submission_preflight_non_claims()
            .into_iter()
            .map(str::to_string)
            .collect(),
    }
}

fn valid_external_replay_preflight_output_request(
    dir: &tempfile::TempDir,
) -> ExternalReplaySubmissionPreflightOutputRequest {
    let preflight_request = valid_external_replay_submission_preflight_request(dir);
    let preflight_report = build_external_replay_submission_preflight_report(&preflight_request);
    assert!(
        preflight_report.validation.valid,
        "{:?}",
        preflight_report.validation.issues
    );
    ExternalReplaySubmissionPreflightOutputRequest {
        output_root: preflight_request.future_output_root.clone(),
        protected_paths: preflight_request.protected_paths.clone(),
        preflight_request,
        preflight_report,
        overwrite: false,
    }
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
fn promotion_preflight_rejects_score_axes_for_local_class_even_at_level2_request() {
    let mut request = valid_request();
    request.requested_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    request.requested_evidence_class = EvidenceClass::LocalReplay;
    request.external_replay_provenance = vec!["external replay provenance declared".to_string()];
    request.populates_score_axes = true;

    let validation = validate_reviewed_promotion_preflight_request(&request);

    assert!(!validation.valid);
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
fn promotion_preflight_reports_shape_digest_marker_and_text_rejections() {
    let mut request = valid_request();
    request.id.clear();
    request.candidate.id.clear();
    request.append_preview.id.clear();
    request.append_preview.source_candidate_id = "candidate_drift".to_string();
    request.append_preview.status = EvidenceAppendPreviewStatus::Blocked;
    request.append_preview.mutates_evidence_ledger = true;
    request.review_decision.id = "review_drift".to_string();
    request.review_decision.source_proposal_id = "proposal_drift".to_string();
    request.review_decision.decision_kind = EvidenceReviewDecisionKind::Reject;
    request.review_decision.decision_status = EvidenceReviewDecisionStatus::FinalizedRejected;
    request.source_artifact_digests[0].hex_digest = "not-a-sha256".to_string();
    request.non_claims.pop();
    request
        .unresolved_quarantine_markers
        .push("quarantine marker remains unresolved".to_string());
    request
        .blocking_markers
        .push("blocking marker remains unresolved".to_string());
    request.claim_text = vec![
        "official benchmark leaderboard claim".to_string(),
        "local soak zk backend performance claim".to_string(),
    ];
    request
        .external_replay_provenance
        .push("formal proof claim".to_string());

    let validation = validate_reviewed_promotion_preflight_request(&request);
    let kinds = validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<Vec<_>>();

    assert!(!validation.valid);
    for expected in [
        ReviewedPromotionPreflightIssueKind::EmptyIdentity,
        ReviewedPromotionPreflightIssueKind::InvalidCandidate,
        ReviewedPromotionPreflightIssueKind::InvalidAppendPreview,
        ReviewedPromotionPreflightIssueKind::AppendPreviewMutatesLedger,
        ReviewedPromotionPreflightIssueKind::CandidatePreviewMismatch,
        ReviewedPromotionPreflightIssueKind::MissingHumanReviewApproval,
        ReviewedPromotionPreflightIssueKind::MissingSourceArtifactDigest,
        ReviewedPromotionPreflightIssueKind::MissingRequiredNonClaim,
        ReviewedPromotionPreflightIssueKind::UnresolvedBlockingMarker,
        ReviewedPromotionPreflightIssueKind::ForbiddenClaimText,
        ReviewedPromotionPreflightIssueKind::LocalSoakTelemetryPerformancePromotion,
    ] {
        assert!(
            kinds.contains(&expected),
            "missing expected issue kind {expected:?}; got {kinds:?}"
        );
    }
}

#[test]
fn promotion_preflight_reports_missing_source_digests_and_render_nonclaims() {
    let mut request = valid_request();
    request.source_artifact_digests.clear();

    let validation = validate_reviewed_promotion_preflight_request(&request);

    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ReviewedPromotionPreflightIssueKind::MissingSourceArtifactDigest
            && issue.path == "request.source_artifact_digests"
    }));

    let mut report = build_reviewed_promotion_preflight_report(&valid_request());
    report.non_claims.clear();
    let error = render_reviewed_promotion_preflight_markdown(&report)
        .expect_err("report missing nonclaims should not render");

    assert!(error
        .to_string()
        .contains("reviewed_promotion_preflight.non_claims"));
}

#[test]
fn promotion_preflight_markdown_lists_invalid_report_issues() {
    let mut request = valid_request();
    request.id.clear();
    let report = build_reviewed_promotion_preflight_report(&request);

    let markdown = render_reviewed_promotion_preflight_markdown(&report)
        .expect("invalid report should render");

    assert!(markdown.contains("EmptyIdentity"));
    assert!(markdown.contains("request.id"));
}

#[test]
fn promotion_preflight_json_deserializers_report_errors() {
    let promotion_error = deserialize_reviewed_promotion_preflight_report_json("{not-json")
        .expect_err("malformed promotion preflight JSON should fail");
    assert!(promotion_error
        .to_string()
        .contains("deserialize_reviewed_promotion_preflight_report_json"));

    let package_error = deserialize_official_submission_package_metadata_json("{not-json")
        .expect_err("malformed official package JSON should fail");
    assert!(package_error
        .to_string()
        .contains("deserialize_official_submission_package_metadata_json"));
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
fn official_submission_metadata_reports_shape_digest_and_text_rejections() {
    let (_, mut package) = accepted_ledger_and_package();
    package.package_id.clear();
    package.source_pack_ids.clear();
    package.external_replay_environment_provenance.clear();
    package.artifact_digests[0].hex_digest = "not-a-sha256".to_string();
    package.non_claims.pop();
    package
        .reproduction_instructions
        .push("official benchmark ranking claim".to_string());

    let validation = validate_official_submission_package_metadata(&package);
    let kinds = validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<Vec<_>>();

    assert!(!validation.valid);
    for expected in [
        OfficialSubmissionPackageIssueKind::EmptyIdentity,
        OfficialSubmissionPackageIssueKind::MissingExternalReplayProvenance,
        OfficialSubmissionPackageIssueKind::MissingArtifactDigest,
        OfficialSubmissionPackageIssueKind::MissingRequiredNonClaim,
        OfficialSubmissionPackageIssueKind::ForbiddenClaimText,
    ] {
        assert!(
            kinds.contains(&expected),
            "missing expected issue kind {expected:?}; got {kinds:?}"
        );
    }
    let render_error = render_official_submission_package_markdown(&package)
        .expect_err("invalid official package should not render");
    assert!(render_error
        .to_string()
        .contains("official_submission_package"));

    let (_, mut package_without_digests) = accepted_ledger_and_package();
    package_without_digests.artifact_digests.clear();
    let missing_digest_validation =
        validate_official_submission_package_metadata(&package_without_digests);
    assert!(!missing_digest_validation.valid);
    assert!(missing_digest_validation.issues.iter().any(|issue| {
        issue.kind == OfficialSubmissionPackageIssueKind::MissingArtifactDigest
            && issue.path == "package.artifact_digests"
    }));
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
fn external_replay_submission_preflight_validates_local_inputs_without_side_effects() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_submission_preflight_request(&dir);
    let validation = validate_external_replay_submission_preflight_request(&request);
    assert!(validation.valid, "{:?}", validation.issues);

    let report = build_external_replay_submission_preflight_report(&request);
    assert!(report.validation.valid, "{:?}", report.validation.issues);
    assert!(!report.runs_external_replay);
    assert!(!report.submits_to_official_endpoint);
    assert!(!report.mutates_accepted_evidence_ledger);
    assert!(!report.writes_generated_artifacts);
    assert!(!report.populates_score_axes);
    assert_eq!(report.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(report.source_summary.accepted_ledger_entry_count, 1);
    assert_eq!(report.source_summary.matched_accepted_evidence_id_count, 1);

    let json = serialize_external_replay_submission_preflight_report_json(&report)
        .expect("preflight report should serialize");
    let reparsed = deserialize_external_replay_submission_preflight_report_json(&json)
        .expect("preflight report should deserialize");
    assert_eq!(report, reparsed);
    let markdown = render_external_replay_submission_preflight_markdown(&report)
        .expect("preflight markdown should render");
    assert!(markdown.contains("External replay run: `false`"));
    assert!(markdown.contains("Official endpoint submitted: `false`"));
    assert_eq!(
        compute_external_replay_submission_preflight_report_digest(&report)
            .expect("digest should compute"),
        compute_external_replay_submission_preflight_report_digest(&reparsed)
            .expect("digest should recompute")
    );
}

#[test]
fn external_replay_submission_preflight_rejects_digest_drift() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_submission_preflight_request(&dir);
    request.expected_package_metadata_digest = digest("different package digest");

    let validation = validate_external_replay_submission_preflight_request(&request);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::PackageDigestMismatch
    }));
}

#[test]
fn external_replay_submission_preflight_rejects_missing_operator_acknowledgement() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_submission_preflight_request(&dir);
    request.operator_acknowledged = false;

    let validation = validate_external_replay_submission_preflight_request(&request);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::MissingOperatorAcknowledgement
    }));
}

#[test]
fn external_replay_submission_preflight_rejects_local_only_and_score_axis_requests() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_submission_preflight_request(&dir);
    request.requested_evidence_class = EvidenceClass::LocalReplay;
    request.requested_claim_boundary = ClaimBoundary::Level1LocalReplay;
    request.populates_score_axes = true;

    let validation = validate_external_replay_submission_preflight_request(&request);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::UnsupportedEvidenceClass
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::LocalOnlyEvidencePromotion
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind
            == ExternalReplaySubmissionPreflightIssueKind::ScoreAxisPopulationWithoutEvidenceClass
    }));
}

#[test]
fn external_replay_submission_preflight_rejects_endpoint_attempt_and_protected_root() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_submission_preflight_request(&dir);
    request.official_endpoint_submission_requested = true;
    request
        .protected_paths
        .push(request.future_output_root.clone());

    let validation = validate_external_replay_submission_preflight_request(&request);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::EndpointSubmissionAttempt
    }));
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == ExternalReplaySubmissionPreflightIssueKind::UnsafeOutputRoot
    }));
}

#[test]
fn external_replay_submission_preflight_source_scan_exposes_no_live_runtime_surface() {
    let source_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("evidence")
        .join("external_submission_preflight.rs");
    let source = std::fs::read_to_string(source_path).expect("source should read");

    for forbidden in [
        "std::process",
        "Command::new",
        "std::net",
        "TcpStream",
        "reqwest",
        "ureq",
        "hyper",
        "std::env::var",
        "submit_to_official",
        "populate_score_axes",
    ] {
        assert!(
            !source.contains(forbidden),
            "external submission preflight must not expose {forbidden}"
        );
    }
    assert!(source.contains("runs_external_replay: false"));
    assert!(source.contains("submits_to_official_endpoint: false"));
    assert!(source.contains("mutates_accepted_evidence_ledger: false"));
    assert!(source.contains("writes_generated_artifacts: false"));
    assert!(source.contains("populates_score_axes: false"));
}

#[test]
fn external_replay_preflight_outputs_write_and_read_declared_files_only() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);

    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    assert!(!output.input_manifest.runs_external_replay);
    assert!(!output.input_manifest.submits_to_official_endpoint);
    assert!(!output.input_manifest.mutates_accepted_evidence_ledger);
    assert!(!output.input_manifest.writes_generated_benchmark_artifacts);
    assert!(!output.input_manifest.populates_score_axes);
    assert_eq!(
        output.input_manifest.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!output.redaction_report.raw_material_retained);
    assert!(output.redaction_report.excludes_raw_credentials);
    assert!(request
        .output_root
        .join(EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH)
        .exists());
    assert!(request
        .output_root
        .join(EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH)
        .exists());

    let readback = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect("preflight outputs should read back");
    assert_eq!(output, readback);
}

#[test]
fn external_replay_preflight_outputs_reject_report_drift_and_side_effects() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_preflight_output_request(&dir);
    request.preflight_report.report_id = "different-report".to_string();
    let drift = write_external_replay_submission_preflight_outputs(&request)
        .expect_err("report drift should reject");
    assert!(drift
        .to_string()
        .contains("does not match supplied request"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_preflight_output_request(&dir);
    request.preflight_report.runs_external_replay = true;
    let side_effect = write_external_replay_submission_preflight_outputs(&request)
        .expect_err("side-effect report should reject");
    assert!(
        side_effect.to_string().contains("forbidden side effect")
            || side_effect
                .to_string()
                .contains("does not match supplied request")
    );
}

#[test]
fn external_replay_preflight_outputs_reject_unsafe_roots_and_overwrite_drift() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_preflight_output_request(&dir);
    request.protected_paths.push(request.output_root.clone());
    let protected = write_external_replay_submission_preflight_outputs(&request)
        .expect_err("protected root should reject");
    assert!(protected.to_string().contains("overlaps protected path"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");

    let mut different = request.clone();
    different.preflight_request.id = "different_preflight".to_string();
    different.preflight_request.overwrite = true;
    different.preflight_report =
        build_external_replay_submission_preflight_report(&different.preflight_request);
    different.overwrite = true;
    let overwrite = write_external_replay_submission_preflight_outputs(&different)
        .expect_err("overwrite drift should reject");
    assert!(overwrite.to_string().contains("refusing repair overwrite"));
}

#[test]
fn external_replay_preflight_outputs_reject_file_repo_parent_and_symlink_roots() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_preflight_output_request(&dir);
    let file_root = dir.path().join("not-a-directory");
    fs::write(&file_root, b"occupied").expect("file root should create");
    request.output_root = file_root;
    request.preflight_request.future_output_root = request.output_root.clone();
    request.preflight_report =
        build_external_replay_submission_preflight_report(&request.preflight_request);
    let file = write_external_replay_submission_preflight_outputs(&request)
        .expect_err("existing file output root should reject");
    assert!(file.to_string().contains("existing file"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_preflight_output_request(&dir);
    request.output_root = std::env::current_dir()
        .expect("current dir should read")
        .join("phase126-forbidden-output");
    request.preflight_request.future_output_root = request.output_root.clone();
    request.preflight_report =
        build_external_replay_submission_preflight_report(&request.preflight_request);
    let repo = write_external_replay_submission_preflight_outputs(&request)
        .expect_err("repository-overlapping output root should reject");
    assert!(repo.to_string().contains("repository root"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_preflight_output_request(&dir);
    request.output_root = dir.path().join("..").join("escaped-output");
    request.preflight_request.future_output_root = request.output_root.clone();
    request.preflight_report =
        build_external_replay_submission_preflight_report(&request.preflight_request);
    let parent = write_external_replay_submission_preflight_outputs(&request)
        .expect_err("parent-directory output root should reject");
    assert!(parent.to_string().contains("parent-directory"));

    #[cfg(unix)]
    {
        let dir = tempfile::tempdir().expect("tempdir should be available");
        let mut request = valid_external_replay_preflight_output_request(&dir);
        let symlink_root = dir.path().join("symlink-output");
        std::os::unix::fs::symlink(dir.path(), &symlink_root)
            .expect("symlink output root should create");
        request.output_root = symlink_root;
        request.preflight_request.future_output_root = request.output_root.clone();
        request.preflight_report =
            build_external_replay_submission_preflight_report(&request.preflight_request);
        let symlink = write_external_replay_submission_preflight_outputs(&request)
            .expect_err("symlink output root should reject");
        assert!(symlink.to_string().contains("symlink"));
    }
}

#[test]
fn external_replay_preflight_outputs_reject_stale_unexpected_and_raw_retention() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");

    fs::write(
        request
            .output_root
            .join(EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH),
        b"stale\n",
    )
    .expect("digest sidecar should tamper");
    let stale = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("stale digest should reject");
    assert!(stale.to_string().contains("digest sidecar"));

    fs::write(
        request
            .output_root
            .join(EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH),
        format!("{}\n", output.preflight_report_json_digest.hex_digest).as_bytes(),
    )
    .expect("digest sidecar should restore");
    fs::write(
        request
            .output_root
            .join("external-replay-submission/raw-response.json"),
        b"raw response body",
    )
    .expect("extra file should write");
    let unexpected = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("unexpected file should reject");
    assert!(unexpected
        .to_string()
        .contains("unexpected file or directory"));

    fs::remove_file(
        request
            .output_root
            .join("external-replay-submission/raw-response.json"),
    )
    .expect("extra file should remove");
    let mut redaction =
        serde_json::to_value(&output.redaction_report).expect("redaction report should convert");
    redaction["raw_material_retained"] = serde_json::Value::Bool(true);
    let redaction_json =
        serde_json::to_string_pretty(&redaction).expect("redaction report should serialize");
    let redaction_digest = compute_artifact_digest_bytes(
        redaction_json.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    );
    fs::write(
        request
            .output_root
            .join(EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_PATH),
        redaction_json.as_bytes(),
    )
    .expect("redaction report should tamper");
    fs::write(
        request
            .output_root
            .join(EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH),
        format!("{}\n", redaction_digest.hex_digest).as_bytes(),
    )
    .expect("redaction digest should update");
    let raw_retention = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("raw retention should reject");
    assert!(raw_retention.to_string().contains("redaction report"));
}

#[test]
fn external_replay_preflight_outputs_reject_each_stale_digest_sidecar() {
    let cases = [
        (
            EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
            "input manifest bytes do not match digest sidecar",
        ),
        (
            EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH,
            "preflight report JSON bytes do not match digest sidecar",
        ),
        (
            EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH,
            "preflight report Markdown bytes do not match digest sidecar",
        ),
        (
            EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH,
            "redaction report bytes do not match digest sidecar",
        ),
        (
            EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH,
            "submission package digest summary bytes do not match digest sidecar",
        ),
        (
            EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH,
            "non-claims bytes do not match digest sidecar",
        ),
    ];

    for (digest_path, expected_message) in cases {
        let dir = tempfile::tempdir().expect("tempdir should be available");
        let request = valid_external_replay_preflight_output_request(&dir);
        write_external_replay_submission_preflight_outputs(&request)
            .expect("preflight outputs should write");
        fs::write(request.output_root.join(digest_path), b"stale\n")
            .expect("digest sidecar should tamper");

        let error = read_external_replay_submission_preflight_outputs(
            &request.output_root,
            &request.protected_paths,
        )
        .expect_err("stale digest sidecar should reject");
        assert!(error.to_string().contains(expected_message), "{error}");
    }
}

#[test]
fn external_replay_preflight_outputs_reject_malformed_json_utf8_and_markdown_drift() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
        b"{",
    );
    let malformed = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("malformed input manifest should reject");
    assert!(malformed.to_string().contains("deserialize"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let invalid_digest = [0xff, 0xfe, 0xfd];
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
        &invalid_digest,
    );
    let utf8 = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("non-UTF-8 input manifest should reject");
    assert!(utf8.to_string().contains("not UTF-8"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH,
        b"# Drifted Preflight Report\n",
    );
    let markdown = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("drifted report markdown should reject");
    assert!(markdown.to_string().contains("Markdown does not match"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH,
        b"{",
    );
    let malformed = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("malformed redaction report should reject");
    assert!(malformed
        .to_string()
        .contains("deserialize_external_replay_submission_preflight_redaction_report_json"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH,
        b"{",
    );
    let malformed = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("malformed package digest summary should reject");
    assert!(malformed
        .to_string()
        .contains("deserialize_external_replay_submission_package_digest_summary_json"));
}

#[test]
fn external_replay_preflight_outputs_reject_manifest_package_and_non_claim_drift() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let mut manifest =
        serde_json::to_value(&output.input_manifest).expect("input manifest should convert");
    manifest["declared_files"] = serde_json::Value::Array(Vec::new());
    let manifest_json =
        serde_json::to_string_pretty(&manifest).expect("input manifest should serialize");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
        manifest_json.as_bytes(),
    );
    let manifest = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("manifest declared-file drift should reject");
    assert!(manifest.to_string().contains("declared files"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let mut package = serde_json::to_value(&output.package_digest_summary)
        .expect("package digest summary should convert");
    package["source_artifact_digests"] = serde_json::Value::Array(Vec::new());
    let package_json =
        serde_json::to_string_pretty(&package).expect("package digest summary should serialize");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH,
        package_json.as_bytes(),
    );
    let package = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("package digest summary drift should reject");
    assert!(package.to_string().contains("package digest summary"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH,
        b"# External Replay Submission Preflight Non-Claims\n\n- drifted non-claim\n",
    );
    let non_claims = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("non-claims markdown drift should reject");
    assert!(non_claims.to_string().contains("non-claims Markdown"));
}

#[test]
fn external_replay_preflight_outputs_reject_incomplete_redaction_policy() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_preflight_output_request(&dir);
    request.preflight_request.redaction_policy = vec!["retain digests only".to_string()];
    request.preflight_report =
        build_external_replay_submission_preflight_report(&request.preflight_request);
    assert!(request.preflight_report.validation.valid);

    let rejected = write_external_replay_submission_preflight_outputs(&request)
        .expect_err("incomplete redaction policy should reject");
    assert!(rejected.to_string().contains("redaction policy"));
}

#[test]
fn external_replay_preflight_outputs_reject_existing_roots_without_overwrite_and_read_files() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    fs::create_dir_all(&request.output_root).expect("output root should create");
    fs::write(request.output_root.join("occupied.txt"), b"occupied")
        .expect("placeholder file should write");

    let occupied = write_external_replay_submission_preflight_outputs(&request)
        .expect_err("non-empty output root should require overwrite");
    assert!(occupied.to_string().contains("explicit overwrite"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let file_root = dir.path().join("preflight-output-file");
    fs::write(&file_root, b"not a directory").expect("file root should write");
    let read_file =
        read_external_replay_submission_preflight_outputs(&file_root, &Vec::<PathBuf>::new())
            .expect_err("readback from a file root should reject");
    assert!(read_file
        .to_string()
        .contains("output root must be a directory"));
}

#[test]
fn external_replay_preflight_outputs_allow_matching_overwrite_and_not_retain_policy_wording() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let mut request = valid_external_replay_preflight_output_request(&dir);
    request.preflight_request.redaction_policy = vec![
        "do not retain raw credential token request response transcript private operator material"
            .to_string(),
    ];
    request.preflight_request.overwrite = true;
    request.preflight_report =
        build_external_replay_submission_preflight_report(&request.preflight_request);

    let first = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    request.overwrite = true;
    let second = write_external_replay_submission_preflight_outputs(&request)
        .expect("matching overwrite should repair deterministically");

    assert_eq!(first, second);
    assert!(!second.input_manifest.runs_external_replay);
    assert!(!second.redaction_report.raw_material_retained);
}

#[test]
fn external_replay_preflight_outputs_reject_tampered_report_side_effects_and_nonclaims() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let mut report =
        serde_json::to_value(&output.preflight_report).expect("preflight report should convert");
    report["validation"]["valid"] = serde_json::Value::Bool(false);
    let report_json =
        serde_json::to_string_pretty(&report).expect("preflight report should serialize");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH,
        report_json.as_bytes(),
    );
    let invalid_report = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("invalid preflight report should reject");
    assert!(invalid_report
        .to_string()
        .contains("validation must be valid"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let mut report = output.preflight_report.clone();
    report.runs_external_replay = true;
    let report_json = serialize_external_replay_submission_preflight_report_json(&report)
        .expect("preflight report should serialize");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH,
        report_json.as_bytes(),
    );
    let side_effect = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("side-effect report should reject");
    assert!(side_effect.to_string().contains("forbidden side effect"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let mut report = output.preflight_report.clone();
    report.non_claims.pop();
    let report_json = serialize_external_replay_submission_preflight_report_json(&report)
        .expect("preflight report should serialize");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH,
        report_json.as_bytes(),
    );
    let missing_nonclaim = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("missing non-claim label should reject");
    assert!(missing_nonclaim
        .to_string()
        .contains("missing required non-claim label"));
}

#[test]
fn external_replay_preflight_outputs_reject_tampered_manifest_identity_and_side_effects() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let mut manifest =
        serde_json::to_value(&output.input_manifest).expect("input manifest should convert");
    manifest["runs_external_replay"] = serde_json::Value::Bool(true);
    let manifest_json =
        serde_json::to_string_pretty(&manifest).expect("input manifest should serialize");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
        manifest_json.as_bytes(),
    );
    let side_effect = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("side-effect manifest should reject");
    assert!(side_effect.to_string().contains("input manifest"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let mut manifest =
        serde_json::to_value(&output.input_manifest).expect("input manifest should convert");
    manifest["preflight_report_id"] = serde_json::Value::String("drifted-report".to_string());
    let manifest_json =
        serde_json::to_string_pretty(&manifest).expect("input manifest should serialize");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
        manifest_json.as_bytes(),
    );
    let report_id = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("manifest report id drift should reject");
    assert!(report_id.to_string().contains("report id does not match"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let mut manifest =
        serde_json::to_value(&output.input_manifest).expect("input manifest should convert");
    manifest["preflight_request"]["id"] = serde_json::Value::String("drifted-request".to_string());
    let manifest_json =
        serde_json::to_string_pretty(&manifest).expect("input manifest should serialize");
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
        manifest_json.as_bytes(),
    );
    let request_id = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("manifest request id drift should reject");
    assert!(request_id.to_string().contains("request id does not match"));
}

#[test]
fn external_replay_preflight_outputs_reject_raw_markers_and_non_utf8_sidecars() {
    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    let output = write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    let mut report = output.preflight_report.clone();
    report
        .non_claims
        .push("raw response retained for operator review".to_string());
    let report_json = serialize_external_replay_submission_preflight_report_json(&report)
        .expect("preflight report should serialize");
    let report_markdown = render_external_replay_submission_preflight_markdown(&report)
        .expect("preflight report markdown should render");
    let non_claims_markdown = external_preflight_non_claims_markdown(&report.non_claims);
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH,
        report_json.as_bytes(),
    );
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH,
        report_markdown.as_bytes(),
    );
    write_external_preflight_file_with_digest(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH,
        non_claims_markdown.as_bytes(),
    );
    let raw_marker = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("raw retention marker should reject");
    assert!(raw_marker
        .to_string()
        .contains("raw retained material markers"));

    let dir = tempfile::tempdir().expect("tempdir should be available");
    let request = valid_external_replay_preflight_output_request(&dir);
    write_external_replay_submission_preflight_outputs(&request)
        .expect("preflight outputs should write");
    fs::write(
        request
            .output_root
            .join(EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH),
        [0xff, 0xfe, 0xfd],
    )
    .expect("digest sidecar should tamper");
    let sidecar = read_external_replay_submission_preflight_outputs(
        &request.output_root,
        &request.protected_paths,
    )
    .expect_err("non-UTF-8 digest sidecar should reject");
    assert!(sidecar.to_string().contains("digest sidecar is not UTF-8"));
}

#[test]
fn external_replay_preflight_output_source_scan_exposes_no_live_runtime_surface() {
    let source_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("evidence")
        .join("external_submission_preflight_output.rs");
    let source = fs::read_to_string(source_path).expect("source should read");

    for forbidden in [
        "std::process",
        "Command::new",
        "std::net",
        "TcpStream",
        "reqwest",
        "ureq",
        "hyper",
        "std::env::var",
        "submit_to_official",
        "populate_score_axes",
        "default_endpoint",
        "default_credential",
    ] {
        assert!(
            !source.contains(forbidden),
            "external preflight output must not expose {forbidden}"
        );
    }
    assert!(source.contains("runs_external_replay: false"));
    assert!(source.contains("submits_to_official_endpoint: false"));
    assert!(source.contains("mutates_accepted_evidence_ledger: false"));
    assert!(source.contains("populates_score_axes: false"));
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

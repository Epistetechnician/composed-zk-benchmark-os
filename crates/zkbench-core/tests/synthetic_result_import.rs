use zkbench_core::{
    deserialize_external_result_candidate_json, import_synthetic_result_candidate_json,
    quarantine_synthetic_result_candidate, score_report_from_evidence,
    serialize_synthetic_result_import_bundle_json, validate_synthetic_result_candidate,
    ClaimBoundary, QuarantineReason, ResultCandidateArtifactResolver,
    SyntheticImportValidationIssue, SyntheticImportValidationIssueKind,
};

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

#[test]
fn valid_synthetic_candidate_imports_to_normalized_draft() {
    let json = include_str!("fixtures/synthetic_result_candidate_valid.json");
    let bundle = import_synthetic_result_candidate_json(json, &resolver())
        .expect("valid synthetic candidate should import");

    assert!(bundle.validation.valid, "{:?}", bundle.validation.issues);
    assert_eq!(bundle.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(bundle.report.candidates_imported, 1);
    assert_eq!(bundle.report.candidates_normalized, 1);
    assert_eq!(bundle.report.candidates_quarantined, 0);
    assert!(bundle.normalized_draft.is_some());
    assert!(bundle.quarantine_manifest.is_none());

    let draft = bundle
        .normalized_draft
        .as_ref()
        .expect("normalized draft should be present");
    assert_eq!(draft.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(draft.metrics.len(), 1);
    assert!(draft.metrics[0].candidate_only);
    assert!(draft.metrics[0].pending_review);
    assert_eq!(draft.artifact_refs.len(), 1);
    assert!(draft.artifact_refs[0].verified_by_importer);

    let serialized =
        serialize_synthetic_result_import_bundle_json(&bundle).expect("bundle serializes");
    assert!(serialized.contains("synthetic_import_bundle_synthetic_candidate_valid"));
}

#[test]
fn invalid_synthetic_candidate_imports_to_quarantine_manifest() {
    let json = include_str!("fixtures/synthetic_result_candidate_bad_digest.json");
    let bundle = import_synthetic_result_candidate_json(json, &resolver())
        .expect("bad synthetic candidate should still parse into a quarantine bundle");

    assert!(!bundle.validation.valid);
    assert_eq!(bundle.report.candidates_normalized, 0);
    assert_eq!(bundle.report.candidates_quarantined, 1);
    assert!(bundle.normalized_draft.is_none());
    assert!(bundle.quarantine_manifest.is_some());
    assert_eq!(
        bundle
            .quarantine_manifest
            .as_ref()
            .expect("quarantine manifest")
            .entries[0]
            .claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn synthetic_metric_candidates_do_not_create_score_values() {
    let report = score_report_from_evidence(&[]);

    assert!(report.performance.is_none());
    assert!(report.formal_evidence.is_none());
}

#[test]
fn quarantine_reason_matches_synthetic_rejection_kind() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    let base_validation = validate_synthetic_result_candidate(&candidate, &resolver());
    assert!(base_validation.valid, "{:?}", base_validation.issues);

    for (issue_kind, expected_reason) in [
        (
            SyntheticImportValidationIssueKind::ClaimBoundaryTooHigh,
            QuarantineReason::ClaimBoundaryTooHigh,
        ),
        (
            SyntheticImportValidationIssueKind::OfficialClaimDetected,
            QuarantineReason::OfficialClaimDetected,
        ),
        (
            SyntheticImportValidationIssueKind::FormalClaimDetected,
            QuarantineReason::FormalClaimDetected,
        ),
        (
            SyntheticImportValidationIssueKind::SoundnessClaimDetected,
            QuarantineReason::SoundnessClaimDetected,
        ),
        (
            SyntheticImportValidationIssueKind::ArtifactDigestMismatch,
            QuarantineReason::ArtifactDigestMismatch,
        ),
        (
            SyntheticImportValidationIssueKind::ArtifactDigestMissing,
            QuarantineReason::InvalidDigest,
        ),
        (
            SyntheticImportValidationIssueKind::ArtifactDigestUnsupported,
            QuarantineReason::InvalidDigest,
        ),
        (
            SyntheticImportValidationIssueKind::ArtifactLookupMissing,
            QuarantineReason::InvalidDigest,
        ),
        (
            SyntheticImportValidationIssueKind::ProvenanceValidationFailed,
            QuarantineReason::ProvenanceValidationFailed,
        ),
        (
            SyntheticImportValidationIssueKind::MetricValidationFailed,
            QuarantineReason::MetricValidationFailed,
        ),
    ] {
        let mut validation = base_validation.clone();
        validation.valid = false;
        validation.issues = vec![SyntheticImportValidationIssue::error(
            issue_kind,
            "candidate.synthetic_check",
            "synthetic rejection branch",
        )];

        let manifest = quarantine_synthetic_result_candidate(&candidate, &validation);

        assert_eq!(manifest.entries[0].reason, expected_reason);
        assert_eq!(manifest.entries[0].validation_issues.len(), 1);
        assert_eq!(
            manifest.entries[0].validation_issues[0].path,
            "candidate.synthetic_check"
        );
    }
}

#[test]
fn quarantine_reason_falls_back_to_pending_review_for_non_classified_issues() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    let mut validation = validate_synthetic_result_candidate(&candidate, &resolver());
    validation.valid = false;
    validation.issues = vec![SyntheticImportValidationIssue::error(
        SyntheticImportValidationIssueKind::SchemaValidationFailed,
        "candidate.schema",
        "schema rejection does not map to a more specific quarantine reason",
    )];

    let manifest = quarantine_synthetic_result_candidate(&candidate, &validation);

    assert_eq!(manifest.entries[0].reason, QuarantineReason::PendingReview);
}

#[test]
fn quarantine_reason_prefers_highest_boundary_risk_when_multiple_issues_exist() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    let mut validation = validate_synthetic_result_candidate(&candidate, &resolver());
    validation.valid = false;
    validation.issues = vec![
        SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::MetricValidationFailed,
            "candidate.normalized_metrics[0].value",
            "metric rejection",
        ),
        SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::ClaimBoundaryTooHigh,
            "candidate.claim_boundary_requested",
            "boundary rejection",
        ),
    ];

    let manifest = quarantine_synthetic_result_candidate(&candidate, &validation);

    assert_eq!(
        manifest.entries[0].reason,
        QuarantineReason::ClaimBoundaryTooHigh
    );
    assert_eq!(manifest.entries[0].validation_issues.len(), 2);
}

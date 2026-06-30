use zkbench_core::{
    build_default_external_result_import_schema, compute_artifact_digest_bytes,
    deserialize_quarantine_manifest_json, external_result_quarantine_record,
    quarantine_external_result_candidate, serialize_quarantine_manifest_json,
    validate_external_result_candidate, validate_external_result_candidate_with_schema,
    validate_external_result_import_schema, validate_quarantine_manifest, ArtifactKind,
    ArtifactRole, ClaimBoundary, EnvironmentProvenance, ExternalMetricCandidate,
    ExternalMetricUnit, ExternalResultCandidate, ExternalResultStatus, ExternalResultValidation,
    ExternalRunProvenanceDraft, ExternalToolProvenance, OperatorProvenance, QuarantineReason,
    QuarantineStatus, QuarantineValidation, SourceProvenance,
};

fn provenance() -> ExternalRunProvenanceDraft {
    ExternalRunProvenanceDraft {
        id: Some("synthetic_provenance_draft".to_string()),
        operator: OperatorProvenance {
            operator_or_agent: Some("local-test".to_string()),
            execution_date_declared_by_operator: Some("operator-declared-date".to_string()),
        },
        external_tool: ExternalToolProvenance {
            external_tool_name: Some("synthetic-tool".to_string()),
            external_tool_version: Some("synthetic-version".to_string()),
            external_tool_source: Some("synthetic-source".to_string()),
            external_tool_commit_or_release: Some("synthetic-release".to_string()),
        },
        environment: EnvironmentProvenance {
            host_os: Some("declared-host-os".to_string()),
            hardware_summary: Some("declared-hardware-summary".to_string()),
            network_policy: Some("network-disabled".to_string()),
        },
        source: SourceProvenance {
            command_plan_id: Some("dry_run_plan_synthetic".to_string()),
            benchmark_pack_id: Some("local_pack_synthetic".to_string()),
            artifact_digest_set: vec![compute_artifact_digest_bytes(
                b"synthetic",
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Digest),
            )],
        },
        notes: vec!["synthetic local validation draft only".to_string()],
    }
}

fn candidate() -> ExternalResultCandidate {
    ExternalResultCandidate {
        result_candidate_id: "candidate_synthetic".to_string(),
        source_benchmark_pack_id: "local_pack_synthetic".to_string(),
        dry_run_plan_id: "dry_run_plan_synthetic".to_string(),
        raw_output_artifact_refs: vec!["artifacts/raw_output.json".to_string()],
        normalized_metrics: Vec::new(),
        result_status: ExternalResultStatus::Quarantined,
        provenance_draft: Some(provenance()),
        artifact_digests: Vec::new(),
        claim_boundary_requested: ClaimBoundary::Level0DesignNote,
        claims_official_benchmark_evidence: false,
        claims_formal_evidence: false,
        claims_proof_system_soundness: false,
        notes: vec!["synthetic candidate only".to_string()],
    }
}

#[test]
fn default_result_import_schema_builds_and_validates() {
    let schema = build_default_external_result_import_schema();
    let validation = validate_external_result_import_schema(&schema);

    assert!(
        validation.valid,
        "validation issues: {:?}",
        validation.issues
    );
    assert_eq!(schema.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!schema.allowed_units.contains(&ExternalMetricUnit::Unknown));
}

#[test]
fn schema_validation_reports_identity_boundary_unknown_units_and_missing_fields() {
    let mut schema = build_default_external_result_import_schema();
    schema.id = " ".to_string();
    schema.claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    schema.allowed_units.push(ExternalMetricUnit::Unknown);
    schema.required_provenance_fields.clear();

    let validation = validate_external_result_import_schema(&schema);

    assert!(!validation.valid);
    assert_result_issue_path(&validation, "schema.id");
    assert_result_issue_path(&validation, "schema.claim_boundary");
    assert_result_issue_path(&validation, "schema.allowed_units");
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.starts_with("schema.required_provenance_fields.")));
}

#[test]
fn missing_provenance_is_rejected() {
    let mut candidate = candidate();
    candidate.provenance_draft = None;

    let validation = validate_external_result_candidate(&candidate);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.contains("provenance")));
}

#[test]
fn elevated_or_forbidden_claims_are_rejected() {
    let mut elevated = candidate();
    elevated.claim_boundary_requested = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    assert!(!validate_external_result_candidate(&elevated).valid);

    let mut official = candidate();
    official.claims_official_benchmark_evidence = true;
    assert!(!validate_external_result_candidate(&official).valid);

    let mut formal = candidate();
    formal.claims_formal_evidence = true;
    assert!(!validate_external_result_candidate(&formal).valid);

    let mut soundness = candidate();
    soundness.claims_proof_system_soundness = true;
    assert!(!validate_external_result_candidate(&soundness).valid);
}

#[test]
fn candidate_validation_reports_identity_status_path_and_provenance_gaps() {
    let mut candidate = candidate();
    candidate.result_candidate_id = " ".to_string();
    candidate.source_benchmark_pack_id = " ".to_string();
    candidate.dry_run_plan_id = " ".to_string();
    candidate.raw_output_artifact_refs = vec![
        "/tmp/raw-output.json".to_string(),
        "../escape/raw-output.json".to_string(),
    ];
    candidate.result_status = ExternalResultStatus::AcceptedAsLocalImportOnly;
    candidate.provenance_draft = None;

    let validation = validate_external_result_candidate(&candidate);

    assert!(!validation.valid);
    assert_result_issue_path(&validation, "candidate.result_candidate_id");
    assert_result_issue_path(&validation, "candidate.source_benchmark_pack_id");
    assert_result_issue_path(&validation, "candidate.dry_run_plan_id");
    assert_result_issue_path(&validation, "candidate.provenance_draft");
    assert_result_issue_path(&validation, "candidate.raw_output_artifact_refs[0]");
    assert_result_issue_path(&validation, "candidate.raw_output_artifact_refs[1]");
    assert_result_issue_path(&validation, "candidate.result_status");
}

#[test]
fn candidate_validation_reports_metric_identity_paths_and_forbidden_notes() {
    let mut candidate = candidate();
    candidate.notes = vec!["this is official benchmark evidence".to_string()];
    candidate.normalized_metrics.push(ExternalMetricCandidate {
        metric_kind: " ".to_string(),
        unit: ExternalMetricUnit::Count,
        value: None,
        source_artifact_ref: Some("../escape/metric.json".to_string()),
        notes: vec!["formal evidence claim".to_string()],
    });

    let validation = validate_external_result_candidate(&candidate);

    assert!(!validation.valid);
    assert_result_issue_path(&validation, "candidate.normalized_metrics[0].metric_kind");
    assert_result_issue_path(
        &validation,
        "candidate.normalized_metrics[0].source_artifact_ref",
    );
    assert_result_issue_path(&validation, "candidate.normalized_metrics[0].notes[0]");
    assert_result_issue_path(&validation, "candidate.notes[0]");
}

#[test]
fn relaxed_import_policy_allows_policy_controlled_local_drift() {
    let mut schema = build_default_external_result_import_schema();
    schema.import_policy.require_source_benchmark_pack_id = false;
    schema.import_policy.require_dry_run_plan_id = false;
    schema.import_policy.require_provenance = false;
    schema.import_policy.reject_level2_plus_claim_requests = false;
    schema.import_policy.reject_official_benchmark_claims = false;
    schema.import_policy.reject_formal_evidence_claims = false;
    schema.import_policy.reject_proof_system_soundness_claims = false;
    schema.import_policy.reject_absolute_paths = false;
    schema.import_policy.require_metric_source_artifact_refs = false;

    let mut candidate = candidate();
    candidate.source_benchmark_pack_id.clear();
    candidate.dry_run_plan_id.clear();
    candidate.raw_output_artifact_refs = vec!["/tmp/raw-output.json".to_string()];
    candidate.provenance_draft = None;
    candidate.claim_boundary_requested = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    candidate.claims_official_benchmark_evidence = true;
    candidate.claims_formal_evidence = true;
    candidate.claims_proof_system_soundness = true;
    candidate.normalized_metrics.push(ExternalMetricCandidate {
        metric_kind: "synthetic_metric".to_string(),
        unit: ExternalMetricUnit::Count,
        value: Some("1".to_string()),
        source_artifact_ref: Some("artifacts/metric.json".to_string()),
        notes: Vec::new(),
    });

    let validation = validate_external_result_candidate_with_schema(&candidate, &schema);

    assert!(
        validation.valid,
        "validation issues: {:?}",
        validation.issues
    );
}

#[test]
fn metric_values_need_source_refs_and_known_units() {
    let mut missing_ref = candidate();
    missing_ref
        .normalized_metrics
        .push(ExternalMetricCandidate {
            metric_kind: "synthetic_metric".to_string(),
            unit: ExternalMetricUnit::Count,
            value: Some("1".to_string()),
            source_artifact_ref: None,
            notes: Vec::new(),
        });
    assert!(!validate_external_result_candidate(&missing_ref).valid);

    let mut unknown_unit = candidate();
    unknown_unit
        .normalized_metrics
        .push(ExternalMetricCandidate {
            metric_kind: "synthetic_metric".to_string(),
            unit: ExternalMetricUnit::Unknown,
            value: None,
            source_artifact_ref: Some("artifacts/metric.json".to_string()),
            notes: Vec::new(),
        });
    assert!(!validate_external_result_candidate(&unknown_unit).valid);
}

#[test]
fn rejected_candidate_can_be_quarantined_and_serialized() {
    let mut candidate = candidate();
    candidate.provenance_draft = None;

    let manifest = quarantine_external_result_candidate(&candidate);
    assert_eq!(
        manifest.entries[0].reason,
        QuarantineReason::MissingProvenance
    );
    let validation = validate_quarantine_manifest(&manifest);
    assert!(
        validation.valid,
        "quarantine issues: {:?}",
        validation.issues
    );

    let json = serialize_quarantine_manifest_json(&manifest).expect("manifest should serialize");
    let parsed = deserialize_quarantine_manifest_json(&json).expect("manifest should deserialize");
    let json_again =
        serialize_quarantine_manifest_json(&parsed).expect("manifest should serialize again");
    assert_eq!(manifest, parsed);
    assert_eq!(json, json_again);
}

#[test]
fn direct_quarantine_record_preserves_validation_context_without_manifest_claims() {
    let mut candidate = candidate();
    candidate.result_candidate_id = "candidate_bad_path".to_string();
    candidate.raw_output_artifact_refs = vec!["../escape/raw-output.json".to_string()];

    let record = external_result_quarantine_record(&candidate);

    assert_eq!(record.result_candidate_id, "candidate_bad_path");
    assert_eq!(record.status, ExternalResultStatus::Quarantined);
    assert_eq!(
        record.claim_boundary_requested,
        ClaimBoundary::Level0DesignNote
    );
    assert!(record
        .validation_issues
        .iter()
        .any(|issue| issue.path == "candidate.raw_output_artifact_refs[0]"));
    assert!(record.notes.iter().any(|note| note.contains("quarantined")));
}

#[test]
fn quarantine_reason_selection_reports_specific_claim_failures() {
    let mut elevated = candidate();
    elevated.claim_boundary_requested = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    assert_eq!(
        quarantine_external_result_candidate(&elevated).entries[0].reason,
        QuarantineReason::ClaimBoundaryTooHigh
    );

    let mut official = candidate();
    official.claims_official_benchmark_evidence = true;
    assert_eq!(
        quarantine_external_result_candidate(&official).entries[0].reason,
        QuarantineReason::OfficialClaimRejected
    );

    let mut formal = candidate();
    formal.claims_formal_evidence = true;
    assert_eq!(
        quarantine_external_result_candidate(&formal).entries[0].reason,
        QuarantineReason::FormalClaimRejected
    );

    let mut soundness = candidate();
    soundness.claims_proof_system_soundness = true;
    assert_eq!(
        quarantine_external_result_candidate(&soundness).entries[0].reason,
        QuarantineReason::FormalClaimRejected
    );
}

#[test]
fn quarantine_reason_selection_reports_metric_path_source_and_pending_review() {
    let mut absolute = candidate();
    absolute.raw_output_artifact_refs = vec!["/tmp/raw-output.json".to_string()];
    assert_eq!(
        quarantine_external_result_candidate(&absolute).entries[0].reason,
        QuarantineReason::AbsolutePathRejected
    );

    let mut unsupported_metric = candidate();
    unsupported_metric
        .normalized_metrics
        .push(ExternalMetricCandidate {
            metric_kind: "synthetic_metric".to_string(),
            unit: ExternalMetricUnit::Unknown,
            value: None,
            source_artifact_ref: Some("artifacts/metric.json".to_string()),
            notes: Vec::new(),
        });
    assert_eq!(
        quarantine_external_result_candidate(&unsupported_metric).entries[0].reason,
        QuarantineReason::UnsupportedMetric
    );

    let mut unknown_source = candidate();
    unknown_source.source_benchmark_pack_id.clear();
    assert_eq!(
        quarantine_external_result_candidate(&unknown_source).entries[0].reason,
        QuarantineReason::UnknownSource
    );

    assert_eq!(
        quarantine_external_result_candidate(&candidate()).entries[0].reason,
        QuarantineReason::PendingReview
    );
}

#[test]
fn quarantine_manifest_rejects_elevated_entry_boundary() {
    let mut candidate = candidate();
    candidate.claim_boundary_requested = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    let manifest = quarantine_external_result_candidate(&candidate);

    let validation = validate_quarantine_manifest(&manifest);

    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.path.contains("claim_boundary") && issue.message.contains("Phase H local limits")
    }));
}

#[test]
fn quarantine_manifest_validation_rejects_manifest_entry_and_ref_drift() {
    let mut manifest = quarantine_external_result_candidate(&candidate());
    manifest.quarantine_id = " ".to_string();
    let entry = manifest
        .entries
        .first_mut()
        .expect("quarantine manifest should carry one entry");
    entry.candidate_result_id.clear();
    entry.source_artifact_refs = vec!["../escape/raw-output.json".to_string()];

    let validation = validate_quarantine_manifest(&manifest);

    assert!(!validation.valid);
    assert_eq!(validation.status, QuarantineStatus::Rejected);
    assert_issue_path(&validation, "manifest.quarantine_id");
    assert_issue_path(&validation, "manifest.entries[0].candidate_result_id");
    assert_issue_path(&validation, "manifest.entries[0].source_artifact_refs[0]");
}

#[test]
fn quarantine_manifest_validation_preserves_valid_status_summary() {
    let mut manifest = quarantine_external_result_candidate(&candidate());
    manifest.validation_status = QuarantineStatus::PendingReview;

    let validation = validate_quarantine_manifest(&manifest);

    assert!(validation.valid, "issues: {:?}", validation.issues);
    assert_eq!(validation.status, QuarantineStatus::PendingReview);
}

fn assert_issue_path(validation: &QuarantineValidation, path: &str) {
    assert!(
        validation.issues.iter().any(|issue| issue.path == path),
        "expected validation issue at {path}, got {:?}",
        validation.issues
    );
}

fn assert_result_issue_path(validation: &ExternalResultValidation, path: &str) {
    assert!(
        validation.issues.iter().any(|issue| issue.path == path),
        "expected validation issue at {path}, got {:?}",
        validation.issues
    );
}

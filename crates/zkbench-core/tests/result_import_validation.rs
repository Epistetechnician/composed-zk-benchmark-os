use zkbench_core::{
    build_default_external_result_import_schema, compute_artifact_digest_bytes,
    deserialize_quarantine_manifest_json, quarantine_external_result_candidate,
    serialize_quarantine_manifest_json, validate_external_result_candidate,
    validate_external_result_import_schema, validate_quarantine_manifest, ArtifactKind,
    ArtifactRole, ClaimBoundary, EnvironmentProvenance, ExternalMetricCandidate,
    ExternalMetricUnit, ExternalResultCandidate, ExternalResultStatus, ExternalRunProvenanceDraft,
    ExternalToolProvenance, OperatorProvenance, QuarantineReason, SourceProvenance,
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

use zkbench_core::{
    compute_zkml_workload_digest_root, deserialize_zkml_workload_manifest_json,
    validate_zkml_workload_manifest, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary, EvidenceClass, ZkMlMetric, ZkMlMetricKind, ZkMlModelArtifactRef,
    ZkMlWorkloadInputKind, ZkMlWorkloadInputRef, ZkMlWorkloadManifest, ZkMlWorkloadManifestVersion,
    ZkMlWorkloadValidationIssueKind,
};

fn digest(byte: u8) -> ArtifactDigest {
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: format!("{byte:02x}").repeat(32),
        byte_len: 64,
        kind: Some(ArtifactKind::Other),
        role: Some(ArtifactRole::Digest),
    }
}

fn invalid_digest() -> ArtifactDigest {
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Unsupported,
        hex_digest: "not-a-sha256".to_string(),
        byte_len: 0,
        kind: Some(ArtifactKind::Other),
        role: Some(ArtifactRole::Digest),
    }
}

fn input(
    input_id: &str,
    kind: ZkMlWorkloadInputKind,
    claim_boundary: ClaimBoundary,
    evidence_class: EvidenceClass,
    digest_byte: u8,
) -> ZkMlWorkloadInputRef {
    ZkMlWorkloadInputRef {
        input_id: input_id.to_string(),
        artifact_uri: format!("artifacts/{input_id}.json"),
        kind,
        digest: digest(digest_byte),
        evidence_class,
        claim_boundary,
        notes: Vec::new(),
    }
}

fn model_artifact() -> ZkMlModelArtifactRef {
    ZkMlModelArtifactRef {
        artifact_id: "small_policy_model".to_string(),
        artifact_uri: "artifacts/small_policy_model.json".to_string(),
        digest: digest(9),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: Vec::new(),
    }
}

fn valid_manifest() -> ZkMlWorkloadManifest {
    let inputs = vec![
        input(
            "zkml_family_metadata",
            ZkMlWorkloadInputKind::BenchmarkFamilyMetadata,
            ClaimBoundary::Level0DesignNote,
            EvidenceClass::DesignNote,
            1,
        ),
        input(
            "local_replay_manifest",
            ZkMlWorkloadInputKind::LocalReplayManifest,
            ClaimBoundary::Level1LocalReplay,
            EvidenceClass::LocalReplay,
            2,
        ),
    ];
    let model_artifacts = vec![model_artifact()];
    let workload_digest_root = compute_zkml_workload_digest_root(&inputs, &model_artifacts)
        .expect("digest root should compute");

    ZkMlWorkloadManifest {
        manifest_id: "phase_179_zkml_workload".to_string(),
        version: ZkMlWorkloadManifestVersion::default(),
        workload_family_id: "ZkMlControlFlowMixed".to_string(),
        source_benchmark_instance_id: "zkml_control_flow_mixed_fixture".to_string(),
        control_flow_machine_id: "policy_gate_machine".to_string(),
        inputs,
        public_input_names: vec!["threshold".to_string()],
        private_witness_names: vec!["model_logits".to_string()],
        model_artifacts,
        threshold_policy: Some("decision >= threshold".to_string()),
        expected_verdict_mapping: "boundary mismatch rejects".to_string(),
        workload_digest_root,
        executable_adapter_authorized: false,
        metrics: vec![
            ZkMlMetric {
                kind: ZkMlMetricKind::ModelArtifactDigestPresent,
                value: Some(1),
                claim_boundary: ClaimBoundary::Level0DesignNote,
                notes: Vec::new(),
            },
            ZkMlMetric {
                kind: ZkMlMetricKind::ProofSizeBytes,
                value: None,
                claim_boundary: ClaimBoundary::Level0DesignNote,
                notes: Vec::new(),
            },
        ],
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
        limitations: vec![
            "model accuracy is not proof-system correctness".to_string(),
            "zkML metrics do not prove semantic soundness".to_string(),
        ],
        notes: Vec::new(),
    }
}

fn assert_issue(
    manifest: &ZkMlWorkloadManifest,
    kind: ZkMlWorkloadValidationIssueKind,
    path: &str,
) {
    let validation = validate_zkml_workload_manifest(manifest);
    assert!(
        validation
            .issues
            .iter()
            .any(|issue| issue.kind == kind && issue.path == path),
        "missing {kind:?} at {path:?}: {:?}",
        validation.issues
    );
}

#[test]
fn zkml_metric_kinds_and_default_version_preserve_execution_boundary() {
    assert_eq!(
        ZkMlWorkloadManifestVersion::default().value,
        "phase-n-zkml-workload-manifest-v0"
    );

    for kind in [
        ZkMlMetricKind::ModelArtifactDigestPresent,
        ZkMlMetricKind::PublicInputCount,
        ZkMlMetricKind::PrivateWitnessCount,
        ZkMlMetricKind::ThresholdPolicyPresent,
        ZkMlMetricKind::BoundaryCheckResult,
        ZkMlMetricKind::ObservationOmissionResult,
    ] {
        assert!(!kind.requires_executable_adapter(), "{kind:?}");
    }

    for kind in [
        ZkMlMetricKind::ModelAccuracyIfSourceDeclares,
        ZkMlMetricKind::ConstraintCount,
        ZkMlMetricKind::ProofSizeBytes,
        ZkMlMetricKind::ProverTimeMs,
        ZkMlMetricKind::VerifierTimeMs,
        ZkMlMetricKind::MemoryBytes,
    ] {
        assert!(kind.requires_executable_adapter(), "{kind:?}");
    }
}

#[test]
fn zkml_manifest_reports_missing_top_level_shape_and_digest_issues() {
    let mut manifest = valid_manifest();
    manifest.manifest_id = " ".to_string();
    manifest.version.value.clear();
    manifest.workload_family_id.clear();
    manifest.source_benchmark_instance_id = "\t".to_string();
    manifest.control_flow_machine_id.clear();
    manifest.expected_verdict_mapping = " ".to_string();
    manifest.inputs.clear();
    manifest.public_input_names.clear();
    manifest.private_witness_names.clear();
    manifest.model_artifacts.clear();
    manifest.threshold_policy = Some(" ".to_string());
    manifest.workload_digest_root = invalid_digest();
    manifest.limitations.clear();

    for (kind, path) in [
        (
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "manifest_id",
        ),
        (
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "version.value",
        ),
        (
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "workload_family_id",
        ),
        (
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "source_benchmark_instance_id",
        ),
        (
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "control_flow_machine_id",
        ),
        (
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "expected_verdict_mapping",
        ),
        (ZkMlWorkloadValidationIssueKind::MissingInputs, "inputs"),
        (
            ZkMlWorkloadValidationIssueKind::MissingPublicInputs,
            "public_input_names",
        ),
        (
            ZkMlWorkloadValidationIssueKind::MissingPrivateWitnesses,
            "private_witness_names",
        ),
        (
            ZkMlWorkloadValidationIssueKind::MissingModelArtifacts,
            "model_artifacts",
        ),
        (
            ZkMlWorkloadValidationIssueKind::MissingThresholdPolicy,
            "threshold_policy",
        ),
        (
            ZkMlWorkloadValidationIssueKind::InvalidDigest,
            "workload_digest_root",
        ),
        (
            ZkMlWorkloadValidationIssueKind::MissingLimitation,
            "limitations",
        ),
    ] {
        assert_issue(&manifest, kind, path);
    }
}

#[test]
fn zkml_manifest_reports_input_and_model_artifact_drift_paths() {
    let mut manifest = valid_manifest();
    manifest.inputs[0].input_id.clear();
    manifest.inputs[0].artifact_uri = "https://example.invalid/input.json".to_string();
    manifest.inputs[0].digest = invalid_digest();
    manifest.inputs[0].kind = ZkMlWorkloadInputKind::EvidenceAppendPreview;
    manifest.inputs[0].claim_boundary = ClaimBoundary::Level1LocalReplay;
    manifest.inputs[1].kind = ZkMlWorkloadInputKind::Level2EligibilityReport;
    manifest.inputs[1].claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    manifest.model_artifacts[0].artifact_id = " ".to_string();
    manifest.model_artifacts[0].artifact_uri = "models/../small_policy_model.json".to_string();
    manifest.model_artifacts[0].digest = invalid_digest();
    manifest.model_artifacts[0].claim_boundary = ClaimBoundary::Level1LocalReplay;

    for (kind, path) in [
        (
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "inputs[0].input_id",
        ),
        (
            ZkMlWorkloadValidationIssueKind::InvalidArtifactRef,
            "inputs[0].artifact_uri",
        ),
        (
            ZkMlWorkloadValidationIssueKind::InvalidDigest,
            "inputs[0].digest",
        ),
        (
            ZkMlWorkloadValidationIssueKind::AppendPreviewBoundary,
            "inputs[0].claim_boundary",
        ),
        (
            ZkMlWorkloadValidationIssueKind::Level2EligibilityBoundary,
            "inputs[1].claim_boundary",
        ),
        (
            ZkMlWorkloadValidationIssueKind::EmptyIdentity,
            "model_artifacts[0].artifact_id",
        ),
        (
            ZkMlWorkloadValidationIssueKind::InvalidArtifactRef,
            "model_artifacts[0].artifact_uri",
        ),
        (
            ZkMlWorkloadValidationIssueKind::InvalidDigest,
            "model_artifacts[0].digest",
        ),
        (
            ZkMlWorkloadValidationIssueKind::ModelArtifactBoundary,
            "model_artifacts[0].claim_boundary",
        ),
    ] {
        assert_issue(&manifest, kind, path);
    }
}

#[test]
fn zkml_manifest_reports_output_metric_and_limitation_boundaries() {
    let mut manifest = valid_manifest();
    manifest.output_claim_boundary = ClaimBoundary::Level1LocalReplay;
    manifest.executable_adapter_authorized = true;
    manifest.metrics.push(ZkMlMetric {
        kind: ZkMlMetricKind::VerifierTimeMs,
        value: Some(42),
        claim_boundary: ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
        notes: Vec::new(),
    });
    manifest.limitations = vec![
        "model accuracy statement without the matching proof wording".to_string(),
        "zkML metrics statement without the semantic boundary wording".to_string(),
    ];

    for (kind, path) in [
        (
            ZkMlWorkloadValidationIssueKind::ClaimBoundaryEscalation,
            "output_claim_boundary",
        ),
        (
            ZkMlWorkloadValidationIssueKind::ExecutableAdapterAuthorized,
            "executable_adapter_authorized",
        ),
        (
            ZkMlWorkloadValidationIssueKind::UnauthorizedExecutableMetric,
            "metrics[2].value",
        ),
        (
            ZkMlWorkloadValidationIssueKind::ClaimBoundaryEscalation,
            "metrics[2].claim_boundary",
        ),
        (
            ZkMlWorkloadValidationIssueKind::MissingLimitation,
            "limitations",
        ),
    ] {
        assert_issue(&manifest, kind, path);
    }
}

#[test]
fn zkml_manifest_malformed_json_reports_deserialization_context() {
    let error = deserialize_zkml_workload_manifest_json("{not-json")
        .expect_err("malformed manifest JSON should fail");

    assert!(error
        .to_string()
        .contains("deserialize_zkml_workload_manifest_json"));
}

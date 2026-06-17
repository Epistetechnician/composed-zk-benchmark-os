use std::fs;
use std::path::Path;

use zkbench_core::{
    compute_zkml_workload_digest_root, deserialize_zkml_workload_manifest_json,
    serialize_zkml_workload_manifest_json, validate_zkml_workload_manifest, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceClass, ZkMlMetric,
    ZkMlMetricKind, ZkMlModelArtifactRef, ZkMlWorkloadInputKind, ZkMlWorkloadInputRef,
    ZkMlWorkloadManifest,
};

use zkbench_core::{ZkMlWorkloadManifestVersion, ZkMlWorkloadValidationIssueKind};

fn digest(byte: u8) -> ArtifactDigest {
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: format!("{byte:02x}").repeat(32),
        byte_len: 64,
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
        notes: vec!["local model-like metadata only".to_string()],
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
        input(
            "append_preview",
            ZkMlWorkloadInputKind::EvidenceAppendPreview,
            ClaimBoundary::Level0DesignNote,
            EvidenceClass::DesignNote,
            3,
        ),
    ];
    let model_artifacts = vec![model_artifact()];
    let workload_digest_root = compute_zkml_workload_digest_root(&inputs, &model_artifacts)
        .expect("digest root should compute");

    ZkMlWorkloadManifest {
        manifest_id: "phase_n_zkml_workload".to_string(),
        version: ZkMlWorkloadManifestVersion::default(),
        workload_family_id: "ZkMlControlFlowMixed".to_string(),
        source_benchmark_instance_id: "zkml_control_flow_mixed_fixture".to_string(),
        control_flow_machine_id: "policy_gate_machine".to_string(),
        inputs,
        public_input_names: vec!["threshold".to_string(), "decision".to_string()],
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
                kind: ZkMlMetricKind::PublicInputCount,
                value: Some(2),
                claim_boundary: ClaimBoundary::Level0DesignNote,
                notes: Vec::new(),
            },
            ZkMlMetric {
                kind: ZkMlMetricKind::ProofSizeBytes,
                value: None,
                claim_boundary: ClaimBoundary::Level0DesignNote,
                notes: vec!["future executable adapter metric only".to_string()],
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

fn issue_kinds(manifest: &ZkMlWorkloadManifest) -> Vec<ZkMlWorkloadValidationIssueKind> {
    validate_zkml_workload_manifest(manifest)
        .issues
        .into_iter()
        .map(|issue| issue.kind)
        .collect()
}

#[test]
fn valid_zkml_workload_manifest_validates_as_level0_metadata() {
    let manifest = valid_manifest();
    let validation = validate_zkml_workload_manifest(&manifest);

    assert!(validation.valid, "issues: {:?}", validation.issues);
    assert_eq!(validation.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn zkml_workload_manifest_round_trips_as_json() {
    let manifest = valid_manifest();
    let json = serialize_zkml_workload_manifest_json(&manifest).expect("manifest should serialize");
    let round_trip =
        deserialize_zkml_workload_manifest_json(&json).expect("manifest should deserialize");

    assert_eq!(round_trip, manifest);
    assert!(!json.contains(concat!("Command", "::new")));
    assert!(!json.contains("official benchmark evidence\": true"));
}

#[test]
fn zkml_manifest_rejects_claim_elevation_execution_and_path_escape() {
    let mut manifest = valid_manifest();
    manifest.output_claim_boundary = ClaimBoundary::Level1LocalReplay;
    manifest.executable_adapter_authorized = true;
    manifest.inputs[0].artifact_uri = "/tmp/zkml_family_metadata.json".to_string();
    manifest.model_artifacts[0].artifact_uri = "../model.json".to_string();
    manifest.model_artifacts[0].claim_boundary = ClaimBoundary::Level1LocalReplay;
    manifest.metrics.push(ZkMlMetric {
        kind: ZkMlMetricKind::VerifierTimeMs,
        value: Some(42),
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        notes: Vec::new(),
    });
    manifest.limitations.clear();

    let kinds = issue_kinds(&manifest);

    assert!(kinds.contains(&ZkMlWorkloadValidationIssueKind::ClaimBoundaryEscalation));
    assert!(kinds.contains(&ZkMlWorkloadValidationIssueKind::ExecutableAdapterAuthorized));
    assert!(kinds.contains(&ZkMlWorkloadValidationIssueKind::InvalidArtifactRef));
    assert!(kinds.contains(&ZkMlWorkloadValidationIssueKind::ModelArtifactBoundary));
    assert!(kinds.contains(&ZkMlWorkloadValidationIssueKind::UnauthorizedExecutableMetric));
    assert!(kinds.contains(&ZkMlWorkloadValidationIssueKind::MissingLimitation));
}

#[test]
fn zkml_manifest_rejects_stale_workload_digest_root() {
    let mut manifest = valid_manifest();
    manifest.model_artifacts[0].digest = digest(12);

    let kinds = issue_kinds(&manifest);

    assert!(kinds.contains(&ZkMlWorkloadValidationIssueKind::WorkloadDigestRootMismatch));
}

#[test]
fn zkml_manifest_rejects_append_preview_and_level2_boundary_drift() {
    let mut manifest = valid_manifest();
    manifest.inputs.push(input(
        "level2_report",
        ZkMlWorkloadInputKind::Level2EligibilityReport,
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
        EvidenceClass::ReproducibleBenchmarkArtifact,
        4,
    ));
    manifest.inputs[2].claim_boundary = ClaimBoundary::Level1LocalReplay;
    manifest.workload_digest_root =
        compute_zkml_workload_digest_root(&manifest.inputs, &manifest.model_artifacts)
            .expect("digest root should recompute");

    let kinds = issue_kinds(&manifest);

    assert!(kinds.contains(&ZkMlWorkloadValidationIssueKind::AppendPreviewBoundary));
    assert!(kinds.contains(&ZkMlWorkloadValidationIssueKind::Level2EligibilityBoundary));
}

#[test]
fn zkml_manifest_source_exposes_no_executable_adapter_hooks() {
    let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crate should live under workspace/crates");
    let source = fs::read_to_string(repo_root.join("crates/zkbench-core/src/zkml.rs"))
        .expect("zkML manifest source should be readable");

    assert!(!source.contains("std::process::Command"));
    assert!(!source.contains(concat!("Command", "::new")));
    assert!(!source.contains("TcpStream"));
    assert!(!source.contains("reqwest"));
    assert!(!source.contains("ureq"));
}

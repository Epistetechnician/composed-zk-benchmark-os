use std::fs;
use std::path::Path;

use tempfile::tempdir;
use zkbench_core::{
    compute_artifact_digest_bytes, read_local_artifact_campaign_outputs,
    render_local_artifact_campaign_markdown, required_local_artifact_campaign_limitations,
    serialize_local_artifact_campaign_manifest_json,
    serialize_local_artifact_campaign_validation_json, validate_local_artifact_campaign_manifest,
    write_local_artifact_campaign_outputs, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary, LocalArtifactCampaignInputKind, LocalArtifactCampaignInputRef,
    LocalArtifactCampaignManifest, LocalArtifactCampaignRetentionPolicy,
    LocalArtifactCampaignValidationIssueKind, LocalArtifactCampaignVersion,
    LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH, LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH,
    LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH, LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH,
    LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH, LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
};

fn digest(label: &str) -> ArtifactDigest {
    let mut hex = format!("{label:0<64}");
    hex.truncate(64);
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: hex,
        byte_len: 32,
        kind: Some(ArtifactKind::Other),
        role: Some(ArtifactRole::Report),
    }
}

fn output_digest(bytes: &[u8]) -> ArtifactDigest {
    compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report))
}

fn write_digest_sidecar(root: &Path, relative_path: &str, bytes: &[u8]) {
    let sidecar = match relative_path {
        LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH => LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH,
        LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH => LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH,
        LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH => LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH,
        _ => panic!("unknown declared campaign file path: {relative_path}"),
    };
    fs::write(
        root.join(sidecar),
        format!("{}\n", output_digest(bytes).hex_digest),
    )
    .expect("digest sidecar writes");
}

fn rewrite_declared_file(root: &Path, relative_path: &str, bytes: &[u8]) {
    fs::write(root.join(relative_path), bytes).expect("declared campaign file writes");
    write_digest_sidecar(root, relative_path, bytes);
}

fn valid_manifest() -> LocalArtifactCampaignManifest {
    LocalArtifactCampaignManifest {
        campaign_id: "phase-194-local-campaign-alpha".to_string(),
        version: LocalArtifactCampaignVersion::default(),
        inputs: vec![
            LocalArtifactCampaignInputRef {
                input_id: "phase-u-output-alpha".to_string(),
                artifact_uri: "campaign-inputs/alpha/local-benchmark-artifact".to_string(),
                kind: LocalArtifactCampaignInputKind::LocalBenchmarkArtifactOutput,
                digest: digest("a"),
                claim_boundary: ClaimBoundary::Level1LocalReplay,
                notes: vec!["valid Phase U local artifact output".to_string()],
            },
            LocalArtifactCampaignInputRef {
                input_id: "pack-alpha".to_string(),
                artifact_uri: "packs/alpha/pack.json".to_string(),
                kind: LocalArtifactCampaignInputKind::BenchmarkPackManifest,
                digest: digest("b"),
                claim_boundary: ClaimBoundary::Level1LocalReplay,
                notes: vec!["source pack manifest".to_string()],
            },
        ],
        output_claim_boundary: ClaimBoundary::Level1LocalReplay,
        retention_policy: LocalArtifactCampaignRetentionPolicy::UntilReviewedPromotion,
        validation_gates: vec![
            "cargo test -p zkbench-core --test phase_u_local_benchmark_artifact".to_string(),
            "cargo test -p zkbench-core --test phase_v_local_artifact_campaign".to_string(),
        ],
        mutates_accepted_evidence_ledger: false,
        external_replay_authorized: false,
        official_benchmark_evidence: false,
        zk_backend_performance_claims: false,
        creates_level2_evidence: false,
        populates_score_axes_from_local_only: false,
        limitations: required_local_artifact_campaign_limitations()
            .into_iter()
            .map(str::to_string)
            .collect(),
        notes: vec!["durable local artifact campaign only".to_string()],
    }
}

fn issue_kinds(
    manifest: &LocalArtifactCampaignManifest,
) -> Vec<LocalArtifactCampaignValidationIssueKind> {
    validate_local_artifact_campaign_manifest(manifest)
        .issues
        .into_iter()
        .map(|issue| issue.kind)
        .collect()
}

#[test]
fn phase_194_campaign_validation_reports_identity_digest_duplicate_and_weak_boundary_edges() {
    let mut manifest = valid_manifest();
    manifest.campaign_id = "".to_string();
    manifest.inputs[0].input_id = " ".to_string();
    manifest.inputs[0].artifact_uri = "campaign-inputs/alpha/local-benchmark-artifact".to_string();
    manifest.inputs[1].artifact_uri = manifest.inputs[0].artifact_uri.clone();
    manifest.inputs[0].claim_boundary = ClaimBoundary::Level0DesignNote;
    manifest.inputs[0].digest = ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Unsupported,
        hex_digest: "not hex".to_string(),
        byte_len: 0,
        kind: None,
        role: None,
    };

    let kinds = issue_kinds(&manifest);

    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::EmptyIdentity));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::InvalidCampaignId));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::DuplicateArtifactUri));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::InvalidDigest));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::ClaimBoundaryEscalation));
}

#[test]
fn phase_194_campaign_validation_reports_missing_inputs_and_input_ref_schemes() {
    let mut manifest = valid_manifest();
    manifest.inputs.clear();
    let kinds = issue_kinds(&manifest);
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::MissingInputs));
    assert!(kinds
        .contains(&LocalArtifactCampaignValidationIssueKind::MissingLocalBenchmarkArtifactOutput));

    let mut manifest = valid_manifest();
    manifest.inputs[0].artifact_uri = "https://example.invalid/artifact".to_string();
    manifest.inputs[1].artifact_uri = "packs/alpha/$pack.json".to_string();
    let validation = validate_local_artifact_campaign_manifest(&manifest);

    assert_eq!(
        validation
            .issues
            .iter()
            .filter(
                |issue| issue.kind == LocalArtifactCampaignValidationIssueKind::InvalidArtifactRef
            )
            .count(),
        2
    );
}

#[test]
fn phase_194_campaign_render_rejects_invalid_manifest_and_invalid_validation_report() {
    let mut invalid_manifest = valid_manifest();
    invalid_manifest.validation_gates.clear();
    let valid_validation = validate_local_artifact_campaign_manifest(&valid_manifest());
    let error = render_local_artifact_campaign_markdown(&invalid_manifest, &valid_validation)
        .expect_err("invalid manifest should not render");
    assert!(error
        .to_string()
        .contains("invalid local artifact campaign manifest"));

    let manifest = valid_manifest();
    let mut invalid_validation = validate_local_artifact_campaign_manifest(&manifest);
    invalid_validation.valid = false;
    let error = render_local_artifact_campaign_markdown(&manifest, &invalid_validation)
        .expect_err("invalid validation report should not render");
    assert!(error
        .to_string()
        .contains("validation report must be valid before rendering"));
}

#[test]
fn phase_194_campaign_output_root_rejects_empty_path_files_and_non_directories() {
    let manifest = valid_manifest();
    let error = write_local_artifact_campaign_outputs(Path::new(""), &manifest, false, &[])
        .expect_err("empty output root should fail");
    assert!(error.to_string().contains("output root must be non-empty"));

    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("campaign-file");
    fs::write(&output_root, "not a directory").expect("output root file writes");

    let write_error = write_local_artifact_campaign_outputs(&output_root, &manifest, false, &[])
        .expect_err("existing file output root should fail");
    assert!(write_error
        .to_string()
        .contains("output root is an existing file"));

    let read_error = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("file output root should not read as campaign directory");
    assert!(read_error
        .to_string()
        .contains("output root must be a directory"));
}

#[test]
fn phase_194_campaign_readback_rejects_digest_consistent_manifest_drift() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("phase-194-campaign");
    let manifest = valid_manifest();
    write_local_artifact_campaign_outputs(&output_root, &manifest, false, &[])
        .expect("campaign writes");

    rewrite_declared_file(
        &output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH,
        b"{not manifest json",
    );
    let error = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("malformed manifest should fail");
    assert!(error
        .to_string()
        .contains("local_artifact_campaign.manifest"));

    rewrite_declared_file(
        &output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH,
        &[0xff, 0xfe, 0xfd],
    );
    let error = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("non-UTF8 manifest should fail");
    assert!(error.to_string().contains("manifest JSON is not UTF-8"));
}

#[test]
fn phase_194_campaign_readback_rejects_validation_and_markdown_semantic_drift() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("phase-194-campaign");
    let manifest = valid_manifest();
    write_local_artifact_campaign_outputs(&output_root, &manifest, false, &[])
        .expect("campaign writes");

    rewrite_declared_file(
        &output_root,
        LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
        b"{not validation json",
    );
    let error = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("malformed validation should fail");
    assert!(error
        .to_string()
        .contains("local_artifact_campaign.validation"));

    let validation = validate_local_artifact_campaign_manifest(&manifest);
    let mut drifted_validation =
        serde_json::to_value(&validation).expect("validation converts to value");
    drifted_validation["input_count"] = serde_json::json!(999);
    let drifted_validation_bytes =
        serde_json::to_vec_pretty(&drifted_validation).expect("validation value serializes");
    rewrite_declared_file(
        &output_root,
        LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
        &drifted_validation_bytes,
    );
    let error = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("validation semantic drift should fail");
    assert!(error
        .to_string()
        .contains("validation report does not match manifest"));

    let validation_json =
        serialize_local_artifact_campaign_validation_json(&validation).expect("validation json");
    rewrite_declared_file(
        &output_root,
        LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
        validation_json.as_bytes(),
    );
    rewrite_declared_file(
        &output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH,
        b"# Local Artifact Campaign\n\nDrifted markdown.\n",
    );
    let error = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("markdown semantic drift should fail");
    assert!(error
        .to_string()
        .contains("rendered Markdown does not match manifest and validation"));
}

#[test]
fn phase_194_campaign_readback_rejects_non_utf8_sidecars_and_declared_files() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("phase-194-campaign");
    let manifest = valid_manifest();
    write_local_artifact_campaign_outputs(&output_root, &manifest, false, &[])
        .expect("campaign writes");

    fs::write(
        output_root.join(LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH),
        [0xff, 0xfe, 0xfd],
    )
    .expect("non-UTF8 sidecar writes");
    let error = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("non-UTF8 sidecar should fail");
    assert!(error
        .to_string()
        .contains("manifest digest sidecar is not UTF-8"));

    let manifest_json =
        serialize_local_artifact_campaign_manifest_json(&manifest).expect("manifest json");
    rewrite_declared_file(
        &output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH,
        manifest_json.as_bytes(),
    );
    rewrite_declared_file(
        &output_root,
        LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH,
        &[0xff, 0xfe, 0xfd],
    );
    let error = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("non-UTF8 markdown should fail");
    assert!(error.to_string().contains("rendered Markdown is not UTF-8"));
}

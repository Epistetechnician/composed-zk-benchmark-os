use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    build_local_artifact_campaign_input_from_phase_u_output,
    compute_local_artifact_campaign_manifest_digest,
    deserialize_local_artifact_campaign_manifest_json, read_local_artifact_campaign_outputs,
    render_local_artifact_campaign_markdown, required_local_artifact_campaign_limitations,
    required_local_benchmark_artifact_limitations, serialize_local_artifact_campaign_manifest_json,
    serialize_local_artifact_campaign_validation_json, validate_local_artifact_campaign_manifest,
    write_local_artifact_campaign_outputs, write_local_benchmark_artifact_outputs, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
    LocalArtifactCampaignInputKind, LocalArtifactCampaignInputRef, LocalArtifactCampaignManifest,
    LocalArtifactCampaignRetentionPolicy, LocalArtifactCampaignValidationIssueKind,
    LocalArtifactCampaignVersion, LocalBenchmarkArtifactInputKind, LocalBenchmarkArtifactInputRef,
    LocalBenchmarkArtifactManifest, LocalBenchmarkArtifactVersion,
    LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH, LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH,
    LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH, LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH,
    LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH, LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
    LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH,
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

fn valid_manifest() -> LocalArtifactCampaignManifest {
    LocalArtifactCampaignManifest {
        campaign_id: "phase-v-local-campaign-alpha".to_string(),
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
        retention_policy: LocalArtifactCampaignRetentionPolicy::ManualDeletion,
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

fn phase_u_manifest() -> LocalBenchmarkArtifactManifest {
    LocalBenchmarkArtifactManifest {
        artifact_id: "phase-u-alpha".to_string(),
        version: LocalBenchmarkArtifactVersion::default(),
        inputs: vec![LocalBenchmarkArtifactInputRef {
            input_id: "pack-alpha".to_string(),
            artifact_uri: "packs/alpha/pack.json".to_string(),
            kind: LocalBenchmarkArtifactInputKind::BenchmarkPackManifest,
            digest: digest("c"),
            claim_boundary: ClaimBoundary::Level1LocalReplay,
            notes: vec!["valid local pack manifest".to_string()],
        }],
        output_claim_boundary: ClaimBoundary::Level1LocalReplay,
        mutates_accepted_evidence_ledger: false,
        external_replay_authorized: false,
        official_benchmark_evidence: false,
        zk_backend_performance_claims: false,
        creates_level2_evidence: false,
        populates_score_axes_from_local_only: false,
        limitations: required_local_benchmark_artifact_limitations()
            .into_iter()
            .map(str::to_string)
            .collect(),
        notes: vec!["local reproducibility packaging only".to_string()],
    }
}

#[test]
fn local_artifact_campaign_manifest_round_trips_and_digests() {
    let manifest = valid_manifest();
    let validation = validate_local_artifact_campaign_manifest(&manifest);
    assert!(validation.valid, "{validation:?}");
    assert!(validation.accepted_evidence_ledger_non_mutation);
    assert!(validation.score_axes_remain_unpopulated);

    let json =
        serialize_local_artifact_campaign_manifest_json(&manifest).expect("serialize manifest");
    let round_trip =
        deserialize_local_artifact_campaign_manifest_json(&json).expect("deserialize manifest");
    assert_eq!(round_trip, manifest);
    assert_eq!(
        compute_local_artifact_campaign_manifest_digest(&manifest).expect("digest"),
        compute_local_artifact_campaign_manifest_digest(&round_trip).expect("digest")
    );

    let validation_json =
        serialize_local_artifact_campaign_validation_json(&validation).expect("validation json");
    assert!(validation_json.contains("accepted_evidence_ledger_non_mutation"));
    let markdown =
        render_local_artifact_campaign_markdown(&manifest, &validation).expect("markdown");
    assert!(markdown.contains("Local artifact campaigns are not official benchmark evidence."));
    assert!(markdown.contains("Official submission requires a separate explicit submission phase."));
}

#[test]
fn local_artifact_campaign_validation_rejects_claim_elevation_and_unsafe_refs() {
    let mut manifest = valid_manifest();
    manifest.campaign_id = "../bad".to_string();
    manifest.output_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    manifest.external_replay_authorized = true;
    manifest.official_benchmark_evidence = true;
    manifest.zk_backend_performance_claims = true;
    manifest.creates_level2_evidence = true;
    manifest.mutates_accepted_evidence_ledger = true;
    manifest.populates_score_axes_from_local_only = true;
    manifest.inputs[0].artifact_uri = "../local-benchmark-artifact".to_string();
    manifest.inputs[1].input_id = manifest.inputs[0].input_id.clone();
    manifest.validation_gates.clear();
    manifest.limitations.pop();

    let validation = validate_local_artifact_campaign_manifest(&manifest);
    assert!(!validation.valid);
    assert!(!validation.accepted_evidence_ledger_non_mutation);
    assert!(!validation.score_axes_remain_unpopulated);
    let kinds = validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<Vec<_>>();
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::InvalidCampaignId));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::DuplicateInputId));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::InvalidArtifactRef));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::ClaimBoundaryEscalation));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::MissingValidationGate));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::ExternalReplayAuthorized));
    assert!(
        kinds.contains(&LocalArtifactCampaignValidationIssueKind::OfficialBenchmarkEvidenceClaim)
    );
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::ZkBackendPerformanceClaim));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::Level2EvidenceClaim));
    assert!(kinds
        .contains(&LocalArtifactCampaignValidationIssueKind::AcceptedEvidenceLedgerMutationClaim));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::LocalOnlyScoreAxisPopulation));
    assert!(kinds.contains(&LocalArtifactCampaignValidationIssueKind::MissingLimitation));
}

#[test]
fn local_artifact_campaign_requires_phase_u_output_reference() {
    let mut manifest = valid_manifest();
    manifest
        .inputs
        .retain(|input| input.kind != LocalArtifactCampaignInputKind::LocalBenchmarkArtifactOutput);

    let validation = validate_local_artifact_campaign_manifest(&manifest);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == LocalArtifactCampaignValidationIssueKind::MissingLocalBenchmarkArtifactOutput
    }));
}

#[test]
fn local_artifact_campaign_input_builder_validates_phase_u_output_root() {
    let dir = tempdir().expect("tempdir");
    let phase_u_root = dir.path().join("local-benchmark-artifact");
    write_local_benchmark_artifact_outputs(&phase_u_root, &phase_u_manifest(), false, &[])
        .expect("phase u output writes");

    let input = build_local_artifact_campaign_input_from_phase_u_output(
        "phase-u-output-alpha",
        "campaign-inputs/alpha/local-benchmark-artifact",
        &phase_u_root,
        &[],
        ClaimBoundary::Level1LocalReplay,
        vec!["validated Phase U output".to_string()],
    )
    .expect("phase u output input builds");
    assert_eq!(
        input.kind,
        LocalArtifactCampaignInputKind::LocalBenchmarkArtifactOutput
    );
    assert_eq!(input.digest.algorithm, ArtifactDigestAlgorithm::Sha256);

    fs::write(
        phase_u_root.join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH),
        "0".repeat(64),
    )
    .expect("tamper phase u digest");
    let error = build_local_artifact_campaign_input_from_phase_u_output(
        "phase-u-output-alpha",
        "campaign-inputs/alpha/local-benchmark-artifact",
        &phase_u_root,
        &[],
        ClaimBoundary::Level1LocalReplay,
        vec![],
    )
    .expect_err("invalid phase u output should be rejected");
    assert!(error
        .to_string()
        .contains("rendered Markdown bytes do not match digest sidecar"));
}

#[test]
fn local_artifact_campaign_outputs_write_and_read_declared_files_only() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("phase-v-campaign");
    let manifest = valid_manifest();

    let output = write_local_artifact_campaign_outputs(&output_root, &manifest, false, &[])
        .expect("write campaign outputs");
    assert!(output.manifest_digest.byte_len > 0);
    assert!(output.validation_digest.byte_len > 0);
    assert!(output.markdown_digest.byte_len > 0);
    assert!(output_root
        .join(LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH)
        .is_file());
    assert!(output_root
        .join(LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH)
        .is_file());
    assert!(output_root
        .join(LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH)
        .is_file());
    assert!(output_root
        .join(LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_DIGEST_PATH)
        .is_file());
    assert!(output_root
        .join(LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH)
        .is_file());
    assert!(output_root
        .join(LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_DIGEST_PATH)
        .is_file());

    let read_output =
        read_local_artifact_campaign_outputs(&output_root, &[]).expect("read outputs");
    assert_eq!(read_output, output);
}

#[test]
fn local_artifact_campaign_outputs_reject_drift_and_repair_overwrite() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("phase-v-campaign");
    let manifest = valid_manifest();

    write_local_artifact_campaign_outputs(&output_root, &manifest, false, &[])
        .expect("write campaign outputs");

    let non_overwrite = write_local_artifact_campaign_outputs(&output_root, &manifest, false, &[])
        .expect_err("non-overwrite should fail");
    assert!(non_overwrite
        .to_string()
        .contains("explicit overwrite is required"));

    let mut drifted_manifest = manifest.clone();
    drifted_manifest.campaign_id = "phase-v-local-campaign-beta".to_string();
    let repair = write_local_artifact_campaign_outputs(&output_root, &drifted_manifest, true, &[])
        .expect_err("repair overwrite should fail");
    assert!(repair.to_string().contains("refusing repair overwrite"));

    fs::write(
        output_root.join(LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_DIGEST_PATH),
        "0".repeat(64),
    )
    .expect("tamper digest");
    let stale = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("stale digest should fail");
    assert!(stale
        .to_string()
        .contains("validation JSON bytes do not match digest sidecar"));
}

#[test]
fn local_artifact_campaign_outputs_reject_partial_unexpected_and_protected_roots() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("phase-v-campaign");
    let manifest = valid_manifest();

    let protected_parent = dir.path().join("protected");
    let protected_child = protected_parent.join("local-benchmark-artifact");
    fs::create_dir_all(&protected_parent).expect("protected parent");
    fs::write(&protected_child, "{}").expect("protected file");
    let overlap = write_local_artifact_campaign_outputs(
        &protected_parent,
        &manifest,
        false,
        std::slice::from_ref(&protected_child),
    )
    .expect_err("protected overlap should fail");
    assert!(overlap.to_string().contains("overlaps protected path"));

    fs::create_dir_all(&output_root).expect("output root");
    fs::write(
        output_root.join(LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH),
        "{}",
    )
    .expect("partial file");
    let partial = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("partial campaign should fail");
    assert!(partial.to_string().contains("missing required output file"));

    fs::remove_dir_all(&output_root).expect("remove partial");
    write_local_artifact_campaign_outputs(&output_root, &manifest, false, &[])
        .expect("write outputs");
    fs::write(output_root.join("unexpected.txt"), "unexpected").expect("unexpected");
    let unexpected = read_local_artifact_campaign_outputs(&output_root, &[])
        .expect_err("unexpected file should fail");
    assert!(unexpected
        .to_string()
        .contains("unexpected file in output root"));
}

#[cfg(unix)]
#[test]
fn local_artifact_campaign_outputs_reject_symlinks() {
    use std::os::unix::fs::symlink;

    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("phase-v-campaign");
    let manifest = valid_manifest();

    write_local_artifact_campaign_outputs(&output_root, &manifest, false, &[])
        .expect("write outputs");
    fs::remove_file(output_root.join(LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH))
        .expect("remove markdown");
    symlink(
        output_root.join(LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH),
        output_root.join(LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH),
    )
    .expect("symlink");

    let error =
        read_local_artifact_campaign_outputs(&output_root, &[]).expect_err("symlink should fail");
    assert!(error.to_string().contains("symlinks are not allowed"));
}

#[cfg(unix)]
#[test]
fn local_artifact_campaign_outputs_reject_symlink_parent_into_protected_root() {
    use std::os::unix::fs::symlink;

    let dir = tempdir().expect("tempdir");
    let protected_root = dir.path().join("protected-source");
    fs::create_dir_all(&protected_root).expect("protected root");
    fs::write(protected_root.join("campaign-manifest.json"), "{}").expect("protected file");

    let linked_root = dir.path().join("linked-source");
    symlink(&protected_root, &linked_root).expect("symlink protected root");
    let output_root = linked_root.join("phase-v-campaign");

    let error = write_local_artifact_campaign_outputs(
        &output_root,
        &valid_manifest(),
        false,
        std::slice::from_ref(&protected_root),
    )
    .expect_err("symlink parent into protected root should fail");
    assert!(error.to_string().contains("overlaps protected path"));
    assert!(!output_root.exists());
}

#[test]
fn local_artifact_campaign_source_scan_exposes_no_runtime_surface() {
    let source = fs::read_to_string("src/local_artifact_campaign.rs").expect("source");
    for forbidden in [
        "std::process::Command",
        "reqwest",
        "TcpStream",
        "CommandLine",
        "package.json",
        "official_benchmark_evidence: true",
        "creates_level2_evidence: true",
        "populates_score_axes_from_local_only: true",
    ] {
        assert!(
            !source.contains(forbidden),
            "unexpected runtime or claim-elevation surface: {forbidden}"
        );
    }
}

use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    compute_local_benchmark_artifact_manifest_digest,
    deserialize_local_benchmark_artifact_manifest_json, read_local_benchmark_artifact_outputs,
    render_local_benchmark_artifact_markdown, required_local_benchmark_artifact_limitations,
    serialize_local_benchmark_artifact_manifest_json, validate_local_benchmark_artifact_manifest,
    write_local_benchmark_artifact_outputs, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary, LocalBenchmarkArtifactInputKind, LocalBenchmarkArtifactInputRef,
    LocalBenchmarkArtifactManifest, LocalBenchmarkArtifactValidationIssueKind,
    LocalBenchmarkArtifactVersion, LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH,
    LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH, LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH,
    LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH,
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

fn valid_manifest() -> LocalBenchmarkArtifactManifest {
    LocalBenchmarkArtifactManifest {
        artifact_id: "local-artifact-alpha".to_string(),
        version: LocalBenchmarkArtifactVersion::default(),
        inputs: vec![
            LocalBenchmarkArtifactInputRef {
                input_id: "pack-alpha".to_string(),
                artifact_uri: "packs/alpha/pack.json".to_string(),
                kind: LocalBenchmarkArtifactInputKind::BenchmarkPackManifest,
                digest: digest("a"),
                claim_boundary: ClaimBoundary::Level1LocalReplay,
                notes: vec!["valid local pack manifest".to_string()],
            },
            LocalBenchmarkArtifactInputRef {
                input_id: "readiness-alpha".to_string(),
                artifact_uri: "packs/alpha/readiness/pack-readiness-report.json".to_string(),
                kind: LocalBenchmarkArtifactInputKind::PackReadinessReport,
                digest: digest("b"),
                claim_boundary: ClaimBoundary::Level0DesignNote,
                notes: vec!["local readiness metadata".to_string()],
            },
        ],
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
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
fn local_benchmark_artifact_manifest_round_trips_and_digests() {
    let manifest = valid_manifest();
    let validation = validate_local_benchmark_artifact_manifest(&manifest);
    assert!(validation.valid, "{validation:?}");

    let json =
        serialize_local_benchmark_artifact_manifest_json(&manifest).expect("serialize manifest");
    let round_trip =
        deserialize_local_benchmark_artifact_manifest_json(&json).expect("deserialize manifest");
    assert_eq!(round_trip, manifest);
    assert_eq!(
        compute_local_benchmark_artifact_manifest_digest(&manifest).expect("digest"),
        compute_local_benchmark_artifact_manifest_digest(&round_trip).expect("digest")
    );

    let markdown = render_local_benchmark_artifact_markdown(&manifest).expect("markdown");
    assert!(markdown.contains("Local benchmark artifacts are not official benchmark evidence."));
    assert!(markdown.contains("Score axes remain unpopulated for local-only evidence."));
}

#[test]
fn local_benchmark_artifact_validation_rejects_claim_elevation_and_unsafe_refs() {
    let mut manifest = valid_manifest();
    manifest.output_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    manifest.external_replay_authorized = true;
    manifest.official_benchmark_evidence = true;
    manifest.zk_backend_performance_claims = true;
    manifest.creates_level2_evidence = true;
    manifest.mutates_accepted_evidence_ledger = true;
    manifest.populates_score_axes_from_local_only = true;
    manifest.inputs[0].artifact_uri = "../pack.json".to_string();
    manifest.limitations.pop();

    let validation = validate_local_benchmark_artifact_manifest(&manifest);
    assert!(!validation.valid);
    let kinds = validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<Vec<_>>();
    assert!(kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::ClaimBoundaryEscalation));
    assert!(kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::InvalidArtifactRef));
    assert!(kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::ExternalReplayAuthorized));
    assert!(
        kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::OfficialBenchmarkEvidenceClaim)
    );
    assert!(kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::ZkBackendPerformanceClaim));
    assert!(kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::Level2EvidenceClaim));
    assert!(kinds
        .contains(&LocalBenchmarkArtifactValidationIssueKind::AcceptedEvidenceLedgerMutationClaim));
    assert!(
        kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::LocalOnlyScoreAxisPopulation)
    );
    assert!(kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::MissingLimitation));
}

#[test]
fn local_benchmark_artifact_outputs_write_and_read_declared_files_only() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("local-benchmark-artifact");
    let manifest = valid_manifest();

    let output = write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect("write outputs");
    assert!(output.manifest_digest.byte_len > 0);
    assert!(output.markdown_digest.byte_len > 0);
    assert!(output_root
        .join(LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH)
        .is_file());
    assert!(output_root
        .join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH)
        .is_file());
    assert!(output_root
        .join(LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH)
        .is_file());
    assert!(output_root
        .join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH)
        .is_file());

    let read_output =
        read_local_benchmark_artifact_outputs(&output_root, &[]).expect("read outputs");
    assert_eq!(read_output, output);
}

#[test]
fn local_benchmark_artifact_outputs_reject_drift_and_repair_overwrite() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("local-benchmark-artifact");
    let manifest = valid_manifest();

    write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect("write outputs");

    let non_overwrite = write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect_err("non-overwrite should fail");
    assert!(non_overwrite
        .to_string()
        .contains("explicit overwrite is required"));

    let mut drifted_manifest = manifest.clone();
    drifted_manifest.artifact_id = "local-artifact-beta".to_string();
    let repair = write_local_benchmark_artifact_outputs(&output_root, &drifted_manifest, true, &[])
        .expect_err("repair overwrite should fail");
    assert!(repair.to_string().contains("refusing repair overwrite"));

    fs::write(
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH),
        "0".repeat(64),
    )
    .expect("tamper digest");
    let stale = read_local_benchmark_artifact_outputs(&output_root, &[])
        .expect_err("stale digest should fail");
    assert!(stale
        .to_string()
        .contains("rendered Markdown bytes do not match digest sidecar"));
}

#[test]
fn local_benchmark_artifact_outputs_reject_partial_unexpected_and_protected_roots() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("local-benchmark-artifact");
    let manifest = valid_manifest();

    let protected_parent = dir.path().join("protected");
    let protected_child = protected_parent.join("pack.json");
    fs::create_dir_all(&protected_parent).expect("protected parent");
    fs::write(&protected_child, "{}").expect("protected file");
    let overlap = write_local_benchmark_artifact_outputs(
        &protected_parent,
        &manifest,
        false,
        std::slice::from_ref(&protected_child),
    )
    .expect_err("protected overlap should fail");
    assert!(overlap.to_string().contains("overlaps protected path"));

    fs::create_dir_all(&output_root).expect("output root");
    fs::write(
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH),
        "{}",
    )
    .expect("partial file");
    let partial = read_local_benchmark_artifact_outputs(&output_root, &[])
        .expect_err("partial bundle should fail");
    assert!(partial.to_string().contains("missing required output file"));

    fs::remove_dir_all(&output_root).expect("remove partial");
    write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect("write outputs");
    fs::write(output_root.join("unexpected.txt"), "unexpected").expect("unexpected");
    let unexpected = read_local_benchmark_artifact_outputs(&output_root, &[])
        .expect_err("unexpected file should fail");
    assert!(unexpected
        .to_string()
        .contains("unexpected file in output root"));
}

#[cfg(unix)]
#[test]
fn local_benchmark_artifact_outputs_reject_symlinks() {
    use std::os::unix::fs::symlink;

    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("local-benchmark-artifact");
    let manifest = valid_manifest();

    write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect("write outputs");
    fs::remove_file(output_root.join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH))
        .expect("remove markdown");
    symlink(
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH),
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH),
    )
    .expect("symlink");

    let error =
        read_local_benchmark_artifact_outputs(&output_root, &[]).expect_err("symlink should fail");
    assert!(error.to_string().contains("symlinks are not allowed"));
}

#[cfg(unix)]
#[test]
fn local_benchmark_artifact_outputs_reject_symlink_parent_into_protected_root() {
    use std::os::unix::fs::symlink;

    let dir = tempdir().expect("tempdir");
    let protected_root = dir.path().join("protected-source");
    fs::create_dir_all(&protected_root).expect("protected root");
    fs::write(protected_root.join("pack.json"), "{}").expect("protected file");

    let linked_root = dir.path().join("linked-source");
    symlink(&protected_root, &linked_root).expect("symlink protected root");
    let output_root = linked_root.join("local-benchmark-artifact");

    let error = write_local_benchmark_artifact_outputs(
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
fn local_benchmark_artifact_source_scan_exposes_no_runtime_surface() {
    let source = fs::read_to_string("src/local_benchmark_artifact.rs").expect("source");
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

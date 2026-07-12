use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    compute_artifact_digest_bytes, deserialize_local_benchmark_artifact_manifest_json,
    read_local_benchmark_artifact_outputs, render_local_benchmark_artifact_markdown,
    required_local_benchmark_artifact_limitations, validate_local_benchmark_artifact_manifest,
    write_local_benchmark_artifact_outputs, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary, LocalBenchmarkArtifactInputKind, LocalBenchmarkArtifactInputRef,
    LocalBenchmarkArtifactManifest, LocalBenchmarkArtifactValidationIssueKind,
    LocalBenchmarkArtifactVersion, LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH,
    LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH, LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH,
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
        artifact_id: "phase-183-local-artifact".to_string(),
        version: LocalBenchmarkArtifactVersion::default(),
        inputs: vec![
            LocalBenchmarkArtifactInputRef {
                input_id: "pack".to_string(),
                artifact_uri: "packs/phase-183/pack.json".to_string(),
                kind: LocalBenchmarkArtifactInputKind::BenchmarkPackManifest,
                digest: digest("a"),
                claim_boundary: ClaimBoundary::Level1LocalReplay,
                notes: vec!["local pack manifest".to_string()],
            },
            LocalBenchmarkArtifactInputRef {
                input_id: "audit".to_string(),
                artifact_uri: "audit/phase-183/index.json".to_string(),
                kind: LocalBenchmarkArtifactInputKind::LocalAuditIndexManifest,
                digest: digest("b"),
                claim_boundary: ClaimBoundary::Level0DesignNote,
                notes: vec!["local audit metadata".to_string()],
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
        notes: vec!["local packaging only".to_string()],
    }
}

fn issue_kinds(
    validation: &zkbench_core::LocalBenchmarkArtifactValidation,
) -> Vec<LocalBenchmarkArtifactValidationIssueKind> {
    validation.issues.iter().map(|issue| issue.kind).collect()
}

#[test]
fn local_artifact_validation_reports_identity_missing_duplicate_digest_and_boundary_drift() {
    let mut manifest = valid_manifest();
    manifest.artifact_id = " ".to_string();
    manifest.inputs[0].input_id = " ".to_string();
    manifest.inputs[1].input_id = " ".to_string();
    manifest.inputs[1].artifact_uri = manifest.inputs[0].artifact_uri.clone();
    manifest.inputs[0].digest.algorithm = ArtifactDigestAlgorithm::Unsupported;
    manifest.inputs[0].digest.hex_digest = "not-hex".to_string();
    manifest.inputs[0].digest.byte_len = 0;
    manifest.inputs[0].claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    manifest.output_claim_boundary = ClaimBoundary::Level1LocalReplay;

    let validation = validate_local_benchmark_artifact_manifest(&manifest);
    assert!(!validation.valid);
    let kinds = issue_kinds(&validation);
    for expected in [
        LocalBenchmarkArtifactValidationIssueKind::EmptyIdentity,
        LocalBenchmarkArtifactValidationIssueKind::DuplicateInputId,
        LocalBenchmarkArtifactValidationIssueKind::DuplicateArtifactUri,
        LocalBenchmarkArtifactValidationIssueKind::InvalidDigest,
        LocalBenchmarkArtifactValidationIssueKind::ClaimBoundaryEscalation,
    ] {
        assert!(
            kinds.contains(&expected),
            "missing {expected:?}: {validation:?}"
        );
    }
}

#[test]
fn local_artifact_validation_reports_missing_inputs_benchmark_pack_and_portability_drift() {
    let mut missing = valid_manifest();
    missing.inputs.clear();
    let validation = validate_local_benchmark_artifact_manifest(&missing);
    let kinds = issue_kinds(&validation);
    assert!(kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::MissingInputs));
    assert!(
        kinds.contains(&LocalBenchmarkArtifactValidationIssueKind::MissingBenchmarkPackManifest)
    );

    let mut no_pack = valid_manifest();
    no_pack.inputs[0].kind = LocalBenchmarkArtifactInputKind::OtherLocalMetadata;
    let validation = validate_local_benchmark_artifact_manifest(&no_pack);
    assert!(issue_kinds(&validation)
        .contains(&LocalBenchmarkArtifactValidationIssueKind::MissingBenchmarkPackManifest));

    let invalid_refs = [
        "",
        "/absolute/path.json",
        "nested\\windows.json",
        "https://example.invalid/artifact.json",
        "unsafe|pipe.json",
        "unsafe;semi.json",
        "unsafe$dollar.json",
    ];
    for artifact_uri in invalid_refs {
        let mut manifest = valid_manifest();
        manifest.inputs[0].artifact_uri = artifact_uri.to_string();
        let validation = validate_local_benchmark_artifact_manifest(&manifest);
        assert!(
            issue_kinds(&validation)
                .contains(&LocalBenchmarkArtifactValidationIssueKind::InvalidArtifactRef),
            "expected invalid artifact uri rejection for {artifact_uri:?}: {validation:?}"
        );
    }
}

#[test]
fn local_artifact_render_and_deserialize_fail_closed_for_invalid_inputs() {
    let mut invalid = valid_manifest();
    invalid.artifact_id.clear();
    let render_error =
        render_local_benchmark_artifact_markdown(&invalid).expect_err("invalid manifest rejects");
    assert!(render_error
        .to_string()
        .contains("invalid local benchmark artifact manifest"));

    let parse_error = deserialize_local_benchmark_artifact_manifest_json("{\"artifact_id\":")
        .expect_err("malformed manifest JSON should report context");
    assert!(parse_error
        .to_string()
        .contains("local_benchmark_artifact.manifest"));
}

#[test]
fn local_artifact_outputs_reject_file_roots_and_allow_matching_overwrite() {
    let dir = tempdir().expect("tempdir");
    let manifest = valid_manifest();
    let file_root = dir.path().join("file-root");
    fs::write(&file_root, "not a directory").expect("file root");

    let write_error = write_local_benchmark_artifact_outputs(&file_root, &manifest, false, &[])
        .expect_err("write should reject file root");
    assert!(write_error
        .to_string()
        .contains("output root is an existing file"));
    let read_error =
        read_local_benchmark_artifact_outputs(&file_root, &[]).expect_err("read rejects file root");
    assert!(read_error
        .to_string()
        .contains("output root must be a directory"));

    let output_root = dir.path().join("artifact-root");
    let first = write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect("initial write");
    let overwrite = write_local_benchmark_artifact_outputs(&output_root, &manifest, true, &[])
        .expect("matching overwrite is idempotent");
    assert_eq!(first, overwrite);
}

#[test]
fn local_artifact_outputs_reject_sidecar_manifest_and_markdown_byte_drift() {
    let dir = tempdir().expect("tempdir");
    let output_root = dir.path().join("artifact-root");
    let manifest = valid_manifest();
    write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect("write outputs");

    fs::write(
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH),
        [0xff],
    )
    .expect("non-utf8 sidecar");
    let non_utf8 = read_local_benchmark_artifact_outputs(&output_root, &[])
        .expect_err("non-UTF8 sidecar should reject");
    assert!(non_utf8
        .to_string()
        .contains("manifest digest sidecar is not UTF-8"));

    fs::remove_dir_all(&output_root).expect("reset outputs after sidecar corruption");
    write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect("restore outputs");
    fs::write(
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MANIFEST_DIGEST_PATH),
        "0".repeat(64),
    )
    .expect("stale manifest digest");
    let stale_manifest = read_local_benchmark_artifact_outputs(&output_root, &[])
        .expect_err("manifest digest drift should reject");
    assert!(stale_manifest
        .to_string()
        .contains("manifest JSON bytes do not match digest sidecar"));

    fs::remove_dir_all(&output_root).expect("reset outputs after stale digest");
    write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect("restore outputs again");
    let bad_markdown = [0xff, 0xfe];
    fs::write(
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH),
        bad_markdown,
    )
    .expect("bad markdown");
    let bad_markdown_digest = compute_artifact_digest_bytes(
        &bad_markdown,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    );
    fs::write(
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH),
        format!("{}\n", bad_markdown_digest.hex_digest),
    )
    .expect("matching digest for bad markdown");
    let markdown_utf8 = read_local_benchmark_artifact_outputs(&output_root, &[])
        .expect_err("non-UTF8 markdown should reject after digest check");
    assert!(markdown_utf8
        .to_string()
        .contains("rendered Markdown is not UTF-8"));

    // Tamper the markdown to valid UTF-8 with different content and a matching
    // digest sidecar so the UTF-8 and digest checks pass but the deterministic
    // render-match check fails.
    fs::remove_dir_all(&output_root).expect("reset outputs before markdown drift");
    write_local_benchmark_artifact_outputs(&output_root, &manifest, false, &[])
        .expect("restore outputs for markdown drift");
    let tampered_markdown = "tampered markdown content that is valid utf-8\n";
    let tampered_bytes = tampered_markdown.as_bytes();
    fs::write(
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH),
        tampered_bytes,
    )
    .expect("tamper markdown to valid utf-8");
    let tampered_digest = compute_artifact_digest_bytes(
        tampered_bytes,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    );
    fs::write(
        output_root.join(LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_DIGEST_PATH),
        format!("{}\n", tampered_digest.hex_digest),
    )
    .expect("matching digest for tampered markdown");
    let markdown_drift = read_local_benchmark_artifact_outputs(&output_root, &[])
        .expect_err("markdown not matching manifest render should reject");
    assert!(markdown_drift
        .to_string()
        .contains("rendered Markdown does not match manifest"));
}

use zkbench_core::{
    build_local_audit_index_manifest_from_report_bundles,
    build_report_bundle_manifest_from_reports, compute_artifact_digest_bytes,
    compute_local_audit_index_manifest_digest, deserialize_local_audit_index_manifest_json,
    read_local_audit_index_outputs, serialize_local_audit_index_manifest_json,
    validate_local_audit_index_manifest, write_local_audit_index_outputs, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceClass,
    LocalAuditIndexInputKind, LocalAuditIndexValidation, LocalAuditIndexValidationIssueKind,
    PackReadinessCheck, PackReadinessCheckKind, PackReadinessInputKind, PackReadinessInputRef,
    PackReadinessReport, PackReadinessValidation, PackReadinessValidationIssue,
    PackReadinessValidationIssueKind, PackReadinessVersion, ReportBundlePackReadinessInput,
    ScoreConfidence, ScoreReport, AUDIT_INDEX_MANIFEST_DIGEST_PATH, AUDIT_INDEX_MANIFEST_PATH,
};

use std::fs;

fn digest(label: &str, kind: ArtifactKind, role: ArtifactRole) -> ArtifactDigest {
    let mut hex = format!("{label:0<64}");
    hex.truncate(64);
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: hex,
        byte_len: label.len().max(1),
        kind: Some(kind),
        role: Some(role),
    }
}

fn score_report() -> ScoreReport {
    ScoreReport {
        evidence_count: 0,
        claim_boundary_max: ClaimBoundary::Level0DesignNote,
        confidence: ScoreConfidence::Low,
        performance: None,
        correctness: None,
        soundness_failure_detection: None,
        recursion_stress: None,
        formal_evidence: None,
        reproducibility: None,
        adapter_portability: None,
        risk_penalties: Vec::new(),
        missing_data: vec!["local-only report has no benchmark evidence".to_string()],
        notes: vec!["score report fixture".to_string()],
    }
}

fn readiness_check(kind: PackReadinessCheckKind, passed: bool) -> PackReadinessCheck {
    PackReadinessCheck {
        kind,
        passed,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec!["local readiness metadata only".to_string()],
    }
}

fn readiness_report(failed: bool) -> PackReadinessReport {
    PackReadinessReport {
        report_id: "sample_pack_readiness".to_string(),
        version: PackReadinessVersion::default(),
        source_pack_id: "sample_pack".to_string(),
        source_pack_digest: digest(
            "a",
            ArtifactKind::BenchmarkPackManifest,
            ArtifactRole::Manifest,
        ),
        inputs: vec![PackReadinessInputRef {
            input_id: "pack_json".to_string(),
            artifact_uri: "pack.json".to_string(),
            kind: PackReadinessInputKind::BenchmarkPackManifest,
            digest: digest(
                "b",
                ArtifactKind::BenchmarkPackManifest,
                ArtifactRole::Manifest,
            ),
            evidence_class: EvidenceClass::DesignNote,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: Vec::new(),
        }],
        replay_commands: Vec::new(),
        checks: vec![
            readiness_check(PackReadinessCheckKind::RelativePathCoverage, true),
            readiness_check(PackReadinessCheckKind::Sha256DigestCoverage, true),
            readiness_check(PackReadinessCheckKind::InertReplayCommandMetadata, true),
            readiness_check(PackReadinessCheckKind::WeakestClaimBoundaryCap, true),
            readiness_check(PackReadinessCheckKind::NoLevel2Evidence, true),
            readiness_check(PackReadinessCheckKind::NoExternalReplay, !failed),
        ],
        external_replay_authorized: false,
        creates_level2_evidence: false,
        official_benchmark_evidence: false,
        zk_backend_performance_claims: false,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
        limitations: vec![
            "pack-readiness is not Level2 evidence".to_string(),
            "local replay is not official benchmark evidence".to_string(),
            "replay command metadata is not execution evidence".to_string(),
        ],
        notes: Vec::new(),
    }
}

fn readiness_validation(valid: bool) -> PackReadinessValidation {
    PackReadinessValidation {
        valid,
        issues: if valid {
            Vec::new()
        } else {
            vec![PackReadinessValidationIssue {
                kind: PackReadinessValidationIssueKind::FailedCheck,
                path: "checks[5].passed".to_string(),
                message: "readiness check failed".to_string(),
            }]
        },
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

fn valid_report_bundle(failed_readiness: bool) -> zkbench_core::ReportBundleManifest {
    build_report_bundle_manifest_from_reports(
        "phase_q_bundle",
        &[score_report()],
        &[ReportBundlePackReadinessInput {
            report: readiness_report(failed_readiness),
            validation: readiness_validation(!failed_readiness),
        }],
    )
    .expect("report bundle manifest builds")
}

fn valid_manifest() -> zkbench_core::LocalAuditIndexManifest {
    build_local_audit_index_manifest_from_report_bundles(
        "phase_r_audit_index",
        "sample_pack",
        &[valid_report_bundle(false)],
    )
    .expect("audit-index manifest builds")
}

fn issue_kinds(
    manifest: &zkbench_core::LocalAuditIndexManifest,
) -> Vec<LocalAuditIndexValidationIssueKind> {
    validate_local_audit_index_manifest(manifest)
        .issues
        .into_iter()
        .map(|issue| issue.kind)
        .collect()
}

fn assert_issue(
    validation: &LocalAuditIndexValidation,
    path: &str,
    kind: LocalAuditIndexValidationIssueKind,
) {
    assert!(
        validation
            .issues
            .iter()
            .any(|issue| issue.path == path && issue.kind == kind),
        "expected {kind:?} issue at {path}, got {:?}",
        validation.issues
    );
}

#[test]
fn audit_index_manifest_builds_from_report_bundle_metadata_and_validates() {
    let manifest = valid_manifest();
    let validation = validate_local_audit_index_manifest(&manifest);

    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(
        manifest.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(manifest
        .inputs
        .iter()
        .any(|input| input.kind == LocalAuditIndexInputKind::ReportBundleManifest));
    assert!(manifest
        .inputs
        .iter()
        .any(|input| input.kind == LocalAuditIndexInputKind::ReportBundleDigestSidecar));
    assert!(manifest
        .inputs
        .iter()
        .any(|input| input.kind == LocalAuditIndexInputKind::ReportBundleRenderedMarkdown));
    assert!(!manifest.mutates_source_pack);
    assert!(!manifest.mutates_source_report);
    assert!(!manifest.mutates_report_bundle);
    assert!(!manifest.mutates_accepted_evidence_ledger);
    assert!(!manifest.populates_score_axes_from_local_only);
}

#[test]
fn audit_index_manifest_round_trips_and_digests_deterministically() {
    let manifest = valid_manifest();
    let json = serialize_local_audit_index_manifest_json(&manifest).expect("serialize");
    let round_trip = deserialize_local_audit_index_manifest_json(&json).expect("deserialize");

    assert_eq!(manifest, round_trip);
    assert_eq!(
        compute_local_audit_index_manifest_digest(&manifest).expect("digest"),
        compute_local_audit_index_manifest_digest(&round_trip).expect("digest")
    );
}

#[test]
fn audit_index_manifest_deserialization_rejects_malformed_json() {
    let error = deserialize_local_audit_index_manifest_json("{not valid audit index json")
        .expect_err("malformed audit-index JSON should fail");

    assert!(format!("{error}").contains("audit_index.manifest"));
}

#[test]
fn audit_index_validation_rejects_claim_elevation_and_evidence_claims() {
    let mut manifest = valid_manifest();
    manifest.output_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    manifest.creates_level2_evidence = true;
    manifest.official_benchmark_evidence = true;
    manifest.zk_backend_performance_claims = true;
    manifest.mutates_accepted_evidence_ledger = true;
    manifest.external_replay_authorized = true;
    manifest.replay_command_execution_output = true;
    manifest.populates_score_axes_from_local_only = true;

    let kinds = issue_kinds(&manifest);
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::ClaimBoundaryEscalation));
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::Level2EvidenceClaim));
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::OfficialBenchmarkEvidenceClaim));
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::ZkBackendPerformanceClaim));
    assert!(
        kinds.contains(&LocalAuditIndexValidationIssueKind::AcceptedEvidenceLedgerMutationClaim)
    );
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::ExternalReplayAuthorized));
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::ReplayCommandExecutionOutput));
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::LocalOnlyScoreAxisPopulation));
}

#[test]
fn audit_index_validation_reports_identity_duplicate_input_and_limitation_paths() {
    let mut manifest = valid_manifest();
    manifest.index_id = " ".to_string();
    manifest.version.value.clear();
    manifest.indexed_pack_id.clear();
    manifest.inputs[1].input_id = manifest.inputs[0].input_id.clone();
    manifest.inputs[1].artifact_uri = manifest.inputs[0].artifact_uri.clone();
    manifest.limitations.clear();

    let validation = validate_local_audit_index_manifest(&manifest);

    assert!(!validation.valid);
    assert_issue(
        &validation,
        "index_id",
        LocalAuditIndexValidationIssueKind::EmptyIdentity,
    );
    assert_issue(
        &validation,
        "version.value",
        LocalAuditIndexValidationIssueKind::EmptyIdentity,
    );
    assert_issue(
        &validation,
        "indexed_pack_id",
        LocalAuditIndexValidationIssueKind::EmptyIdentity,
    );
    assert_issue(
        &validation,
        "inputs[1].input_id",
        LocalAuditIndexValidationIssueKind::DuplicateInputId,
    );
    assert_issue(
        &validation,
        "inputs[1].artifact_uri",
        LocalAuditIndexValidationIssueKind::DuplicateArtifactUri,
    );
    assert_issue(
        &validation,
        "limitations",
        LocalAuditIndexValidationIssueKind::MissingLimitation,
    );
}

#[test]
fn audit_index_validation_reports_missing_inputs_without_claim_promotion() {
    let mut manifest = valid_manifest();
    manifest.inputs.clear();

    let validation = validate_local_audit_index_manifest(&manifest);

    assert!(!validation.valid);
    assert_eq!(validation.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_issue(
        &validation,
        "inputs",
        LocalAuditIndexValidationIssueKind::MissingInputs,
    );
}

#[test]
fn audit_index_validation_rejects_source_mutation_claims() {
    let mut manifest = valid_manifest();
    manifest.mutates_source_pack = true;
    manifest.mutates_source_report = true;
    manifest.mutates_report_bundle = true;

    let kinds = issue_kinds(&manifest);
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::SourceMutationClaim));
}

#[test]
fn audit_index_validation_rejects_path_digest_and_source_drift() {
    let mut manifest = valid_manifest();
    manifest.inputs[0].artifact_uri = "../report-bundle.json".to_string();
    manifest.inputs[0].digest.hex_digest = "bad".to_string();
    manifest.inputs[1].source_input_ids = vec!["missing_source".to_string()];

    let kinds = issue_kinds(&manifest);
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::InvalidArtifactRef));
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::InvalidDigest));
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::MissingSourceRef));
}

#[test]
fn audit_index_validation_requires_failed_readiness_visibility() {
    let mut manifest = build_local_audit_index_manifest_from_report_bundles(
        "phase_r_audit_index_with_failure",
        "sample_pack",
        &[valid_report_bundle(true)],
    )
    .expect("audit-index manifest builds");

    let validation = validate_local_audit_index_manifest(&manifest);
    assert!(validation.valid, "{:?}", validation.issues);

    manifest.failed_readiness_visible = false;
    let kinds = issue_kinds(&manifest);
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::FailedReadinessHidden));
}

#[test]
fn audit_index_validation_requires_local_only_warning_visibility() {
    let mut manifest = valid_manifest();
    let rendered = manifest
        .inputs
        .iter_mut()
        .find(|input| input.kind == LocalAuditIndexInputKind::ReportBundleRenderedMarkdown)
        .expect("rendered Markdown input exists");
    rendered.local_only_warnings_visible = false;

    let kinds = issue_kinds(&manifest);
    assert!(kinds.contains(&LocalAuditIndexValidationIssueKind::LocalOnlyWarningsHidden));
}

#[test]
fn audit_index_outputs_reject_file_roots_missing_files_and_invalid_utf8() {
    let manifest = valid_manifest();
    let dir = tempfile::tempdir().expect("tempdir");

    let file_root = dir.path().join("audit-index-file-root");
    fs::write(&file_root, b"not a directory\n").expect("file root");
    let file_root_error = write_local_audit_index_outputs(&file_root, &manifest, false)
        .expect_err("file output root should fail");
    assert!(file_root_error
        .to_string()
        .contains("output root exists and is not a directory"));

    let missing_root = dir.path().join("audit-index-missing");
    let missing_error =
        read_local_audit_index_outputs(&missing_root).expect_err("missing files should fail");
    assert!(missing_error
        .to_string()
        .contains(AUDIT_INDEX_MANIFEST_PATH));

    let non_utf8_sidecar_root = dir.path().join("audit-index-non-utf8-sidecar");
    fs::create_dir_all(non_utf8_sidecar_root.join("digests")).expect("digest dir");
    let manifest_json =
        serialize_local_audit_index_manifest_json(&manifest).expect("manifest json");
    fs::write(
        non_utf8_sidecar_root.join(AUDIT_INDEX_MANIFEST_PATH),
        manifest_json.as_bytes(),
    )
    .expect("manifest file");
    fs::write(
        non_utf8_sidecar_root.join(AUDIT_INDEX_MANIFEST_DIGEST_PATH),
        [0xff, 0xfe, 0xfd],
    )
    .expect("non-utf8 digest sidecar");
    let sidecar_error = read_local_audit_index_outputs(&non_utf8_sidecar_root)
        .expect_err("non-UTF-8 digest sidecar should fail");
    assert!(sidecar_error
        .to_string()
        .contains("manifest digest sidecar is not UTF-8"));

    let non_utf8_manifest_root = dir.path().join("audit-index-non-utf8-manifest");
    fs::create_dir_all(non_utf8_manifest_root.join("digests")).expect("digest dir");
    let manifest_bytes = vec![0xff, 0xfe, 0xfd];
    let manifest_digest = compute_artifact_digest_bytes(
        &manifest_bytes,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    );
    fs::write(
        non_utf8_manifest_root.join(AUDIT_INDEX_MANIFEST_PATH),
        &manifest_bytes,
    )
    .expect("non-utf8 manifest");
    fs::write(
        non_utf8_manifest_root.join(AUDIT_INDEX_MANIFEST_DIGEST_PATH),
        format!("{}\n", manifest_digest.hex_digest),
    )
    .expect("matching digest sidecar");
    let manifest_error = read_local_audit_index_outputs(&non_utf8_manifest_root)
        .expect_err("non-UTF-8 manifest should fail after digest check");
    assert!(manifest_error
        .to_string()
        .contains("manifest JSON is not UTF-8"));
}

#[test]
fn audit_index_outputs_reject_digest_consistent_invalid_manifest() {
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("audit-index-invalid-manifest");
    fs::create_dir_all(output_root.join("digests")).expect("digest dir");
    let invalid_manifest_json = br#"{
  "index_id": "",
  "version": { "value": "" },
  "indexed_pack_id": "",
  "inputs": [],
  "output_claim_boundary": "Level0DesignNote",
  "limitations": []
}
"#;
    let digest = compute_artifact_digest_bytes(
        invalid_manifest_json,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    );
    fs::write(
        output_root.join(AUDIT_INDEX_MANIFEST_PATH),
        invalid_manifest_json,
    )
    .expect("invalid manifest");
    fs::write(
        output_root.join(AUDIT_INDEX_MANIFEST_DIGEST_PATH),
        format!("{}\n", digest.hex_digest),
    )
    .expect("matching digest");

    let error = read_local_audit_index_outputs(&output_root)
        .expect_err("digest-consistent invalid manifest should fail validation");
    assert!(error.to_string().contains("manifest validation failed"));
}

#[test]
fn audit_index_outputs_write_read_and_preserve_source_files() {
    let manifest = valid_manifest();
    let dir = tempfile::tempdir().expect("tempdir");
    let source_root = dir.path().join("source");
    fs::create_dir_all(source_root.join("report-bundles")).expect("source dirs");
    fs::write(
        source_root.join("report-bundles/report-bundle-manifest.json"),
        b"{\"bundle\":\"source\"}\n",
    )
    .expect("source manifest");
    let source_before = fs::read(source_root.join("report-bundles/report-bundle-manifest.json"))
        .expect("source before");

    let output_root = dir.path().join("audit-index");
    let output = write_local_audit_index_outputs(&output_root, &manifest, false)
        .expect("audit-index output writes");
    assert_eq!(
        output.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(output.validation.valid, "{:?}", output.validation.issues);
    assert_eq!(output.manifest, manifest);
    assert!(output_root.join("audit-index-manifest.json").is_file());
    assert!(output_root
        .join("digests/audit-index-manifest.sha256")
        .is_file());

    let read_output =
        read_local_audit_index_outputs(&output_root).expect("audit-index output reads");
    assert_eq!(read_output.manifest, manifest);
    assert_eq!(read_output.manifest_digest, output.manifest_digest);
    assert_eq!(
        fs::read(source_root.join("report-bundles/report-bundle-manifest.json"))
            .expect("source after"),
        source_before
    );
}

#[test]
fn audit_index_outputs_reject_invalid_manifest_and_unsafe_roots() {
    let mut manifest = valid_manifest();
    manifest.creates_level2_evidence = true;
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("audit-index");
    let validation_error = write_local_audit_index_outputs(&output_root, &manifest, false)
        .expect_err("invalid manifest should fail");
    assert!(validation_error
        .to_string()
        .contains("manifest validation failed"));

    let manifest = valid_manifest();
    let unsafe_root = dir.path().join("../audit-index");
    let root_error = write_local_audit_index_outputs(&unsafe_root, &manifest, false)
        .expect_err("unsafe root should fail");
    assert!(root_error
        .to_string()
        .contains("must not contain parent-directory components"));
}

#[test]
fn audit_index_outputs_reject_overwrite_and_manifest_drift() {
    let manifest = valid_manifest();
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("audit-index");
    write_local_audit_index_outputs(&output_root, &manifest, false)
        .expect("initial write succeeds");

    let overwrite_error = write_local_audit_index_outputs(&output_root, &manifest, false)
        .expect_err("non-empty root without overwrite should fail");
    assert!(overwrite_error
        .to_string()
        .contains("explicit overwrite approval is required"));

    let mut drifted_manifest = manifest.clone();
    drifted_manifest.index_id = "phase_r_audit_index_drifted".to_string();
    let drift_error = write_local_audit_index_outputs(&output_root, &drifted_manifest, true)
        .expect_err("overwrite drift should fail");
    assert!(drift_error
        .to_string()
        .contains("does not match supplied manifest"));
}

#[test]
fn audit_index_outputs_reject_materialized_file_drift() {
    let manifest = valid_manifest();
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("audit-index");
    write_local_audit_index_outputs(&output_root, &manifest, false)
        .expect("initial write succeeds");

    fs::write(
        output_root.join("digests/audit-index-manifest.sha256"),
        b"0000000000000000000000000000000000000000000000000000000000000000\n",
    )
    .expect("tamper digest");
    let digest_error =
        read_local_audit_index_outputs(&output_root).expect_err("stale digest should fail");
    assert!(digest_error
        .to_string()
        .contains("manifest JSON bytes do not match digest sidecar"));

    let output_root = dir.path().join("audit-index-tampered-manifest");
    write_local_audit_index_outputs(&output_root, &manifest, false)
        .expect("initial tampered-manifest fixture write succeeds");
    fs::write(
        output_root.join("audit-index-manifest.json"),
        b"{\"index_id\":\"tampered\"}\n",
    )
    .expect("tamper manifest");
    let manifest_error =
        read_local_audit_index_outputs(&output_root).expect_err("tampered manifest should fail");
    assert!(manifest_error
        .to_string()
        .contains("manifest JSON bytes do not match digest sidecar"));
}

#[test]
fn audit_index_outputs_reject_unexpected_files_on_read_and_overwrite() {
    let manifest = valid_manifest();
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("audit-index");
    write_local_audit_index_outputs(&output_root, &manifest, false)
        .expect("initial write succeeds");
    fs::write(output_root.join("unexpected.txt"), b"stale\n").expect("unexpected file");

    let read_error =
        read_local_audit_index_outputs(&output_root).expect_err("unexpected file should fail");
    assert!(read_error
        .to_string()
        .contains("contains an unexpected file"));

    let write_error = write_local_audit_index_outputs(&output_root, &manifest, true)
        .expect_err("unexpected file should fail even with overwrite");
    assert!(write_error
        .to_string()
        .contains("contains an unexpected file"));
}

#[cfg(unix)]
#[test]
fn audit_index_outputs_reject_symlinks_on_read_and_overwrite() {
    use std::os::unix::fs::symlink;

    let manifest = valid_manifest();
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("audit-index");
    fs::create_dir_all(&output_root).expect("output root");
    fs::write(dir.path().join("outside.json"), b"{}\n").expect("outside file");
    symlink(
        dir.path().join("outside.json"),
        output_root.join("audit-index-manifest.json"),
    )
    .expect("symlink");

    let read_error =
        read_local_audit_index_outputs(&output_root).expect_err("symlink read should fail");
    assert!(read_error.to_string().contains("must not contain symlinks"));

    let write_error = write_local_audit_index_outputs(&output_root, &manifest, true)
        .expect_err("symlink write should fail");
    assert!(write_error
        .to_string()
        .contains("must not contain symlinks"));
}

#[test]
fn audit_index_source_exposes_no_external_execution_hooks() {
    let source = include_str!("../src/audit_index.rs");

    for forbidden in ["std::process", "Command::new", "std::net", "TcpStream"] {
        assert!(
            !source.contains(forbidden),
            "audit_index.rs must not expose {forbidden}"
        );
    }
}

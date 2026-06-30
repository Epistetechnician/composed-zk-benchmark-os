use std::fs;

use zkbench_core::{
    build_report_bundle_manifest_from_reports, build_report_bundle_rendered_markdown_payloads,
    compute_report_bundle_manifest_digest, deserialize_report_bundle_manifest_json,
    read_report_bundle_outputs, serialize_report_bundle_manifest_json,
    validate_report_bundle_manifest, write_report_bundle_outputs, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceClass,
    PackReadinessCheck, PackReadinessCheckKind, PackReadinessInputKind, PackReadinessInputRef,
    PackReadinessReport, PackReadinessValidation, PackReadinessValidationIssue,
    PackReadinessValidationIssueKind, PackReadinessVersion, ReportBundlePackReadinessInput,
    ReportBundleRenderedMarkdown, ReportBundleValidationIssueKind, ScoreConfidence, ScoreReport,
};

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

fn valid_manifest() -> zkbench_core::ReportBundleManifest {
    build_report_bundle_manifest_from_reports(
        "phase_q_bundle",
        &[score_report()],
        &[ReportBundlePackReadinessInput {
            report: readiness_report(false),
            validation: readiness_validation(true),
        }],
    )
    .expect("report bundle manifest builds")
}

fn valid_manifest_with_payloads() -> (
    zkbench_core::ReportBundleManifest,
    Vec<ReportBundleRenderedMarkdown>,
) {
    let score = score_report();
    let readiness_input = ReportBundlePackReadinessInput {
        report: readiness_report(false),
        validation: readiness_validation(true),
    };
    let manifest = build_report_bundle_manifest_from_reports(
        "phase_q_bundle",
        std::slice::from_ref(&score),
        std::slice::from_ref(&readiness_input),
    )
    .expect("report bundle manifest builds");

    let payloads = build_report_bundle_rendered_markdown_payloads(
        &manifest,
        std::slice::from_ref(&score),
        std::slice::from_ref(&readiness_input),
    )
    .expect("rendered Markdown payloads build");

    (manifest, payloads)
}

fn issue_kinds(
    manifest: &zkbench_core::ReportBundleManifest,
) -> Vec<ReportBundleValidationIssueKind> {
    validate_report_bundle_manifest(manifest)
        .issues
        .into_iter()
        .map(|issue| issue.kind)
        .collect()
}

#[test]
fn report_bundle_manifest_builds_from_existing_local_reports_and_validates() {
    let manifest = valid_manifest();
    let validation = validate_report_bundle_manifest(&manifest);

    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(
        manifest.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(manifest.inputs.len(), 3);
    assert_eq!(manifest.rendered_reports.len(), 2);
    assert!(!manifest.creates_level2_evidence);
    assert!(!manifest.official_benchmark_evidence);
    assert!(!manifest.zk_backend_performance_claims);
    assert!(!manifest.mutates_accepted_evidence_ledger);
}

#[test]
fn report_bundle_manifest_round_trips_and_digests_deterministically() {
    let manifest = valid_manifest();
    let json = serialize_report_bundle_manifest_json(&manifest).expect("serialize");
    let round_trip = deserialize_report_bundle_manifest_json(&json).expect("deserialize");

    assert_eq!(manifest, round_trip);
    assert_eq!(
        compute_report_bundle_manifest_digest(&manifest).expect("digest"),
        compute_report_bundle_manifest_digest(&round_trip).expect("digest")
    );
}

#[test]
fn report_bundle_validation_rejects_claim_elevation_and_evidence_claims() {
    let mut manifest = valid_manifest();
    manifest.output_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    manifest.creates_level2_evidence = true;
    manifest.official_benchmark_evidence = true;
    manifest.zk_backend_performance_claims = true;
    manifest.mutates_accepted_evidence_ledger = true;
    manifest.external_replay_authorized = true;
    manifest.replay_command_execution_output = true;

    let kinds = issue_kinds(&manifest);
    assert!(kinds.contains(&ReportBundleValidationIssueKind::ClaimBoundaryEscalation));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::Level2EvidenceClaim));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::OfficialBenchmarkEvidenceClaim));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::ZkBackendPerformanceClaim));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::AcceptedEvidenceLedgerMutationClaim));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::ExternalReplayAuthorized));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::ReplayCommandExecutionOutput));
}

#[test]
fn report_bundle_validation_rejects_path_digest_and_source_drift() {
    let mut manifest = valid_manifest();
    manifest.inputs[0].artifact_uri = "../score.json".to_string();
    manifest.inputs[0].digest.hex_digest = "bad".to_string();
    manifest.rendered_reports[0].source_input_ids = vec!["missing_source".to_string()];

    let kinds = issue_kinds(&manifest);
    assert!(kinds.contains(&ReportBundleValidationIssueKind::InvalidArtifactRef));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::InvalidDigest));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::MissingSourceRef));
}

#[test]
fn report_bundle_validation_reports_identity_digest_limitation_and_rendered_metadata_gaps() {
    let mut manifest = valid_manifest();
    manifest.bundle_id = "   ".to_string();
    manifest.version.value.clear();
    manifest.inputs[0].input_id.clear();
    manifest.inputs[1].input_id = manifest.inputs[0].input_id.clone();
    manifest.inputs[0].digest.algorithm = ArtifactDigestAlgorithm::Unsupported;
    manifest.inputs[1].digest.byte_len = 0;
    manifest.inputs[2].claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    manifest.rendered_reports[0].rendered_report_id.clear();
    manifest.rendered_reports[0].title.clear();
    manifest.rendered_reports[0].source_input_ids.clear();
    manifest.rendered_reports[0].claim_boundary = ClaimBoundary::Level1LocalReplay;
    manifest.rendered_reports[0].local_only_warnings_visible = false;
    manifest.limitations.clear();

    let validation = validate_report_bundle_manifest(&manifest);
    assert!(!validation.valid);
    let kinds = validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<Vec<_>>();

    assert!(kinds.contains(&ReportBundleValidationIssueKind::EmptyIdentity));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::DuplicateInputId));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::InvalidDigest));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::ClaimBoundaryEscalation));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::MissingSourceRef));
    assert!(kinds.contains(&ReportBundleValidationIssueKind::MissingLimitation));
}

#[test]
fn report_bundle_validation_rejects_missing_inputs_rendered_reports_and_shell_refs() {
    let mut manifest = valid_manifest();
    manifest.inputs.clear();
    manifest.rendered_reports.clear();
    let missing = issue_kinds(&manifest);
    assert!(missing.contains(&ReportBundleValidationIssueKind::MissingInputs));
    assert!(missing.contains(&ReportBundleValidationIssueKind::MissingRenderedReport));

    let mut manifest = valid_manifest();
    manifest.inputs[0].artifact_uri = "score_reports/score.json;rm".to_string();
    manifest.rendered_reports[0].artifact_uri = "score_reports/not-rendered.txt".to_string();
    let validation = validate_report_bundle_manifest(&manifest);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == ReportBundleValidationIssueKind::InvalidArtifactRef));
}

#[test]
fn report_bundle_validation_requires_failed_readiness_visibility() {
    let mut manifest = build_report_bundle_manifest_from_reports(
        "phase_q_bundle_with_failure",
        &[],
        &[ReportBundlePackReadinessInput {
            report: readiness_report(true),
            validation: readiness_validation(false),
        }],
    )
    .expect("report bundle manifest builds");

    let validation = validate_report_bundle_manifest(&manifest);
    assert!(validation.valid, "{:?}", validation.issues);

    manifest.rendered_reports[0].failed_readiness_visible = false;
    let kinds = issue_kinds(&manifest);
    assert!(kinds.contains(&ReportBundleValidationIssueKind::FailedReadinessHidden));
}

#[test]
fn report_bundle_outputs_write_read_and_preserve_source_files() {
    let (manifest, payloads) = valid_manifest_with_payloads();
    let dir = tempfile::tempdir().expect("tempdir");
    let source_root = dir.path().join("source");
    fs::create_dir_all(source_root.join("reports")).expect("source dirs");
    fs::write(source_root.join("pack.json"), b"{\"id\":\"source_pack\"}\n").expect("pack source");
    fs::write(
        source_root.join("reports/score_report.json"),
        b"{\"report\":\"source\"}\n",
    )
    .expect("report source");
    let pack_before = fs::read(source_root.join("pack.json")).expect("pack before");
    let report_before =
        fs::read(source_root.join("reports/score_report.json")).expect("report before");

    let output_root = dir.path().join("report-bundle");
    let output = write_report_bundle_outputs(&output_root, &manifest, &payloads, false)
        .expect("report-bundle output writes");
    assert_eq!(
        output.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(output.validation.valid, "{:?}", output.validation.issues);
    assert_eq!(
        output.rendered_reports.len(),
        manifest.rendered_reports.len()
    );
    assert!(output_root.join("report-bundle-manifest.json").is_file());
    assert!(output_root
        .join("digests/report-bundle-manifest.sha256")
        .is_file());
    assert!(output_root.join("rendered/score_report_0.md").is_file());
    assert!(output_root
        .join("rendered/pack_readiness_report_0.md")
        .is_file());

    let read_output = read_report_bundle_outputs(&output_root).expect("report-bundle output reads");
    assert_eq!(read_output.manifest, manifest);
    assert_eq!(read_output.manifest_digest, output.manifest_digest);
    assert_eq!(read_output.rendered_reports, output.rendered_reports);
    assert_eq!(
        fs::read(source_root.join("pack.json")).expect("pack after"),
        pack_before
    );
    assert_eq!(
        fs::read(source_root.join("reports/score_report.json")).expect("report after"),
        report_before
    );
}

#[test]
fn report_bundle_outputs_reject_payload_and_overwrite_drift() {
    let (manifest, mut payloads) = valid_manifest_with_payloads();
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("report-bundle");

    let missing_payload_error =
        write_report_bundle_outputs(&output_root, &manifest, &payloads[..1], false)
            .expect_err("missing rendered Markdown payload should fail");
    assert!(missing_payload_error
        .to_string()
        .contains("missing rendered Markdown payload"));

    payloads[0].markdown.push_str("\nlocal tamper\n");
    let digest_error = write_report_bundle_outputs(&output_root, &manifest, &payloads, false)
        .expect_err("rendered Markdown digest drift should fail");
    assert!(digest_error
        .to_string()
        .contains("rendered Markdown digest does not match manifest"));

    let (_, payloads) = valid_manifest_with_payloads();
    write_report_bundle_outputs(&output_root, &manifest, &payloads, false)
        .expect("initial write succeeds");
    let overwrite_error = write_report_bundle_outputs(&output_root, &manifest, &payloads, false)
        .expect_err("non-empty root without overwrite should fail");
    assert!(overwrite_error
        .to_string()
        .contains("explicit overwrite approval is required"));
}

#[test]
fn report_bundle_outputs_reject_invalid_empty_duplicate_and_extra_payloads() {
    let (manifest, payloads) = valid_manifest_with_payloads();
    let dir = tempfile::tempdir().expect("tempdir");

    let mut empty_id = payloads.clone();
    empty_id[0].rendered_report_id.clear();
    let error =
        write_report_bundle_outputs(dir.path().join("empty-id"), &manifest, &empty_id, false)
            .expect_err("empty payload id should reject");
    assert!(error
        .to_string()
        .contains("invalid report-bundle output identity"));

    let mut empty_markdown = payloads.clone();
    empty_markdown[0].markdown.clear();
    let error = write_report_bundle_outputs(
        dir.path().join("empty-markdown"),
        &manifest,
        &empty_markdown,
        false,
    )
    .expect_err("empty markdown payload should reject");
    assert!(error
        .to_string()
        .contains("rendered Markdown payload must not be empty"));

    let mut duplicate = payloads.clone();
    duplicate.push(duplicate[0].clone());
    let error = write_report_bundle_outputs(
        dir.path().join("duplicate-payload"),
        &manifest,
        &duplicate,
        false,
    )
    .expect_err("duplicate payload id should reject");
    assert!(error
        .to_string()
        .contains("duplicate rendered Markdown payload id"));

    let mut extra = payloads.clone();
    extra.push(ReportBundleRenderedMarkdown {
        rendered_report_id: "extra_rendered_payload".to_string(),
        markdown: "# Extra rendered payload\n".to_string(),
    });
    let error =
        write_report_bundle_outputs(dir.path().join("extra-payload"), &manifest, &extra, false)
            .expect_err("extra payload should reject");
    assert!(error
        .to_string()
        .contains("extra rendered Markdown payload exists"));
}

#[test]
fn report_bundle_outputs_reject_file_roots_invalid_roots_and_manifest_readback_failures() {
    let (manifest, payloads) = valid_manifest_with_payloads();
    let dir = tempfile::tempdir().expect("tempdir");

    let file_root = dir.path().join("not-a-directory");
    fs::write(&file_root, b"occupied").expect("file root should write");
    let error = write_report_bundle_outputs(&file_root, &manifest, &payloads, false)
        .expect_err("file output root should reject");
    assert!(error.to_string().contains("not a directory"));

    let error = write_report_bundle_outputs("bad://report-bundle", &manifest, &payloads, false)
        .expect_err("invalid output root should reject");
    assert!(error
        .to_string()
        .contains("invalid report-bundle output root"));

    let output_root = dir.path().join("report-bundle-readback");
    write_report_bundle_outputs(&output_root, &manifest, &payloads, false)
        .expect("initial write succeeds");

    fs::write(
        output_root.join("digests/report-bundle-manifest.sha256"),
        &[0xff, 0xfe, 0xfd],
    )
    .expect("non-UTF-8 digest sidecar should write");
    let error =
        read_report_bundle_outputs(&output_root).expect_err("non-UTF-8 sidecar should reject");
    assert!(error
        .to_string()
        .contains("manifest digest sidecar is not UTF-8"));

    write_report_bundle_outputs(&output_root, &manifest, &payloads, true)
        .expect("repair output succeeds");
    fs::write(
        output_root.join("report-bundle-manifest.json"),
        &[0xff, 0xfe, 0xfd],
    )
    .expect("non-UTF-8 manifest should write");
    let manifest_digest = zkbench_core::compute_artifact_digest_bytes(
        &[0xff, 0xfe, 0xfd],
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    );
    fs::write(
        output_root.join("digests/report-bundle-manifest.sha256"),
        format!("{}\n", manifest_digest.hex_digest).as_bytes(),
    )
    .expect("digest sidecar should repair");
    let error =
        read_report_bundle_outputs(&output_root).expect_err("non-UTF-8 manifest should reject");
    assert!(error.to_string().contains("manifest JSON is not UTF-8"));
}

#[test]
fn report_bundle_outputs_reject_materialized_file_drift() {
    let (manifest, payloads) = valid_manifest_with_payloads();
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("report-bundle");
    write_report_bundle_outputs(&output_root, &manifest, &payloads, false)
        .expect("initial write succeeds");

    fs::write(
        output_root.join("rendered/score_report_0.md"),
        b"# tampered rendered report\n",
    )
    .expect("tamper rendered Markdown");
    let markdown_error =
        read_report_bundle_outputs(&output_root).expect_err("tampered Markdown should fail");
    assert!(markdown_error
        .to_string()
        .contains("rendered Markdown bytes do not match manifest digest"));

    write_report_bundle_outputs(&output_root, &manifest, &payloads, true)
        .expect("overwrite declared outputs");
    fs::write(output_root.join("rendered/extra.md"), b"# extra\n").expect("extra rendered file");
    let extra_error =
        read_report_bundle_outputs(&output_root).expect_err("extra rendered file should fail");
    assert!(extra_error.to_string().contains("without a manifest entry"));

    fs::remove_file(output_root.join("rendered/extra.md")).expect("remove extra file");
    fs::write(
        output_root.join("digests/report-bundle-manifest.sha256"),
        b"0000000000000000000000000000000000000000000000000000000000000000\n",
    )
    .expect("tamper manifest digest");
    let manifest_error =
        read_report_bundle_outputs(&output_root).expect_err("stale manifest sidecar should fail");
    assert!(manifest_error
        .to_string()
        .contains("manifest JSON bytes do not match digest sidecar"));
}

#[test]
fn report_bundle_rendered_payload_helper_rejects_source_drift() {
    let score = score_report();
    let readiness_input = ReportBundlePackReadinessInput {
        report: readiness_report(false),
        validation: readiness_validation(true),
    };
    let manifest = build_report_bundle_manifest_from_reports(
        "phase_q_bundle",
        std::slice::from_ref(&score),
        std::slice::from_ref(&readiness_input),
    )
    .expect("report bundle manifest builds");

    let payloads = build_report_bundle_rendered_markdown_payloads(
        &manifest,
        std::slice::from_ref(&score),
        std::slice::from_ref(&readiness_input),
    )
    .expect("matching sources produce payloads");
    assert_eq!(payloads.len(), manifest.rendered_reports.len());

    let mut drifted_score = score;
    drifted_score
        .notes
        .push("source report drift after manifest build".to_string());
    let error = build_report_bundle_rendered_markdown_payloads(
        &manifest,
        std::slice::from_ref(&drifted_score),
        std::slice::from_ref(&readiness_input),
    )
    .expect_err("source drift should fail");
    assert!(error
        .to_string()
        .contains("source reports do not match report-bundle manifest inputs"));
}

#[test]
fn report_bundle_outputs_reject_duplicate_rendered_paths_and_unsafe_roots() {
    let (mut manifest, payloads) = valid_manifest_with_payloads();
    manifest.rendered_reports[1].artifact_uri = manifest.rendered_reports[0].artifact_uri.clone();
    let validation = validate_report_bundle_manifest(&manifest);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == ReportBundleValidationIssueKind::InvalidArtifactRef));

    let dir = tempfile::tempdir().expect("tempdir");
    let unsafe_root = dir.path().join("../report-bundle");
    let error = write_report_bundle_outputs(&unsafe_root, &manifest, &payloads, false)
        .expect_err("unsafe root should fail");
    assert!(error
        .to_string()
        .contains("must not contain parent-directory components"));
}

#[test]
fn report_bundle_outputs_reject_unexpected_files_on_overwrite() {
    let (manifest, payloads) = valid_manifest_with_payloads();
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("report-bundle");
    write_report_bundle_outputs(&output_root, &manifest, &payloads, false)
        .expect("initial write succeeds");
    fs::write(output_root.join("unexpected.txt"), b"stale\n").expect("unexpected file");

    let error = write_report_bundle_outputs(&output_root, &manifest, &payloads, true)
        .expect_err("unexpected file should fail even with overwrite");
    assert!(error.to_string().contains("contains an unexpected file"));
}

#[cfg(unix)]
#[test]
fn report_bundle_outputs_reject_symlinks_on_overwrite() {
    use std::os::unix::fs::symlink;

    let (manifest, payloads) = valid_manifest_with_payloads();
    let dir = tempfile::tempdir().expect("tempdir");
    let output_root = dir.path().join("report-bundle");
    fs::create_dir_all(&output_root).expect("output root");
    fs::write(dir.path().join("outside.md"), b"# outside\n").expect("outside file");
    symlink(
        dir.path().join("outside.md"),
        output_root.join("report-bundle-manifest.json"),
    )
    .expect("symlink");

    let error = write_report_bundle_outputs(&output_root, &manifest, &payloads, true)
        .expect_err("symlink should fail");
    assert!(error.to_string().contains("must not contain symlinks"));
}

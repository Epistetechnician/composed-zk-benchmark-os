use zkbench_core::{
    build_local_audit_index_manifest_from_report_bundles,
    build_report_bundle_manifest_from_reports, compute_local_audit_index_manifest_digest,
    deserialize_local_audit_index_manifest_json, serialize_local_audit_index_manifest_json,
    validate_local_audit_index_manifest, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary, EvidenceClass, LocalAuditIndexInputKind,
    LocalAuditIndexValidationIssueKind, PackReadinessCheck, PackReadinessCheckKind,
    PackReadinessInputKind, PackReadinessInputRef, PackReadinessReport, PackReadinessValidation,
    PackReadinessValidationIssue, PackReadinessValidationIssueKind, PackReadinessVersion,
    ReportBundlePackReadinessInput, ScoreConfidence, ScoreReport,
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
fn audit_index_source_exposes_no_output_writer_or_execution_hooks() {
    let source = include_str!("../src/audit_index.rs");

    for forbidden in [
        "std::process",
        "Command::new",
        "std::net",
        "TcpStream",
        "write_local_audit_index",
        "read_local_audit_index",
        "create_dir",
        "fs::write",
    ] {
        assert!(
            !source.contains(forbidden),
            "audit_index.rs must not expose {forbidden}"
        );
    }
}

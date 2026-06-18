use std::fs;
use std::path::Path;

use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, build_pack_readiness_report_from_reader,
    compute_pack_readiness_report_digest, deserialize_pack_readiness_report_json,
    generate_instance, read_pack_readiness_report, read_pack_readiness_validation,
    run_local_replay, serialize_pack_readiness_report_json, validate_pack_readiness_report,
    write_pack_readiness_outputs_for_pack, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary, EvidenceClass,
    EvidenceLedger, GeneratorConfig, InstanceParams, PackReadinessCheck, PackReadinessCheckKind,
    PackReadinessInputKind, PackReadinessInputRef, PackReadinessReplayCommandMetadata,
    PackReadinessReport, PackReadinessValidationIssueKind, PackReadinessVersion,
    PACK_READINESS_REPORT_PATH, PACK_READINESS_VALIDATION_PATH, PACK_VALIDATION_REPORT_PATH,
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

fn input(
    input_id: &str,
    kind: PackReadinessInputKind,
    claim_boundary: ClaimBoundary,
    evidence_class: EvidenceClass,
    digest_byte: u8,
) -> PackReadinessInputRef {
    PackReadinessInputRef {
        input_id: input_id.to_string(),
        artifact_uri: format!("artifacts/{input_id}.json"),
        kind,
        digest: digest(digest_byte),
        evidence_class,
        claim_boundary,
        notes: Vec::new(),
    }
}

fn check(kind: PackReadinessCheckKind) -> PackReadinessCheck {
    PackReadinessCheck {
        kind,
        passed: true,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: Vec::new(),
    }
}

fn valid_report() -> PackReadinessReport {
    PackReadinessReport {
        report_id: "phase_o_pack_readiness".to_string(),
        version: PackReadinessVersion::default(),
        source_pack_id: "phase_f_local_pack".to_string(),
        source_pack_digest: digest(1),
        inputs: vec![
            input(
                "pack_manifest",
                PackReadinessInputKind::BenchmarkPackManifest,
                ClaimBoundary::Level1LocalReplay,
                EvidenceClass::LocalReplay,
                2,
            ),
            input(
                "pack_validation",
                PackReadinessInputKind::BenchmarkPackValidationReport,
                ClaimBoundary::Level0DesignNote,
                EvidenceClass::DesignNote,
                3,
            ),
            input(
                "append_preview",
                PackReadinessInputKind::EvidenceAppendPreview,
                ClaimBoundary::Level0DesignNote,
                EvidenceClass::DesignNote,
                4,
            ),
        ],
        replay_commands: vec![PackReadinessReplayCommandMetadata {
            command_id: "local_replay_manifest_roundtrip".to_string(),
            action_label: "local replay manifest roundtrip".to_string(),
            input_artifact_uri: "replay/manifests/local.json".to_string(),
            output_artifact_uri: "readiness/local_replay_manifest_roundtrip.json".to_string(),
            inert: true,
            notes: vec!["metadata only".to_string()],
        }],
        checks: vec![
            check(PackReadinessCheckKind::RelativePathCoverage),
            check(PackReadinessCheckKind::Sha256DigestCoverage),
            check(PackReadinessCheckKind::ManifestSummaryConsistency),
            check(PackReadinessCheckKind::ReplayRoundTripReady),
            check(PackReadinessCheckKind::EvidenceLedgerDigestChainReady),
            check(PackReadinessCheckKind::ScoreReportClaimCap),
            check(PackReadinessCheckKind::InertReplayCommandMetadata),
            check(PackReadinessCheckKind::WeakestClaimBoundaryCap),
            check(PackReadinessCheckKind::NoLevel2Evidence),
            check(PackReadinessCheckKind::NoExternalReplay),
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

fn issue_kinds(report: &PackReadinessReport) -> Vec<PackReadinessValidationIssueKind> {
    validate_pack_readiness_report(report)
        .issues
        .into_iter()
        .map(|issue| issue.kind)
        .collect()
}

fn write_sample_pack(pack_id: &str) -> tempfile::TempDir {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(111),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let replay_manifest =
        build_local_replay_manifest_for_instance(&instance).expect("replay manifest should build");
    let replay_result = run_local_replay(&replay_manifest).expect("local replay should run");

    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&replay_result)
        .expect("local replay evidence should append");

    let dir = tempdir().expect("tempdir should be available for pack write");
    BenchmarkPackWriter::new(pack_id)
        .with_generated_instance(instance)
        .with_replay_manifest(replay_manifest)
        .with_replay_result(replay_result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("sample pack should write");
    dir
}

#[test]
fn valid_pack_readiness_report_validates_as_level0_metadata() {
    let report = valid_report();
    let validation = validate_pack_readiness_report(&report);

    assert!(validation.valid, "issues: {:?}", validation.issues);
    assert_eq!(validation.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        report.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn pack_readiness_report_round_trips_as_json_and_digests() {
    let report = valid_report();
    let json = serialize_pack_readiness_report_json(&report).expect("report should serialize");
    let round_trip =
        deserialize_pack_readiness_report_json(&json).expect("report should deserialize");
    let report_digest =
        compute_pack_readiness_report_digest(&round_trip).expect("report digest should compute");

    assert_eq!(round_trip, report);
    assert_eq!(report_digest.algorithm, ArtifactDigestAlgorithm::Sha256);
    assert!(!json.contains(concat!("Command", "::new")));
    assert!(!json.contains("official benchmark evidence\": true"));
    assert!(!json.contains("creates_level2_evidence\": true"));
}

#[test]
fn pack_readiness_builds_from_existing_local_pack_reader() {
    let dir = write_sample_pack("phase_o_constructed_readiness_pack");
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load");
    let pack_validation = reader.validate();
    assert!(
        pack_validation.valid,
        "pack validation errors: {:?}",
        pack_validation.errors
    );

    let report = build_pack_readiness_report_from_reader(&reader, &pack_validation)
        .expect("readiness report should build from local pack metadata");
    let validation = validate_pack_readiness_report(&report);

    assert!(validation.valid, "issues: {:?}", validation.issues);
    assert_eq!(report.source_pack_id, reader.manifest().id);
    assert_eq!(
        report.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!report.external_replay_authorized);
    assert!(!report.creates_level2_evidence);
    assert!(!report.official_benchmark_evidence);
    assert!(!report.zk_backend_performance_claims);
    assert!(report
        .inputs
        .iter()
        .any(|input| input.kind == PackReadinessInputKind::BenchmarkPackManifest));
    assert!(report
        .inputs
        .iter()
        .any(|input| input.kind == PackReadinessInputKind::BenchmarkPackValidationReport));
    assert!(report
        .inputs
        .iter()
        .any(|input| input.kind == PackReadinessInputKind::LocalReplayManifest));
    assert!(report.replay_commands.iter().all(|command| command.inert));
}

#[test]
fn pack_readiness_outputs_write_adjacent_metadata_without_manifest_mutation() {
    let dir = write_sample_pack("phase_o_readiness_output_pack");
    let output = write_pack_readiness_outputs_for_pack(dir.path())
        .expect("readiness outputs should write next to the local pack");

    assert_eq!(
        output.pack_validation_relative_path,
        PACK_VALIDATION_REPORT_PATH
    );
    assert_eq!(output.report_relative_path, PACK_READINESS_REPORT_PATH);
    assert_eq!(
        output.readiness_validation_relative_path,
        PACK_READINESS_VALIDATION_PATH
    );
    assert_eq!(
        output.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(output.readiness_validation.valid);
    assert_eq!(
        output.readiness_validation.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(dir.path().join(PACK_VALIDATION_REPORT_PATH).is_file());
    assert!(dir.path().join(PACK_READINESS_REPORT_PATH).is_file());
    assert!(dir.path().join(PACK_READINESS_VALIDATION_PATH).is_file());
    assert!(output.pack_validation_digest.byte_len > 0);
    assert!(output.report_digest.byte_len > 0);
    assert!(output.readiness_validation_digest.byte_len > 0);

    let read_report = read_pack_readiness_report(dir.path()).expect("report should read back");
    let read_validation =
        read_pack_readiness_validation(dir.path()).expect("validation should read back");
    assert_eq!(read_report, output.report);
    assert_eq!(read_validation, output.readiness_validation);
    assert!(!read_report.external_replay_authorized);
    assert!(!read_report.creates_level2_evidence);
    assert!(!read_report.official_benchmark_evidence);
    assert!(!read_report.zk_backend_performance_claims);

    let reader =
        BenchmarkPackReader::read(dir.path()).expect("pack reader should still load pack.json");
    assert!(reader.validate().valid);
    assert!(!reader
        .manifest()
        .files
        .iter()
        .any(|file| file.relative_path.starts_with("readiness/")));
}

#[test]
fn pack_readiness_outputs_write_failed_local_validation_without_claim_elevation() {
    let dir = write_sample_pack("phase_o_readiness_invalid_pack");
    fs::write(dir.path().join("reports/score_report.json"), "{}")
        .expect("test should tamper score report");

    let output = write_pack_readiness_outputs_for_pack(dir.path())
        .expect("failed local validation should still produce bounded metadata");
    let read_report = read_pack_readiness_report(dir.path()).expect("report should read back");
    let read_validation =
        read_pack_readiness_validation(dir.path()).expect("validation should read back");
    let kinds: Vec<_> = read_validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect();

    assert!(!output.readiness_validation.valid);
    assert!(!read_validation.valid);
    assert!(kinds.contains(&PackReadinessValidationIssueKind::FailedCheck));
    assert_eq!(
        read_report.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!read_report.external_replay_authorized);
    assert!(!read_report.creates_level2_evidence);
    assert!(!read_report.official_benchmark_evidence);
    assert!(!read_report.zk_backend_performance_claims);
}

#[test]
fn pack_readiness_builder_fails_closed_when_pack_validation_fails() {
    let dir = write_sample_pack("phase_o_invalid_readiness_pack");
    fs::write(dir.path().join("reports/score_report.json"), "{}")
        .expect("test should tamper score report");
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load");
    let pack_validation = reader.validate();
    assert!(!pack_validation.valid);

    let report = build_pack_readiness_report_from_reader(&reader, &pack_validation)
        .expect("readiness report should build from invalid local validation metadata");
    let validation = validate_pack_readiness_report(&report);
    let kinds: Vec<_> = validation.issues.iter().map(|issue| issue.kind).collect();

    assert!(!validation.valid);
    assert!(kinds.contains(&PackReadinessValidationIssueKind::FailedCheck));
    assert!(!kinds.contains(&PackReadinessValidationIssueKind::ExternalReplayAuthorized));
    assert!(!report.external_replay_authorized);
    assert!(!report.creates_level2_evidence);
}

#[test]
fn pack_readiness_rejects_level2_official_external_and_performance_claims() {
    let mut report = valid_report();
    report.output_claim_boundary = ClaimBoundary::Level1LocalReplay;
    report.external_replay_authorized = true;
    report.creates_level2_evidence = true;
    report.official_benchmark_evidence = true;
    report.zk_backend_performance_claims = true;
    report.limitations.clear();

    let kinds = issue_kinds(&report);

    assert!(kinds.contains(&PackReadinessValidationIssueKind::ClaimBoundaryEscalation));
    assert!(kinds.contains(&PackReadinessValidationIssueKind::ExternalReplayAuthorized));
    assert!(kinds.contains(&PackReadinessValidationIssueKind::Level2EvidenceClaim));
    assert!(kinds.contains(&PackReadinessValidationIssueKind::OfficialBenchmarkEvidenceClaim));
    assert!(kinds.contains(&PackReadinessValidationIssueKind::ZkBackendPerformanceClaim));
    assert!(kinds.contains(&PackReadinessValidationIssueKind::MissingLimitation));
}

#[test]
fn pack_readiness_rejects_non_inert_replay_command_metadata() {
    let mut report = valid_report();
    report.replay_commands[0].inert = false;
    report.replay_commands[0].action_label = "cargo test; rm -rf target".to_string();
    report.replay_commands[0].input_artifact_uri = "/tmp/replay.json".to_string();
    report.replay_commands[0].output_artifact_uri = "../readiness/result.json".to_string();

    let kinds = issue_kinds(&report);

    assert!(kinds.contains(&PackReadinessValidationIssueKind::NonInertReplayCommand));
    assert!(kinds.contains(&PackReadinessValidationIssueKind::InvalidArtifactRef));
}

#[test]
fn pack_readiness_rejects_missing_and_failed_required_checks() {
    let mut report = valid_report();
    report
        .checks
        .retain(|check| check.kind != PackReadinessCheckKind::Sha256DigestCoverage);
    report
        .checks
        .iter_mut()
        .find(|check| check.kind == PackReadinessCheckKind::NoLevel2Evidence)
        .expect("NoLevel2Evidence check should exist")
        .passed = false;

    let kinds = issue_kinds(&report);

    assert!(kinds.contains(&PackReadinessValidationIssueKind::MissingRequiredCheck));
    assert!(kinds.contains(&PackReadinessValidationIssueKind::FailedCheck));
}

#[test]
fn pack_readiness_rejects_append_preview_and_level2_boundary_drift() {
    let mut report = valid_report();
    report.inputs.push(input(
        "level2_report",
        PackReadinessInputKind::Level2EligibilityReport,
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
        EvidenceClass::ReproducibleBenchmarkArtifact,
        5,
    ));
    report.inputs[2].claim_boundary = ClaimBoundary::Level1LocalReplay;

    let kinds = issue_kinds(&report);

    assert!(kinds.contains(&PackReadinessValidationIssueKind::AppendPreviewBoundary));
    assert!(kinds.contains(&PackReadinessValidationIssueKind::Level2EligibilityBoundary));
    assert!(kinds.contains(&PackReadinessValidationIssueKind::ClaimBoundaryEscalation));
}

#[test]
fn pack_readiness_source_exposes_no_executable_adapter_hooks() {
    let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crate should live under workspace/crates");
    let source = fs::read_to_string(repo_root.join("crates/zkbench-core/src/pack/readiness.rs"))
        .expect("pack readiness source should be readable");

    assert!(!source.contains("std::process::Command"));
    assert!(!source.contains(concat!("Command", "::new")));
    assert!(!source.contains("TcpStream"));
    assert!(!source.contains("reqwest"));
    assert!(!source.contains("ureq"));
}

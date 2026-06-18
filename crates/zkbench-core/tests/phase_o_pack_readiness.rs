use std::fs;
use std::path::Path;

use zkbench_core::{
    compute_pack_readiness_report_digest, deserialize_pack_readiness_report_json,
    serialize_pack_readiness_report_json, validate_pack_readiness_report, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceClass,
    PackReadinessCheck, PackReadinessCheckKind, PackReadinessInputKind, PackReadinessInputRef,
    PackReadinessReplayCommandMetadata, PackReadinessReport, PackReadinessValidationIssueKind,
    PackReadinessVersion,
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

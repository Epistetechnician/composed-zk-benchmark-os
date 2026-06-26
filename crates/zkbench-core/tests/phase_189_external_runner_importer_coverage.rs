use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    build_default_artifact_capture_contract, compute_artifact_digest_bytes,
    deserialize_external_result_candidate_json, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary, ExternalMetricUnit, ResultCandidateArtifactLookup,
    ResultCandidateArtifactResolver, ResultCandidateSource, ResultCandidateSourceKind,
    SyntheticImportValidationIssueKind, SyntheticResultImportConfig, SyntheticResultImporter,
    ZkBenchError,
};

fn candidate() -> zkbench_core::ExternalResultCandidate {
    deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("valid synthetic candidate fixture should parse")
}

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

fn issue_kinds(
    validation: &zkbench_core::SyntheticImportValidation,
) -> Vec<SyntheticImportValidationIssueKind> {
    validation.issues.iter().map(|issue| issue.kind).collect()
}

#[test]
fn relative_file_resolver_reads_declared_files_and_rejects_unsafe_refs() {
    let root = tempdir().expect("tempdir should be available");
    fs::create_dir(root.path().join("artifacts")).expect("artifact dir should be created");
    fs::write(
        root.path().join("artifacts/synthetic_metric_source.json"),
        b"synthetic metric source v1\n",
    )
    .expect("fixture artifact should be written");

    let resolver = ResultCandidateArtifactResolver::from_relative_files(
        root.path(),
        &["artifacts/synthetic_metric_source.json".to_string()],
    )
    .expect("relative resolver should read declared artifact");
    assert_eq!(resolver.lookups.len(), 1);
    assert_eq!(
        resolver.lookups[0].source_kind,
        ResultCandidateSourceKind::RelativeFile
    );
    assert_eq!(
        resolver
            .lookup("artifacts/synthetic_metric_source.json")
            .and_then(|lookup| lookup.bytes.as_ref())
            .expect("lookup should carry bytes"),
        b"synthetic metric source v1\n"
    );

    let unsafe_ref = ResultCandidateArtifactResolver::from_relative_files(
        root.path(),
        &["../synthetic_metric_source.json".to_string()],
    )
    .expect_err("traversal refs should be rejected");
    assert!(matches!(
        unsafe_ref,
        ZkBenchError::SyntheticImport { ref path, .. }
            if path == "artifact_resolver.from_relative_files.artifact_ref"
    ));

    let missing_ref = ResultCandidateArtifactResolver::from_relative_files(
        root.path(),
        &["artifacts/missing.json".to_string()],
    )
    .expect_err("missing declared artifact should be reported");
    assert!(matches!(
        missing_ref,
        ZkBenchError::SyntheticImport { ref path, .. }
            if path.ends_with("artifacts/missing.json")
    ));
}

#[test]
fn importer_reports_malformed_json_with_import_context() {
    let error = SyntheticResultImporter::new(resolver())
        .import_candidate_json("{")
        .expect_err("malformed candidate JSON should fail before validation");

    assert!(matches!(
        error,
        ZkBenchError::Deserialization { ref path, .. } if path == "import_candidate_json"
    ));
}

#[test]
fn explicit_config_and_source_are_preserved_on_quarantine_bundle() {
    let mut config = SyntheticResultImportConfig {
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        artifact_capture_contract: build_default_artifact_capture_contract(),
        ..SyntheticResultImportConfig::default()
    };
    config.artifact_capture_contract.expected_artifacts.clear();

    let source = ResultCandidateSource {
        id: "phase_189_fixture_source".to_string(),
        kind: ResultCandidateSourceKind::SyntheticFixture,
        relative_uri: Some("fixtures/synthetic_result_candidate_valid.json".to_string()),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec!["phase 189 local fixture source".to_string()],
    };
    let importer = SyntheticResultImporter::with_config(config, resolver(), source.clone());
    let bundle = importer
        .import_candidate(candidate())
        .expect("invalid config should quarantine rather than throw");

    assert_eq!(bundle.source, source);
    assert!(bundle.normalized_draft.is_none());
    assert!(bundle.quarantine_manifest.is_some());
    assert!(!bundle.validation.valid);
    let kinds = issue_kinds(&bundle.validation);
    assert!(kinds.contains(&SyntheticImportValidationIssueKind::ClaimBoundaryTooHigh));
    assert!(kinds.contains(&SyntheticImportValidationIssueKind::SchemaValidationFailed));
    assert!(bundle
        .validation
        .issues
        .iter()
        .any(|issue| issue.path == "contract.expected_artifacts"));
}

#[test]
fn artifact_digest_validation_reports_resolver_and_candidate_edge_cases() {
    let mut unsupported_lookup = resolver()
        .lookup("artifacts/synthetic_metric_source.json")
        .expect("fixture lookup should exist")
        .clone();
    unsupported_lookup.expected_digest.algorithm = ArtifactDigestAlgorithm::Unsupported;
    let unsupported_resolver =
        ResultCandidateArtifactResolver::with_lookups(vec![unsupported_lookup]);
    let unsupported =
        zkbench_core::validate_synthetic_result_candidate(&candidate(), &unsupported_resolver);
    assert!(unsupported
        .artifact_digest_validation
        .issues
        .iter()
        .any(|issue| issue.kind == SyntheticImportValidationIssueKind::ArtifactDigestUnsupported));

    let mut stale_lookup = ResultCandidateArtifactLookup {
        artifact_ref: "artifacts/synthetic_metric_source.json".to_string(),
        expected_digest: compute_artifact_digest_bytes(
            b"declared digest bytes",
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Output),
        ),
        bytes: Some(b"different resolver bytes".to_vec()),
        source_kind: ResultCandidateSourceKind::InMemory,
        notes: vec!["phase 189 stale lookup".to_string()],
    };
    let stale_resolver = ResultCandidateArtifactResolver::with_lookups(vec![stale_lookup.clone()]);
    let stale = zkbench_core::validate_synthetic_result_candidate(&candidate(), &stale_resolver);
    assert!(stale
        .artifact_digest_validation
        .issues
        .iter()
        .any(|issue| issue.message == "resolver digest does not match resolver bytes"));

    stale_lookup.expected_digest = compute_artifact_digest_bytes(
        b"synthetic metric source v1\n",
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Output),
    );
    stale_lookup.bytes = Some(b"synthetic metric source v1\n".to_vec());
    let mut no_candidate_digest = candidate();
    no_candidate_digest.artifact_digests.clear();
    let missing = zkbench_core::validate_synthetic_result_candidate(
        &no_candidate_digest,
        &ResultCandidateArtifactResolver::with_lookups(vec![stale_lookup]),
    );
    assert!(missing
        .artifact_digest_validation
        .issues
        .iter()
        .any(|issue| issue.kind == SyntheticImportValidationIssueKind::ArtifactDigestMissing));
}

#[test]
fn metric_and_claim_text_scans_report_nested_rejection_paths() {
    let mut candidate = candidate();
    candidate.normalized_metrics[0].unit = ExternalMetricUnit::Milliseconds;
    candidate.normalized_metrics[0].value = Some("not-an-integer".to_string());
    candidate.normalized_metrics[0].source_artifact_ref = Some("../metric.json".to_string());
    candidate.normalized_metrics[0]
        .notes
        .push("this is a machine-checked proof".to_string());
    candidate
        .notes
        .push("official benchmark result".to_string());
    candidate.notes.push("proof-system soundness".to_string());

    let validation = zkbench_core::validate_synthetic_result_candidate(&candidate, &resolver());

    assert!(!validation.valid);
    assert!(validation
        .metric_candidate_validation
        .issues
        .iter()
        .any(
            |issue| issue.path == "candidate.normalized_metrics[0].value"
                && issue.message == "numeric metric values must parse as integers"
        ));
    assert!(validation
        .artifact_digest_validation
        .issues
        .iter()
        .any(
            |issue| issue.path == "candidate.normalized_metrics[0].source_artifact_ref"
                && issue.kind == SyntheticImportValidationIssueKind::PathRejected
        ));
    assert!(validation.official_claim_detection.detected);
    assert!(validation.formal_claim_detection.detected);
    assert!(validation.soundness_claim_detection.detected);
    assert!(validation
        .formal_claim_detection
        .issues
        .iter()
        .any(|issue| issue.path == "candidate.normalized_metrics[0].notes[2]"));
}

use zkbench_core::{
    deserialize_external_result_candidate_json, validate_synthetic_result_candidate,
    ArtifactDigestAlgorithm, ResultCandidateArtifactResolver, SyntheticImportValidationIssueKind,
};

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

#[test]
fn valid_candidate_digest_matches_local_artifact_bytes() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    let validation = validate_synthetic_result_candidate(&candidate, &resolver());

    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(
        validation
            .artifact_digest_validation
            .matched_artifact_ref_count,
        2
    );
}

#[test]
fn bad_candidate_digest_is_rejected() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_bad_digest.json"
    ))
    .expect("fixture should parse");
    let validation = validate_synthetic_result_candidate(&candidate, &resolver());

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| { issue.kind == SyntheticImportValidationIssueKind::ArtifactDigestMismatch }));
}

#[test]
fn missing_resolver_lookup_is_rejected() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    let validation =
        validate_synthetic_result_candidate(&candidate, &ResultCandidateArtifactResolver::new());

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| { issue.kind == SyntheticImportValidationIssueKind::ArtifactLookupMissing }));
}

#[test]
fn unsupported_digest_algorithm_is_rejected() {
    let mut candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    candidate.artifact_digests[0].algorithm = ArtifactDigestAlgorithm::Unsupported;

    let validation = validate_synthetic_result_candidate(&candidate, &resolver());
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == SyntheticImportValidationIssueKind::ArtifactDigestUnsupported
    }));
}

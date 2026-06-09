use zkbench_core::{
    deserialize_external_result_candidate_json, validate_synthetic_result_candidate,
    ExternalMetricCandidate, ExternalMetricUnit, ResultCandidateArtifactResolver,
    SyntheticImportValidationIssueKind,
};

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

#[test]
fn metric_value_without_source_artifact_is_rejected() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_metric_without_source.json"
    ))
    .expect("fixture should parse");
    let validation = validate_synthetic_result_candidate(&candidate, &resolver());

    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == SyntheticImportValidationIssueKind::MetricValidationFailed
            && issue.path.contains("source_artifact_ref")
    }));
}

#[test]
fn unknown_metric_unit_is_rejected() {
    let mut candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    candidate.normalized_metrics.push(ExternalMetricCandidate {
        metric_kind: "SyntheticUnknownUnit".to_string(),
        unit: ExternalMetricUnit::Unknown,
        value: None,
        source_artifact_ref: Some("artifacts/synthetic_metric_source.json".to_string()),
        notes: Vec::new(),
    });

    let validation = validate_synthetic_result_candidate(&candidate, &resolver());
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == SyntheticImportValidationIssueKind::MetricValidationFailed
            && issue.path.contains("unit")
    }));
}

#[test]
fn negative_numeric_metric_value_is_rejected() {
    let mut candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    candidate.normalized_metrics.push(ExternalMetricCandidate {
        metric_kind: "SyntheticDurationCheck".to_string(),
        unit: ExternalMetricUnit::Milliseconds,
        value: Some("-1".to_string()),
        source_artifact_ref: Some("artifacts/synthetic_metric_source.json".to_string()),
        notes: Vec::new(),
    });

    let validation = validate_synthetic_result_candidate(&candidate, &resolver());
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == SyntheticImportValidationIssueKind::MetricValidationFailed
            && issue.path.contains("value")
    }));
}

use zkbench_core::{
    deserialize_external_result_candidate_json, validate_synthetic_result_candidate,
    ResultCandidateArtifactResolver, SyntheticImportValidationIssueKind,
};

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

#[test]
fn valid_candidate_provenance_passes_contract_validation() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    let validation = validate_synthetic_result_candidate(&candidate, &resolver());

    assert!(
        validation.provenance_contract_validation.valid,
        "{:?}",
        validation.provenance_contract_validation.issues
    );
}

#[test]
fn missing_provenance_is_rejected() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_missing_provenance.json"
    ))
    .expect("fixture should parse");
    let validation = validate_synthetic_result_candidate(&candidate, &resolver());

    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == SyntheticImportValidationIssueKind::ProvenanceValidationFailed
    }));
}

#[test]
fn provenance_forbidden_claim_text_is_rejected() {
    let mut candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    candidate
        .provenance_draft
        .as_mut()
        .expect("provenance should exist")
        .notes
        .push("formal proof for the imported candidate".to_string());

    let validation = validate_synthetic_result_candidate(&candidate, &resolver());
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.kind == SyntheticImportValidationIssueKind::ProvenanceValidationFailed
    }));
}

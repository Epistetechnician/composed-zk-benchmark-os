use zkbench_core::{
    build_default_artifact_capture_contract, deserialize_artifact_capture_contract_json,
    serialize_artifact_capture_contract_json, validate_artifact_capture_contract, ClaimBoundary,
    ExpectedArtifactRole,
};

#[test]
fn default_contract_includes_expected_future_artifact_roles() {
    let contract = build_default_artifact_capture_contract();
    let roles = contract
        .expected_artifacts
        .iter()
        .map(|artifact| artifact.role)
        .collect::<Vec<_>>();

    assert!(roles.contains(&ExpectedArtifactRole::InputManifest));
    assert!(roles.contains(&ExpectedArtifactRole::CandidateWorkloadManifest));
    assert!(roles.contains(&ExpectedArtifactRole::ExternalToolVersion));
    assert!(roles.contains(&ExpectedArtifactRole::RawExternalOutput));
    assert!(roles.contains(&ExpectedArtifactRole::NormalizedResultCandidate));
    assert!(roles.contains(&ExpectedArtifactRole::ProvenanceRecord));
    assert!(roles.contains(&ExpectedArtifactRole::ValidationReport));
    assert!(roles.contains(&ExpectedArtifactRole::EvidenceAppendProposal));
    assert!(contract.has_no_actual_external_artifacts());
    assert_eq!(contract.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn contract_round_trips_through_json() {
    let contract = build_default_artifact_capture_contract();
    let json =
        serialize_artifact_capture_contract_json(&contract).expect("contract should serialize");
    let parsed =
        deserialize_artifact_capture_contract_json(&json).expect("contract should deserialize");
    let json_again =
        serialize_artifact_capture_contract_json(&parsed).expect("contract should serialize again");

    assert_eq!(contract, parsed);
    assert_eq!(json, json_again);
}

#[test]
fn contract_rejects_absolute_artifact_paths() {
    let mut contract = build_default_artifact_capture_contract();
    contract.expected_artifacts[0].relative_path_hint = Some("/tmp/raw-output.json".to_string());

    let validation = validate_artifact_capture_contract(&contract);
    assert!(!validation.valid);
    assert!(validation
        .errors
        .iter()
        .any(|issue| issue.message.contains("absolute")));
}

#[test]
fn contract_distinguishes_expected_from_captured_artifacts() {
    let contract = build_default_artifact_capture_contract();
    assert!(!contract.expected_artifacts.is_empty());
    assert!(contract.captured_artifacts.is_empty());
    assert_eq!(contract.claim_boundary, ClaimBoundary::Level0DesignNote);
}

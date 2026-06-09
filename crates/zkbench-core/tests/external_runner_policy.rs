use zkbench_core::{
    build_default_external_runner_policy, deserialize_external_runner_policy_json,
    serialize_external_runner_policy_json, validate_external_runner_policy, ClaimBoundary,
    ExternalExecutionMode,
};

#[test]
fn default_policy_is_disabled_and_requires_review_gates() {
    let policy = build_default_external_runner_policy();

    assert_eq!(policy.mode, ExternalExecutionMode::Disabled);
    assert!(policy.gate.requires_manual_review);
    assert!(policy.gate.requires_artifact_capture_contract);
    assert!(policy.gate.requires_provenance_contract);
    assert!(policy.gate.requires_result_import_validation);
    assert!(policy.gate.requires_claim_boundary_review);
    assert!(!policy.allows_live_execution());
    assert_eq!(policy.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn default_claim_policy_rejects_level2_actual_evidence() {
    let policy = build_default_external_runner_policy();

    assert!(policy
        .claim_boundary_policy
        .permits_actual_claim_boundary(ClaimBoundary::Level1LocalReplay));
    assert!(!policy
        .claim_boundary_policy
        .permits_actual_claim_boundary(ClaimBoundary::Level2ReproducibleBenchmarkArtifact));
}

#[test]
fn policy_round_trips_through_json() {
    let policy = build_default_external_runner_policy();
    let json = serialize_external_runner_policy_json(&policy).expect("policy should serialize");
    let parsed = deserialize_external_runner_policy_json(&json).expect("policy should deserialize");
    let json_again =
        serialize_external_runner_policy_json(&parsed).expect("policy should serialize again");

    assert_eq!(policy, parsed);
    assert_eq!(json, json_again);
}

#[test]
fn policy_rejects_absolute_paths_and_live_mode() {
    let mut policy = build_default_external_runner_policy();
    policy
        .path_policy
        .allowed_relative_roots
        .push("/tmp/external".to_string());
    assert!(!validate_external_runner_policy(&policy).is_empty());

    let mut live = build_default_external_runner_policy();
    live.mode = ExternalExecutionMode::FutureLiveExecutionNotImplemented;
    let issues = validate_external_runner_policy(&live);
    assert!(issues
        .iter()
        .any(|issue| issue.message.contains("live external execution")));
}

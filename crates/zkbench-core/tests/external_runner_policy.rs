use zkbench_core::{
    build_default_external_runner_policy, deserialize_external_runner_policy_json,
    serialize_external_runner_policy_json, validate_external_runner_policy, ClaimBoundary,
    ExternalExecutionMode, ExternalRunnerPolicy,
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
fn phase_h_default_and_manual_handoff_policy_helpers_are_bounded() {
    let default = ExternalRunnerPolicy::phase_h_default();
    let manual = ExternalRunnerPolicy::phase_h_manual_handoff_only();

    assert_eq!(default, build_default_external_runner_policy());
    assert_eq!(manual.mode, ExternalExecutionMode::ManualHandoffOnly);
    assert!(!manual.allows_live_execution());
    assert!(validate_external_runner_policy(&manual).is_empty());
    assert!(manual
        .notes
        .iter()
        .any(|note| note.contains("no live execution API")));
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
fn policy_validation_reports_identity_boundary_gate_and_path_flags() {
    let mut policy = build_default_external_runner_policy();
    policy.id.clear();
    policy.claim_boundary = ClaimBoundary::Level1LocalReplay;
    policy.claim_boundary_policy.maximum_actual_claim_boundary = ClaimBoundary::Level0DesignNote;
    policy.gate.requires_manual_review = false;
    policy.path_policy.allow_absolute_paths = true;

    let issues = validate_external_runner_policy(&policy);
    let paths = issues
        .iter()
        .map(|issue| issue.path.as_str())
        .collect::<Vec<_>>();

    for expected_path in [
        "policy.id",
        "policy.claim_boundary",
        "policy.claim_boundary_policy",
        "policy.gate",
        "policy.path_policy.allow_absolute_paths",
    ] {
        assert!(
            paths.contains(&expected_path),
            "missing expected issue path {expected_path}; got {issues:?}"
        );
    }
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

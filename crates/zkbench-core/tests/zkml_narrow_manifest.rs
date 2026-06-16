use zkbench_core::{
    build_default_zkml_narrow_adapter_manifest, build_zkml_narrow_workload_plan,
    deserialize_zkml_narrow_manifest_json, deserialize_zkml_narrow_workload_plan_json,
    serialize_zkml_narrow_manifest_json, serialize_zkml_narrow_workload_plan_json, ClaimBoundary,
    ZkmlNarrowAdapterStatus, ZkmlNarrowExecutionPolicy,
};

#[test]
fn default_zkml_narrow_manifest_is_inert_and_claim_safe() {
    let manifest = build_default_zkml_narrow_adapter_manifest();

    assert!(matches!(
        manifest.adapter_status,
        ZkmlNarrowAdapterStatus::WorkloadPlanningOnly
            | ZkmlNarrowAdapterStatus::ExternalExecutionDisabled
    ));
    assert!(!manifest.source_policy.external_repo_checkout_allowed);
    assert!(!manifest.source_policy.external_command_execution_allowed);
    assert!(
        !manifest
            .source_policy
            .external_benchmark_result_import_allowed
    );
    assert!(manifest.capability_declaration.supports_zkml_metrics);
    assert!(
        manifest
            .capability_declaration
            .supports_public_private_boundary_checks
    );
    assert!(!manifest.capability_declaration.supports_execution);
    assert!(!manifest.claim_boundary_policy.allow_level2_in_phase_l);
    assert_eq!(
        manifest.claim_boundary_policy.phase_l_artifact_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(manifest
        .scope
        .supported_semantic_fixture_ids
        .contains(&"zkml_control_flow_mixed".to_string()));
}

#[test]
fn zkml_narrow_manifest_round_trips_deterministically() {
    let manifest = build_default_zkml_narrow_adapter_manifest();
    let json = serialize_zkml_narrow_manifest_json(&manifest)
        .expect("manifest should serialize as deterministic JSON");
    let parsed = deserialize_zkml_narrow_manifest_json(&json).expect("manifest should deserialize");
    let json_again =
        serialize_zkml_narrow_manifest_json(&parsed).expect("manifest should serialize again");

    assert_eq!(manifest, parsed);
    assert_eq!(json, json_again);
    assert!(json.contains("candidate workload mapping only"));
    assert!(json.contains("zkML metrics do not prove semantic soundness"));
}

#[test]
fn zkml_narrow_workload_plan_round_trips_deterministically() {
    let plan = build_zkml_narrow_workload_plan().expect("workload plan should build");
    let json =
        serialize_zkml_narrow_workload_plan_json(&plan).expect("workload plan should serialize");
    let parsed =
        deserialize_zkml_narrow_workload_plan_json(&json).expect("plan should deserialize");
    let json_again =
        serialize_zkml_narrow_workload_plan_json(&parsed).expect("plan should serialize again");

    assert_eq!(plan, parsed);
    assert_eq!(json, json_again);
    assert_eq!(plan.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(plan.execution_policy, ZkmlNarrowExecutionPolicy::Disabled);
    assert_eq!(plan.scope.machine_id, "zkml_control_flow_mixed");
    assert!(plan
        .scope
        .public_input_fields
        .contains(&"confidence".to_string()));
}

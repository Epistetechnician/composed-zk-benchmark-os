use zkbench_core::{
    build_default_gnark_recursion_adapter_manifest, build_gnark_recursion_envelope_plan,
    deserialize_gnark_recursion_envelope_plan_json, deserialize_gnark_recursion_manifest_json,
    serialize_gnark_recursion_envelope_plan_json, serialize_gnark_recursion_manifest_json,
    ClaimBoundary, GnarkRecursionAdapterStatus, GnarkRecursionExecutionPolicy,
};

#[test]
fn default_gnark_recursion_manifest_is_inert_and_claim_safe() {
    let manifest = build_default_gnark_recursion_adapter_manifest();

    assert!(matches!(
        manifest.adapter_status,
        GnarkRecursionAdapterStatus::EnvelopePlanningOnly
            | GnarkRecursionAdapterStatus::ExternalExecutionDisabled
    ));
    assert!(!manifest.source_policy.external_repo_checkout_allowed);
    assert!(!manifest.source_policy.external_command_execution_allowed);
    assert!(
        !manifest
            .source_policy
            .external_benchmark_result_import_allowed
    );
    assert!(manifest.source_policy.future_source_verification_required);
    assert!(manifest.schema_assumption.future_verification_required);
    assert!(manifest.schema_assumption.internal_candidate_mapping);
    assert!(!manifest.schema_assumption.official_schema_claimed);
    assert!(!manifest.compatibility_target.complete_compatibility_claimed);
    assert!(!manifest.claim_boundary_policy.allow_level2_in_phase_k);
    assert!(manifest.capability_declaration.supports_recursion);
    assert!(!manifest.capability_declaration.supports_execution);
    assert_eq!(
        manifest.claim_boundary_policy.phase_k_artifact_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(manifest
        .scope
        .supported_semantic_fixture_ids
        .contains(&"recursive_loop_envelope".to_string()));
}

#[test]
fn gnark_recursion_manifest_round_trips_deterministically() {
    let manifest = build_default_gnark_recursion_adapter_manifest();
    let json = serialize_gnark_recursion_manifest_json(&manifest)
        .expect("manifest should serialize as deterministic JSON");
    let parsed =
        deserialize_gnark_recursion_manifest_json(&json).expect("manifest should deserialize");
    let json_again =
        serialize_gnark_recursion_manifest_json(&parsed).expect("manifest should serialize again");

    assert_eq!(manifest, parsed);
    assert_eq!(json, json_again);
    assert!(json.contains("candidate envelope mapping only"));
    assert!(json.contains("Recursion proof is not semantic proof"));
}

#[test]
fn gnark_recursion_envelope_plan_round_trips_deterministically() {
    let plan = build_gnark_recursion_envelope_plan().expect("envelope plan should build");
    let json = serialize_gnark_recursion_envelope_plan_json(&plan)
        .expect("envelope plan should serialize");
    let parsed =
        deserialize_gnark_recursion_envelope_plan_json(&json).expect("plan should deserialize");
    let json_again =
        serialize_gnark_recursion_envelope_plan_json(&parsed).expect("plan should serialize again");

    assert_eq!(plan, parsed);
    assert_eq!(json, json_again);
    assert_eq!(plan.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        plan.execution_policy,
        GnarkRecursionExecutionPolicy::Disabled
    );
    assert_eq!(plan.scope.machine_id, "recursive_loop_envelope");
}

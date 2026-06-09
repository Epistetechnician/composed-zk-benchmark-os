use zkbench_core::{
    build_default_zk_harness_adapter_manifest, deserialize_zk_harness_manifest_json,
    serialize_zk_harness_manifest_json, ClaimBoundary, ZkHarnessAdapterStatus,
};

#[test]
fn default_zk_harness_manifest_is_dry_run_only_and_claim_safe() {
    let manifest = build_default_zk_harness_adapter_manifest();

    assert!(matches!(
        manifest.adapter_status,
        ZkHarnessAdapterStatus::DryRunOnly | ZkHarnessAdapterStatus::ExternalExecutionDisabled
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
    assert!(!manifest.claim_boundary_policy.allow_level2_in_phase_g);
    assert_eq!(
        manifest.claim_boundary_policy.phase_g_artifact_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn zk_harness_manifest_round_trips_deterministically() {
    let manifest = build_default_zk_harness_adapter_manifest();
    let json = serialize_zk_harness_manifest_json(&manifest)
        .expect("manifest should serialize as deterministic JSON");
    let parsed =
        deserialize_zk_harness_manifest_json(&json).expect("manifest should deserialize from JSON");
    let json_again =
        serialize_zk_harness_manifest_json(&parsed).expect("manifest should serialize again");

    assert_eq!(manifest, parsed);
    assert_eq!(json, json_again);
    assert!(json.contains("candidate dry-run mapping only"));
    assert!(!json.contains("\"complete_compatibility_claimed\": true"));
}

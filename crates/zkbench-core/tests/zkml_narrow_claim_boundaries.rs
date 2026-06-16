use zkbench_core::{
    build_zkml_narrow_workload_plan, serialize_zkml_narrow_workload_plan_json, ClaimBoundary,
    MutationClass,
};

#[test]
fn workload_plan_does_not_emit_evidence_records_or_performance_values() {
    let plan = build_zkml_narrow_workload_plan().expect("workload plan should build");

    assert_eq!(plan.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        plan.evidence_mapping.current_phase_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!plan.evidence_mapping.emits_evidence_records);
    assert!(
        plan.evidence_policy
            .zkml_metrics_do_not_prove_semantic_soundness
    );
    assert!(plan
        .scope
        .supported_mutation_classes
        .contains(&MutationClass::ObservationOmission));

    let json =
        serialize_zkml_narrow_workload_plan_json(&plan).expect("workload plan should serialize");
    assert!(plan
        .metric_schema
        .iter()
        .all(|metric| !metric.contains(':')));
    assert!(!json.contains("benchmark pass"));
    assert!(!json.contains("official benchmark evidence"));
    assert!(!json.contains("BackendOutcome::Accepted"));
}

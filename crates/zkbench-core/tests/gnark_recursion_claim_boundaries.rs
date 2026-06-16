use zkbench_core::{
    build_gnark_recursion_envelope_plan, serialize_gnark_recursion_envelope_plan_json,
    ClaimBoundary,
};

#[test]
fn envelope_plan_does_not_emit_evidence_records_or_performance_values() {
    let plan = build_gnark_recursion_envelope_plan().expect("envelope plan should build");

    assert_eq!(plan.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        plan.evidence_mapping.current_phase_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!plan.evidence_mapping.emits_evidence_records);
    assert!(plan.evidence_policy.recursion_proof_is_not_semantic_proof);

    let json = serialize_gnark_recursion_envelope_plan_json(&plan)
        .expect("envelope plan should serialize");
    assert!(plan
        .metric_schema
        .iter()
        .all(|metric| !metric.contains(':')));
    assert!(!json.contains("benchmark pass"));
    assert!(!json.contains("official benchmark evidence"));
    assert!(!json.contains("BackendOutcome::Accepted"));
}

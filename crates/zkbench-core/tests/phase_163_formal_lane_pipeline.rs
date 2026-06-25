//! Phase 163 — formal lane pipeline wiring.

use zkbench_core::{
    evaluate_formal_lane_pipeline, generate_instance, pipeline_outcome_is_declared_only,
    ClaimBoundary, FormalLaneProofStatus, FormalPropertyScopeKind, GeneratorConfig, InstanceParams,
    MutationClass, SoakTelemetryCounters,
};

#[test]
fn formal_lane_pipeline_stays_declared_only() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop(),
        InstanceParams::default(),
    )
    .expect("instance should generate");
    let outcome =
        evaluate_formal_lane_pipeline(MutationClass::InvariantWeakening, &instance.surface_spec)
            .expect("pipeline should evaluate");
    assert!(outcome.template_derived);
    assert_eq!(outcome.mutation_class, MutationClass::InvariantWeakening);
    assert_eq!(
        outcome.primary_formal_scope,
        FormalPropertyScopeKind::Invariant
    );
    assert_eq!(outcome.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        outcome.proof_status,
        Some(FormalLaneProofStatus::DeclaredOnly)
    );
    assert!(outcome.no_template_reason.is_none());
    assert!(outcome
        .nonclaims
        .iter()
        .any(|item| item.contains("not proof")));
    assert!(pipeline_outcome_is_declared_only(&outcome));
}

#[test]
fn soak_telemetry_records_formal_lane_pipeline() {
    let mut counters = SoakTelemetryCounters::default();
    counters.record_formal_lane_pipeline(true, true);
    assert_eq!(counters.formal_lane_template_derived_count, 1);
    assert_eq!(counters.formal_lane_evaluation_count, 1);
    assert_eq!(counters.formal_lane_declared_only_count, 1);
}

#[test]
fn formal_lane_pipeline_records_no_template_reason() {
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("instance should generate");
    let outcome =
        evaluate_formal_lane_pipeline(MutationClass::InvariantWeakening, &instance.surface_spec)
            .expect("pipeline should evaluate");
    assert!(!outcome.template_derived);
    assert_eq!(
        outcome.primary_formal_scope,
        FormalPropertyScopeKind::Invariant
    );
    assert_eq!(outcome.proof_status, None);
    assert!(outcome
        .no_template_reason
        .as_deref()
        .is_some_and(|reason| reason.contains("no invariant")));
    assert!(!pipeline_outcome_is_declared_only(&outcome));
}

#[test]
fn soak_telemetry_records_formal_scope_and_status_detail() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop(),
        InstanceParams::default(),
    )
    .expect("instance should generate");
    let outcome =
        evaluate_formal_lane_pipeline(MutationClass::InvariantWeakening, &instance.surface_spec)
            .expect("pipeline should evaluate");
    let mut counters = SoakTelemetryCounters::default();
    counters.record_formal_lane_pipeline_outcome(&outcome);
    assert_eq!(counters.formal_lane_template_derived_count, 1);
    assert_eq!(counters.formal_lane_evaluation_count, 1);
    assert_eq!(counters.formal_lane_declared_only_count, 1);
    assert_eq!(counters.formal_lane_no_template_count, 0);
    assert!(counters
        .formal_lane_count_by_scope
        .iter()
        .any(
            |metric| metric.metric_name == "formal_lane_scope_invariant_count" && metric.count == 1
        ));
    assert!(counters
        .formal_lane_count_by_status
        .iter()
        .any(
            |metric| metric.metric_name == "formal_lane_status_declared_only_count"
                && metric.count == 1
        ));
}

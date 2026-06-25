//! Phase 163 — formal lane pipeline wiring.

use zkbench_core::{
    evaluate_formal_lane_pipeline, generate_instance, pipeline_outcome_is_declared_only,
    ClaimBoundary, GeneratorConfig, InstanceParams, MutationClass, SoakTelemetryCounters,
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
    assert_eq!(outcome.claim_boundary, ClaimBoundary::Level0DesignNote);
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

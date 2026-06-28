//! Phase 200 mutation invalid-unroll-bounds coverage thirty-fifth tranche.
//!
//! Focused local regression coverage for reachable
//! `InvalidUnrollBoundsPass::apply` paths in
//! `crates/zkbench-core/src/mutation/invalid_unroll_bounds.rs`. The
//! `negate_bound` `Bool` and `RawText` arms remain structurally unreachable
//! because the selector already restricts the bound to executable `Expr`
//! variants; the `target.bound is None` arm is structurally unreachable because
//! the selector already requires `Some(...)`. This tranche does not force those
//! branches.

use zkbench_core::{
    apply_mutation_pass, generate_instance, ClaimBoundary, ExpectedVerdict, GeneratorConfig,
    InstanceParams, InvalidUnrollBoundsPass, MutationClass, MutationPass, MutationSafetyClass,
};

fn bounded_counter_loop() -> GeneratorConfig {
    GeneratorConfig::bounded_counter_loop().loop_bound(3)
}

#[test]
fn invalid_unroll_bounds_pass_reports_its_mutation_class() {
    assert_eq!(
        InvalidUnrollBoundsPass.mutation_class(),
        MutationClass::InvalidUnrollBounds
    );
}

#[test]
fn invalid_unroll_bounds_rejects_instance_without_any_declared_trace() {
    let mut instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop instance should generate");
    instance.accepted_traces.clear();
    instance.rejected_traces.clear();

    let error = apply_mutation_pass(&instance, &InvalidUnrollBoundsPass)
        .expect_err("missing trace should be rejected before bound mutation");
    assert!(error
        .to_string()
        .contains("source instance declares no accepted or rejected trace"));
}

#[test]
fn invalid_unroll_bounds_preserves_primary_trace_and_level1_boundary() {
    let instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop instance should generate");
    let expected_primary_id = instance.primary_trace.id.clone();
    let mutated = apply_mutation_pass(&instance, &InvalidUnrollBoundsPass)
        .expect("invalid unroll bounds should apply");
    assert_eq!(mutated.primary_trace.id, expected_primary_id);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.safety_class, MutationSafetyClass::NearValid);
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
    assert!(mutated
        .provenance
        .affected_guard_ids
        .iter()
        .any(|guard| guard.ends_with(".bound")));
}

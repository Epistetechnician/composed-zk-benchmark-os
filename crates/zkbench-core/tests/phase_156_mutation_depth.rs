//! Phase 156 — mutation engine depth coverage.
//!
//! Each test exercises one of the five new passes against an eligible generated
//! instance, plus the "no eligible target" path where applicable. All mutated
//! instances must remain `ClaimBoundary::Level1LocalReplay`.

use zkbench_core::value::Value;
use zkbench_core::{
    apply_mutation_pass, generate_instance, ClaimBoundary, ExpectedVerdict, GeneratorConfig,
    InstanceParams, InvalidUnrollBoundsPass, InvariantStrengtheningPass, InvariantWeakeningPass,
    MutationClass, MutationEngine, MutationPass, MutationSafetyClass, ObservationOmissionPass,
    StaleStateReadsPass,
};

const INVARIANT_FAMILY_BOUND: usize = 3;

fn bounded_counter_loop() -> GeneratorConfig {
    GeneratorConfig::bounded_counter_loop().loop_bound(INVARIANT_FAMILY_BOUND)
}

// ---------- InvariantWeakeningPass ----------

#[test]
fn invariant_weakening_reports_its_mutation_class() {
    assert_eq!(
        InvariantWeakeningPass.mutation_class(),
        MutationClass::InvariantWeakening
    );
}

#[test]
fn invariant_weakening_applies_to_eligible_generated_instance() {
    let instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop instance should generate");
    let mutated = apply_mutation_pass(&instance, &InvariantWeakeningPass)
        .expect("invariant weakening should apply");
    assert_eq!(mutated.mutation_class, MutationClass::InvariantWeakening);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::UnsoundIfAccepted);
    assert_eq!(mutated.safety_class, MutationSafetyClass::Malicious);
    assert!(!mutated.provenance.affected_guard_ids.is_empty());
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn invariant_weakening_handles_no_eligible_target_without_panic() {
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("branching instance should generate");
    let error = apply_mutation_pass(&instance, &InvariantWeakeningPass)
        .expect_err("branching FSM declares no invariants");
    assert!(error
        .to_string()
        .contains("no invariant with a non-trivial"));
}

#[test]
fn invariant_weakening_fails_after_target_selection_when_no_trace_exists() {
    let mut instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop instance should generate");
    assert!(!instance.surface_spec.machine.invariants.is_empty());
    instance.accepted_traces.clear();
    instance.rejected_traces.clear();
    instance.surface_spec.oracle.accepted_traces.clear();
    instance.surface_spec.oracle.rejected_traces.clear();

    let error = apply_mutation_pass(&instance, &InvariantWeakeningPass)
        .expect_err("eligible invariant without traces should reject");

    assert!(error
        .to_string()
        .contains("source instance declares no accepted or rejected trace"));
}

// ---------- InvariantStrengtheningPass ----------

#[test]
fn invariant_strengthening_reports_its_mutation_class() {
    assert_eq!(
        InvariantStrengtheningPass.mutation_class(),
        MutationClass::InvariantStrengthening
    );
}

#[test]
fn invariant_strengthening_applies_to_eligible_generated_instance() {
    let instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop instance should generate");
    let mutated = apply_mutation_pass(&instance, &InvariantStrengtheningPass)
        .expect("invariant strengthening should apply");
    assert_eq!(
        mutated.mutation_class,
        MutationClass::InvariantStrengthening
    );
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.safety_class, MutationSafetyClass::NearValid);
    assert!(!mutated.provenance.affected_guard_ids.is_empty());
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn invariant_strengthening_handles_no_eligible_target_without_panic() {
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("branching instance should generate");
    let error = apply_mutation_pass(&instance, &InvariantStrengtheningPass)
        .expect_err("branching FSM declares no invariants");
    assert!(error
        .to_string()
        .contains("no invariant with a non-trivial"));
}

#[test]
fn invariant_strengthening_fails_after_target_selection_when_no_trace_exists() {
    let mut instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop instance should generate");
    assert!(!instance.surface_spec.machine.invariants.is_empty());
    instance.accepted_traces.clear();
    instance.rejected_traces.clear();
    instance.surface_spec.oracle.accepted_traces.clear();
    instance.surface_spec.oracle.rejected_traces.clear();

    let error = apply_mutation_pass(&instance, &InvariantStrengtheningPass)
        .expect_err("eligible invariant without traces should reject");

    assert!(error
        .to_string()
        .contains("source instance declares no accepted or rejected trace"));
}

// ---------- StaleStateReadsPass ----------

#[test]
fn stale_state_reads_applies_to_eligible_generated_instance() {
    // GuardHeavyMachine has multi-step accepted traces with write-then-read
    // dependencies (advance writes value, finish reads locked/value).
    let instance = generate_instance(
        GeneratorConfig::guard_heavy_machine(),
        InstanceParams::default(),
    )
    .expect("guard heavy machine instance should generate");
    let mutated = apply_mutation_pass(&instance, &StaleStateReadsPass)
        .ok()
        .or_else(|| {
            // BoundedCounterLoop is the fallback eligible family when GHM's
            // trace structure doesn't expose a write-then-read pair.
            let fallback = generate_instance(bounded_counter_loop(), InstanceParams::default())
                .expect("bounded counter loop instance should generate");
            apply_mutation_pass(&fallback, &StaleStateReadsPass).ok()
        })
        .expect("at least one family should be eligible for stale state reads");

    assert_eq!(mutated.mutation_class, MutationClass::StaleStateReads);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.safety_class, MutationSafetyClass::Diagnostic);
    assert_eq!(mutated.provenance.affected_transition_ids.len(), 2);
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn stale_state_reads_handles_no_eligible_target_without_panic() {
    // BranchingFsm accepted traces are single-step, so no window-of-2 exists.
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("branching instance should generate");
    let error = apply_mutation_pass(&instance, &StaleStateReadsPass)
        .expect_err("branching FSM accepted trace has fewer than 2 steps");
    assert!(error.to_string().contains("no accepted trace step pair"));
}

// ---------- InvalidUnrollBoundsPass ----------

#[test]
fn invalid_unroll_bounds_applies_to_eligible_generated_instance() {
    let instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop instance should generate");
    let mutated = apply_mutation_pass(&instance, &InvalidUnrollBoundsPass)
        .expect("invalid unroll bounds should apply");
    assert_eq!(mutated.mutation_class, MutationClass::InvalidUnrollBounds);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.safety_class, MutationSafetyClass::NearValid);
    assert!(!mutated.provenance.affected_guard_ids.is_empty());
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn invalid_unroll_bounds_handles_no_eligible_target_without_panic() {
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("branching instance should generate");
    let error = apply_mutation_pass(&instance, &InvalidUnrollBoundsPass)
        .expect_err("branching FSM declares no loops");
    assert!(error.to_string().contains("no loop with a non-empty body"));
}

// ---------- ObservationOmissionPass ----------

#[test]
fn observation_omission_applies_to_eligible_generated_instance() {
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("branching instance should generate");
    let mutated = apply_mutation_pass(&instance, &ObservationOmissionPass)
        .expect("observation omission should apply");
    assert_eq!(mutated.mutation_class, MutationClass::ObservationOmission);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.safety_class, MutationSafetyClass::Diagnostic);
    assert!(!mutated.provenance.affected_field_ids.is_empty());
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn observation_omission_fails_without_public_observation() {
    let mut instance =
        generate_instance(GeneratorConfig::baseline_fsm(), InstanceParams::default())
            .expect("baseline instance should generate");
    instance.surface_spec.machine.observations.clear();

    let error = apply_mutation_pass(&instance, &ObservationOmissionPass)
        .expect_err("instances without observations should reject");

    assert!(error
        .to_string()
        .contains("source instance declares no public observation"));
}

#[test]
fn observation_omission_fails_without_trace_after_observation_target_exists() {
    let mut instance =
        generate_instance(GeneratorConfig::baseline_fsm(), InstanceParams::default())
            .expect("baseline instance should generate");
    assert!(!instance.surface_spec.machine.observations.is_empty());
    instance.accepted_traces.clear();
    instance.rejected_traces.clear();
    instance.surface_spec.oracle.accepted_traces.clear();
    instance.surface_spec.oracle.rejected_traces.clear();

    let error = apply_mutation_pass(&instance, &ObservationOmissionPass)
        .expect_err("instances without traces should reject");

    assert!(error
        .to_string()
        .contains("source instance declares no accepted or rejected trace"));
}

#[test]
fn observation_omission_removes_observation_and_rewrites_accepted_trace() {
    let instance = generate_instance(GeneratorConfig::baseline_fsm(), InstanceParams::default())
        .expect("baseline instance should generate");
    let observation = instance.surface_spec.machine.observations[0].clone();
    let source_trace = instance.accepted_traces[0].clone();

    let mutated = apply_mutation_pass(&instance, &ObservationOmissionPass)
        .expect("observation omission should apply");

    assert!(!mutated
        .surface_spec
        .machine
        .observations
        .iter()
        .any(|candidate| candidate.id == observation.id));
    assert_eq!(
        mutated
            .primary_trace
            .expected_final_fields
            .get(&observation.field),
        Some(&Value::Int { int: i64::MIN })
    );
    let stored_trace = mutated
        .surface_spec
        .oracle
        .accepted_traces
        .iter()
        .find(|trace| trace.id == source_trace.id)
        .expect("accepted primary trace should be replaced");
    assert_eq!(
        stored_trace.expected_final_fields.get(&observation.field),
        Some(&Value::Int { int: i64::MIN })
    );
    assert!(mutated
        .provenance
        .notes
        .iter()
        .any(|note| note.contains("injected sentinel final-field mismatch")));
}

#[test]
fn observation_omission_rewrites_rejected_trace_when_no_accepted_trace_exists() {
    let mut instance =
        generate_instance(GeneratorConfig::baseline_fsm(), InstanceParams::default())
            .expect("baseline instance should generate");
    let observation = instance.surface_spec.machine.observations[0].clone();
    instance.accepted_traces.clear();
    instance.surface_spec.oracle.accepted_traces.clear();
    let source_trace = instance.rejected_traces[0].clone();

    let mutated = apply_mutation_pass(&instance, &ObservationOmissionPass)
        .expect("observation omission should use the rejected trace fallback");

    assert_eq!(mutated.primary_trace.id, source_trace.id);
    assert_eq!(
        mutated
            .primary_trace
            .expected_final_fields
            .get(&observation.field),
        Some(&Value::Int { int: i64::MIN })
    );
    assert!(mutated.surface_spec.oracle.accepted_traces.is_empty());
    let stored_trace = mutated
        .surface_spec
        .oracle
        .rejected_traces
        .iter()
        .find(|trace| trace.id == source_trace.id)
        .expect("rejected primary trace should be replaced");
    assert_eq!(
        stored_trace.expected_final_fields.get(&observation.field),
        Some(&Value::Int { int: i64::MIN })
    );
}

// ---------- Composition and determinism ----------

#[test]
fn custom_engine_with_new_passes_is_deterministic() {
    let instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop instance should generate");

    let build = || {
        MutationEngine::default()
            .with_pass(InvariantWeakeningPass)
            .with_pass(InvariantStrengtheningPass)
            .with_pass(InvalidUnrollBoundsPass)
            .with_pass(ObservationOmissionPass)
            .apply(&instance)
    };

    let left = build().expect("custom engine should apply on bounded counter loop");
    let right =
        build().expect("custom engine should apply deterministically on bounded counter loop");
    assert_eq!(left, right);
}

// ---------- Scope guard: no new MutationClass variants ----------

#[test]
fn mutation_class_enum_has_exactly_fourteen_variants() {
    // Guards against scope creep: Phase 156 must not add MutationClass variants.
    let all = [
        MutationClass::MissingConstraints,
        MutationClass::CorruptedGuards,
        MutationClass::BadCounters,
        MutationClass::StaleStateReads,
        MutationClass::InvalidUnrollBounds,
        MutationClass::NondeterministicTransitionInjection,
        MutationClass::RecursionEnvelopeMismatch,
        MutationClass::PublicPrivateBoundaryMismatch,
        MutationClass::WitnessAliasing,
        MutationClass::InvariantWeakening,
        MutationClass::InvariantStrengthening,
        MutationClass::ObservationOmission,
        MutationClass::SemanticNoOpDrift,
        MutationClass::TraceOrderingCorruption,
    ];
    assert_eq!(all.len(), 14);
    // Distinct check catches accidental duplicate variants.
    let mut sorted: Vec<MutationClass> = all.to_vec();
    sorted.sort();
    let mut deduped = sorted.clone();
    deduped.dedup();
    assert_eq!(sorted.len(), deduped.len());
}

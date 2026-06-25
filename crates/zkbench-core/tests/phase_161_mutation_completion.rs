//! Phase 161 — complete the remaining six mutation passes (14/14).

use zkbench_core::{
    apply_mutation_for_class, apply_mutation_pass, generate_instance, ClaimBoundary,
    ExpectedVerdict, GeneratorConfig, InstanceParams, MutationClass, MutationSafetyClass,
    NondeterministicTransitionInjectionPass, PublicPrivateBoundaryMismatchPass,
    RecursionEnvelopeMismatchPass, SemanticNoOpDriftPass, TraceOrderingCorruptionPass,
    WitnessAliasingPass,
};

fn bounded_counter_loop() -> GeneratorConfig {
    GeneratorConfig::bounded_counter_loop().loop_bound(3)
}

fn nested_loop() -> GeneratorConfig {
    GeneratorConfig::nested_loop().loop_bound(2)
}

fn guard_heavy_machine() -> GeneratorConfig {
    GeneratorConfig::guard_heavy_machine().loop_bound(2)
}

#[test]
fn nondeterministic_transition_injection_applies() {
    let instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop should generate");
    let mutated = apply_mutation_pass(&instance, &NondeterministicTransitionInjectionPass)
        .expect("nondeterministic injection should apply");
    assert_eq!(
        mutated.mutation_class,
        MutationClass::NondeterministicTransitionInjection
    );
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.safety_class, MutationSafetyClass::Malicious);
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn recursion_envelope_mismatch_applies() {
    let instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop should generate");
    let mutated = apply_mutation_pass(&instance, &RecursionEnvelopeMismatchPass)
        .expect("recursion envelope mismatch should apply");
    assert_eq!(
        mutated.mutation_class,
        MutationClass::RecursionEnvelopeMismatch
    );
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn public_private_boundary_mismatch_applies_on_public_field_family() {
    let instance = generate_instance(
        GeneratorConfig::public_private_boundary_stress(),
        InstanceParams::default(),
    )
    .expect("public/private family should generate once Phase 164 lands");
    let mutated = apply_mutation_pass(&instance, &PublicPrivateBoundaryMismatchPass)
        .expect("public/private mismatch should apply");
    assert_eq!(
        mutated.mutation_class,
        MutationClass::PublicPrivateBoundaryMismatch
    );
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn witness_aliasing_applies() {
    let instance = generate_instance(guard_heavy_machine(), InstanceParams::default())
        .expect("guard-heavy machine should generate");
    let mutated = apply_mutation_pass(&instance, &WitnessAliasingPass)
        .expect("witness aliasing should apply");
    assert_eq!(mutated.mutation_class, MutationClass::WitnessAliasing);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn semantic_no_op_drift_applies() {
    let instance = generate_instance(nested_loop(), InstanceParams::default())
        .expect("nested loop should generate");
    let mutated = apply_mutation_pass(&instance, &SemanticNoOpDriftPass)
        .expect("semantic no-op drift should apply");
    assert_eq!(mutated.mutation_class, MutationClass::SemanticNoOpDrift);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn trace_ordering_corruption_applies() {
    let instance = generate_instance(nested_loop(), InstanceParams::default())
        .expect("nested loop should generate");
    let mutated = apply_mutation_pass(&instance, &TraceOrderingCorruptionPass)
        .expect("trace ordering corruption should apply");
    assert_eq!(
        mutated.mutation_class,
        MutationClass::TraceOrderingCorruption
    );
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn apply_mutation_for_class_dispatches_all_fourteen_variants() {
    let cases = [
        (
            MutationClass::MissingConstraints,
            GeneratorConfig::branching_fsm(),
        ),
        (MutationClass::CorruptedGuards, bounded_counter_loop()),
        (MutationClass::BadCounters, bounded_counter_loop()),
        (
            MutationClass::StaleStateReads,
            GeneratorConfig::guard_heavy_machine(),
        ),
        (MutationClass::InvalidUnrollBounds, bounded_counter_loop()),
        (
            MutationClass::NondeterministicTransitionInjection,
            bounded_counter_loop(),
        ),
        (
            MutationClass::RecursionEnvelopeMismatch,
            bounded_counter_loop(),
        ),
        (
            MutationClass::PublicPrivateBoundaryMismatch,
            GeneratorConfig::public_private_boundary_stress(),
        ),
        (
            MutationClass::WitnessAliasing,
            GeneratorConfig::guard_heavy_machine(),
        ),
        (MutationClass::InvariantWeakening, bounded_counter_loop()),
        (
            MutationClass::InvariantStrengthening,
            bounded_counter_loop(),
        ),
        (
            MutationClass::ObservationOmission,
            GeneratorConfig::branching_fsm(),
        ),
        (MutationClass::SemanticNoOpDrift, nested_loop()),
        (MutationClass::TraceOrderingCorruption, nested_loop()),
    ];
    assert_eq!(cases.len(), 14);
    for (mutation_class, config) in cases {
        let instance = generate_instance(config, InstanceParams::default())
            .unwrap_or_else(|err| panic!("{mutation_class:?} fixture should generate: {err:?}"));
        let mutated = apply_mutation_for_class(&instance, mutation_class)
            .unwrap_or_else(|err| panic!("{mutation_class:?} should dispatch and apply: {err:?}"));
        assert_eq!(mutated.mutation_class, mutation_class);
        assert_eq!(mutated.claim_boundary, ClaimBoundary::Level1LocalReplay);
    }
}

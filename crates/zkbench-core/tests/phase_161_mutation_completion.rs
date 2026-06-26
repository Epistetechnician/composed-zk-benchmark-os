//! Phase 161 — complete the remaining six mutation passes (14/14).

use zkbench_core::{
    apply_mutation_for_class, apply_mutation_pass, generate_instance, value::FieldVisibility,
    ClaimBoundary, ExpectedVerdict, GeneratorConfig, InstanceParams, MutationClass, MutationPass,
    MutationSafetyClass, NondeterministicTransitionInjectionPass,
    PublicPrivateBoundaryMismatchPass, RecursionEnvelopeMismatchPass, SemanticNoOpDriftPass,
    TraceOrderingCorruptionPass, WitnessAliasingPass,
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
fn public_private_boundary_mismatch_reports_its_class() {
    assert_eq!(
        PublicPrivateBoundaryMismatchPass.mutation_class(),
        MutationClass::PublicPrivateBoundaryMismatch
    );
}

#[test]
fn public_private_boundary_mismatch_moves_public_input_policy_first() {
    let instance = generate_instance(
        GeneratorConfig::public_private_boundary_stress(),
        InstanceParams::default(),
    )
    .expect("public/private family should generate");
    let public_input = instance.surface_spec.machine.witness_policy.public_inputs[0].clone();

    let mutated = apply_mutation_pass(&instance, &PublicPrivateBoundaryMismatchPass)
        .expect("public/private mismatch should apply");

    assert!(mutated
        .provenance
        .description
        .contains("moved public input"));
    assert!(mutated
        .surface_spec
        .machine
        .witness_policy
        .private_witnesses
        .contains(&public_input));
    assert!(!mutated
        .surface_spec
        .machine
        .witness_policy
        .public_inputs
        .contains(&public_input));
    assert_eq!(mutated.provenance.affected_field_ids, vec![public_input]);
}

#[test]
fn public_private_boundary_mismatch_reclassifies_public_field_when_policy_is_empty() {
    let mut instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop should generate");
    instance
        .surface_spec
        .machine
        .witness_policy
        .public_inputs
        .clear();
    instance
        .surface_spec
        .machine
        .witness_policy
        .private_witnesses
        .clear();
    let public_field = instance
        .surface_spec
        .machine
        .fields
        .iter()
        .find(|field| field.visibility == FieldVisibility::Public)
        .expect("generated fixture should contain public field")
        .id
        .clone();

    let mutated = apply_mutation_pass(&instance, &PublicPrivateBoundaryMismatchPass)
        .expect("public field mismatch should apply");

    assert!(mutated
        .provenance
        .description
        .contains("reclassified public field"));
    assert_eq!(
        mutated.provenance.affected_field_ids,
        vec![public_field.clone()]
    );
    assert_eq!(
        mutated
            .surface_spec
            .machine
            .fields
            .iter()
            .find(|field| field.id == public_field)
            .expect("affected field should remain declared")
            .visibility,
        FieldVisibility::Private
    );
}

#[test]
fn public_private_boundary_mismatch_reclassifies_observed_field_when_fields_are_private() {
    let mut instance = generate_instance(
        GeneratorConfig::public_private_boundary_stress(),
        InstanceParams::default(),
    )
    .expect("public/private family should generate");
    instance
        .surface_spec
        .machine
        .witness_policy
        .public_inputs
        .clear();
    for field in &mut instance.surface_spec.machine.fields {
        field.visibility = FieldVisibility::Private;
    }
    let observed_field = instance.surface_spec.machine.observations[0].field.clone();

    let mutated = apply_mutation_pass(&instance, &PublicPrivateBoundaryMismatchPass)
        .expect("observed field mismatch should apply");

    assert!(mutated
        .provenance
        .description
        .contains("reclassified observed field"));
    assert_eq!(mutated.provenance.affected_field_ids, vec![observed_field]);
}

#[test]
fn public_private_boundary_mismatch_fails_without_public_or_observed_target() {
    let mut instance = generate_instance(bounded_counter_loop(), InstanceParams::default())
        .expect("bounded counter loop should generate");
    instance
        .surface_spec
        .machine
        .witness_policy
        .public_inputs
        .clear();
    instance.surface_spec.machine.observations.clear();
    for field in &mut instance.surface_spec.machine.fields {
        field.visibility = FieldVisibility::Private;
    }

    let error = apply_mutation_pass(&instance, &PublicPrivateBoundaryMismatchPass)
        .expect_err("no eligible public/private target should fail");

    assert!(error.to_string().contains("no public input"));
}

#[test]
fn public_private_boundary_mismatch_fails_without_declared_trace() {
    let mut instance = generate_instance(
        GeneratorConfig::public_private_boundary_stress(),
        InstanceParams::default(),
    )
    .expect("public/private family should generate");
    instance.accepted_traces.clear();
    instance.rejected_traces.clear();

    let error = apply_mutation_pass(&instance, &PublicPrivateBoundaryMismatchPass)
        .expect_err("no declared trace should fail before mutation");

    assert!(error.to_string().contains("no declared trace"));
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
fn trace_ordering_corruption_reports_its_class() {
    assert_eq!(
        TraceOrderingCorruptionPass.mutation_class(),
        MutationClass::TraceOrderingCorruption
    );
}

#[test]
fn trace_ordering_corruption_swaps_first_two_accepted_trace_steps() {
    let instance = generate_instance(nested_loop(), InstanceParams::default())
        .expect("nested loop should generate");
    let original_first = instance.accepted_traces[0].steps[0].transition.clone();
    let original_second = instance.accepted_traces[0].steps[1].transition.clone();

    let mutated = apply_mutation_pass(&instance, &TraceOrderingCorruptionPass)
        .expect("trace ordering corruption should apply");

    assert_eq!(mutated.primary_trace.steps[0].transition, original_second);
    assert_eq!(mutated.primary_trace.steps[1].transition, original_first);
    assert_eq!(
        mutated.provenance.affected_transition_ids,
        vec![original_second.clone(), original_first.clone()]
    );
    assert!(mutated
        .provenance
        .description
        .contains("swapped trace steps"));
    assert!(mutated
        .provenance
        .notes
        .contains(&"Trace ordering corruption mutates the primary trace only.".to_string()));
}

#[test]
fn trace_ordering_corruption_fails_without_accepted_trace() {
    let mut instance = generate_instance(nested_loop(), InstanceParams::default())
        .expect("nested loop should generate");
    instance.accepted_traces.clear();

    let error = apply_mutation_pass(&instance, &TraceOrderingCorruptionPass)
        .expect_err("missing accepted trace should fail");

    assert!(error.to_string().contains("no accepted trace"));
}

#[test]
fn trace_ordering_corruption_fails_on_single_step_trace() {
    let mut instance = generate_instance(nested_loop(), InstanceParams::default())
        .expect("nested loop should generate");
    instance.accepted_traces[0].steps.truncate(1);

    let error = apply_mutation_pass(&instance, &TraceOrderingCorruptionPass)
        .expect_err("single-step accepted trace should fail");

    assert!(error.to_string().contains("at least two steps"));
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

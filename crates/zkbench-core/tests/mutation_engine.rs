use zkbench_core::{
    apply_mutation_pass, generate_instance, BadCountersPass, CorruptedGuardsPass, ExpectedVerdict,
    GeneratorConfig, InstanceParams, MissingConstraintsPass, MutationClass, MutationEngine,
    MutationSafetyClass,
};

#[test]
fn missing_constraints_applies_to_eligible_generated_instance() {
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("branching instance should generate");
    let mutated = apply_mutation_pass(&instance, &MissingConstraintsPass)
        .expect("missing constraints should apply");
    assert_eq!(mutated.mutation_class, MutationClass::MissingConstraints);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::UnsoundIfAccepted);
    assert_eq!(mutated.safety_class, MutationSafetyClass::Malicious);
    assert!(!mutated.provenance.affected_transition_ids.is_empty());
}

#[test]
fn corrupted_guards_applies_to_eligible_generated_instance() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    let mutated = apply_mutation_pass(&instance, &CorruptedGuardsPass)
        .expect("corrupted guards should apply");
    assert_eq!(mutated.mutation_class, MutationClass::CorruptedGuards);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.safety_class, MutationSafetyClass::NearValid);
    assert!(!mutated.provenance.affected_transition_ids.is_empty());
}

#[test]
fn bad_counters_applies_to_eligible_generated_instance() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    let mutated =
        apply_mutation_pass(&instance, &BadCountersPass).expect("bad counters should apply");
    assert_eq!(mutated.mutation_class, MutationClass::BadCounters);
    assert_eq!(mutated.expected_verdict, ExpectedVerdict::Reject);
    assert_eq!(mutated.safety_class, MutationSafetyClass::Diagnostic);
    assert!(!mutated.provenance.affected_action_ids.is_empty());
}

#[test]
fn mutation_application_is_deterministic() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    let left = MutationEngine::default()
        .with_pass(CorruptedGuardsPass)
        .with_pass(BadCountersPass)
        .apply(&instance)
        .expect("mutation engine should apply");
    let right = MutationEngine::default()
        .with_pass(CorruptedGuardsPass)
        .with_pass(BadCountersPass)
        .apply(&instance)
        .expect("mutation engine should apply deterministically");
    assert_eq!(left, right);
}

#[test]
fn mutation_pass_handles_no_eligible_target_without_panic() {
    let instance = generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
        .expect("branching instance should generate");
    let error = apply_mutation_pass(&instance, &BadCountersPass)
        .expect_err("branching FSM has no integer counter action");
    assert!(error.to_string().contains("no accepted trace action"));
}

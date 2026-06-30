use zkbench_core::{
    apply_mutation_pass,
    dsl::{GuardExpr, TraceSpec, TraceStepSpec},
    generate_instance, BadCountersPass, CorruptedGuardsPass, ExpectedVerdict, GeneratorConfig,
    GuardSpec, InstanceParams, MissingConstraintsPass, MutationClass, MutationEngine, MutationPass,
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
fn missing_constraints_reports_its_class() {
    assert_eq!(
        MissingConstraintsPass.mutation_class(),
        MutationClass::MissingConstraints
    );
}

#[test]
fn missing_constraints_fails_without_rejected_trace_target() {
    let mut instance =
        generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
            .expect("branching instance should generate");
    instance.rejected_traces.clear();

    let error = apply_mutation_pass(&instance, &MissingConstraintsPass)
        .expect_err("missing rejected traces should fail");

    assert!(error
        .to_string()
        .contains("no rejected trace step with a non-trivial guard was eligible"));
}

#[test]
fn missing_constraints_skips_ineligible_rejected_traces_before_target() {
    let mut instance =
        generate_instance(GeneratorConfig::branching_fsm(), InstanceParams::default())
            .expect("branching instance should generate");
    instance.rejected_traces.insert(
        0,
        TraceSpec {
            id: "empty_rejected_trace".to_string(),
            initial_state: None,
            initial_fields: Default::default(),
            steps: Vec::new(),
            expected_final_state: None,
            expected_final_fields: Default::default(),
            expected_verdict: Some(ExpectedVerdict::Reject),
            requires_capabilities: Vec::new(),
        },
    );
    instance.rejected_traces.insert(
        1,
        TraceSpec {
            id: "unknown_transition_rejected_trace".to_string(),
            initial_state: None,
            initial_fields: Default::default(),
            steps: vec![TraceStepSpec {
                transition: "missing-transition".to_string(),
            }],
            expected_final_state: None,
            expected_final_fields: Default::default(),
            expected_verdict: Some(ExpectedVerdict::Reject),
            requires_capabilities: Vec::new(),
        },
    );

    let mutated = apply_mutation_pass(&instance, &MissingConstraintsPass)
        .expect("later rejected trace should still provide a target");

    assert_ne!(mutated.primary_trace.id, "empty_rejected_trace");
    assert_ne!(
        mutated.primary_trace.id,
        "unknown_transition_rejected_trace"
    );
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
fn corrupted_guards_reports_its_class() {
    assert_eq!(
        CorruptedGuardsPass.mutation_class(),
        MutationClass::CorruptedGuards
    );
}

#[test]
fn corrupted_guards_records_guard_provenance() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");

    let mutated = apply_mutation_pass(&instance, &CorruptedGuardsPass)
        .expect("corrupted guards should apply");
    let transition_id = mutated.provenance.affected_transition_ids[0].clone();
    let original_transition = instance
        .surface_spec
        .machine
        .transitions
        .iter()
        .find(|transition| transition.id == transition_id)
        .expect("original transition should exist");
    let mutated_transition = mutated
        .surface_spec
        .machine
        .transitions
        .iter()
        .find(|transition| transition.id == transition_id)
        .expect("mutated transition should exist");

    assert_ne!(mutated_transition.guard, original_transition.guard);
    assert_eq!(
        mutated.provenance.affected_guard_ids,
        vec![format!("{transition_id}.guard")]
    );
    assert!(mutated.provenance.affected_action_ids.is_empty());
    assert!(mutated.provenance.affected_field_ids.is_empty());
    assert!(mutated.provenance.description.contains("corrupted guard"));
    assert!(mutated
        .provenance
        .notes
        .iter()
        .any(|note| note.contains("before guard")));
    assert!(mutated
        .provenance
        .notes
        .iter()
        .any(|note| note.contains("after guard")));
}

#[test]
fn corrupted_guards_fails_without_accepted_trace() {
    let mut instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    instance.accepted_traces.clear();

    let error = apply_mutation_pass(&instance, &CorruptedGuardsPass)
        .expect_err("missing accepted traces should fail");

    assert!(error
        .to_string()
        .contains("no accepted trace step with an executable guard"));
}

#[test]
fn corrupted_guards_skips_missing_trace_step_transition() {
    let mut instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    instance.accepted_traces.insert(
        0,
        TraceSpec {
            id: "unknown_transition_trace".to_string(),
            initial_state: None,
            initial_fields: Default::default(),
            steps: vec![TraceStepSpec {
                transition: "missing-transition".to_string(),
            }],
            expected_final_state: None,
            expected_final_fields: Default::default(),
            expected_verdict: Some(ExpectedVerdict::Accept),
            requires_capabilities: Vec::new(),
        },
    );

    let mutated = apply_mutation_pass(&instance, &CorruptedGuardsPass)
        .expect("later accepted trace should still provide a target");

    assert_ne!(mutated.primary_trace.id, "unknown_transition_trace");
    assert!(!mutated.provenance.affected_transition_ids.is_empty());
}

#[test]
fn corrupted_guards_fails_when_guards_are_not_corruptible() {
    let mut instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    for transition in &mut instance.surface_spec.machine.transitions {
        transition.guard = GuardSpec::Expr(GuardExpr::RawText {
            raw_text: "operator-only predicate".to_string(),
        });
    }

    let error = apply_mutation_pass(&instance, &CorruptedGuardsPass)
        .expect_err("raw-text guards should not be treated as executable targets");

    assert!(error
        .to_string()
        .contains("no accepted trace step with an executable guard"));
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

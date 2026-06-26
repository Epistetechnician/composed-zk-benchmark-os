use zkbench_core::{
    apply_default_mutations, apply_mutation_pass,
    dsl::{ActionSpec, OperandSpec},
    evaluate_mutated_instance, generate_instance, BadCountersPass, GeneratorConfig, InstanceParams,
    MutationClass, OracleOutcome,
};

fn bounded_counter_instance() -> zkbench_core::generator::GeneratedBenchmarkInstance {
    generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded counter instance should generate")
}

fn rewrite_counter_actions(
    instance: &mut zkbench_core::generator::GeneratedBenchmarkInstance,
    rewrite: impl Fn(&mut ActionSpec),
) {
    for transition in &mut instance.surface_spec.machine.transitions {
        for action in &mut transition.actions {
            rewrite(action);
        }
    }
}

#[test]
fn apply_default_mutations_runs_the_phase_d_e_bundle() {
    let instance = bounded_counter_instance();

    let mutations = apply_default_mutations(&instance)
        .expect("default mutation bundle should apply to bounded counter fixture");

    let classes = mutations
        .iter()
        .map(|mutation| mutation.mutation_class)
        .collect::<Vec<_>>();
    assert_eq!(
        classes,
        vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
            MutationClass::BadCounters,
        ]
    );
    assert!(mutations
        .iter()
        .all(|mutation| mutation.source_instance_id == instance.id));
}

#[test]
fn evaluate_mutated_instance_reports_primary_trace_outcome() {
    let instance = bounded_counter_instance();
    let mutation = apply_mutation_pass(&instance, &BadCountersPass)
        .expect("bad counter mutation should apply");

    let outcomes = evaluate_mutated_instance(&mutation)
        .expect("mutated primary trace should evaluate locally");

    assert_eq!(outcomes.len(), 1);
    assert!(matches!(outcomes[0], OracleOutcome::Rejected { .. }));
}

#[test]
fn bad_counter_action_handles_add_assign_integer_other_than_one() {
    let mut instance = bounded_counter_instance();
    rewrite_counter_actions(&mut instance, |action| {
        if let ActionSpec::AddAssign { add_assign } = action {
            let mut changed = add_assign.clone();
            changed.value = OperandSpec::Literal(zkbench_core::value::Value::Int { int: 5 });
            *action = ActionSpec::AddAssign {
                add_assign: changed,
            };
        }
    });

    let mutation = apply_mutation_pass(&instance, &BadCountersPass)
        .expect("bad counter mutation should handle non-default add_assign integer");

    assert!(mutation
        .provenance
        .notes
        .iter()
        .any(|note| note.contains("incremented add_assign integer operand from 5")));
}

#[test]
fn bad_counter_action_handles_sub_assign_integer_updates() {
    let mut instance = bounded_counter_instance();
    rewrite_counter_actions(&mut instance, |action| {
        if let ActionSpec::AddAssign { add_assign } = action {
            *action = ActionSpec::SubAssign {
                sub_assign: add_assign.clone(),
            };
        }
    });

    let mutation = apply_mutation_pass(&instance, &BadCountersPass)
        .expect("bad counter mutation should handle sub_assign integer updates");

    assert!(mutation
        .provenance
        .notes
        .iter()
        .any(|note| note.contains("incremented sub_assign integer operand")));
    assert!(!mutation.provenance.affected_field_ids.is_empty());
}

use zkbench_core::{
    apply_mutation_pass, classify_result, evaluate_trace, BackendOutcome, BadCountersPass,
    CorruptedGuardsPass, ExpectedVerdict, GeneratorConfig, InstanceParams, MissingConstraintsPass,
    OracleOutcome, ResultClassification,
};

#[test]
fn missing_constraints_turns_false_branch_guard_into_local_acceptance() {
    let instance = zkbench_core::generate_instance(
        GeneratorConfig::branching_fsm().seed(1),
        InstanceParams::default(),
    )
    .expect("branching instance should generate");
    let original_trace = &instance.rejected_traces[0];
    let original = evaluate_trace(&instance.semantic_ir, original_trace)
        .expect("original rejected trace should evaluate");
    assert!(matches!(original, OracleOutcome::Rejected { .. }));

    let mutated = apply_mutation_pass(&instance, &MissingConstraintsPass)
        .expect("missing constraints should apply");
    let mutated_outcome = evaluate_trace(&mutated.semantic_ir, &mutated.primary_trace)
        .expect("mutated trace should evaluate");
    assert_eq!(mutated_outcome, OracleOutcome::Accepted);
    assert_eq!(
        classify_result(ExpectedVerdict::Reject, BackendOutcome::Accepted),
        ResultClassification::ExpectedRejectAcceptedUnsoundCandidate
    );
}

#[test]
fn corrupted_guards_changes_a_trace_outcome() {
    let instance = zkbench_core::generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    let trace = &instance.accepted_traces[0];
    let original =
        evaluate_trace(&instance.semantic_ir, trace).expect("original trace should evaluate");
    let mutated = apply_mutation_pass(&instance, &CorruptedGuardsPass)
        .expect("corrupted guards should apply");
    let changed = evaluate_trace(&mutated.semantic_ir, &mutated.primary_trace)
        .expect("mutated trace should evaluate");
    assert_ne!(original, changed);
    assert!(matches!(changed, OracleOutcome::Rejected { .. }));
}

#[test]
fn bad_counters_rejects_original_accepted_bounded_trace() {
    let instance = zkbench_core::generate_instance(
        GeneratorConfig::bounded_counter_loop().loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    let trace = &instance.accepted_traces[0];
    assert_eq!(
        evaluate_trace(&instance.semantic_ir, trace).expect("original trace should evaluate"),
        OracleOutcome::Accepted
    );

    let mutated =
        apply_mutation_pass(&instance, &BadCountersPass).expect("bad counters should apply");
    let changed = evaluate_trace(&mutated.semantic_ir, &mutated.primary_trace)
        .expect("mutated trace should evaluate");
    assert!(
        matches!(changed, OracleOutcome::Rejected { .. }),
        "bad counter mutation should cause semantic rejection, not backend failure"
    );
    assert_eq!(
        classify_result(ExpectedVerdict::Accept, BackendOutcome::Rejected),
        ResultClassification::ExpectedAcceptRejected
    );
}

#[test]
fn timeout_and_capability_gap_classification_remain_non_failures() {
    assert_eq!(
        classify_result(ExpectedVerdict::Reject, BackendOutcome::Timeout),
        ResultClassification::Timeout
    );
    assert_eq!(
        classify_result(ExpectedVerdict::Reject, BackendOutcome::CapabilityGap),
        ResultClassification::CapabilityGap
    );
}

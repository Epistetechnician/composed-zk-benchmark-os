use zkbench_core::{evaluate_trace, lower_to_ir, parse_yaml_ast, OracleOutcome};

fn ir_from_fixture(yaml: &str) -> zkbench_core::Result<zkbench_core::SemanticIr> {
    lower_to_ir(parse_yaml_ast(yaml)?)
}

#[test]
fn baseline_accepted_trace_is_accepted() {
    let ir = ir_from_fixture(include_str!("fixtures/baseline_fsm.yaml"))
        .expect("baseline fixture should lower");
    let trace = &ir.oracle.accepted_traces[0];
    let outcome = evaluate_trace(&ir, trace).expect("oracle should evaluate baseline trace");
    assert_eq!(outcome, OracleOutcome::Accepted);
}

#[test]
fn baseline_rejected_trace_is_rejected() {
    let ir = ir_from_fixture(include_str!("fixtures/baseline_fsm.yaml"))
        .expect("baseline fixture should lower");
    let trace = &ir.oracle.rejected_traces[0];
    let outcome = evaluate_trace(&ir, trace).expect("oracle should evaluate rejected trace");
    assert!(matches!(outcome, OracleOutcome::Rejected { .. }));
}

#[test]
fn bounded_counter_accepted_trace_is_accepted() {
    let ir = ir_from_fixture(include_str!("fixtures/bounded_counter_loop.yaml"))
        .expect("bounded counter fixture should lower");
    let trace = &ir.oracle.accepted_traces[0];
    let outcome = evaluate_trace(&ir, trace).expect("oracle should evaluate bounded trace");
    assert_eq!(outcome, OracleOutcome::Accepted);
}

#[test]
fn bounded_counter_invalid_trace_is_rejected() {
    let ir = ir_from_fixture(include_str!("fixtures/bounded_counter_loop.yaml"))
        .expect("bounded counter fixture should lower");
    let trace = &ir.oracle.rejected_traces[0];
    let outcome = evaluate_trace(&ir, trace).expect("oracle should evaluate invalid trace");
    assert!(matches!(outcome, OracleOutcome::Rejected { .. }));
}

#[test]
fn recursive_metadata_trace_is_not_fake_success() {
    let ir = ir_from_fixture(include_str!("fixtures/recursive_loop_envelope.yaml"))
        .expect("recursive fixture should lower");
    let trace = &ir.oracle.accepted_traces[0];
    let outcome = evaluate_trace(&ir, trace).expect("oracle should evaluate recursive trace");
    assert!(
        matches!(
            outcome,
            OracleOutcome::CapabilityGap { .. } | OracleOutcome::Inconclusive { .. }
        ),
        "recursion metadata must not be accepted as fake proof evidence"
    );
}

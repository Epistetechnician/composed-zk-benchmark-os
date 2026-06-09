use zkbench_core::{
    evaluate_trace, generate_family, parse_yaml_ast, ClaimBoundary, GeneratorConfig, OracleOutcome,
};

fn assert_generated_family_is_locally_valid(config: GeneratorConfig) {
    let family = generate_family(config).expect("family generation should succeed");
    assert!(family.claim_boundary <= ClaimBoundary::Level1LocalReplay);
    assert!(!family.semantic_ir.oracle.accepted_traces.is_empty());
    assert!(!family.semantic_ir.oracle.rejected_traces.is_empty());

    for trace in &family.semantic_ir.oracle.accepted_traces {
        let outcome = evaluate_trace(&family.semantic_ir, trace)
            .expect("accepted trace should evaluate locally");
        assert_eq!(outcome, OracleOutcome::Accepted);
    }

    for trace in &family.semantic_ir.oracle.rejected_traces {
        let outcome = evaluate_trace(&family.semantic_ir, trace)
            .expect("rejected trace should evaluate locally");
        assert!(matches!(outcome, OracleOutcome::Rejected { .. }));
    }
}

#[test]
fn generated_baseline_validates_lowers_and_evaluates() {
    assert_generated_family_is_locally_valid(
        GeneratorConfig::baseline_fsm()
            .state_count(4)
            .trace_length(3),
    );
}

#[test]
fn generated_branching_validates_lowers_and_evaluates() {
    assert_generated_family_is_locally_valid(GeneratorConfig::branching_fsm().seed(5));
}

#[test]
fn generated_bounded_counter_validates_lowers_and_evaluates() {
    assert_generated_family_is_locally_valid(GeneratorConfig::bounded_counter_loop().loop_bound(3));
}

#[test]
fn generated_fixture_examples_parse() {
    for yaml in [
        include_str!("fixtures/generated_baseline_family.yaml"),
        include_str!("fixtures/generated_bounded_counter_family.yaml"),
    ] {
        let ast = parse_yaml_ast(yaml).expect("generated fixture example should parse");
        assert!(ast.spec.evidence.claim_boundary <= ClaimBoundary::Level1LocalReplay);
    }
}

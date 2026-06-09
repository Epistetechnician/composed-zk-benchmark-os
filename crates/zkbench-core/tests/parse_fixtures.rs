use zkbench_core::{parse_yaml_ast, ClaimBoundary};

const FIXTURES: [(&str, &str); 8] = [
    ("baseline_fsm", include_str!("fixtures/baseline_fsm.yaml")),
    (
        "bounded_counter_loop",
        include_str!("fixtures/bounded_counter_loop.yaml"),
    ),
    (
        "recursive_loop_envelope",
        include_str!("fixtures/recursive_loop_envelope.yaml"),
    ),
    (
        "adversarial_stale_read_machine",
        include_str!("fixtures/adversarial_stale_read_machine.yaml"),
    ),
    (
        "zkml_control_flow_mixed",
        include_str!("fixtures/zkml_control_flow_mixed.yaml"),
    ),
    (
        "public_private_boundary_mismatch",
        include_str!("fixtures/public_private_boundary_mismatch.yaml"),
    ),
    (
        "generated_baseline_family",
        include_str!("fixtures/generated_baseline_family.yaml"),
    ),
    (
        "generated_bounded_counter_family",
        include_str!("fixtures/generated_bounded_counter_family.yaml"),
    ),
];

#[test]
fn every_fixture_parses_and_stays_claim_capped() {
    for (name, yaml) in FIXTURES {
        let ast = parse_yaml_ast(yaml).unwrap_or_else(|error| {
            panic!("fixture {name} should parse and validate: {error}");
        });
        assert!(
            !ast.spec.machine.id.is_empty(),
            "fixture {name} should declare a machine id"
        );
        assert!(
            ast.spec.evidence.claim_boundary <= ClaimBoundary::Level1LocalReplay,
            "fixture {name} must not overclaim evidence"
        );
        assert!(
            ast.spec
                .targets
                .iter()
                .any(|target| target.id == "local_oracle"),
            "fixture {name} should include a local_oracle target"
        );
    }
}

use zkbench_core::{lower_to_ir, parse_yaml_ast};

fn expect_parse_error(yaml: &str, needle: &str) {
    let error = parse_yaml_ast(yaml).expect_err("fixture should be rejected");
    assert!(
        error.to_string().contains(needle),
        "expected error to contain {needle:?}, got {error}"
    );
}

#[test]
fn baseline_fixture_lowers_to_semantic_ir() {
    let ast = parse_yaml_ast(include_str!("fixtures/baseline_fsm.yaml"))
        .expect("baseline fixture should parse");
    let ir = lower_to_ir(ast).expect("baseline fixture should lower");
    assert_eq!(ir.machine.id, "baseline_fsm");
    assert_eq!(ir.machine.initial_state, "start");
    assert_eq!(ir.machine.transitions.len(), 1);
}

#[test]
fn bounded_counter_fixture_lowers_to_semantic_ir() {
    let ast = parse_yaml_ast(include_str!("fixtures/bounded_counter_loop.yaml"))
        .expect("bounded counter fixture should parse");
    let ir = lower_to_ir(ast).expect("bounded counter fixture should lower");
    assert_eq!(ir.machine.id, "bounded_counter_loop");
    assert_eq!(ir.machine.loops.len(), 1);
    assert_eq!(ir.machine.invariants.len(), 1);
}

#[test]
fn semantic_ir_field_lookup_returns_present_and_missing_fields() {
    let ast = parse_yaml_ast(include_str!("fixtures/baseline_fsm.yaml"))
        .expect("baseline fixture should parse");
    let ir = lower_to_ir(ast).expect("baseline fixture should lower");

    assert_eq!(
        ir.field("counter").expect("counter field should exist").id,
        "counter"
    );
    assert!(ir.field("missing").is_none());
}

#[test]
fn duplicate_state_ids_are_rejected() {
    let yaml = r#"
machine:
  id: duplicate_states
  initial_state: s
  states:
    - id: s
    - id: s
  fields: []
  transitions: []
evidence:
  claim_boundary: Level1LocalReplay
"#;
    let error = parse_yaml_ast(yaml).expect_err("duplicate state ids should be rejected");
    assert!(error.to_string().contains("duplicate id"));
}

#[test]
fn unknown_transition_state_is_rejected() {
    let yaml = r#"
machine:
  id: unknown_state
  initial_state: s
  states:
    - id: s
  fields:
    - id: flag
      type: bool
      initial:
        bool: true
      visibility: public
  transitions:
    - id: bad
      from: s
      to: missing
      guard: true
      actions: []
evidence:
  claim_boundary: Level1LocalReplay
"#;
    let error = parse_yaml_ast(yaml).expect_err("unknown transition state should be rejected");
    assert!(error.to_string().contains("target state"));
}

#[test]
fn unknown_field_reference_is_rejected() {
    let yaml = r#"
machine:
  id: unknown_field
  initial_state: s
  states:
    - id: s
  fields:
    - id: counter
      type: int
      initial:
        int: 0
      visibility: public
  transitions:
    - id: bad
      from: s
      to: s
      guard:
        eq:
          left:
            field: missing
          right:
            int: 0
      actions: []
evidence:
  claim_boundary: Level1LocalReplay
"#;
    let error = parse_yaml_ast(yaml).expect_err("unknown field reference should be rejected");
    assert!(error.to_string().contains("unknown field"));
}

#[test]
fn validation_rejects_missing_ids_states_and_type_mismatches() {
    expect_parse_error(
        r#"
machine:
  id: ""
  initial_state: s
  states:
    - id: s
evidence:
  claim_boundary: Level1LocalReplay
"#,
        "machine id is empty",
    );
    expect_parse_error(
        r#"
machine:
  id: missing_initial
  initial_state: missing
  states:
    - id: s
evidence:
  claim_boundary: Level1LocalReplay
"#,
        "initial state",
    );
    expect_parse_error(
        r#"
machine:
  id: type_mismatch
  initial_state: s
  states:
    - id: s
  fields:
    - id: counter
      type: int
      initial:
        bool: true
evidence:
  claim_boundary: Level1LocalReplay
"#,
        "initial value does not match",
    );
}

#[test]
fn validation_rejects_unknown_transition_action_invariant_and_io_fields() {
    expect_parse_error(
        r#"
machine:
  id: unknown_source
  initial_state: s
  states:
    - id: s
  transitions:
    - id: bad
      from: missing
      to: s
evidence:
  claim_boundary: Level1LocalReplay
"#,
        "source state",
    );
    expect_parse_error(
        r#"
machine:
  id: unknown_action_field
  initial_state: s
  states:
    - id: s
  fields:
    - id: counter
      type: int
      initial:
        int: 0
  transitions:
    - id: bad
      from: s
      to: s
      actions:
        - add_assign:
            field: missing
            value:
              field: counter
evidence:
  claim_boundary: Level1LocalReplay
"#,
        "action references unknown field",
    );
    expect_parse_error(
        r#"
machine:
  id: unknown_invariant_field
  initial_state: s
  states:
    - id: s
  fields:
    - id: counter
      type: int
      initial:
        int: 0
  invariants:
    - id: invariant
      guard:
        eq:
          left:
            field: missing
          right:
            int: 0
evidence:
  claim_boundary: Level1LocalReplay
"#,
        "guard references unknown field",
    );
    for (field_block, needle) in [
        (
            r#"
  observations:
    - id: obs
      field: missing
"#,
            "observed field",
        ),
        (
            r#"
  public_inputs:
    - id: public
      field: missing
"#,
            "public input field",
        ),
        (
            r#"
  private_witnesses:
    - id: private
      field: missing
"#,
            "private witness field",
        ),
        (
            r#"
  witness_policy:
    public_inputs:
      - missing
"#,
            "public input field",
        ),
        (
            r#"
  witness_policy:
    private_witnesses:
      - missing
"#,
            "private witness field",
        ),
    ] {
        expect_parse_error(
            &format!(
                r#"
machine:
  id: unknown_io_field
  initial_state: s
  states:
    - id: s
  fields:
    - id: counter
      type: int
      initial:
        int: 0
{field_block}
evidence:
  claim_boundary: Level1LocalReplay
"#
            ),
            needle,
        );
    }
}

#[test]
fn validation_rejects_invalid_trace_references_and_duplicate_top_level_ids() {
    for (trace_block, needle) in [
        (
            r#"
  accepted_traces:
    - id: ""
"#,
            "trace id is empty",
        ),
        (
            r#"
  accepted_traces:
    - id: bad_initial
      initial_state: missing
"#,
            "initial state",
        ),
        (
            r#"
  accepted_traces:
    - id: bad_final
      expected_final_state: missing
"#,
            "expected final state",
        ),
        (
            r#"
  accepted_traces:
    - id: bad_initial_field
      initial_fields:
        missing:
          int: 0
"#,
            "initial field",
        ),
        (
            r#"
  accepted_traces:
    - id: bad_expected_field
      expected_final_fields:
        missing:
          int: 0
"#,
            "expected field",
        ),
        (
            r#"
  accepted_traces:
    - id: bad_step
      steps:
        - transition: missing
"#,
            "transition",
        ),
    ] {
        expect_parse_error(
            &format!(
                r#"
machine:
  id: trace_validation
  initial_state: s
  states:
    - id: s
  fields:
    - id: counter
      type: int
      initial:
        int: 0
oracle:
{trace_block}
evidence:
  claim_boundary: Level1LocalReplay
"#
            ),
            needle,
        );
    }

    expect_parse_error(
        r#"
machine:
  id: duplicate_transitions
  initial_state: s
  states:
    - id: s
  transitions:
    - id: repeat
      from: s
      to: s
    - id: repeat
      from: s
      to: s
evidence:
  claim_boundary: Level1LocalReplay
"#,
        "duplicate id",
    );
    expect_parse_error(
        r#"
machine:
  id: duplicate_targets
  initial_state: s
  states:
    - id: s
targets:
  - id: target
    kind: local
  - id: target
    kind: local
evidence:
  claim_boundary: Level1LocalReplay
"#,
        "duplicate id",
    );
}

#[test]
fn validation_rejects_actual_level2_claim_boundary_but_allows_planned_metadata() {
    let actual_level2 = r#"
machine:
  id: actual_level2
  initial_state: s
  states:
    - id: s
evidence:
  claim_boundary: Level2ReproducibleBenchmarkArtifact
"#;
    expect_parse_error(actual_level2, "exceeds Level1LocalReplay");

    let planned_level2 = r#"
machine:
  id: planned_level2
  initial_state: s
  states:
    - id: s
evidence:
  claim_boundary: Level2ReproducibleBenchmarkArtifact
  planned: true
"#;
    let ast = parse_yaml_ast(planned_level2).expect("planned metadata may exceed local boundary");
    let ir = lower_to_ir(ast).expect("planned metadata should lower");
    assert!(ir.evidence.planned);
}

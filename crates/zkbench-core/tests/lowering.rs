use zkbench_core::{lower_to_ir, parse_yaml_ast};

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

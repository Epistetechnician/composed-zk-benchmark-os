use std::collections::BTreeMap;

use zkbench_core::dsl::{ActionSpec, AssignAction, BinaryGuard, GuardExpr, GuardSpec, OperandSpec};
use zkbench_core::value::Value;
use zkbench_core::{
    evaluate_trace, lower_to_ir, parse_yaml_ast, OracleOutcome, TraceSpec, TraceStepSpec,
};

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

#[test]
fn oracle_evaluates_boolean_combinators_text_values_and_assignment_actions() {
    let ir = ir_from_fixture(
        r#"
machine:
  id: combinator_machine
  initial_state: start
  states:
    - id: start
    - id: mid
    - id: done
  fields:
    - id: counter
      type: int
      initial:
        int: 5
    - id: flag
      type: bool
      initial:
        bool: false
    - id: label
      type: text
      initial:
        text: old
  transitions:
    - id: prepare
      from: start
      to: mid
      guard:
        and:
          - true
          - not: false
          - gt:
              left:
                field: counter
              right:
                int: 4
          - or:
              - false
              - eq:
                  left:
                    field: label
                  right:
                    text: old
      actions:
        - noop: true
        - assign:
            field: flag
            value:
              bool: true
        - assign:
            field: label
            value:
              text: done
        - sub_assign:
            field: counter
            value:
              int: 2
    - id: finish
      from: mid
      to: done
      guard:
        and:
          - neq:
              left:
                field: flag
              right:
                bool: false
          - gte:
              left:
                field: counter
              right:
                int: 3
          - lte:
              left:
                field: counter
              right:
                int: 3
      actions: []
oracle:
  accepted_traces:
    - id: combinators_accept
      steps:
        - transition: prepare
        - transition: finish
      expected_final_state: done
      expected_final_fields:
        counter:
          int: 3
        flag:
          bool: true
        label:
          text: done
evidence:
  claim_boundary: Level1LocalReplay
"#,
    )
    .expect("combinator fixture should lower");

    let trace = &ir.oracle.accepted_traces[0];
    let outcome = evaluate_trace(&ir, trace).expect("oracle should evaluate combinator trace");
    assert_eq!(outcome, OracleOutcome::Accepted);
}

#[test]
fn oracle_reports_capability_gaps_for_raw_guards_and_actions() {
    let raw_guard_ir = ir_from_fixture(
        r#"
machine:
  id: raw_guard_machine
  initial_state: start
  states:
    - id: start
    - id: done
  fields:
    - id: counter
      type: int
      initial:
        int: 0
  transitions:
    - id: raw_guard
      from: start
      to: done
      guard:
        or:
          - false
          - raw_text: requires external transcript semantics
oracle:
  accepted_traces:
    - id: raw_guard_gap
      steps:
        - transition: raw_guard
evidence:
  claim_boundary: Level1LocalReplay
"#,
    )
    .expect("raw guard fixture should lower");
    let raw_guard_outcome = evaluate_trace(&raw_guard_ir, &raw_guard_ir.oracle.accepted_traces[0])
        .expect("oracle should evaluate raw guard trace");
    assert!(matches!(
        raw_guard_outcome,
        OracleOutcome::CapabilityGap { reason } if reason.contains("raw text")
    ));

    let raw_action_ir = ir_from_fixture(
        r#"
machine:
  id: raw_action_machine
  initial_state: start
  states:
    - id: start
    - id: done
  fields:
    - id: counter
      type: int
      initial:
        int: 0
  transitions:
    - id: raw_action
      from: start
      to: done
      guard: true
      actions:
        - raw_text: mutate external prover state
oracle:
  accepted_traces:
    - id: raw_action_gap
      steps:
        - transition: raw_action
evidence:
  claim_boundary: Level1LocalReplay
"#,
    )
    .expect("raw action fixture should lower");
    let raw_action_outcome =
        evaluate_trace(&raw_action_ir, &raw_action_ir.oracle.accepted_traces[0])
            .expect("oracle should evaluate raw action trace");
    assert!(matches!(
        raw_action_outcome,
        OracleOutcome::CapabilityGap { reason } if reason.contains("raw text")
    ));
}

#[test]
fn oracle_rejects_trace_shape_drift_and_final_expectation_mismatches() {
    let ir = ir_from_fixture(include_str!("fixtures/baseline_fsm.yaml"))
        .expect("baseline fixture should lower");
    let trace = &ir.oracle.accepted_traces[0];

    let mut bad_initial = trace.clone();
    bad_initial.initial_state = Some("ghost".to_string());
    let bad_initial_outcome =
        evaluate_trace(&ir, &bad_initial).expect("oracle should evaluate bad initial state");
    assert!(matches!(
        bad_initial_outcome,
        OracleOutcome::Rejected { reason } if reason.contains("initial state")
    ));

    let mut unknown_transition = trace.clone();
    unknown_transition.steps = vec![TraceStepSpec {
        transition: "ghost_transition".to_string(),
    }];
    let unknown_transition_outcome = evaluate_trace(&ir, &unknown_transition)
        .expect("oracle should evaluate unknown transition");
    assert!(matches!(
        unknown_transition_outcome,
        OracleOutcome::Rejected { reason } if reason.contains("not declared")
    ));

    let mut wrong_start = trace.clone();
    wrong_start.steps.push(TraceStepSpec {
        transition: "advance".to_string(),
    });
    let wrong_start_outcome =
        evaluate_trace(&ir, &wrong_start).expect("oracle should evaluate wrong start state");
    assert!(matches!(
        wrong_start_outcome,
        OracleOutcome::Rejected { reason } if reason.contains("current state")
    ));

    let mut wrong_final_state = trace.clone();
    wrong_final_state.expected_final_state = Some("start".to_string());
    let wrong_final_state_outcome =
        evaluate_trace(&ir, &wrong_final_state).expect("oracle should evaluate wrong final state");
    assert!(matches!(
        wrong_final_state_outcome,
        OracleOutcome::Rejected { reason } if reason.contains("expected final state")
    ));

    let mut wrong_final_field = trace.clone();
    wrong_final_field
        .expected_final_fields
        .insert("counter".to_string(), Value::Int { int: 99 });
    let wrong_final_field_outcome =
        evaluate_trace(&ir, &wrong_final_field).expect("oracle should evaluate wrong final field");
    assert!(matches!(
        wrong_final_field_outcome,
        OracleOutcome::Rejected { reason } if reason.contains("expected final field")
    ));
}

#[test]
fn oracle_rejects_arithmetic_type_errors_and_overflow() {
    for (yaml, expected_reason) in [
        (
            r#"
machine:
  id: non_integer_field_machine
  initial_state: start
  states:
    - id: start
    - id: done
  fields:
    - id: flag
      type: bool
      initial:
        bool: true
  transitions:
    - id: add_to_bool
      from: start
      to: done
      actions:
        - add_assign:
            field: flag
            value:
              int: 1
oracle:
  accepted_traces:
    - id: add_to_bool_rejects
      steps:
        - transition: add_to_bool
evidence:
  claim_boundary: Level1LocalReplay
"#,
            "not an integer",
        ),
        (
            r#"
machine:
  id: non_integer_operand_machine
  initial_state: start
  states:
    - id: start
    - id: done
  fields:
    - id: counter
      type: int
      initial:
        int: 1
  transitions:
    - id: add_bool
      from: start
      to: done
      actions:
        - add_assign:
            field: counter
            value:
              bool: true
oracle:
  accepted_traces:
    - id: add_bool_rejects
      steps:
        - transition: add_bool
evidence:
  claim_boundary: Level1LocalReplay
"#,
            "operand is not an integer",
        ),
        (
            r#"
machine:
  id: overflow_machine
  initial_state: start
  states:
    - id: start
    - id: done
  fields:
    - id: counter
      type: int
      initial:
        int: 9223372036854775807
  transitions:
    - id: overflow
      from: start
      to: done
      actions:
        - add_assign:
            field: counter
            value:
              int: 1
oracle:
  accepted_traces:
    - id: overflow_rejects
      steps:
        - transition: overflow
evidence:
  claim_boundary: Level1LocalReplay
"#,
            "overflow",
        ),
    ] {
        let ir = ir_from_fixture(yaml).expect("arithmetic fixture should lower");
        let outcome = evaluate_trace(&ir, &ir.oracle.accepted_traces[0])
            .expect("oracle should evaluate arithmetic error trace");
        assert!(matches!(
            outcome,
            OracleOutcome::Rejected { reason } if reason.contains(expected_reason)
        ));
    }
}

#[test]
fn oracle_errors_when_required_initial_field_is_missing() {
    let ir = ir_from_fixture(
        r#"
machine:
  id: missing_initial_machine
  initial_state: start
  states:
    - id: start
  fields:
    - id: counter
      type: int
oracle:
  accepted_traces:
    - id: empty_trace
evidence:
  claim_boundary: Level1LocalReplay
"#,
    )
    .expect("missing initial fixture should lower");
    let err = evaluate_trace(&ir, &ir.oracle.accepted_traces[0])
        .expect_err("missing initial field should error before evaluation");
    assert!(err.to_string().contains("no initial value"));
}

#[test]
fn oracle_rejects_missing_expected_final_field_after_manual_trace_override() {
    let ir = ir_from_fixture(include_str!("fixtures/baseline_fsm.yaml"))
        .expect("baseline fixture should lower");
    let trace = TraceSpec {
        id: "missing_final_field".to_string(),
        initial_state: None,
        initial_fields: BTreeMap::new(),
        steps: Vec::new(),
        expected_final_state: Some("start".to_string()),
        expected_final_fields: BTreeMap::from([(
            "ghost_counter".to_string(),
            Value::Int { int: 0 },
        )]),
        expected_verdict: None,
        requires_capabilities: Vec::new(),
    };
    let outcome =
        evaluate_trace(&ir, &trace).expect("oracle should evaluate missing expected field");
    assert!(matches!(
        outcome,
        OracleOutcome::Rejected { reason } if reason.contains("is missing")
    ));
}

#[test]
fn expression_helpers_collect_references_and_detect_raw_text() {
    let guard = GuardSpec::Expr(GuardExpr::And {
        and: vec![
            GuardSpec::Expr(GuardExpr::Eq {
                eq: BinaryGuard {
                    left: OperandSpec::Field {
                        field: "left_counter".to_string(),
                    },
                    right: OperandSpec::Literal(Value::Int { int: 1 }),
                },
            }),
            GuardSpec::Expr(GuardExpr::Or {
                or: vec![
                    GuardSpec::Expr(GuardExpr::Not {
                        not: Box::new(GuardSpec::Bool(false)),
                    }),
                    GuardSpec::Expr(GuardExpr::RawText {
                        raw_text: "requires backend transcript".to_string(),
                    }),
                ],
            }),
            GuardSpec::Expr(GuardExpr::Gte {
                gte: BinaryGuard {
                    left: OperandSpec::Field {
                        field: "lower_bound".to_string(),
                    },
                    right: OperandSpec::Field {
                        field: "right_bound".to_string(),
                    },
                },
            }),
        ],
    });

    let mut refs = std::collections::BTreeSet::new();
    guard.collect_field_references(&mut refs);
    assert_eq!(
        refs.into_iter().collect::<Vec<_>>(),
        vec!["left_counter", "lower_bound", "right_bound"]
    );
    assert!(guard.contains_raw_text());
    assert!(!GuardSpec::Bool(true).contains_raw_text());

    let actions = [
        ActionSpec::Noop { noop: true },
        ActionSpec::Assign {
            assign: AssignAction {
                field: "assigned".to_string(),
                value: OperandSpec::Field {
                    field: "source".to_string(),
                },
            },
        },
        ActionSpec::AddAssign {
            add_assign: AssignAction {
                field: "added".to_string(),
                value: OperandSpec::Literal(Value::Int { int: 1 }),
            },
        },
        ActionSpec::SubAssign {
            sub_assign: AssignAction {
                field: "subtracted".to_string(),
                value: OperandSpec::Field {
                    field: "delta".to_string(),
                },
            },
        },
        ActionSpec::RawText {
            raw_text: "external update".to_string(),
        },
    ];
    let mut action_refs = std::collections::BTreeSet::new();
    for action in &actions {
        action.collect_field_references(&mut action_refs);
    }
    assert_eq!(
        action_refs.into_iter().collect::<Vec<_>>(),
        vec!["added", "assigned", "delta", "source", "subtracted"]
    );
    assert!(!actions[0].contains_raw_text());
    assert!(actions[4].contains_raw_text());
}

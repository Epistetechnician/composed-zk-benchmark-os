//! Oracle completeness audit.
//!
//! Static analysis over an existing `SurfaceSpec` reporting which constructs
//! the shipped v0 oracle (`crate::dsl::oracle::evaluate_trace`) can evaluate
//! locally. The audit does not change the oracle; it exposes what the oracle
//! can and cannot evaluate so downstream mutation and formal phases can reason
//! about gaps honestly.
//!
//! All output is local static analysis capped at `Level0DesignNote`. It is not
//! proof of oracle correctness, not benchmark evidence, not accepted evidence,
//! not formal evidence, and not evidence that any backend would produce any
//! particular outcome.

use serde::{Deserialize, Serialize};

use crate::dsl::expr::{ActionSpec, GuardExpr, GuardSpec, OperandSpec};
use crate::dsl::SurfaceSpec;
use crate::value::Value;

/// Completeness label for one audited construct.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OracleCompletenessLabel {
    /// Construct is fully inside the v0 executable oracle subset.
    Executable,
    /// Construct uses RawText and will produce a CapabilityGap.
    RawTextCapabilityGap,
    /// Construct references an operand type the oracle cannot evaluate
    /// (e.g. non-integer literal in a comparison guard).
    NonExecutableOperandCapabilityGap,
    /// Construct is structurally incapable of evaluation regardless of operand
    /// types (reserved for future constructs; none shipped today).
    StructurallyIncapable,
}

/// Kind of audited construct.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OracleCompletenessConstructKind {
    /// Transition guard.
    TransitionGuard,
    /// Transition action.
    TransitionAction,
    /// Invariant guard.
    InvariantGuard,
    /// Loop bound.
    LoopBound,
}

/// One audited construct and its label.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OracleCompletenessConstruct {
    /// Construct kind.
    pub kind: OracleCompletenessConstructKind,
    /// Construct id (transition id, invariant id, loop id, or action slot id).
    pub id: String,
    /// Completeness label.
    pub label: OracleCompletenessLabel,
    /// Human-readable detail.
    pub detail: String,
}

/// Complete audit over a `SurfaceSpec`.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct OracleCompletenessAudit {
    /// One entry per audited construct, in declaration order.
    pub constructs: Vec<OracleCompletenessConstruct>,
    /// Number of constructs labeled `Executable`.
    pub executable_count: usize,
    /// Number of constructs labeled `RawTextCapabilityGap` or
    /// `NonExecutableOperandCapabilityGap`.
    pub capability_gap_count: usize,
    /// Number of constructs labeled `StructurallyIncapable`.
    pub structurally_incapable_count: usize,
    /// True when every construct is `Executable`.
    pub is_fully_executable: bool,
}

/// Audit a `SurfaceSpec` for oracle completeness. Walks every transition guard,
/// every transition action, every invariant guard, and every loop bound in
/// declaration order. Classification mirrors the shipped oracle's static
/// raw-text and literal operand gap checks over this generated surface.
pub fn audit_oracle_completeness(surface: &SurfaceSpec) -> OracleCompletenessAudit {
    let mut constructs = Vec::new();

    for transition in &surface.machine.transitions {
        let guard_id = format!("{}.guard", transition.id);
        let label = classify_guard(&transition.guard);
        constructs.push(OracleCompletenessConstruct {
            kind: OracleCompletenessConstructKind::TransitionGuard,
            id: guard_id.clone(),
            label: label.0,
            detail: label.1,
        });

        for (index, action) in transition.actions.iter().enumerate() {
            let action_id = format!("{}.actions[{index}]", transition.id);
            let label = classify_action(action);
            constructs.push(OracleCompletenessConstruct {
                kind: OracleCompletenessConstructKind::TransitionAction,
                id: action_id.clone(),
                label: label.0,
                detail: label.1,
            });
        }
    }

    for invariant in &surface.machine.invariants {
        let invariant_id = format!("{}.guard", invariant.id);
        let label = classify_guard(&invariant.guard);
        constructs.push(OracleCompletenessConstruct {
            kind: OracleCompletenessConstructKind::InvariantGuard,
            id: invariant_id.clone(),
            label: label.0,
            detail: label.1,
        });
    }

    for entry in &surface.machine.loops {
        if let Some(bound) = &entry.bound {
            let bound_id = format!("{}.bound", entry.id);
            let label = classify_guard(bound);
            constructs.push(OracleCompletenessConstruct {
                kind: OracleCompletenessConstructKind::LoopBound,
                id: bound_id.clone(),
                label: label.0,
                detail: label.1,
            });
        }
    }

    let executable_count = constructs
        .iter()
        .filter(|c| c.label == OracleCompletenessLabel::Executable)
        .count();
    let capability_gap_count = constructs
        .iter()
        .filter(|c| {
            matches!(
                c.label,
                OracleCompletenessLabel::RawTextCapabilityGap
                    | OracleCompletenessLabel::NonExecutableOperandCapabilityGap
            )
        })
        .count();
    let structurally_incapable_count = constructs
        .iter()
        .filter(|c| c.label == OracleCompletenessLabel::StructurallyIncapable)
        .count();
    let is_fully_executable = !constructs.is_empty() && executable_count == constructs.len();

    OracleCompletenessAudit {
        constructs,
        executable_count,
        capability_gap_count,
        structurally_incapable_count,
        is_fully_executable,
    }
}

/// Classify a guard exactly as the shipped oracle would treat it.
fn classify_guard(guard: &GuardSpec) -> (OracleCompletenessLabel, String) {
    if guard.contains_raw_text() {
        return (
            OracleCompletenessLabel::RawTextCapabilityGap,
            "guard uses raw text and will produce a CapabilityGap".to_string(),
        );
    }
    if let Some(detail) = guard_non_int_literal_in_comparison(guard) {
        return (
            OracleCompletenessLabel::NonExecutableOperandCapabilityGap,
            detail,
        );
    }
    (
        OracleCompletenessLabel::Executable,
        "guard is inside the v0 executable subset".to_string(),
    )
}

/// Classify an action exactly as the shipped oracle would treat it.
fn classify_action(action: &ActionSpec) -> (OracleCompletenessLabel, String) {
    if action.contains_raw_text() {
        return (
            OracleCompletenessLabel::RawTextCapabilityGap,
            "action uses raw text and will produce a CapabilityGap".to_string(),
        );
    }
    (
        OracleCompletenessLabel::Executable,
        "action is inside the v0 executable subset".to_string(),
    )
}

/// Return `Some(detail)` when a comparison guard (`Lt`/`Lte`/`Gt`/`Gte`)
/// carries a non-integer literal operand. The oracle's `compare_ints` would
/// fall through to `CapabilityGap` for such operands.
fn guard_non_int_literal_in_comparison(guard: &GuardSpec) -> Option<String> {
    match guard {
        GuardSpec::Bool(_) => None,
        GuardSpec::Expr(expr) => non_int_literal_in_comparison(expr),
    }
}

fn non_int_literal_in_comparison(expr: &GuardExpr) -> Option<String> {
    let binary = match expr {
        GuardExpr::Lt { lt } => lt,
        GuardExpr::Lte { lte } => lte,
        GuardExpr::Gt { gt } => gt,
        GuardExpr::Gte { gte } => gte,
        GuardExpr::And { and } => return and.iter().find_map(guard_non_int_literal_in_comparison),
        GuardExpr::Or { or } => return or.iter().find_map(guard_non_int_literal_in_comparison),
        GuardExpr::Not { not } => return guard_non_int_literal_in_comparison(not),
        GuardExpr::Eq { .. } | GuardExpr::Neq { .. } | GuardExpr::RawText { .. } => return None,
    };
    for operand in [&binary.left, &binary.right] {
        if let OperandSpec::Literal(Value::Bool { .. } | Value::Text { .. }) = operand {
            return Some(
                "comparison guard has a non-integer literal operand and will produce a CapabilityGap"
                    .to_string(),
            );
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dsl::{
        BinaryGuard, GuardExpr, GuardSpec, InvariantSpec, LoopSpec, OperandSpec, SurfaceSpec,
        TransitionSpec,
    };
    use crate::value::Value;

    fn empty_surface() -> SurfaceSpec {
        SurfaceSpec {
            machine: crate::dsl::MachineSpec {
                id: "test_machine".to_string(),
                description: None,
                initial_state: "s0".to_string(),
                semantic_equivalence_class: None,
                states: Vec::new(),
                fields: Vec::new(),
                transitions: Vec::new(),
                loops: Vec::new(),
                invariants: Vec::new(),
                observations: Vec::new(),
                witness_policy: Default::default(),
                public_inputs: Vec::new(),
                private_witnesses: Vec::new(),
            },
            oracle: Default::default(),
            targets: Vec::new(),
            mutations: Vec::new(),
            evidence: Default::default(),
        }
    }

    #[test]
    fn empty_machine_is_not_fully_executable() {
        let audit = audit_oracle_completeness(&empty_surface());
        assert!(!audit.is_fully_executable);
        assert_eq!(audit.executable_count, 0);
    }

    #[test]
    fn executable_transition_guard_is_labeled_executable() {
        let mut surface = empty_surface();
        surface.machine.transitions.push(TransitionSpec {
            id: "t0".to_string(),
            from: "s0".to_string(),
            to: "s1".to_string(),
            guard: GuardSpec::Expr(GuardExpr::Lt {
                lt: BinaryGuard {
                    left: OperandSpec::Literal(Value::Int { int: 1 }),
                    right: OperandSpec::Literal(Value::Int { int: 2 }),
                },
            }),
            actions: Vec::new(),
        });
        let audit = audit_oracle_completeness(&surface);
        assert!(audit.is_fully_executable);
        assert_eq!(audit.executable_count, 1);
        assert_eq!(audit.capability_gap_count, 0);
    }

    #[test]
    fn raw_text_guard_is_labeled_capability_gap() {
        let mut surface = empty_surface();
        surface.machine.transitions.push(TransitionSpec {
            id: "t0".to_string(),
            from: "s0".to_string(),
            to: "s1".to_string(),
            guard: GuardSpec::Expr(GuardExpr::RawText {
                raw_text: "custom_predicate(x)".to_string(),
            }),
            actions: Vec::new(),
        });
        let audit = audit_oracle_completeness(&surface);
        assert!(!audit.is_fully_executable);
        assert_eq!(audit.capability_gap_count, 1);
        assert_eq!(audit.executable_count, 0);
        assert_eq!(
            audit.constructs[0].label,
            OracleCompletenessLabel::RawTextCapabilityGap
        );
    }

    #[test]
    fn raw_text_action_is_labeled_capability_gap() {
        let mut surface = empty_surface();
        surface.machine.transitions.push(TransitionSpec {
            id: "t0".to_string(),
            from: "s0".to_string(),
            to: "s1".to_string(),
            guard: GuardSpec::Bool(true),
            actions: vec![ActionSpec::RawText {
                raw_text: "custom_action()".to_string(),
            }],
        });
        let audit = audit_oracle_completeness(&surface);
        assert!(!audit.is_fully_executable);
        assert_eq!(audit.capability_gap_count, 1);
    }

    #[test]
    fn bool_literal_in_comparison_is_non_executable_operand_gap() {
        let mut surface = empty_surface();
        surface.machine.transitions.push(TransitionSpec {
            id: "t0".to_string(),
            from: "s0".to_string(),
            to: "s1".to_string(),
            guard: GuardSpec::Expr(GuardExpr::Lt {
                lt: BinaryGuard {
                    left: OperandSpec::Literal(Value::Bool { bool: true }),
                    right: OperandSpec::Literal(Value::Int { int: 2 }),
                },
            }),
            actions: Vec::new(),
        });
        let audit = audit_oracle_completeness(&surface);
        assert!(!audit.is_fully_executable);
        assert_eq!(audit.capability_gap_count, 1);
        assert_eq!(
            audit.constructs[0].label,
            OracleCompletenessLabel::NonExecutableOperandCapabilityGap
        );
    }

    #[test]
    fn nested_bool_literal_in_comparison_is_non_executable_operand_gap() {
        let mut surface = empty_surface();
        surface.machine.transitions.push(TransitionSpec {
            id: "t0".to_string(),
            from: "s0".to_string(),
            to: "s1".to_string(),
            guard: GuardSpec::Expr(GuardExpr::And {
                and: vec![
                    GuardSpec::Expr(GuardExpr::Eq {
                        eq: BinaryGuard {
                            left: OperandSpec::Literal(Value::Int { int: 1 }),
                            right: OperandSpec::Literal(Value::Int { int: 1 }),
                        },
                    }),
                    GuardSpec::Expr(GuardExpr::Not {
                        not: Box::new(GuardSpec::Expr(GuardExpr::Gt {
                            gt: BinaryGuard {
                                left: OperandSpec::Literal(Value::Text {
                                    text: "not-int".to_string(),
                                }),
                                right: OperandSpec::Literal(Value::Int { int: 2 }),
                            },
                        })),
                    }),
                ],
            }),
            actions: Vec::new(),
        });
        let audit = audit_oracle_completeness(&surface);
        assert!(!audit.is_fully_executable);
        assert_eq!(audit.capability_gap_count, 1);
        assert_eq!(
            audit.constructs[0].label,
            OracleCompletenessLabel::NonExecutableOperandCapabilityGap
        );
    }

    #[test]
    fn counts_are_consistent_with_construct_vector() {
        let mut surface = empty_surface();
        surface.machine.transitions.push(TransitionSpec {
            id: "t0".to_string(),
            from: "s0".to_string(),
            to: "s1".to_string(),
            guard: GuardSpec::Bool(true),
            actions: vec![
                ActionSpec::Noop { noop: true },
                ActionSpec::RawText {
                    raw_text: "x".to_string(),
                },
            ],
        });
        surface.machine.invariants.push(InvariantSpec {
            id: "inv0".to_string(),
            guard: GuardSpec::Bool(true),
            scope: None,
        });
        let audit = audit_oracle_completeness(&surface);
        assert_eq!(
            audit.constructs.len(),
            audit.executable_count
                + audit.capability_gap_count
                + audit.structurally_incapable_count
        );
        // t0.guard (executable), t0.actions[0] (executable), t0.actions[1] (gap), inv0.guard (executable)
        assert_eq!(audit.executable_count, 3);
        assert_eq!(audit.capability_gap_count, 1);
    }

    #[test]
    fn audit_is_deterministic() {
        let mut surface = empty_surface();
        surface.machine.loops.push(LoopSpec {
            id: "loop0".to_string(),
            bound: Some(GuardSpec::Bool(true)),
            body: vec!["t0".to_string()],
            metadata: Default::default(),
        });
        let left = audit_oracle_completeness(&surface);
        let right = audit_oracle_completeness(&surface);
        assert_eq!(left, right);
    }
}

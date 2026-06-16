//! Local oracle evaluation for a deliberately small v0 executable subset.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::value::Value;

use super::expr::{ActionSpec, BinaryGuard, GuardExpr, GuardSpec, OperandSpec};
use super::ir::SemanticIr;
use super::surface::TraceSpec;

/// Local oracle outcome for trace evaluation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum OracleOutcome {
    /// Trace is locally semantically valid.
    Accepted,
    /// Trace is locally semantically invalid.
    Rejected { reason: String },
    /// Trace requires semantics outside the v0 executable subset.
    CapabilityGap { reason: String },
    /// Trace cannot be classified from available observations.
    Inconclusive { reason: String },
}

/// Evaluate a trace against canonical Semantic IR using the v0 executable subset.
pub fn evaluate_trace(ir: &SemanticIr, trace: &TraceSpec) -> Result<OracleOutcome> {
    if !trace.requires_capabilities.is_empty() {
        return Ok(OracleOutcome::CapabilityGap {
            reason: format!(
                "trace requires unsupported capabilities: {}",
                trace.requires_capabilities.join(", ")
            ),
        });
    }

    let mut fields = ir.initial_field_values()?;
    for (field, value) in &trace.initial_fields {
        fields.insert(field.clone(), value.clone());
    }

    let mut current_state = trace
        .initial_state
        .clone()
        .unwrap_or_else(|| ir.machine.initial_state.clone());
    if ir.state(&current_state).is_none() {
        return Ok(OracleOutcome::Rejected {
            reason: format!("initial state '{current_state}' is not declared"),
        });
    }

    if let Some(outcome) = evaluate_invariants(ir, &fields)? {
        return Ok(outcome);
    }

    for step in &trace.steps {
        let transition = match ir.transition(&step.transition) {
            Some(transition) => transition,
            None => {
                return Ok(OracleOutcome::Rejected {
                    reason: format!("transition '{}' is not declared", step.transition),
                })
            }
        };

        if transition.from != current_state {
            return Ok(OracleOutcome::Rejected {
                reason: format!(
                    "transition '{}' starts at '{}' but current state is '{}'",
                    transition.id, transition.from, current_state
                ),
            });
        }

        match eval_guard(&transition.guard.guard, &fields)? {
            GuardEval::Bool(true) => {}
            GuardEval::Bool(false) => {
                return Ok(OracleOutcome::Rejected {
                    reason: format!("transition '{}' guard evaluated false", transition.id),
                })
            }
            GuardEval::CapabilityGap(reason) => return Ok(OracleOutcome::CapabilityGap { reason }),
        }

        for action in &transition.actions {
            if let Some(outcome) = apply_action(&action.action, &mut fields)? {
                return Ok(outcome);
            }
        }

        current_state = transition.to.clone();

        if let Some(outcome) = evaluate_invariants(ir, &fields)? {
            return Ok(outcome);
        }
    }

    if let Some(expected_final_state) = &trace.expected_final_state {
        if expected_final_state != &current_state {
            return Ok(OracleOutcome::Rejected {
                reason: format!(
                    "expected final state '{}' but observed '{}'",
                    expected_final_state, current_state
                ),
            });
        }
    }

    for (field, expected) in &trace.expected_final_fields {
        match fields.get(field) {
            Some(observed) if observed == expected => {}
            Some(observed) => {
                return Ok(OracleOutcome::Rejected {
                    reason: format!(
                        "expected final field '{field}' to be {:?} but observed {:?}",
                        expected, observed
                    ),
                })
            }
            None => {
                return Ok(OracleOutcome::Rejected {
                    reason: format!("expected final field '{field}' is missing"),
                })
            }
        }
    }

    Ok(OracleOutcome::Accepted)
}

enum GuardEval {
    Bool(bool),
    CapabilityGap(String),
}

fn evaluate_invariants(
    ir: &SemanticIr,
    fields: &BTreeMap<String, Value>,
) -> Result<Option<OracleOutcome>> {
    for invariant in &ir.machine.invariants {
        match eval_guard(&invariant.guard.guard, fields)? {
            GuardEval::Bool(true) => {}
            GuardEval::Bool(false) => {
                return Ok(Some(OracleOutcome::Rejected {
                    reason: format!("invariant '{}' evaluated false", invariant.id),
                }))
            }
            GuardEval::CapabilityGap(reason) => {
                return Ok(Some(OracleOutcome::CapabilityGap { reason }))
            }
        }
    }
    Ok(None)
}

fn eval_guard(guard: &GuardSpec, fields: &BTreeMap<String, Value>) -> Result<GuardEval> {
    match guard {
        GuardSpec::Bool(value) => Ok(GuardEval::Bool(*value)),
        GuardSpec::Expr(expr) => eval_guard_expr(expr, fields),
    }
}

fn eval_guard_expr(expr: &GuardExpr, fields: &BTreeMap<String, Value>) -> Result<GuardEval> {
    match expr {
        GuardExpr::Eq { eq: binary } => compare_values(binary, fields, |left, right| left == right),
        GuardExpr::Neq { neq: binary } => {
            compare_values(binary, fields, |left, right| left != right)
        }
        GuardExpr::Lt { lt: binary } => compare_ints(binary, fields, |left, right| left < right),
        GuardExpr::Lte { lte: binary } => compare_ints(binary, fields, |left, right| left <= right),
        GuardExpr::Gt { gt: binary } => compare_ints(binary, fields, |left, right| left > right),
        GuardExpr::Gte { gte: binary } => compare_ints(binary, fields, |left, right| left >= right),
        GuardExpr::And { and: guards } => {
            for guard in guards {
                match eval_guard(guard, fields)? {
                    GuardEval::Bool(true) => {}
                    GuardEval::Bool(false) => return Ok(GuardEval::Bool(false)),
                    GuardEval::CapabilityGap(reason) => {
                        return Ok(GuardEval::CapabilityGap(reason))
                    }
                }
            }
            Ok(GuardEval::Bool(true))
        }
        GuardExpr::Or { or: guards } => {
            let mut gap = None;
            for guard in guards {
                match eval_guard(guard, fields)? {
                    GuardEval::Bool(true) => return Ok(GuardEval::Bool(true)),
                    GuardEval::Bool(false) => {}
                    GuardEval::CapabilityGap(reason) => gap = Some(reason),
                }
            }
            if let Some(reason) = gap {
                Ok(GuardEval::CapabilityGap(reason))
            } else {
                Ok(GuardEval::Bool(false))
            }
        }
        GuardExpr::Not { not: guard } => match eval_guard(guard, fields)? {
            GuardEval::Bool(value) => Ok(GuardEval::Bool(!value)),
            GuardEval::CapabilityGap(reason) => Ok(GuardEval::CapabilityGap(reason)),
        },
        GuardExpr::RawText { raw_text: text } => Ok(GuardEval::CapabilityGap(format!(
            "guard uses non-executable raw text: {text}"
        ))),
    }
}

fn compare_values(
    binary: &BinaryGuard,
    fields: &BTreeMap<String, Value>,
    compare: impl FnOnce(&Value, &Value) -> bool,
) -> Result<GuardEval> {
    let left = eval_operand(&binary.left, fields)?;
    let right = eval_operand(&binary.right, fields)?;
    Ok(GuardEval::Bool(compare(&left, &right)))
}

fn compare_ints(
    binary: &BinaryGuard,
    fields: &BTreeMap<String, Value>,
    compare: impl FnOnce(i64, i64) -> bool,
) -> Result<GuardEval> {
    let left = eval_operand(&binary.left, fields)?;
    let right = eval_operand(&binary.right, fields)?;
    match (left.as_int(), right.as_int()) {
        (Some(left), Some(right)) => Ok(GuardEval::Bool(compare(left, right))),
        _ => Ok(GuardEval::CapabilityGap(
            "integer comparison received non-integer operand".to_string(),
        )),
    }
}

fn eval_operand(operand: &OperandSpec, fields: &BTreeMap<String, Value>) -> Result<Value> {
    match operand {
        OperandSpec::Literal(value) => Ok(value.clone()),
        OperandSpec::Field { field } => fields.get(field).cloned().ok_or_else(|| {
            ZkBenchError::oracle(
                format!("fields.{field}"),
                "field reference was not available during oracle evaluation",
            )
        }),
    }
}

fn apply_action(
    action: &ActionSpec,
    fields: &mut BTreeMap<String, Value>,
) -> Result<Option<OracleOutcome>> {
    match action {
        ActionSpec::Noop { .. } => Ok(None),
        ActionSpec::RawText { raw_text: text } => Ok(Some(OracleOutcome::CapabilityGap {
            reason: format!("action uses non-executable raw text: {text}"),
        })),
        ActionSpec::Assign { assign } => {
            let value = eval_operand(&assign.value, fields)?;
            fields.insert(assign.field.clone(), value);
            Ok(None)
        }
        ActionSpec::AddAssign { add_assign: assign } => {
            apply_int_update(&assign.field, &assign.value, fields, i64::checked_add)
        }
        ActionSpec::SubAssign { sub_assign: assign } => {
            apply_int_update(&assign.field, &assign.value, fields, i64::checked_sub)
        }
    }
}

fn apply_int_update(
    field: &str,
    operand: &OperandSpec,
    fields: &mut BTreeMap<String, Value>,
    update: impl FnOnce(i64, i64) -> Option<i64>,
) -> Result<Option<OracleOutcome>> {
    let current = match fields.get(field).and_then(Value::as_int) {
        Some(value) => value,
        None => {
            return Ok(Some(OracleOutcome::Rejected {
                reason: format!("field '{field}' is not an integer for arithmetic update"),
            }))
        }
    };
    let operand = match eval_operand(operand, fields)?.as_int() {
        Some(value) => value,
        None => {
            return Ok(Some(OracleOutcome::Rejected {
                reason: "arithmetic operand is not an integer".to_string(),
            }))
        }
    };
    let updated = match update(current, operand) {
        Some(value) => value,
        None => {
            return Ok(Some(OracleOutcome::Rejected {
                reason: format!("integer overflow while updating field '{field}'"),
            }))
        }
    };
    fields.insert(field.to_string(), Value::Int { int: updated });
    Ok(None)
}

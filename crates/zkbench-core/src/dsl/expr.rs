//! Guard, operand, and action syntax for the v0 executable subset.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::value::Value;

/// Operand used by guards and actions.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum OperandSpec {
    /// Reference to a machine field.
    Field { field: String },
    /// Literal value.
    Literal(Value),
}

/// Binary guard expression payload.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BinaryGuard {
    /// Left operand.
    pub left: OperandSpec,
    /// Right operand.
    pub right: OperandSpec,
}

/// Executable and non-executable guard expressions.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum GuardSpec {
    /// Boolean literal guard.
    Bool(bool),
    /// Structured guard expression.
    Expr(GuardExpr),
}

impl Default for GuardSpec {
    fn default() -> Self {
        Self::Bool(true)
    }
}

/// Structured guard expression variants.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum GuardExpr {
    /// Equality.
    Eq { eq: BinaryGuard },
    /// Inequality.
    Neq { neq: BinaryGuard },
    /// Less-than comparison.
    Lt { lt: BinaryGuard },
    /// Less-than-or-equal comparison.
    Lte { lte: BinaryGuard },
    /// Greater-than comparison.
    Gt { gt: BinaryGuard },
    /// Greater-than-or-equal comparison.
    Gte { gte: BinaryGuard },
    /// Boolean conjunction.
    And { and: Vec<GuardSpec> },
    /// Boolean disjunction.
    Or { or: Vec<GuardSpec> },
    /// Boolean negation.
    Not { not: Box<GuardSpec> },
    /// Explicitly non-executable guard text.
    RawText { raw_text: String },
}

/// Assign action payload.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AssignAction {
    /// Target field.
    pub field: String,
    /// Source operand.
    pub value: OperandSpec,
}

/// Executable and non-executable transition actions.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ActionSpec {
    /// No state update.
    Noop { noop: bool },
    /// Assign a field to an operand value.
    Assign { assign: AssignAction },
    /// Add an integer operand to an integer field.
    AddAssign { add_assign: AssignAction },
    /// Subtract an integer operand from an integer field.
    SubAssign { sub_assign: AssignAction },
    /// Explicitly non-executable action text.
    RawText { raw_text: String },
}

impl OperandSpec {
    /// Collect referenced field identifiers.
    pub fn collect_field_references(&self, refs: &mut BTreeSet<String>) {
        match self {
            Self::Field { field } => {
                refs.insert(field.clone());
            }
            Self::Literal(_) => {}
        }
    }
}

impl GuardSpec {
    /// Collect referenced field identifiers.
    pub fn collect_field_references(&self, refs: &mut BTreeSet<String>) {
        match self {
            Self::Bool(_) => {}
            Self::Expr(expr) => expr.collect_field_references(refs),
        }
    }

    /// Return true if the guard uses raw text and cannot be evaluated locally.
    pub fn contains_raw_text(&self) -> bool {
        match self {
            Self::Bool(_) => false,
            Self::Expr(expr) => expr.contains_raw_text(),
        }
    }
}

impl GuardExpr {
    fn collect_field_references(&self, refs: &mut BTreeSet<String>) {
        match self {
            Self::Eq { eq: binary }
            | Self::Neq { neq: binary }
            | Self::Lt { lt: binary }
            | Self::Lte { lte: binary }
            | Self::Gt { gt: binary }
            | Self::Gte { gte: binary } => {
                binary.left.collect_field_references(refs);
                binary.right.collect_field_references(refs);
            }
            Self::And { and: guards } | Self::Or { or: guards } => {
                for guard in guards {
                    guard.collect_field_references(refs);
                }
            }
            Self::Not { not: guard } => guard.collect_field_references(refs),
            Self::RawText { .. } => {}
        }
    }

    fn contains_raw_text(&self) -> bool {
        match self {
            Self::RawText { .. } => true,
            Self::And { and: guards } | Self::Or { or: guards } => {
                guards.iter().any(GuardSpec::contains_raw_text)
            }
            Self::Not { not: guard } => guard.contains_raw_text(),
            Self::Eq { .. }
            | Self::Neq { .. }
            | Self::Lt { .. }
            | Self::Lte { .. }
            | Self::Gt { .. }
            | Self::Gte { .. } => false,
        }
    }
}

impl ActionSpec {
    /// Collect referenced field identifiers.
    pub fn collect_field_references(&self, refs: &mut BTreeSet<String>) {
        match self {
            Self::Noop { .. } | Self::RawText { .. } => {}
            Self::Assign { assign: action }
            | Self::AddAssign { add_assign: action }
            | Self::SubAssign { sub_assign: action } => {
                refs.insert(action.field.clone());
                action.value.collect_field_references(refs);
            }
        }
    }

    /// Return true if the action uses raw text and cannot be evaluated locally.
    pub fn contains_raw_text(&self) -> bool {
        matches!(self, Self::RawText { .. })
    }
}

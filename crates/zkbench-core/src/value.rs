//! Primitive values used by the v0 executable subset.

use serde::{Deserialize, Serialize};

/// Field value for local trace execution.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum Value {
    /// Signed integer value for counters, bounds, and small arithmetic.
    Int { int: i64 },
    /// Boolean value.
    Bool { bool: bool },
    /// Text value for metadata-like executable fields.
    Text { text: String },
}

/// Supported field types in the v0 executable subset.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ValueType {
    /// Integer field.
    Int,
    /// Boolean field.
    Bool,
    /// Text field.
    Text,
}

/// Public/private/internal field visibility.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "snake_case")]
pub enum FieldVisibility {
    /// Public input or observation.
    Public,
    /// Private witness value.
    Private,
    /// Internal state not intended as public input or witness.
    #[default]
    Internal,
}

impl Value {
    /// Check whether the value matches a declared field type.
    pub fn matches_type(&self, value_type: &ValueType) -> bool {
        matches!(
            (self, value_type),
            (Self::Int { .. }, ValueType::Int)
                | (Self::Bool { .. }, ValueType::Bool)
                | (Self::Text { .. }, ValueType::Text)
        )
    }

    /// Return the value as an integer when possible.
    pub fn as_int(&self) -> Option<i64> {
        match self {
            Self::Int { int } => Some(*int),
            Self::Bool { .. } | Self::Text { .. } => None,
        }
    }
}

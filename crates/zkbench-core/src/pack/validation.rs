//! Benchmark pack validation result types.

use serde::{Deserialize, Serialize};

use super::manifest::BenchmarkPackSummary;

/// Local pack validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkPackValidation {
    /// True when local file and ledger checks pass.
    pub valid: bool,
    /// Validation errors.
    pub errors: Vec<BenchmarkPackValidationError>,
    /// Pack summary from the manifest.
    pub summary: BenchmarkPackSummary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Pack validation error.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkPackValidationError {
    /// Relative path or logical path.
    pub path: String,
    /// Error message.
    pub message: String,
}

impl BenchmarkPackValidation {
    /// Build a validation result from errors.
    pub fn from_errors(
        errors: Vec<BenchmarkPackValidationError>,
        summary: BenchmarkPackSummary,
    ) -> Self {
        Self {
            valid: errors.is_empty(),
            errors,
            summary,
            notes: vec![
                "Pack validation checks local file integrity only; it is not official benchmark evidence.".to_string(),
            ],
        }
    }
}

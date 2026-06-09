//! Shared validation helpers for external-runner boundary artifacts.

use serde::{Deserialize, Serialize};

use crate::evidence::ClaimBoundary;

/// Severity for external-runner boundary validation issues.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExternalValidationIssueSeverity {
    /// Validation error.
    Error,
    /// Validation warning.
    Warning,
}

/// Shared validation issue for Phase H boundary artifacts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: ExternalValidationIssueSeverity,
}

impl ExternalValidationIssue {
    /// Build an error issue.
    pub fn error(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Error,
        }
    }

    /// Build a warning issue.
    pub fn warning(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Warning,
        }
    }
}

/// Returns true when text looks like an absolute path or parent traversal.
pub fn contains_rejected_path(text: &str) -> bool {
    text.starts_with('/')
        || text.starts_with("~/")
        || text.contains("..")
        || text.contains('\\')
        || looks_like_windows_absolute_path(text)
}

/// Returns true when text looks like shell payload rather than inert metadata.
pub fn contains_shell_payload(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    lowered.contains(" && ")
        || lowered.contains(" || ")
        || lowered.contains(" ; ")
        || lowered.contains(" | ")
        || lowered.contains("$(")
        || lowered.contains('`')
        || lowered.contains("bash ")
        || lowered.contains("sh ")
        || lowered.contains("zsh ")
        || lowered.starts_with("bash")
        || lowered.starts_with("sh ")
        || lowered.starts_with("zsh")
}

/// Returns true when free text makes a Phase H forbidden claim.
pub fn contains_forbidden_claim_text(text: &str) -> bool {
    contains_official_claim_text(text)
        || contains_formal_claim_text(text)
        || contains_soundness_claim_text(text)
        || text.to_ascii_lowercase().contains("sota result")
        || text.to_ascii_lowercase().contains("performance evidence")
}

/// Returns true when free text claims official benchmark status.
pub fn contains_official_claim_text(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    lowered.contains("official benchmark evidence")
        || lowered.contains("official benchmark result")
        || lowered.contains("official zk-harness result")
        || lowered.contains("verified benchmark result")
        || lowered.contains("zk-harness result")
}

/// Returns true when free text claims formal proof or formal evidence.
pub fn contains_formal_claim_text(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    lowered.contains("formal evidence")
        || lowered.contains("formal proof")
        || lowered.contains("machine-checked proof")
}

/// Returns true when free text claims proof-system soundness.
pub fn contains_soundness_claim_text(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    lowered.contains("proof-system soundness")
        || lowered.contains("proved sound")
        || lowered.contains("proves soundness")
}

/// Return true if an actual Phase H artifact may use this claim boundary.
pub fn phase_h_actual_claim_allowed(boundary: ClaimBoundary) -> bool {
    boundary <= ClaimBoundary::Level1LocalReplay
}

/// Return true if a Phase H handoff/schema artifact must stay Level 0.
pub fn phase_h_design_artifact_claim_allowed(boundary: ClaimBoundary) -> bool {
    boundary == ClaimBoundary::Level0DesignNote
}

fn looks_like_windows_absolute_path(text: &str) -> bool {
    let bytes = text.as_bytes();
    bytes.len() >= 3
        && bytes[1] == b':'
        && (bytes[2] == b'/' || bytes[2] == b'\\')
        && bytes[0].is_ascii_alphabetic()
}

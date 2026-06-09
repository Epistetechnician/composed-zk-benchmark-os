//! Mutation provenance structures.

use serde::{Deserialize, Serialize};

use crate::evidence::{ClaimBoundary, ExpectedVerdict};

use super::{MutationClass, MutationSafetyClass};

/// Provenance for a local mutation output.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MutationProvenance {
    /// Stable mutation id.
    pub mutation_id: String,
    /// Mutation class.
    pub mutation_class: MutationClass,
    /// Source instance id.
    pub source_instance_id: String,
    /// Affected machine id.
    pub affected_machine_id: String,
    /// Affected transition ids.
    pub affected_transition_ids: Vec<String>,
    /// Affected guard ids where available.
    pub affected_guard_ids: Vec<String>,
    /// Affected action ids where available.
    pub affected_action_ids: Vec<String>,
    /// Affected field ids where available.
    pub affected_field_ids: Vec<String>,
    /// Description.
    pub description: String,
    /// Expected verdict.
    pub expected_verdict: ExpectedVerdict,
    /// Safety class.
    pub safety_class: MutationSafetyClass,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    pub notes: Vec<String>,
}

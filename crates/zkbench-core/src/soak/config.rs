//! Deterministic soak configuration and report metadata.

use serde::{Deserialize, Serialize};

use crate::evidence::ClaimBoundary;
use crate::generator::FamilyKind;

/// Soak execution report schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakExecutionReportVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for SoakExecutionReportVersion {
    fn default() -> Self {
        Self {
            value: "phase-l-local-soak-v0".to_string(),
        }
    }
}

/// Deterministic soak plan describing the local execution grid.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakPlan {
    /// Implemented family kinds to exercise.
    pub family_kinds: Vec<FamilyKind>,
    /// Explicit deterministic seeds. No system randomness is used.
    pub seeds: Vec<u64>,
    /// Whether default mutation passes are applied and replayed.
    pub apply_mutations: bool,
    /// Maximum claim boundary allowed for soak outputs.
    pub claim_boundary_cap: ClaimBoundary,
}

impl Default for SoakPlan {
    fn default() -> Self {
        Self {
            family_kinds: vec![
                FamilyKind::BaselineFsm,
                FamilyKind::BranchingFsm,
                FamilyKind::BoundedCounterLoop,
            ],
            seeds: vec![11, 17, 23],
            apply_mutations: true,
            claim_boundary_cap: ClaimBoundary::Level1LocalReplay,
        }
    }
}

/// Full soak configuration including output layout.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakConfig {
    /// Deterministic soak plan.
    pub plan: SoakPlan,
    /// Relative directory under the soak root where packs are written.
    pub packs_subdirectory: String,
    /// Whether conservative score reports are included in each pack.
    pub include_score_report: bool,
}

impl Default for SoakConfig {
    fn default() -> Self {
        Self {
            plan: SoakPlan::default(),
            packs_subdirectory: "packs".to_string(),
            include_score_report: true,
        }
    }
}

/// Descriptor for one soak-produced benchmark pack.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakPackDescriptor {
    /// Pack id written by the soak runner.
    pub pack_id: String,
    /// Family kind for this pack.
    pub family_kind: FamilyKind,
    /// Seed used for generation.
    pub seed: u64,
    /// Relative path from the soak root to the pack directory.
    pub pack_root_relative: String,
    /// Replay results written into the pack.
    pub replay_result_count: usize,
    /// Mutated instances written into the pack.
    pub mutated_instance_count: usize,
    /// Mutation passes skipped because no eligible target existed.
    pub mutation_passes_skipped: usize,
}

/// One soak failure record.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakFailure {
    /// Family kind associated with the failure.
    pub family_kind: FamilyKind,
    /// Seed associated with the failure.
    pub seed: u64,
    /// Failure message.
    pub message: String,
}

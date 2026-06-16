//! Named soak campaign presets for quick local execution grids.

use crate::evidence::ClaimBoundary;
use crate::generator::FamilyKind;

use super::config::{SoakConfig, SoakPlan};

/// Quick campaign across all implemented v0 families with all three mutation passes.
pub fn quick_three_family_all_passes() -> SoakPlan {
    SoakPlan {
        family_kinds: vec![
            FamilyKind::BaselineFsm,
            FamilyKind::BranchingFsm,
            FamilyKind::BoundedCounterLoop,
        ],
        seeds: vec![5, 11, 17, 23, 29],
        apply_mutations: true,
        claim_boundary_cap: ClaimBoundary::Level1LocalReplay,
    }
}

/// Smaller quick grid for fast regression checks.
pub fn quick_three_family_smoke() -> SoakPlan {
    SoakPlan {
        family_kinds: vec![
            FamilyKind::BaselineFsm,
            FamilyKind::BranchingFsm,
            FamilyKind::BoundedCounterLoop,
        ],
        seeds: vec![11, 17],
        apply_mutations: true,
        claim_boundary_cap: ClaimBoundary::Level1LocalReplay,
    }
}

/// Build a soak config from a named quick plan.
pub fn soak_config_from_plan(plan: SoakPlan) -> SoakConfig {
    SoakConfig {
        plan,
        packs_subdirectory: "packs".to_string(),
        include_score_report: true,
    }
}

/// Default quick campaign config for Phase L operational use.
pub fn quick_campaign_config() -> SoakConfig {
    soak_config_from_plan(quick_three_family_all_passes())
}

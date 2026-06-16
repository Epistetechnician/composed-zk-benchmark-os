//! Narrow zkML adapter capability declarations.

use serde::{Deserialize, Serialize};

use crate::adapters::AdapterCapabilitySet;

/// Capability declaration for the Phase L narrow zkML preparation layer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowAdapterCapabilityDeclaration {
    /// Can create inert workload plans from semantic fixtures.
    pub supports_workload_planning: bool,
    /// Can preserve semantic fixture references by digest.
    pub preserves_fixture_digests: bool,
    /// Can map public/private boundary metadata.
    pub maps_public_private_boundary_metadata: bool,
    /// Live execution support. False for Phase L.
    pub supports_execution: bool,
    /// Proving support. False for Phase L.
    pub supports_proving: bool,
    /// Verification timing support. False for Phase L.
    pub supports_verification_timing: bool,
    /// Constraint count support. False for Phase L.
    pub supports_constraint_count: bool,
    /// Formal semantics support. False for Phase L.
    pub supports_formal_semantics: bool,
    /// Machine-checked proof support. False for Phase L.
    pub supports_machine_checked_proof: bool,
    /// Recursion support. False for Phase L.
    pub supports_recursion: bool,
    /// zkML metrics schema support. True for Phase L.
    pub supports_zkml_metrics: bool,
    /// Public/private boundary checks. True for Phase L.
    pub supports_public_private_boundary_checks: bool,
}

/// Conservative Phase L capability declaration.
pub fn default_zkml_narrow_capability_declaration() -> ZkmlNarrowAdapterCapabilityDeclaration {
    ZkmlNarrowAdapterCapabilityDeclaration {
        supports_workload_planning: true,
        preserves_fixture_digests: true,
        maps_public_private_boundary_metadata: true,
        supports_execution: false,
        supports_proving: false,
        supports_verification_timing: false,
        supports_constraint_count: false,
        supports_formal_semantics: false,
        supports_machine_checked_proof: false,
        supports_recursion: false,
        supports_zkml_metrics: true,
        supports_public_private_boundary_checks: true,
    }
}

/// Conservative generic capability flags for the narrow zkML preparation target.
pub fn zkml_narrow_capabilities() -> AdapterCapabilitySet {
    AdapterCapabilitySet {
        supports_execution: false,
        supports_proving: false,
        supports_verification_timing: false,
        supports_negative_tests: true,
        supports_trace_export: true,
        supports_constraint_count: false,
        supports_formal_semantics: false,
        supports_machine_checked_proof: false,
        supports_recursion: false,
        supports_zkml_metrics: true,
        supports_replay_manifest: true,
        supports_artifact_hashing: true,
        supports_public_private_boundary_checks: true,
    }
}

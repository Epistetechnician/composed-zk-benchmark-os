//! gnark recursion adapter capability declarations.

use serde::{Deserialize, Serialize};

use crate::adapters::AdapterCapabilitySet;

/// Capability declaration for the Phase K gnark recursion preparation layer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionAdapterCapabilityDeclaration {
    /// Can create inert recursion envelope plans.
    pub supports_envelope_planning: bool,
    /// Can preserve semantic fixture references by digest.
    pub preserves_fixture_digests: bool,
    /// Can map recursion envelope metadata.
    pub maps_recursion_envelope_metadata: bool,
    /// Live execution support. False for Phase K.
    pub supports_execution: bool,
    /// Proving support. False for Phase K.
    pub supports_proving: bool,
    /// Verification timing support. False for Phase K.
    pub supports_verification_timing: bool,
    /// Constraint count support. False for Phase K.
    pub supports_constraint_count: bool,
    /// Formal semantics support. False for Phase K.
    pub supports_formal_semantics: bool,
    /// Machine-checked proof support. False for Phase K.
    pub supports_machine_checked_proof: bool,
    /// Recursion envelope planning support. True for Phase K.
    pub supports_recursion: bool,
    /// zkML metrics support. False for Phase K.
    pub supports_zkml_metrics: bool,
}

/// Conservative Phase K capability declaration.
pub fn default_gnark_recursion_capability_declaration() -> GnarkRecursionAdapterCapabilityDeclaration
{
    GnarkRecursionAdapterCapabilityDeclaration {
        supports_envelope_planning: true,
        preserves_fixture_digests: true,
        maps_recursion_envelope_metadata: true,
        supports_execution: false,
        supports_proving: false,
        supports_verification_timing: false,
        supports_constraint_count: false,
        supports_formal_semantics: false,
        supports_machine_checked_proof: false,
        supports_recursion: true,
        supports_zkml_metrics: false,
    }
}

/// Conservative generic capability flags for the gnark recursion preparation target.
pub fn gnark_recursion_capabilities() -> AdapterCapabilitySet {
    AdapterCapabilitySet {
        supports_execution: false,
        supports_proving: false,
        supports_verification_timing: false,
        supports_negative_tests: true,
        supports_trace_export: false,
        supports_constraint_count: false,
        supports_formal_semantics: false,
        supports_machine_checked_proof: false,
        supports_recursion: true,
        supports_zkml_metrics: false,
        supports_replay_manifest: true,
        supports_artifact_hashing: true,
        supports_public_private_boundary_checks: false,
    }
}

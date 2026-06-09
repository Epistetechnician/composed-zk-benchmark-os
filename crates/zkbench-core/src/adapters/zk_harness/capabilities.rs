//! zk-Harness dry-run capability declarations.

use serde::{Deserialize, Serialize};

use crate::adapters::AdapterCapabilitySet;

/// Capability declaration for the Phase G zk-Harness preparation layer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessAdapterCapabilityDeclaration {
    /// Can create dry-run plans from local packs.
    pub supports_dry_run_planning: bool,
    /// Can preserve source pack digests as data.
    pub preserves_pack_digests: bool,
    /// Can export trace mapping data.
    pub exports_trace_mapping_data: bool,
    /// Can consume local replay manifests as data.
    pub consumes_local_replay_manifest_data: bool,
    /// Live execution support. False for Phase G.
    pub supports_execution: bool,
    /// Proving support. False for Phase G.
    pub supports_proving: bool,
    /// Verification timing support. False for Phase G.
    pub supports_verification_timing: bool,
    /// Constraint count support. False for Phase G.
    pub supports_constraint_count: bool,
    /// Formal semantics support. False for Phase G.
    pub supports_formal_semantics: bool,
    /// Machine-checked proof support. False for Phase G.
    pub supports_machine_checked_proof: bool,
    /// Recursion support. False for Phase G.
    pub supports_recursion: bool,
    /// zkML metrics support. False for Phase G.
    pub supports_zkml_metrics: bool,
}

/// Conservative Phase G capability declaration.
pub fn default_zk_harness_capability_declaration() -> ZkHarnessAdapterCapabilityDeclaration {
    ZkHarnessAdapterCapabilityDeclaration {
        supports_dry_run_planning: true,
        preserves_pack_digests: true,
        exports_trace_mapping_data: true,
        consumes_local_replay_manifest_data: true,
        supports_execution: false,
        supports_proving: false,
        supports_verification_timing: false,
        supports_constraint_count: false,
        supports_formal_semantics: false,
        supports_machine_checked_proof: false,
        supports_recursion: false,
        supports_zkml_metrics: false,
    }
}

/// Conservative generic capability flags for the dry-run preparation target.
pub fn zk_harness_dry_run_capabilities() -> AdapterCapabilitySet {
    AdapterCapabilitySet {
        supports_execution: false,
        supports_proving: false,
        supports_verification_timing: false,
        supports_negative_tests: false,
        supports_trace_export: true,
        supports_constraint_count: false,
        supports_formal_semantics: false,
        supports_machine_checked_proof: false,
        supports_recursion: false,
        supports_zkml_metrics: false,
        supports_replay_manifest: true,
        supports_artifact_hashing: true,
        supports_public_private_boundary_checks: false,
    }
}

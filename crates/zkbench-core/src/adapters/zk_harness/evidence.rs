//! Evidence and claim-boundary policies for zk-Harness dry-run planning.

use serde::{Deserialize, Serialize};

use crate::evidence::{ClaimBoundary, EvidenceClass};

/// Evidence policy for Phase G.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessEvidencePolicy {
    /// Dry-run plan generation boundary.
    pub dry_run_plan_claim_boundary: ClaimBoundary,
    /// Maximum boundary for referenced local pack evidence.
    pub local_source_pack_claim_boundary_max: ClaimBoundary,
    /// Future live external replay can reach Level2 only after artifacts exist.
    pub future_live_external_replay_may_reach_level2_after_validation: bool,
    /// Imported external results require provenance and validation.
    pub imported_results_require_provenance_and_validation: bool,
    /// Benchmark pass is not proof.
    pub benchmark_pass_is_not_proof: bool,
    /// Local replay is not official benchmark evidence.
    pub local_replay_is_not_official_benchmark_evidence: bool,
    /// External replay is not formal evidence.
    pub external_replay_is_not_formal_evidence: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkHarnessEvidencePolicy {
    fn default() -> Self {
        Self {
            dry_run_plan_claim_boundary: ClaimBoundary::Level0DesignNote,
            local_source_pack_claim_boundary_max: ClaimBoundary::Level1LocalReplay,
            future_live_external_replay_may_reach_level2_after_validation: true,
            imported_results_require_provenance_and_validation: true,
            benchmark_pass_is_not_proof: true,
            local_replay_is_not_official_benchmark_evidence: true,
            external_replay_is_not_formal_evidence: true,
            notes: vec![
                "Dry-run planning creates adapter preparation metadata only.".to_string(),
                "Future external replay requires reviewed provenance and artifact validation."
                    .to_string(),
            ],
        }
    }
}

/// Claim-boundary policy for zk-Harness adapter preparation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessClaimBoundaryPolicy {
    /// Boundary for Phase G artifacts.
    pub phase_g_artifact_boundary: ClaimBoundary,
    /// Maximum boundary retained for local pack references.
    pub local_pack_reference_boundary_max: ClaimBoundary,
    /// Whether Phase G may create Level2 actual evidence.
    pub allow_level2_in_phase_g: bool,
    /// Whether local source evidence elevation is forbidden.
    pub prevent_local_evidence_elevation: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkHarnessClaimBoundaryPolicy {
    fn default() -> Self {
        Self {
            phase_g_artifact_boundary: ClaimBoundary::Level0DesignNote,
            local_pack_reference_boundary_max: ClaimBoundary::Level1LocalReplay,
            allow_level2_in_phase_g: false,
            prevent_local_evidence_elevation: true,
            notes: vec![
                "zk-Harness dry-run plans are not benchmark results.".to_string(),
                "External execution is disabled by default.".to_string(),
            ],
        }
    }
}

/// Schema for future zk-Harness evidence mapping.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessEvidenceMapping {
    /// Evidence class emitted by Phase G planning.
    pub dry_run_evidence_class: EvidenceClass,
    /// Current phase claim boundary.
    pub current_phase_claim_boundary: ClaimBoundary,
    /// Future external replay boundary after artifact validation.
    pub future_external_replay_boundary_after_validation: ClaimBoundary,
    /// Whether this dry-run plan emits evidence records.
    pub emits_evidence_records: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkHarnessEvidenceMapping {
    fn default() -> Self {
        Self {
            dry_run_evidence_class: EvidenceClass::DesignNote,
            current_phase_claim_boundary: ClaimBoundary::Level0DesignNote,
            future_external_replay_boundary_after_validation:
                ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
            emits_evidence_records: false,
            notes: vec![
                "Dry-run plan generation is design metadata only.".to_string(),
                "No zk-Harness ReplayResult is created in Phase G.".to_string(),
            ],
        }
    }
}

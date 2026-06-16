//! Evidence and claim-boundary policies for gnark recursion envelope planning.

use serde::{Deserialize, Serialize};

use crate::evidence::{ClaimBoundary, EvidenceClass};

/// Evidence policy for Phase K.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionEvidencePolicy {
    /// Envelope plan generation boundary.
    pub envelope_plan_claim_boundary: ClaimBoundary,
    /// Maximum boundary for referenced semantic fixture metadata.
    pub semantic_fixture_claim_boundary_max: ClaimBoundary,
    /// Future live gnark replay can reach Level2 only after artifacts exist.
    pub future_live_gnark_replay_may_reach_level2_after_validation: bool,
    /// Imported external results require provenance and validation.
    pub imported_results_require_provenance_and_validation: bool,
    /// Recursion proof is not semantic proof.
    pub recursion_proof_is_not_semantic_proof: bool,
    /// Benchmark pass is not proof.
    pub benchmark_pass_is_not_proof: bool,
    /// Local replay is not official benchmark evidence.
    pub local_replay_is_not_official_benchmark_evidence: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for GnarkRecursionEvidencePolicy {
    fn default() -> Self {
        Self {
            envelope_plan_claim_boundary: ClaimBoundary::Level0DesignNote,
            semantic_fixture_claim_boundary_max: ClaimBoundary::Level0DesignNote,
            future_live_gnark_replay_may_reach_level2_after_validation: true,
            imported_results_require_provenance_and_validation: true,
            recursion_proof_is_not_semantic_proof: true,
            benchmark_pass_is_not_proof: true,
            local_replay_is_not_official_benchmark_evidence: true,
            notes: vec![
                "Envelope planning creates adapter preparation metadata only.".to_string(),
                "Recursion proof is not semantic proof.".to_string(),
            ],
        }
    }
}

/// Claim-boundary policy for gnark recursion adapter preparation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionClaimBoundaryPolicy {
    /// Boundary for Phase K artifacts.
    pub phase_k_artifact_boundary: ClaimBoundary,
    /// Maximum boundary retained for semantic fixture references.
    pub semantic_fixture_reference_boundary_max: ClaimBoundary,
    /// Whether Phase K may create Level2 actual evidence.
    pub allow_level2_in_phase_k: bool,
    /// Whether recursion proof can elevate semantic evidence.
    pub prevent_recursion_proof_elevation: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for GnarkRecursionClaimBoundaryPolicy {
    fn default() -> Self {
        Self {
            phase_k_artifact_boundary: ClaimBoundary::Level0DesignNote,
            semantic_fixture_reference_boundary_max: ClaimBoundary::Level0DesignNote,
            allow_level2_in_phase_k: false,
            prevent_recursion_proof_elevation: true,
            notes: vec![
                "gnark recursion envelope plans are not benchmark results.".to_string(),
                "External execution is disabled by default.".to_string(),
            ],
        }
    }
}

/// Schema for future gnark recursion evidence mapping.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionEvidenceMapping {
    /// Evidence class emitted by Phase K planning.
    pub envelope_plan_evidence_class: EvidenceClass,
    /// Current phase claim boundary.
    pub current_phase_claim_boundary: ClaimBoundary,
    /// Future external replay boundary after artifact validation.
    pub future_external_replay_boundary_after_validation: ClaimBoundary,
    /// Whether this envelope plan emits evidence records.
    pub emits_evidence_records: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for GnarkRecursionEvidenceMapping {
    fn default() -> Self {
        Self {
            envelope_plan_evidence_class: EvidenceClass::DesignNote,
            current_phase_claim_boundary: ClaimBoundary::Level0DesignNote,
            future_external_replay_boundary_after_validation:
                ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
            emits_evidence_records: false,
            notes: vec![
                "Envelope plan generation is design metadata only.".to_string(),
                "No gnark recursion proof is created in Phase K.".to_string(),
            ],
        }
    }
}

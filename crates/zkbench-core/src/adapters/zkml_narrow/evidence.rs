//! Evidence and claim-boundary policies for narrow zkML workload planning.

use serde::{Deserialize, Serialize};

use crate::evidence::{ClaimBoundary, EvidenceClass};

/// Evidence policy for Phase L.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowEvidencePolicy {
    /// Workload plan generation boundary.
    pub workload_plan_claim_boundary: ClaimBoundary,
    /// Maximum boundary for referenced semantic fixture metadata.
    pub semantic_fixture_claim_boundary_max: ClaimBoundary,
    /// Future live zkML replay can reach Level2 only after artifacts exist.
    pub future_live_zkml_replay_may_reach_level2_after_validation: bool,
    /// Imported external results require provenance and validation.
    pub imported_results_require_provenance_and_validation: bool,
    /// zkML metrics do not prove semantic soundness.
    pub zkml_metrics_do_not_prove_semantic_soundness: bool,
    /// Model accuracy is not proof-system correctness.
    pub model_accuracy_is_not_proof_system_correctness: bool,
    /// Benchmark pass is not proof.
    pub benchmark_pass_is_not_proof: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkmlNarrowEvidencePolicy {
    fn default() -> Self {
        Self {
            workload_plan_claim_boundary: ClaimBoundary::Level0DesignNote,
            semantic_fixture_claim_boundary_max: ClaimBoundary::Level0DesignNote,
            future_live_zkml_replay_may_reach_level2_after_validation: true,
            imported_results_require_provenance_and_validation: true,
            zkml_metrics_do_not_prove_semantic_soundness: true,
            model_accuracy_is_not_proof_system_correctness: true,
            benchmark_pass_is_not_proof: true,
            notes: vec![
                "Workload planning creates adapter preparation metadata only.".to_string(),
                "zkML metrics do not prove semantic soundness.".to_string(),
            ],
        }
    }
}

/// Claim-boundary policy for narrow zkML adapter preparation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowClaimBoundaryPolicy {
    /// Boundary for Phase L artifacts.
    pub phase_l_artifact_boundary: ClaimBoundary,
    /// Maximum boundary retained for semantic fixture references.
    pub semantic_fixture_reference_boundary_max: ClaimBoundary,
    /// Whether Phase L may create Level2 actual evidence.
    pub allow_level2_in_phase_l: bool,
    /// Whether zkML metrics can elevate semantic evidence.
    pub prevent_zkml_metric_elevation: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkmlNarrowClaimBoundaryPolicy {
    fn default() -> Self {
        Self {
            phase_l_artifact_boundary: ClaimBoundary::Level0DesignNote,
            semantic_fixture_reference_boundary_max: ClaimBoundary::Level0DesignNote,
            allow_level2_in_phase_l: false,
            prevent_zkml_metric_elevation: true,
            notes: vec![
                "Narrow zkML workload plans are not benchmark results.".to_string(),
                "External execution is disabled by default.".to_string(),
            ],
        }
    }
}

/// Schema for future narrow zkML evidence mapping.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowEvidenceMapping {
    /// Evidence class emitted by Phase L planning.
    pub workload_plan_evidence_class: EvidenceClass,
    /// Current phase claim boundary.
    pub current_phase_claim_boundary: ClaimBoundary,
    /// Future external replay boundary after artifact validation.
    pub future_external_replay_boundary_after_validation: ClaimBoundary,
    /// Whether this workload plan emits evidence records.
    pub emits_evidence_records: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkmlNarrowEvidenceMapping {
    fn default() -> Self {
        Self {
            workload_plan_evidence_class: EvidenceClass::DesignNote,
            current_phase_claim_boundary: ClaimBoundary::Level0DesignNote,
            future_external_replay_boundary_after_validation:
                ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
            emits_evidence_records: false,
            notes: vec![
                "Workload plan generation is design metadata only.".to_string(),
                "No zkML benchmark result is created in Phase L.".to_string(),
            ],
        }
    }
}

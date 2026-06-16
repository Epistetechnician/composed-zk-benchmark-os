//! Narrow zkML adapter manifest schema.

use serde::{Deserialize, Serialize};

use crate::mutation::MutationClass;

use super::capabilities::{
    default_zkml_narrow_capability_declaration, ZkmlNarrowAdapterCapabilityDeclaration,
};
use super::evidence::{ZkmlNarrowClaimBoundaryPolicy, ZkmlNarrowEvidencePolicy};
use super::mapping::{default_zkml_narrow_fixture_scope, ZkmlNarrowUnsupportedFeature};

/// Narrow zkML adapter manifest id.
pub type ZkmlNarrowAdapterManifestId = String;

/// Narrow zkML adapter manifest version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowAdapterManifestVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ZkmlNarrowAdapterManifestVersion {
    fn default() -> Self {
        Self {
            value: "phase-l-narrow-zkml-adapter-manifest-v0".to_string(),
        }
    }
}

/// Adapter status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkmlNarrowAdapterStatus {
    /// Design-only metadata.
    DesignOnly,
    /// Workload-planning only.
    WorkloadPlanningOnly,
    /// External execution disabled.
    ExternalExecutionDisabled,
    /// Future live adapter placeholder.
    FutureLiveAdapter,
}

/// Integration phase.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkmlNarrowIntegrationPhase {
    /// Phase L adapter preparation.
    AdapterPreparation,
    /// Workload planning phase.
    WorkloadPlanning,
    /// Future external execution phase.
    FutureLiveExecution,
}

/// Review status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkmlNarrowReviewStatus {
    /// Draft manifest.
    Draft,
    /// Ready for design review.
    ReadyForReview,
    /// Future verified status.
    FutureVerified,
}

/// Source policy for Phase L.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowSourcePolicy {
    /// External repo checkout allowed.
    pub external_repo_checkout_allowed: bool,
    /// External command execution allowed.
    pub external_command_execution_allowed: bool,
    /// External benchmark result import allowed.
    pub external_benchmark_result_import_allowed: bool,
    /// Future source verification required.
    pub future_source_verification_required: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkmlNarrowSourcePolicy {
    fn default() -> Self {
        Self {
            external_repo_checkout_allowed: false,
            external_command_execution_allowed: false,
            external_benchmark_result_import_allowed: false,
            future_source_verification_required: true,
            notes: vec![
                "Phase L does not clone external zkML benchmark repos.".to_string(),
                "Phase L does not execute external zkML commands.".to_string(),
                "Phase L does not import external benchmark data.".to_string(),
            ],
        }
    }
}

/// Schema assumption for Phase L.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowSchemaAssumption {
    /// Internal candidate mapping.
    pub internal_candidate_mapping: bool,
    /// Future schema verification required.
    pub future_verification_required: bool,
    /// Whether complete official zkML schema compatibility is claimed.
    pub official_schema_claimed: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkmlNarrowSchemaAssumption {
    fn default() -> Self {
        Self {
            internal_candidate_mapping: true,
            future_verification_required: true,
            official_schema_claimed: false,
            notes: vec![
                "Candidate mapping only; not an official zkML benchmark schema claim.".to_string(),
            ],
        }
    }
}

/// Conservative compatibility target.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowCompatibilityTarget {
    /// Target name.
    pub target_name: String,
    /// Target role.
    pub target_role: String,
    /// Compatibility level.
    pub compatibility_level: String,
    /// Complete compatibility claim.
    pub complete_compatibility_claimed: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkmlNarrowCompatibilityTarget {
    fn default() -> Self {
        Self {
            target_name: "narrow_zkml_workload".to_string(),
            target_role: "future mixed control-flow and zkML metrics lane".to_string(),
            compatibility_level: "candidate workload mapping only".to_string(),
            complete_compatibility_claimed: false,
            notes: vec![
                "Future source verification is required before live integration.".to_string(),
            ],
        }
    }
}

/// Adapter scope.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowAdapterScope {
    /// Supported semantic fixture ids.
    pub supported_semantic_fixture_ids: Vec<String>,
    /// Supported mutation classes for boundary and observation stress.
    pub supported_mutation_classes: Vec<MutationClass>,
    /// Unsupported features.
    #[serde(default)]
    pub unsupported_features: Vec<ZkmlNarrowUnsupportedFeature>,
}

impl Default for ZkmlNarrowAdapterScope {
    fn default() -> Self {
        let scope = default_zkml_narrow_fixture_scope();
        Self {
            supported_semantic_fixture_ids: vec![scope.machine_id.clone()],
            supported_mutation_classes: scope.supported_mutation_classes.clone(),
            unsupported_features: vec![
                ZkmlNarrowUnsupportedFeature::new(
                    "live_zkml_execution",
                    "external execution is disabled by default",
                ),
                ZkmlNarrowUnsupportedFeature::new(
                    "official_schema_compatibility",
                    "candidate mapping only until source verification",
                ),
                ZkmlNarrowUnsupportedFeature::new(
                    "metric_ingestion",
                    "metric mappings are schema-only in Phase L",
                ),
                ZkmlNarrowUnsupportedFeature::new(
                    "model_artifact_import",
                    "model artifacts remain pending in Phase L",
                ),
            ],
        }
    }
}

/// Narrow zkML adapter preparation manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowAdapterManifest {
    /// Manifest id.
    pub id: ZkmlNarrowAdapterManifestId,
    /// Manifest version.
    pub manifest_version: ZkmlNarrowAdapterManifestVersion,
    /// Adapter id.
    pub adapter_id: String,
    /// Adapter status.
    pub adapter_status: ZkmlNarrowAdapterStatus,
    /// Integration phase.
    pub integration_phase: ZkmlNarrowIntegrationPhase,
    /// Source policy.
    pub source_policy: ZkmlNarrowSourcePolicy,
    /// Schema assumption.
    pub schema_assumption: ZkmlNarrowSchemaAssumption,
    /// Compatibility target.
    pub compatibility_target: ZkmlNarrowCompatibilityTarget,
    /// Adapter scope.
    pub scope: ZkmlNarrowAdapterScope,
    /// Capability declaration.
    pub capability_declaration: ZkmlNarrowAdapterCapabilityDeclaration,
    /// Evidence policy.
    pub evidence_policy: ZkmlNarrowEvidencePolicy,
    /// Claim-boundary policy.
    pub claim_boundary_policy: ZkmlNarrowClaimBoundaryPolicy,
    /// Review status.
    pub review_status: ZkmlNarrowReviewStatus,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Build the conservative Phase L narrow zkML adapter manifest.
pub fn build_default_zkml_narrow_adapter_manifest() -> ZkmlNarrowAdapterManifest {
    ZkmlNarrowAdapterManifest {
        id: "zkml_narrow_adapter_manifest_phase_l".to_string(),
        manifest_version: ZkmlNarrowAdapterManifestVersion::default(),
        adapter_id: "zkml_narrow_workload_adapter_v0".to_string(),
        adapter_status: ZkmlNarrowAdapterStatus::WorkloadPlanningOnly,
        integration_phase: ZkmlNarrowIntegrationPhase::AdapterPreparation,
        source_policy: ZkmlNarrowSourcePolicy::default(),
        schema_assumption: ZkmlNarrowSchemaAssumption::default(),
        compatibility_target: ZkmlNarrowCompatibilityTarget::default(),
        scope: ZkmlNarrowAdapterScope::default(),
        capability_declaration: default_zkml_narrow_capability_declaration(),
        evidence_policy: ZkmlNarrowEvidencePolicy::default(),
        claim_boundary_policy: ZkmlNarrowClaimBoundaryPolicy::default(),
        review_status: ZkmlNarrowReviewStatus::Draft,
        notes: vec![
            "Narrow zkML workload plans are not benchmark results.".to_string(),
            "zkML metrics do not prove semantic soundness.".to_string(),
            "External execution is disabled by default.".to_string(),
        ],
    }
}

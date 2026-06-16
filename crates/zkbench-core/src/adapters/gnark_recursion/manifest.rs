//! gnark recursion adapter manifest schema.

use serde::{Deserialize, Serialize};

use crate::mutation::MutationClass;

use super::capabilities::{
    default_gnark_recursion_capability_declaration, GnarkRecursionAdapterCapabilityDeclaration,
};
use super::evidence::{GnarkRecursionClaimBoundaryPolicy, GnarkRecursionEvidencePolicy};
use super::mapping::{default_gnark_recursion_fixture_scope, GnarkRecursionUnsupportedFeature};

/// gnark recursion adapter manifest id.
pub type GnarkRecursionAdapterManifestId = String;

/// gnark recursion adapter manifest version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionAdapterManifestVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for GnarkRecursionAdapterManifestVersion {
    fn default() -> Self {
        Self {
            value: "phase-k-gnark-recursion-adapter-manifest-v0".to_string(),
        }
    }
}

/// Adapter status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GnarkRecursionAdapterStatus {
    /// Design-only metadata.
    DesignOnly,
    /// Envelope-planning only.
    EnvelopePlanningOnly,
    /// External execution disabled.
    ExternalExecutionDisabled,
    /// Future live adapter placeholder.
    FutureLiveAdapter,
}

/// Integration phase.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GnarkRecursionIntegrationPhase {
    /// Phase K adapter preparation.
    AdapterPreparation,
    /// Envelope planning phase.
    EnvelopePlanning,
    /// Future external execution phase.
    FutureLiveExecution,
}

/// Review status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GnarkRecursionReviewStatus {
    /// Draft manifest.
    Draft,
    /// Ready for design review.
    ReadyForReview,
    /// Future verified status.
    FutureVerified,
}

/// Source policy for Phase K.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionSourcePolicy {
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

impl Default for GnarkRecursionSourcePolicy {
    fn default() -> Self {
        Self {
            external_repo_checkout_allowed: false,
            external_command_execution_allowed: false,
            external_benchmark_result_import_allowed: false,
            future_source_verification_required: true,
            notes: vec![
                "Phase K does not clone gnark or Go dependencies.".to_string(),
                "Phase K does not execute external recursion commands.".to_string(),
                "Phase K does not import external benchmark data.".to_string(),
            ],
        }
    }
}

/// Schema assumption for Phase K.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionSchemaAssumption {
    /// Internal candidate mapping.
    pub internal_candidate_mapping: bool,
    /// Future schema verification required.
    pub future_verification_required: bool,
    /// Whether complete official gnark schema compatibility is claimed.
    pub official_schema_claimed: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for GnarkRecursionSchemaAssumption {
    fn default() -> Self {
        Self {
            internal_candidate_mapping: true,
            future_verification_required: true,
            official_schema_claimed: false,
            notes: vec!["Candidate mapping only; not an official gnark schema claim.".to_string()],
        }
    }
}

/// Conservative compatibility target.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionCompatibilityTarget {
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

impl Default for GnarkRecursionCompatibilityTarget {
    fn default() -> Self {
        Self {
            target_name: "gnark".to_string(),
            target_role: "future recursion-envelope lane".to_string(),
            compatibility_level: "candidate envelope mapping only".to_string(),
            complete_compatibility_claimed: false,
            notes: vec![
                "Future source verification is required before live integration.".to_string(),
            ],
        }
    }
}

/// Adapter scope.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionAdapterScope {
    /// Supported semantic fixture ids.
    pub supported_semantic_fixture_ids: Vec<String>,
    /// Supported mutation classes for recursion envelope stress.
    pub supported_mutation_classes: Vec<MutationClass>,
    /// Unsupported features.
    #[serde(default)]
    pub unsupported_features: Vec<GnarkRecursionUnsupportedFeature>,
}

impl Default for GnarkRecursionAdapterScope {
    fn default() -> Self {
        let scope = default_gnark_recursion_fixture_scope();
        Self {
            supported_semantic_fixture_ids: vec![scope.machine_id.clone()],
            supported_mutation_classes: vec![MutationClass::RecursionEnvelopeMismatch],
            unsupported_features: vec![
                GnarkRecursionUnsupportedFeature::new(
                    "live_gnark_execution",
                    "external execution is disabled by default",
                ),
                GnarkRecursionUnsupportedFeature::new(
                    "official_schema_compatibility",
                    "candidate mapping only until source verification",
                ),
                GnarkRecursionUnsupportedFeature::new(
                    "metric_ingestion",
                    "metric mappings are schema-only in Phase K",
                ),
            ],
        }
    }
}

/// gnark recursion adapter preparation manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionAdapterManifest {
    /// Manifest id.
    pub id: GnarkRecursionAdapterManifestId,
    /// Manifest version.
    pub manifest_version: GnarkRecursionAdapterManifestVersion,
    /// Adapter id.
    pub adapter_id: String,
    /// Adapter status.
    pub adapter_status: GnarkRecursionAdapterStatus,
    /// Integration phase.
    pub integration_phase: GnarkRecursionIntegrationPhase,
    /// Source policy.
    pub source_policy: GnarkRecursionSourcePolicy,
    /// Schema assumption.
    pub schema_assumption: GnarkRecursionSchemaAssumption,
    /// Compatibility target.
    pub compatibility_target: GnarkRecursionCompatibilityTarget,
    /// Adapter scope.
    pub scope: GnarkRecursionAdapterScope,
    /// Capability declaration.
    pub capability_declaration: GnarkRecursionAdapterCapabilityDeclaration,
    /// Evidence policy.
    pub evidence_policy: GnarkRecursionEvidencePolicy,
    /// Claim-boundary policy.
    pub claim_boundary_policy: GnarkRecursionClaimBoundaryPolicy,
    /// Review status.
    pub review_status: GnarkRecursionReviewStatus,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Build the conservative Phase K gnark recursion adapter manifest.
pub fn build_default_gnark_recursion_adapter_manifest() -> GnarkRecursionAdapterManifest {
    GnarkRecursionAdapterManifest {
        id: "gnark_recursion_adapter_manifest_phase_k".to_string(),
        manifest_version: GnarkRecursionAdapterManifestVersion::default(),
        adapter_id: "gnark_recursion_envelope_adapter_v0".to_string(),
        adapter_status: GnarkRecursionAdapterStatus::EnvelopePlanningOnly,
        integration_phase: GnarkRecursionIntegrationPhase::AdapterPreparation,
        source_policy: GnarkRecursionSourcePolicy::default(),
        schema_assumption: GnarkRecursionSchemaAssumption::default(),
        compatibility_target: GnarkRecursionCompatibilityTarget::default(),
        scope: GnarkRecursionAdapterScope::default(),
        capability_declaration: default_gnark_recursion_capability_declaration(),
        evidence_policy: GnarkRecursionEvidencePolicy::default(),
        claim_boundary_policy: GnarkRecursionClaimBoundaryPolicy::default(),
        review_status: GnarkRecursionReviewStatus::Draft,
        notes: vec![
            "gnark recursion envelope plans are not benchmark results.".to_string(),
            "Recursion proof is not semantic proof.".to_string(),
            "External execution is disabled by default.".to_string(),
        ],
    }
}

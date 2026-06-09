//! zk-Harness adapter manifest schema.

use serde::{Deserialize, Serialize};

use crate::evidence::ArtifactKind;
use crate::generator::FamilyKind;
use crate::mutation::MutationClass;

use super::capabilities::{
    default_zk_harness_capability_declaration, ZkHarnessAdapterCapabilityDeclaration,
};
use super::evidence::{ZkHarnessClaimBoundaryPolicy, ZkHarnessEvidencePolicy};
use super::mapping::ZkHarnessUnsupportedFeature;

/// zk-Harness adapter manifest id.
pub type ZkHarnessAdapterManifestId = String;

/// zk-Harness adapter manifest version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessAdapterManifestVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ZkHarnessAdapterManifestVersion {
    fn default() -> Self {
        Self {
            value: "phase-g-zk-harness-adapter-manifest-v0".to_string(),
        }
    }
}

/// Adapter status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkHarnessAdapterStatus {
    /// Design-only metadata.
    DesignOnly,
    /// Dry-run planning only.
    DryRunOnly,
    /// External execution disabled.
    ExternalExecutionDisabled,
    /// Future live adapter placeholder.
    FutureLiveAdapter,
}

/// Integration phase.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkHarnessIntegrationPhase {
    /// Phase G adapter preparation.
    AdapterPreparation,
    /// Dry-run planning phase.
    DryRunPlanning,
    /// Future external execution phase.
    FutureLiveExecution,
}

/// Review status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkHarnessReviewStatus {
    /// Draft manifest.
    Draft,
    /// Ready for design review.
    ReadyForReview,
    /// Future verified status.
    FutureVerified,
}

/// Source policy for Phase G.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessSourcePolicy {
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

impl Default for ZkHarnessSourcePolicy {
    fn default() -> Self {
        Self {
            external_repo_checkout_allowed: false,
            external_command_execution_allowed: false,
            external_benchmark_result_import_allowed: false,
            future_source_verification_required: true,
            notes: vec![
                "Phase G does not clone zk-Harness.".to_string(),
                "Phase G does not execute external benchmark commands.".to_string(),
                "Phase G does not import external benchmark data.".to_string(),
            ],
        }
    }
}

/// Schema assumption for Phase G.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessSchemaAssumption {
    /// Internal candidate mapping.
    pub internal_candidate_mapping: bool,
    /// Future schema verification required.
    pub future_verification_required: bool,
    /// Whether complete official schema compatibility is claimed.
    pub official_schema_claimed: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ZkHarnessSchemaAssumption {
    fn default() -> Self {
        Self {
            internal_candidate_mapping: true,
            future_verification_required: true,
            official_schema_claimed: false,
            notes: vec![
                "Candidate mapping only; not an official zk-Harness schema claim.".to_string(),
            ],
        }
    }
}

/// Conservative compatibility target.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessCompatibilityTarget {
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

impl Default for ZkHarnessCompatibilityTarget {
    fn default() -> Self {
        Self {
            target_name: "zk-Harness".to_string(),
            target_role: "future benchmark runner".to_string(),
            compatibility_level: "candidate dry-run mapping only".to_string(),
            complete_compatibility_claimed: false,
            notes: vec![
                "Future source verification is required before live integration.".to_string(),
            ],
        }
    }
}

/// Adapter scope.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessAdapterScope {
    /// Supported local family kinds.
    pub supported_local_family_kinds: Vec<FamilyKind>,
    /// Supported mutation classes for candidate negative tests.
    pub supported_mutation_classes: Vec<MutationClass>,
    /// Supported local artifact kinds.
    pub supported_local_artifact_kinds: Vec<ArtifactKind>,
    /// Unsupported features.
    #[serde(default)]
    pub unsupported_features: Vec<ZkHarnessUnsupportedFeature>,
}

impl Default for ZkHarnessAdapterScope {
    fn default() -> Self {
        Self {
            supported_local_family_kinds: vec![
                FamilyKind::BaselineFsm,
                FamilyKind::BranchingFsm,
                FamilyKind::BoundedCounterLoop,
            ],
            supported_mutation_classes: vec![
                MutationClass::MissingConstraints,
                MutationClass::CorruptedGuards,
                MutationClass::BadCounters,
            ],
            supported_local_artifact_kinds: vec![
                ArtifactKind::GeneratedInstance,
                ArtifactKind::MutatedInstance,
                ArtifactKind::ReplayManifest,
                ArtifactKind::ReplayResult,
                ArtifactKind::EvidenceLedger,
                ArtifactKind::BenchmarkPackManifest,
                ArtifactKind::ScoreReport,
            ],
            unsupported_features: vec![
                ZkHarnessUnsupportedFeature::new(
                    "live_zk_harness_execution",
                    "external execution is disabled by default",
                ),
                ZkHarnessUnsupportedFeature::new(
                    "official_schema_compatibility",
                    "candidate mapping only until source verification",
                ),
                ZkHarnessUnsupportedFeature::new(
                    "metric_ingestion",
                    "metric mappings are schema-only in Phase G",
                ),
            ],
        }
    }
}

/// zk-Harness adapter preparation manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessAdapterManifest {
    /// Manifest id.
    pub id: ZkHarnessAdapterManifestId,
    /// Manifest version.
    pub manifest_version: ZkHarnessAdapterManifestVersion,
    /// Adapter id.
    pub adapter_id: String,
    /// Adapter status.
    pub adapter_status: ZkHarnessAdapterStatus,
    /// Integration phase.
    pub integration_phase: ZkHarnessIntegrationPhase,
    /// Source policy.
    pub source_policy: ZkHarnessSourcePolicy,
    /// Schema assumption.
    pub schema_assumption: ZkHarnessSchemaAssumption,
    /// Compatibility target.
    pub compatibility_target: ZkHarnessCompatibilityTarget,
    /// Adapter scope.
    pub scope: ZkHarnessAdapterScope,
    /// Capability declaration.
    pub capability_declaration: ZkHarnessAdapterCapabilityDeclaration,
    /// Evidence policy.
    pub evidence_policy: ZkHarnessEvidencePolicy,
    /// Claim-boundary policy.
    pub claim_boundary_policy: ZkHarnessClaimBoundaryPolicy,
    /// Review status.
    pub review_status: ZkHarnessReviewStatus,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ZkHarnessAdapterManifest {
    /// Build the conservative Phase G default manifest.
    pub fn phase_g_default() -> Self {
        build_default_zk_harness_adapter_manifest()
    }
}

/// Build the conservative Phase G zk-Harness adapter manifest.
pub fn build_default_zk_harness_adapter_manifest() -> ZkHarnessAdapterManifest {
    ZkHarnessAdapterManifest {
        id: "zk_harness_adapter_manifest_phase_g".to_string(),
        manifest_version: ZkHarnessAdapterManifestVersion::default(),
        adapter_id: "zk_harness_dry_run_adapter_v0".to_string(),
        adapter_status: ZkHarnessAdapterStatus::DryRunOnly,
        integration_phase: ZkHarnessIntegrationPhase::AdapterPreparation,
        source_policy: ZkHarnessSourcePolicy::default(),
        schema_assumption: ZkHarnessSchemaAssumption::default(),
        compatibility_target: ZkHarnessCompatibilityTarget::default(),
        scope: ZkHarnessAdapterScope::default(),
        capability_declaration: default_zk_harness_capability_declaration(),
        evidence_policy: ZkHarnessEvidencePolicy::default(),
        claim_boundary_policy: ZkHarnessClaimBoundaryPolicy::default(),
        review_status: ZkHarnessReviewStatus::Draft,
        notes: vec![
            "zk-Harness dry-run plans are not benchmark results.".to_string(),
            "External execution is disabled by default.".to_string(),
            "No performance claim is created by this manifest.".to_string(),
        ],
    }
}

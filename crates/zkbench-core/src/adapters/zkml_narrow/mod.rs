//! Narrow zkML adapter preparation.
//!
//! Phase L is inert manifest and workload-planning only. It does not invoke
//! external zkML tooling, import model artifacts, or produce benchmark evidence.

use serde::{Deserialize, Serialize};

pub mod capabilities;
pub mod evidence;
pub mod export;
pub mod manifest;
pub mod mapping;
pub mod validation;
pub mod workload;

pub use capabilities::{
    default_zkml_narrow_capability_declaration, zkml_narrow_capabilities,
    ZkmlNarrowAdapterCapabilityDeclaration,
};
pub use evidence::{
    ZkmlNarrowClaimBoundaryPolicy, ZkmlNarrowEvidenceMapping, ZkmlNarrowEvidencePolicy,
};
pub use export::{
    build_zkml_narrow_workload_plan, build_zkml_narrow_workload_plan_from_manifest,
    deserialize_zkml_narrow_manifest_json, deserialize_zkml_narrow_workload_plan_json,
    serialize_zkml_narrow_manifest_json, serialize_zkml_narrow_workload_plan_json,
};
pub use manifest::{
    build_default_zkml_narrow_adapter_manifest, ZkmlNarrowAdapterManifest,
    ZkmlNarrowAdapterManifestId, ZkmlNarrowAdapterManifestVersion, ZkmlNarrowAdapterScope,
    ZkmlNarrowAdapterStatus, ZkmlNarrowCompatibilityTarget, ZkmlNarrowIntegrationPhase,
    ZkmlNarrowReviewStatus, ZkmlNarrowSchemaAssumption, ZkmlNarrowSourcePolicy,
};
pub use mapping::{
    default_zkml_narrow_fixture_scope, ZkmlNarrowFixtureRef, ZkmlNarrowUnsupportedFeature,
    ZkmlNarrowWorkloadScope,
};
pub use validation::{
    validate_zkml_narrow_workload_plan, ZkmlNarrowWorkloadValidation,
    ZkmlNarrowWorkloadValidationIssue,
};
pub use workload::{
    build_default_zkml_narrow_workload_plan, ZkmlNarrowExecutionPolicy, ZkmlNarrowPlannedCommand,
    ZkmlNarrowToolRef, ZkmlNarrowWorkloadPlan, ZkmlNarrowWorkloadPlanId,
    ZkmlNarrowWorkloadPlanVersion, ZkmlNarrowWorkloadStep, ZkmlNarrowWorkloadStepKind,
};

/// Registry entry for the Phase L narrow zkML adapter preparation layer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowAdapterRegistryEntry {
    /// Registry id.
    pub id: String,
    /// Adapter manifest id.
    pub adapter_manifest_id: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Registry entry for a narrow zkML workload plan schema.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowWorkloadPlanRegistryEntry {
    /// Registry id.
    pub id: String,
    /// Plan version.
    pub plan_version: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

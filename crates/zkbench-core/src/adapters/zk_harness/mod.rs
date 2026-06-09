//! zk-Harness adapter preparation.
//!
//! Phase G is dry-run only. It produces reviewable adapter manifests and inert
//! planned command data. It does not clone zk-Harness, invoke external tools,
//! ingest external benchmark data, or produce official benchmark evidence.

use serde::{Deserialize, Serialize};

pub mod capabilities;
pub mod dry_run;
pub mod evidence;
pub mod export;
pub mod handoff;
pub mod manifest;
pub mod mapping;
pub mod metrics;
pub mod validation;

pub use capabilities::{
    default_zk_harness_capability_declaration, zk_harness_dry_run_capabilities,
    ZkHarnessAdapterCapabilityDeclaration,
};
pub use dry_run::{
    ZkHarnessCommandArgument, ZkHarnessCommandArtifact, ZkHarnessCommandEnvironment,
    ZkHarnessDryRunPlan, ZkHarnessDryRunPlanId, ZkHarnessDryRunPlanVersion, ZkHarnessDryRunPlanner,
    ZkHarnessExecutionPolicy, ZkHarnessExternalToolRef, ZkHarnessPlanStep, ZkHarnessPlanStepKind,
    ZkHarnessPlanSubject, ZkHarnessPlannedCommand,
};
pub use evidence::{
    ZkHarnessClaimBoundaryPolicy, ZkHarnessEvidenceMapping, ZkHarnessEvidencePolicy,
};
pub use export::{
    build_zk_harness_dry_run_plan_from_pack, deserialize_zk_harness_dry_run_plan_json,
    deserialize_zk_harness_manifest_json, export_pack_to_zk_harness_dry_run_plan,
    serialize_zk_harness_dry_run_plan_json, serialize_zk_harness_manifest_json,
};
pub use handoff::{
    build_manual_handoff_bundle_from_zk_harness_plan, build_zk_harness_manual_handoff_bundle,
    default_zk_harness_future_execution_prerequisites, ZkHarnessArtifactExpectation,
    ZkHarnessFutureExecutionPrerequisite, ZkHarnessManualHandoffBundle,
    ZkHarnessManualHandoffMapping, ZkHarnessResultImportExpectation,
};
pub use manifest::{
    build_default_zk_harness_adapter_manifest, ZkHarnessAdapterManifest,
    ZkHarnessAdapterManifestId, ZkHarnessAdapterManifestVersion, ZkHarnessAdapterScope,
    ZkHarnessAdapterStatus, ZkHarnessCompatibilityTarget, ZkHarnessIntegrationPhase,
    ZkHarnessReviewStatus, ZkHarnessSchemaAssumption, ZkHarnessSourcePolicy,
};
pub use mapping::{
    ZkHarnessArtifactMapping, ZkHarnessExpectedOutcomeMapping, ZkHarnessFamilyMapping,
    ZkHarnessMappingWarning, ZkHarnessMutationMapping, ZkHarnessPackExportManifest,
    ZkHarnessPackMapping, ZkHarnessTraceMapping, ZkHarnessUnsupportedFeature,
};
pub use metrics::{ZkHarnessMetricKind, ZkHarnessMetricMapping};
pub use validation::{
    validate_zk_harness_dry_run_plan, ZkHarnessDryRunValidation, ZkHarnessDryRunValidationIssue,
};

/// Registry entry for the Phase G zk-Harness dry-run adapter preparation layer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessAdapterRegistryEntry {
    /// Registry id.
    pub id: String,
    /// Adapter manifest id.
    pub adapter_manifest_id: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Registry entry for a dry-run plan schema.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessDryRunPlanRegistryEntry {
    /// Registry id.
    pub id: String,
    /// Plan version.
    pub plan_version: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

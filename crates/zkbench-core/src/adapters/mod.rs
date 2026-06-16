//! Backend adapter traits and capability declarations.
//!
//! This module intentionally defines contracts only. It does not implement any
//! external adapters and does not shell out to benchmark or proof systems.

pub mod gnark_recursion;
pub mod local_json;
pub mod zk_harness;
pub mod zkml_narrow;

use serde::{Deserialize, Serialize};

use crate::dsl::SemanticIr;
use crate::error::Result;
use crate::evidence::EvidenceRecord;
use crate::generator::BenchmarkInstance;
use crate::replay::{ReplayManifest, ReplayResult};

pub use gnark_recursion::{
    build_default_gnark_recursion_adapter_manifest, build_gnark_recursion_envelope_plan,
    build_gnark_recursion_envelope_plan_from_manifest,
    default_gnark_recursion_capability_declaration, deserialize_gnark_recursion_envelope_plan_json,
    deserialize_gnark_recursion_manifest_json, gnark_recursion_capabilities,
    serialize_gnark_recursion_envelope_plan_json, serialize_gnark_recursion_manifest_json,
    validate_gnark_recursion_envelope_plan, GnarkRecursionAdapterCapabilityDeclaration,
    GnarkRecursionAdapterManifest, GnarkRecursionAdapterManifestId,
    GnarkRecursionAdapterManifestVersion, GnarkRecursionAdapterRegistryEntry,
    GnarkRecursionAdapterScope, GnarkRecursionAdapterStatus, GnarkRecursionClaimBoundaryPolicy,
    GnarkRecursionCompatibilityTarget, GnarkRecursionEnvelopePlan, GnarkRecursionEnvelopePlanId,
    GnarkRecursionEnvelopePlanRegistryEntry, GnarkRecursionEnvelopePlanVersion,
    GnarkRecursionEnvelopeScope, GnarkRecursionEnvelopeStep, GnarkRecursionEnvelopeStepKind,
    GnarkRecursionEnvelopeValidation, GnarkRecursionEnvelopeValidationIssue,
    GnarkRecursionEvidenceMapping, GnarkRecursionEvidencePolicy, GnarkRecursionExecutionPolicy,
    GnarkRecursionFixtureRef, GnarkRecursionIntegrationPhase, GnarkRecursionPlannedCommand,
    GnarkRecursionReviewStatus, GnarkRecursionSchemaAssumption, GnarkRecursionSourcePolicy,
    GnarkRecursionToolRef, GnarkRecursionUnsupportedFeature,
};
pub use local_json::{
    local_json_capabilities, LocalJsonAdapter, LocalJsonAdapterConfig, LocalJsonReplayInput,
    LocalJsonReplayOutput, LocalJsonReplaySummary, LOCAL_JSON_ADAPTER_ID,
};
pub use zk_harness::{
    build_default_zk_harness_adapter_manifest, build_manual_handoff_bundle_from_zk_harness_plan,
    build_zk_harness_dry_run_plan_from_pack, build_zk_harness_manual_handoff_bundle,
    default_zk_harness_capability_declaration, default_zk_harness_future_execution_prerequisites,
    deserialize_zk_harness_dry_run_plan_json, deserialize_zk_harness_manifest_json,
    export_pack_to_zk_harness_dry_run_plan, serialize_zk_harness_dry_run_plan_json,
    serialize_zk_harness_manifest_json, validate_zk_harness_dry_run_plan,
    zk_harness_dry_run_capabilities, ZkHarnessAdapterCapabilityDeclaration,
    ZkHarnessAdapterManifest, ZkHarnessAdapterManifestId, ZkHarnessAdapterManifestVersion,
    ZkHarnessAdapterRegistryEntry, ZkHarnessAdapterScope, ZkHarnessAdapterStatus,
    ZkHarnessArtifactExpectation, ZkHarnessArtifactMapping, ZkHarnessClaimBoundaryPolicy,
    ZkHarnessCommandArgument, ZkHarnessCommandArtifact, ZkHarnessCommandEnvironment,
    ZkHarnessCompatibilityTarget, ZkHarnessDryRunPlan, ZkHarnessDryRunPlanId,
    ZkHarnessDryRunPlanRegistryEntry, ZkHarnessDryRunPlanVersion, ZkHarnessDryRunPlanner,
    ZkHarnessDryRunValidation, ZkHarnessDryRunValidationIssue, ZkHarnessEvidenceMapping,
    ZkHarnessEvidencePolicy, ZkHarnessExecutionPolicy, ZkHarnessExpectedOutcomeMapping,
    ZkHarnessExternalToolRef, ZkHarnessFamilyMapping, ZkHarnessFutureExecutionPrerequisite,
    ZkHarnessIntegrationPhase, ZkHarnessManualHandoffBundle, ZkHarnessManualHandoffMapping,
    ZkHarnessMappingWarning, ZkHarnessMetricKind, ZkHarnessMetricMapping, ZkHarnessMutationMapping,
    ZkHarnessPackExportManifest, ZkHarnessPackMapping, ZkHarnessPlanStep, ZkHarnessPlanStepKind,
    ZkHarnessPlanSubject, ZkHarnessPlannedCommand, ZkHarnessResultImportExpectation,
    ZkHarnessReviewStatus, ZkHarnessSchemaAssumption, ZkHarnessSourcePolicy, ZkHarnessTraceMapping,
    ZkHarnessUnsupportedFeature,
};
pub use zkml_narrow::{
    build_default_zkml_narrow_adapter_manifest, build_zkml_narrow_workload_plan,
    build_zkml_narrow_workload_plan_from_manifest, default_zkml_narrow_capability_declaration,
    deserialize_zkml_narrow_manifest_json, deserialize_zkml_narrow_workload_plan_json,
    serialize_zkml_narrow_manifest_json, serialize_zkml_narrow_workload_plan_json,
    validate_zkml_narrow_workload_plan, zkml_narrow_capabilities,
    ZkmlNarrowAdapterCapabilityDeclaration, ZkmlNarrowAdapterManifest, ZkmlNarrowAdapterManifestId,
    ZkmlNarrowAdapterManifestVersion, ZkmlNarrowAdapterRegistryEntry, ZkmlNarrowAdapterScope,
    ZkmlNarrowAdapterStatus, ZkmlNarrowClaimBoundaryPolicy, ZkmlNarrowCompatibilityTarget,
    ZkmlNarrowEvidenceMapping, ZkmlNarrowEvidencePolicy, ZkmlNarrowExecutionPolicy,
    ZkmlNarrowFixtureRef, ZkmlNarrowIntegrationPhase, ZkmlNarrowPlannedCommand,
    ZkmlNarrowReviewStatus, ZkmlNarrowSchemaAssumption, ZkmlNarrowSourcePolicy, ZkmlNarrowToolRef,
    ZkmlNarrowUnsupportedFeature, ZkmlNarrowWorkloadPlan, ZkmlNarrowWorkloadPlanId,
    ZkmlNarrowWorkloadPlanRegistryEntry, ZkmlNarrowWorkloadPlanVersion, ZkmlNarrowWorkloadScope,
    ZkmlNarrowWorkloadStep, ZkmlNarrowWorkloadStepKind, ZkmlNarrowWorkloadValidation,
    ZkmlNarrowWorkloadValidationIssue,
};

/// Backend target metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BackendTarget {
    /// Target id.
    pub id: String,
    /// Target kind, for example `local_oracle` or a future backend family.
    pub kind: String,
    /// Optional target version.
    #[serde(default)]
    pub version: Option<String>,
    /// Declared capabilities.
    #[serde(default)]
    pub capabilities: AdapterCapabilitySet,
}

/// Adapter capability flags. These are descriptive flags, not evidence claims.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct AdapterCapabilitySet {
    /// Supports execution.
    #[serde(default)]
    pub supports_execution: bool,
    /// Supports proving.
    #[serde(default)]
    pub supports_proving: bool,
    /// Supports verification timing.
    #[serde(default)]
    pub supports_verification_timing: bool,
    /// Supports negative tests.
    #[serde(default)]
    pub supports_negative_tests: bool,
    /// Supports trace export.
    #[serde(default)]
    pub supports_trace_export: bool,
    /// Supports constraint count.
    #[serde(default)]
    pub supports_constraint_count: bool,
    /// Supports formal semantics.
    #[serde(default)]
    pub supports_formal_semantics: bool,
    /// Supports machine-checked proof.
    #[serde(default)]
    pub supports_machine_checked_proof: bool,
    /// Supports recursion.
    #[serde(default)]
    pub supports_recursion: bool,
    /// Supports zkML metrics.
    #[serde(default)]
    pub supports_zkml_metrics: bool,
    /// Supports replay manifest.
    #[serde(default)]
    pub supports_replay_manifest: bool,
    /// Supports artifact hashing.
    #[serde(default)]
    pub supports_artifact_hashing: bool,
    /// Supports public/private boundary checks.
    #[serde(default)]
    pub supports_public_private_boundary_checks: bool,
}

/// Backend adapter contract for future phases.
pub trait BackendAdapter {
    /// Backend target metadata.
    fn target(&self) -> BackendTarget;

    /// Capabilities advertised by this adapter.
    fn capabilities(&self) -> AdapterCapabilitySet {
        self.target().capabilities
    }

    /// Prepare a replay manifest for an instance. Future adapters implement
    /// this without changing Semantic IR semantics.
    fn prepare_replay(
        &self,
        ir: &SemanticIr,
        instance: &BenchmarkInstance,
    ) -> Result<ReplayManifest>;

    /// Normalize a replay result into an Evidence Record.
    fn normalize_result(&self, result: &ReplayResult) -> Result<EvidenceRecord>;
}

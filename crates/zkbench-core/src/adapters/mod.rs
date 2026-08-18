//! Backend adapter traits and capability declarations.
//!
//! This module intentionally defines contracts only. It does not implement any
//! external adapters and does not shell out to benchmark or proof systems.

pub mod local_json;
pub mod metacognitive_monitor_control;
pub mod opaque_trace_replay;
pub mod zk_harness;

use serde::{Deserialize, Serialize};

use crate::dsl::SemanticIr;
use crate::error::Result;
use crate::evidence::EvidenceRecord;
use crate::generator::BenchmarkInstance;
use crate::replay::{ReplayManifest, ReplayResult};

pub use local_json::{
    local_json_capabilities, LocalJsonAdapter, LocalJsonAdapterConfig, LocalJsonReplayInput,
    LocalJsonReplayOutput, LocalJsonReplaySummary, LOCAL_JSON_ADAPTER_ID,
};
pub use metacognitive_monitor_control::{
    build_metacognitive_monitor_control_case, expected_metacognitive_monitor_control_verdict,
    validate_metacognitive_monitor_control_candidate,
    validate_metacognitive_monitor_control_result, MetacognitiveConfidenceMethod,
    MetacognitiveControlAction, MetacognitiveMonitorControlCandidate,
    MetacognitiveMonitorControlCase, MetacognitiveMonitorControlObservation,
    MetacognitiveMonitorControlResult, MetacognitiveMonitorControlValidation,
    MetacognitiveMonitorControlValidationIssue, MetacognitiveMonitorControlValidationIssueKind,
    MetacognitiveMonitorControlVariant, MetacognitiveSignalSource, MetacognitiveSplit,
    METACOGNITIVE_MAX_CONFIDENCE_MILLI, METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY,
    METACOGNITIVE_MONITOR_CONTROL_FAMILY_ID, METACOGNITIVE_MONITOR_CONTROL_SCHEMA_VERSION,
};
pub use opaque_trace_replay::{
    build_opaque_trace_replay_case, expected_opaque_trace_replay_quarantine_status,
    expected_opaque_trace_replay_verdict, validate_opaque_trace_replay_adapter_result,
    validate_opaque_trace_replay_candidate, OpaqueTraceReplayAdapterObservation,
    OpaqueTraceReplayAdapterResult, OpaqueTraceReplayBoundary, OpaqueTraceReplayCandidate,
    OpaqueTraceReplayCase, OpaqueTraceReplayContextBinding, OpaqueTraceReplayMutationProvenance,
    OpaqueTraceReplayValidation, OpaqueTraceReplayValidationIssue,
    OpaqueTraceReplayValidationIssueKind, OpaqueTraceReplayVariant,
    OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY, OPAQUE_TRACE_REPLAY_FAMILY_ID,
    OPAQUE_TRACE_REPLAY_SCHEMA_VERSION,
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

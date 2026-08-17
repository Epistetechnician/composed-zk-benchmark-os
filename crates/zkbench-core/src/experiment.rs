//! Versioned experiment bundles and static plugin seams.
//!
//! State slice: `benchmark-os-experiment-bundle-plugin-contract-v1`.
//!
//! This module composes the existing local generator, replay, provenance, and
//! report primitives into one deterministic experiment lifecycle. The plugin
//! seams are deliberately in-process and static: they do not discover dynamic
//! libraries, execute processes, access the network, or promote evidence.
//!
//! Extension state slice: `benchmark-os-static-plugin-registry-dispatch-v1`.
//! Integrity extension: `benchmark-os-experiment-bundle-integrity-v1`.
//! Output-binding extension: `benchmark-os-plugin-output-binding-v1`.
//! Validated-output extension: `benchmark-os-validated-plugin-output-value-v1`.
//! Factory-catalog extension: `benchmark-os-experiment-plugin-factory-catalog-v1`.
//! Artifact-access extension: `benchmark-os-experiment-bundle-artifact-access-v1`.
//! Registry separation extension: `benchmark-os-plugin-registry-descriptor-only-separation-v1`.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::adapters::LocalJsonAdapter;
use crate::dsl::OracleOutcome;
use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    canonical_json_bytes, compute_artifact_digest, compute_artifact_digest_bytes, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
};
use crate::generator::{
    generate_instance, GeneratedBenchmarkInstance, GeneratorConfig, InstanceParams,
};
use crate::replay::{build_local_replay_manifest_for_instance, ReplayManifest, ReplayResult};

/// Experiment bundle schema version.
pub const EXPERIMENT_BUNDLE_SCHEMA_VERSION: &str = "benchmark-os-experiment-bundle-v1";

/// Static local JSON plugin id.
pub const LOCAL_JSON_EXPERIMENT_PLUGIN_ID: &str = "local-json-experiment-plugin-v1";

/// Claim ceiling for the local experiment bundle slice.
pub const EXPERIMENT_BUNDLE_CLAIM_BOUNDARY: ClaimBoundary = ClaimBoundary::Level1LocalReplay;

/// Experiment bundle schema version wrapper.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentBundleVersion {
    /// Logical schema version.
    pub value: String,
}

impl Default for ExperimentBundleVersion {
    fn default() -> Self {
        Self {
            value: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
        }
    }
}

/// Experiment lifecycle status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExperimentLifecycle {
    /// The task was prepared, executed, evaluated, and packaged.
    Completed,
}

/// Stable task-plugin descriptor.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentTaskDescriptor {
    /// Stable task id.
    pub task_id: String,
    /// Task implementation id.
    pub plugin_id: String,
    /// Human-readable description.
    pub description: String,
}

/// Configuration bytes carried by every experiment bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentConfig {
    /// Stable configuration id.
    pub config_id: String,
    /// Configuration schema version.
    pub schema_version: String,
    /// Plugin that owns the configuration.
    pub plugin_id: String,
    /// Deterministic JSON bytes represented as UTF-8 text.
    pub canonical_json: String,
    /// Digest over `canonical_json` bytes.
    pub digest: ArtifactDigest,
}

/// Versioned data identity carried by every experiment bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentDataVersion {
    /// Logical data/source id.
    pub source_id: String,
    /// Generator or source version.
    pub version: String,
    /// Digest over the exact data payload used by the task.
    pub digest: ArtifactDigest,
    /// Deterministic provenance marker.
    pub provenance: String,
}

/// Versioned model/runtime identity carried by every experiment bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentModelVersion {
    /// Logical model or adapter id.
    pub model_id: String,
    /// Model/runtime version.
    pub version: String,
    /// Runtime label.
    pub runtime: String,
    /// Digest over the model/runtime identity metadata.
    pub artifact_digest: ArtifactDigest,
}

/// Standardized measurement status used by metrics and mechanism records.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MeasurementStatus {
    /// A value was collected and is bound to a source artifact.
    Collected,
    /// The collector did not attempt this measurement.
    NotCollected,
    /// The selected model/runtime does not expose this measurement.
    Unsupported,
    /// Collection was attempted but failed.
    Failed,
}

/// Deterministic scalar values supported by the first bundle schema.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MeasurementValue {
    /// Non-negative count.
    Count(u64),
    /// Signed integer.
    Integer(i64),
    /// Ratio in basis points.
    RatioBasisPoints(u64),
    /// Boolean observation.
    Boolean(bool),
    /// Bounded textual label.
    Text(String),
    /// Digest or identity string.
    Digest(String),
}

/// Mechanism measurement category.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum MechanismMeasurementKind {
    /// Summary exposed by the local trace/replay seam.
    TraceOutcome,
    /// State-transition observation.
    StateTransition,
    /// Activation-level observation.
    Activation,
    /// Attention-level observation.
    Attention,
    /// Causal intervention/effect observation.
    CausalEffect,
    /// Future mechanism category.
    Other,
}

/// One entry in the standardized mechanism ledger.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MechanismMeasurement {
    /// Stable measurement id.
    pub measurement_id: String,
    /// Measurement category.
    pub kind: MechanismMeasurementKind,
    /// Collection status.
    pub status: MeasurementStatus,
    /// Optional value; absent when not collected, unsupported, or failed.
    #[serde(default)]
    pub value: Option<MeasurementValue>,
    /// Optional unit label.
    #[serde(default)]
    pub unit: Option<String>,
    /// Relative artifact URI supplying the measurement.
    #[serde(default)]
    pub source_artifact_uri: Option<String>,
    /// Required explanation for every non-collected status.
    #[serde(default)]
    pub reason: Option<String>,
}

/// Versioned mechanism ledger. Sparse entries are valid when absence is explicit.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MechanismLedger {
    /// Ledger schema version.
    pub schema_version: String,
    /// Collector implementation id.
    pub collector_id: String,
    /// Stable ordered measurement entries.
    pub measurements: Vec<MechanismMeasurement>,
    /// Maximum claim boundary for these measurements.
    pub claim_boundary: ClaimBoundary,
    /// Explicit collector notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Metric measurement category.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum MetricKind {
    /// Count of discrete observations.
    Count,
    /// Signed integer metric.
    Integer,
    /// Duration represented in milliseconds.
    DurationMillis,
    /// Ratio represented in basis points.
    RatioBasisPoints,
    /// Bounded status label.
    StatusLabel,
}

/// One standardized metric entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetricMeasurement {
    /// Stable metric id.
    pub metric_id: String,
    /// Metric category.
    pub kind: MetricKind,
    /// Collection status.
    pub status: MeasurementStatus,
    /// Optional value; absent when not collected, unsupported, or failed.
    #[serde(default)]
    pub value: Option<MeasurementValue>,
    /// Optional unit label.
    #[serde(default)]
    pub unit: Option<String>,
    /// Relative artifact URI supplying the metric.
    #[serde(default)]
    pub source_artifact_uri: Option<String>,
    /// Required explanation for every non-collected status.
    #[serde(default)]
    pub reason: Option<String>,
}

/// Versioned metrics report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentMetrics {
    /// Metrics schema version.
    pub schema_version: String,
    /// Evaluator implementation id.
    pub evaluator_id: String,
    /// Stable metric entries.
    pub measurements: Vec<MetricMeasurement>,
    /// Maximum claim boundary for these metrics.
    pub claim_boundary: ClaimBoundary,
    /// Explicit evaluator notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Human-readable report carried by every experiment bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentReport {
    /// Report schema version.
    pub schema_version: String,
    /// Human-readable title.
    pub title: String,
    /// Deterministic summary.
    pub summary: String,
    /// Maximum claim boundary for the report.
    pub claim_boundary: ClaimBoundary,
    /// Explicit non-claims.
    pub non_claims: Vec<String>,
    /// Additional report notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Artifact categories inside an experiment bundle.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ExperimentArtifactKind {
    /// Configuration payload.
    Config,
    /// Data-version record.
    DataVersion,
    /// Model-version record.
    ModelVersion,
    /// Mechanism ledger.
    MechanismLedger,
    /// Metrics report.
    Metrics,
    /// Human-readable report.
    Report,
    /// Replay manifest.
    ReplayManifest,
    /// Replay result.
    ReplayResult,
}

/// Digest-bound artifact reference inside an experiment bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentArtifactRef {
    /// Portable relative URI.
    pub uri: String,
    /// Artifact category.
    pub kind: ExperimentArtifactKind,
    /// Digest over the exact serialized payload.
    pub digest: ArtifactDigest,
    /// Whether the artifact is required for bundle completeness.
    pub required: bool,
}

/// Complete experiment artifact bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentBundle {
    /// Stable bundle id.
    pub bundle_id: String,
    /// Bundle schema version.
    pub schema_version: ExperimentBundleVersion,
    /// Lifecycle status.
    pub lifecycle: ExperimentLifecycle,
    /// Task configuration.
    pub config: ExperimentConfig,
    /// Data identity.
    pub data_version: ExperimentDataVersion,
    /// Model/runtime identity.
    pub model_version: ExperimentModelVersion,
    /// Mechanism ledger.
    pub mechanism_ledger: MechanismLedger,
    /// Metrics report.
    pub metrics: ExperimentMetrics,
    /// Human-readable report.
    pub report: ExperimentReport,
    /// All component artifact references.
    pub artifacts: Vec<ExperimentArtifactRef>,
    /// Bundle claim ceiling.
    pub claim_boundary: ClaimBoundary,
    /// Bundle-level non-claims.
    pub non_claims: Vec<String>,
}

impl ExperimentBundle {
    /// Return exactly one artifact of the requested kind.
    ///
    /// Composition Adapters must not select the first matching entry from a
    /// malformed bundle. This Interface owns missing-kind and duplicate-kind
    /// failure semantics while the aggregate bundle validator retains its
    /// complete diagnostic report.
    pub fn artifact(&self, kind: ExperimentArtifactKind) -> Result<&ExperimentArtifactRef> {
        let mut matches = self
            .artifacts
            .iter()
            .filter(|artifact| artifact.kind == kind);
        let artifact = matches.next().ok_or_else(|| {
            ZkBenchError::validation(
                "experiment_bundle.artifacts",
                format!("required artifact kind {kind:?} is missing"),
            )
        })?;
        if matches.next().is_some() {
            return Err(ZkBenchError::validation(
                "experiment_bundle.artifacts",
                format!("artifact kind {kind:?} is duplicated"),
            ));
        }
        Ok(artifact)
    }
}

/// Descriptor-bound experiment output that has passed complete bundle
/// validation.
///
/// This value is the typed handoff between a plugin seam and its consumers.
/// Callers do not need to rediscover descriptor identity, schema, artifact, or
/// claim-boundary checks after construction. The serialized bundle remains the
/// same `ExperimentBundle` wire value.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedExperimentPluginOutput {
    descriptor: ExperimentPluginDescriptor,
    bundle: ExperimentBundle,
}

impl ValidatedExperimentPluginOutput {
    /// Validate and bind one plugin descriptor to one emitted bundle.
    pub fn new(descriptor: ExperimentPluginDescriptor, bundle: ExperimentBundle) -> Result<Self> {
        validate_experiment_plugin_output(&descriptor, &bundle)?;
        Ok(Self { descriptor, bundle })
    }

    /// Return the descriptor that produced and validated the bundle.
    pub fn descriptor(&self) -> &ExperimentPluginDescriptor {
        &self.descriptor
    }

    /// Return the validated experiment bundle.
    pub fn bundle(&self) -> &ExperimentBundle {
        &self.bundle
    }

    /// Split the validated handoff into its descriptor and bundle values.
    pub fn into_parts(self) -> (ExperimentPluginDescriptor, ExperimentBundle) {
        (self.descriptor, self.bundle)
    }

    /// Return the bundle for compatibility callers that do not need the
    /// descriptor-bound handoff.
    pub fn into_bundle(self) -> ExperimentBundle {
        self.bundle
    }
}

/// Prepared task input shared by model, collector, and evaluator seams.
#[derive(Debug, Clone, PartialEq)]
pub struct ExperimentTaskInput {
    /// Task descriptor.
    pub descriptor: ExperimentTaskDescriptor,
    /// Frozen configuration.
    pub config: ExperimentConfig,
    /// Frozen data identity.
    pub data_version: ExperimentDataVersion,
    /// Generated Benchmark Instance used by this local slice.
    pub instance: GeneratedBenchmarkInstance,
}

/// Model execution output shared by collector and evaluator seams.
#[derive(Debug, Clone, PartialEq)]
pub struct ExperimentModelRun {
    /// Model/runtime identity used for execution.
    pub model_version: ExperimentModelVersion,
    /// Replay manifest emitted before local execution.
    pub replay_manifest: ReplayManifest,
    /// Local replay result.
    pub replay_result: ReplayResult,
    /// Replay artifacts available to downstream seams.
    pub artifacts: Vec<ExperimentArtifactRef>,
}

/// Evaluator output before bundle assembly.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExperimentEvaluation {
    /// Standardized metrics.
    pub metrics: ExperimentMetrics,
    /// Human-readable report.
    pub report: ExperimentReport,
}

/// Task seam for preparing a frozen experiment input.
pub trait ExperimentTask {
    /// Return stable task metadata.
    fn descriptor(&self) -> &ExperimentTaskDescriptor;

    /// Prepare deterministic configuration, data identity, and task payload.
    fn prepare(&self) -> Result<ExperimentTaskInput>;
}

/// Model/runtime seam for executing a prepared task.
pub trait ExperimentModel {
    /// Return the exact model/runtime identity.
    fn model_version(&self) -> &ExperimentModelVersion;

    /// Execute the model/runtime against the prepared input.
    fn execute(&self, input: &ExperimentTaskInput) -> Result<ExperimentModelRun>;
}

/// Mechanism-collection seam.
pub trait MechanismCollector {
    /// Return stable collector metadata.
    fn collector_id(&self) -> &str;

    /// Collect a sparse but explicit mechanism ledger.
    fn collect(
        &self,
        input: &ExperimentTaskInput,
        run: &ExperimentModelRun,
    ) -> Result<MechanismLedger>;
}

/// Evaluation seam.
pub trait Evaluator {
    /// Return stable evaluator metadata.
    fn evaluator_id(&self) -> &str;

    /// Evaluate the prepared input, model run, and mechanism ledger.
    fn evaluate(
        &self,
        input: &ExperimentTaskInput,
        run: &ExperimentModelRun,
        mechanisms: &MechanismLedger,
    ) -> Result<ExperimentEvaluation>;
}

/// Plugin descriptor used by the static registry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentPluginDescriptor {
    /// Stable plugin id.
    pub plugin_id: String,
    /// Plugin version.
    pub version: String,
    /// Task implementation id.
    pub task_id: String,
    /// Model implementation id.
    pub model_id: String,
    /// Mechanism collector id.
    pub collector_id: String,
    /// Evaluator id.
    pub evaluator_id: String,
    /// Maximum claim boundary emitted by the plugin.
    pub claim_boundary: ClaimBoundary,
}

impl ExperimentPluginDescriptor {
    /// Validate the stable identity and claim ceiling of one plugin descriptor.
    pub fn validate(&self, path: &str) -> Result<()> {
        for (field, value) in [
            ("plugin_id", &self.plugin_id),
            ("version", &self.version),
            ("task_id", &self.task_id),
            ("model_id", &self.model_id),
            ("collector_id", &self.collector_id),
            ("evaluator_id", &self.evaluator_id),
        ] {
            if value.trim().is_empty() {
                return Err(ZkBenchError::validation(
                    format!("{path}.{field}"),
                    "plugin descriptor value must not be empty",
                ));
            }
        }
        if self.claim_boundary > EXPERIMENT_BUNDLE_CLAIM_BOUNDARY {
            return Err(ZkBenchError::ClaimBoundary {
                message: format!(
                    "plugin {} exceeds {}",
                    self.plugin_id, EXPERIMENT_BUNDLE_CLAIM_BOUNDARY
                ),
            });
        }
        Ok(())
    }
}

/// Composition seam for one complete experiment plugin.
pub trait ExperimentPlugin: Send + Sync {
    /// Return plugin metadata.
    fn descriptor(&self) -> &ExperimentPluginDescriptor;

    /// Run the complete local lifecycle and emit one bundle.
    fn run(&self) -> Result<ExperimentBundle>;

    /// Run the lifecycle and return one descriptor-bound validated output.
    fn run_validated_output(&self) -> Result<ValidatedExperimentPluginOutput> {
        ValidatedExperimentPluginOutput::new(self.descriptor().clone(), self.run()?)
    }

    /// Run the lifecycle and fail closed if the output is not bound to the
    /// plugin descriptor that produced it.
    fn run_validated(&self) -> Result<ExperimentBundle> {
        Ok(self.run_validated_output()?.into_bundle())
    }
}

/// Validate the descriptor-to-bundle binding for one plugin output.
pub fn validate_experiment_plugin_output(
    descriptor: &ExperimentPluginDescriptor,
    bundle: &ExperimentBundle,
) -> Result<()> {
    descriptor.validate("plugin_descriptor")?;
    let validation = validate_experiment_bundle(bundle);
    if !validation.valid {
        return Err(ZkBenchError::validation(
            "plugin_output.bundle",
            format!("plugin output bundle is invalid: {:?}", validation.issues),
        ));
    }
    if descriptor.version != bundle.schema_version.value {
        return Err(ZkBenchError::validation(
            "plugin_output.schema_version",
            "plugin descriptor version does not match bundle schema version",
        ));
    }
    let bindings = [
        (
            "plugin_output.config.plugin_id",
            descriptor.plugin_id.as_str(),
            bundle.config.plugin_id.as_str(),
        ),
        (
            "plugin_output.model_version.model_id",
            descriptor.model_id.as_str(),
            bundle.model_version.model_id.as_str(),
        ),
        (
            "plugin_output.mechanism_ledger.collector_id",
            descriptor.collector_id.as_str(),
            bundle.mechanism_ledger.collector_id.as_str(),
        ),
        (
            "plugin_output.metrics.evaluator_id",
            descriptor.evaluator_id.as_str(),
            bundle.metrics.evaluator_id.as_str(),
        ),
    ];
    for (path, expected, actual) in bindings {
        if expected != actual {
            return Err(ZkBenchError::validation(
                path,
                format!("descriptor expects {expected}, bundle reports {actual}"),
            ));
        }
    }
    for (path, claim_boundary) in [
        ("plugin_output.bundle.claim_boundary", bundle.claim_boundary),
        (
            "plugin_output.mechanism_ledger.claim_boundary",
            bundle.mechanism_ledger.claim_boundary,
        ),
        (
            "plugin_output.metrics.claim_boundary",
            bundle.metrics.claim_boundary,
        ),
        (
            "plugin_output.report.claim_boundary",
            bundle.report.claim_boundary,
        ),
    ] {
        if claim_boundary > descriptor.claim_boundary {
            return Err(ZkBenchError::ClaimBoundary {
                message: format!(
                    "{} exceeds plugin descriptor ceiling {}",
                    path, descriptor.claim_boundary
                ),
            });
        }
    }
    Ok(())
}

/// Static descriptor metadata inventory.
///
/// This registry is intentionally not executable. `ExperimentPluginFactoryCatalog`
/// owns factory construction and lifecycle dispatch; this value remains the
/// serializable metadata projection used by callers that need to inspect
/// plugin descriptors without carrying executable factory state.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentPluginRegistry {
    /// Known in-process plugin descriptors.
    pub plugins: Vec<ExperimentPluginDescriptor>,
}

impl Default for ExperimentPluginRegistry {
    fn default() -> Self {
        Self {
            plugins: vec![local_json_experiment_plugin_descriptor()],
        }
    }
}

impl ExperimentPluginRegistry {
    /// Resolve a static plugin descriptor by id.
    pub fn resolve(&self, plugin_id: &str) -> Option<&ExperimentPluginDescriptor> {
        self.plugins
            .iter()
            .find(|plugin| plugin.plugin_id == plugin_id)
    }

    /// Validate registry descriptors and reject duplicate plugin ids.
    pub fn validate(&self) -> Result<()> {
        let mut plugin_ids = BTreeSet::new();
        for (index, plugin) in self.plugins.iter().enumerate() {
            plugin.validate(&format!("plugins[{index}]"))?;
            if !plugin_ids.insert(&plugin.plugin_id) {
                return Err(ZkBenchError::validation(
                    format!("plugins[{index}].plugin_id"),
                    "plugin id is duplicated",
                ));
            }
        }
        Ok(())
    }
}

/// Return the descriptor for the shipped local JSON plugin.
pub fn local_json_experiment_plugin_descriptor() -> ExperimentPluginDescriptor {
    ExperimentPluginDescriptor {
        plugin_id: LOCAL_JSON_EXPERIMENT_PLUGIN_ID.to_string(),
        version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
        task_id: "generated-benchmark-instance-task".to_string(),
        model_id: "local_json_adapter_v0".to_string(),
        collector_id: "local-replay-mechanism-collector-v1".to_string(),
        evaluator_id: "local-replay-evaluator-v1".to_string(),
        claim_boundary: EXPERIMENT_BUNDLE_CLAIM_BOUNDARY,
    }
}

/// Execute the standard experiment lifecycle and assemble one bundle.
pub fn execute_experiment(
    task: &dyn ExperimentTask,
    model: &dyn ExperimentModel,
    collector: &dyn MechanismCollector,
    evaluator: &dyn Evaluator,
) -> Result<ExperimentBundle> {
    let input = task.prepare()?;
    let run = model.execute(&input)?;
    let mechanisms = collector.collect(&input, &run)?;
    let evaluation = evaluator.evaluate(&input, &run, &mechanisms)?;
    let bundle_id = bundle_id(&input, &run)?;
    let mut bundle = ExperimentBundle {
        bundle_id,
        schema_version: ExperimentBundleVersion::default(),
        lifecycle: ExperimentLifecycle::Completed,
        config: input.config,
        data_version: input.data_version,
        model_version: run.model_version.clone(),
        mechanism_ledger: mechanisms,
        metrics: evaluation.metrics,
        report: evaluation.report,
        artifacts: Vec::new(),
        claim_boundary: EXPERIMENT_BUNDLE_CLAIM_BOUNDARY,
        non_claims: required_non_claims(),
    };
    bundle.artifacts = build_bundle_artifacts(&bundle, &run)?;
    let validation = validate_experiment_bundle(&bundle);
    if !validation.valid {
        return Err(ZkBenchError::validation(
            "experiment_bundle",
            format!("bundle assembly failed validation: {:?}", validation.issues),
        ));
    }
    Ok(bundle)
}

/// Validate the complete experiment bundle and all cross-references.
pub fn validate_experiment_bundle(bundle: &ExperimentBundle) -> ExperimentBundleValidation {
    let mut issues = Vec::new();
    if bundle.bundle_id.trim().is_empty() {
        issues.push(issue(
            ExperimentBundleValidationIssueKind::EmptyIdentity,
            "bundle_id",
            "bundle id must not be empty",
        ));
    }
    if bundle.schema_version.value != EXPERIMENT_BUNDLE_SCHEMA_VERSION {
        issues.push(issue(
            ExperimentBundleValidationIssueKind::UnsupportedSchemaVersion,
            "schema_version.value",
            "unsupported experiment bundle schema version",
        ));
    }
    for (path, value) in [
        ("config.config_id", bundle.config.config_id.as_str()),
        ("config.plugin_id", bundle.config.plugin_id.as_str()),
        (
            "config.canonical_json",
            bundle.config.canonical_json.as_str(),
        ),
        (
            "data_version.source_id",
            bundle.data_version.source_id.as_str(),
        ),
        ("data_version.version", bundle.data_version.version.as_str()),
        (
            "data_version.provenance",
            bundle.data_version.provenance.as_str(),
        ),
        (
            "model_version.model_id",
            bundle.model_version.model_id.as_str(),
        ),
        (
            "model_version.version",
            bundle.model_version.version.as_str(),
        ),
        (
            "model_version.runtime",
            bundle.model_version.runtime.as_str(),
        ),
        (
            "mechanism_ledger.collector_id",
            bundle.mechanism_ledger.collector_id.as_str(),
        ),
        ("metrics.evaluator_id", bundle.metrics.evaluator_id.as_str()),
        ("report.title", bundle.report.title.as_str()),
        ("report.summary", bundle.report.summary.as_str()),
    ] {
        if value.trim().is_empty() {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::EmptyIdentity,
                path,
                "required component identity must not be empty",
            ));
        }
    }
    for (path, schema_version) in [
        (
            "config.schema_version",
            bundle.config.schema_version.as_str(),
        ),
        (
            "mechanism_ledger.schema_version",
            bundle.mechanism_ledger.schema_version.as_str(),
        ),
        (
            "metrics.schema_version",
            bundle.metrics.schema_version.as_str(),
        ),
        (
            "report.schema_version",
            bundle.report.schema_version.as_str(),
        ),
    ] {
        if schema_version != EXPERIMENT_BUNDLE_SCHEMA_VERSION {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::UnsupportedSchemaVersion,
                path,
                "component schema version must match the experiment bundle schema",
            ));
        }
    }
    if bundle.claim_boundary > EXPERIMENT_BUNDLE_CLAIM_BOUNDARY
        || bundle.mechanism_ledger.claim_boundary > EXPERIMENT_BUNDLE_CLAIM_BOUNDARY
        || bundle.metrics.claim_boundary > EXPERIMENT_BUNDLE_CLAIM_BOUNDARY
        || bundle.report.claim_boundary > EXPERIMENT_BUNDLE_CLAIM_BOUNDARY
    {
        issues.push(issue(
            ExperimentBundleValidationIssueKind::ClaimBoundaryEscalation,
            "claim_boundary",
            "experiment bundle components exceed the local slice claim ceiling",
        ));
    }
    if bundle.non_claims.is_empty() || bundle.report.non_claims.is_empty() {
        issues.push(issue(
            ExperimentBundleValidationIssueKind::MissingNonClaim,
            "non_claims",
            "bundle and report must carry explicit non-claims",
        ));
    }

    validate_digest(&bundle.config.digest, "config.digest", &mut issues);
    validate_digest(
        &bundle.data_version.digest,
        "data_version.digest",
        &mut issues,
    );
    validate_digest(
        &bundle.model_version.artifact_digest,
        "model_version.artifact_digest",
        &mut issues,
    );
    let expected_config_digest = compute_artifact_digest_bytes(
        bundle.config.canonical_json.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    );
    if bundle.config.digest != expected_config_digest {
        issues.push(issue(
            ExperimentBundleValidationIssueKind::DigestBindingMismatch,
            "config.digest",
            "config digest does not match canonical_json bytes",
        ));
    }
    if let Ok(expected_model_digest) = compute_artifact_digest(
        &(
            bundle.model_version.model_id.as_str(),
            bundle.model_version.version.as_str(),
            bundle.model_version.runtime.as_str(),
        ),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    ) {
        if bundle.model_version.artifact_digest != expected_model_digest {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::DigestBindingMismatch,
                "model_version.artifact_digest",
                "model identity digest does not match model_id, version, and runtime",
            ));
        }
    }
    validate_component_artifact_binding(
        bundle,
        ExperimentArtifactKind::Config,
        &bundle.config,
        "artifacts[config]",
        &mut issues,
    );
    validate_component_artifact_binding(
        bundle,
        ExperimentArtifactKind::DataVersion,
        &bundle.data_version,
        "artifacts[data_version]",
        &mut issues,
    );
    validate_component_artifact_binding(
        bundle,
        ExperimentArtifactKind::ModelVersion,
        &bundle.model_version,
        "artifacts[model_version]",
        &mut issues,
    );
    validate_component_artifact_binding(
        bundle,
        ExperimentArtifactKind::MechanismLedger,
        &bundle.mechanism_ledger,
        "artifacts[mechanism_ledger]",
        &mut issues,
    );
    validate_component_artifact_binding(
        bundle,
        ExperimentArtifactKind::Metrics,
        &bundle.metrics,
        "artifacts[metrics]",
        &mut issues,
    );
    validate_component_artifact_binding(
        bundle,
        ExperimentArtifactKind::Report,
        &bundle.report,
        "artifacts[report]",
        &mut issues,
    );

    let mut uris = BTreeSet::new();
    let mut kinds = BTreeSet::new();
    for (index, artifact) in bundle.artifacts.iter().enumerate() {
        let path = format!("artifacts[{index}]");
        if artifact.uri.trim().is_empty()
            || artifact.uri.starts_with('/')
            || artifact.uri.contains("..")
        {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::InvalidArtifactUri,
                format!("{path}.uri"),
                "artifact URI must be non-empty and portable",
            ));
        }
        if !uris.insert(artifact.uri.clone()) {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::DuplicateArtifactUri,
                format!("{path}.uri"),
                "artifact URI is duplicated",
            ));
        }
        if !kinds.insert(artifact.kind) {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::DuplicateArtifactKind,
                format!("{path}.kind"),
                "each bundle artifact kind must occur exactly once",
            ));
        }
        validate_digest(&artifact.digest, &format!("{path}.digest"), &mut issues);
        if !artifact.required {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::OptionalRequiredArtifact,
                format!("{path}.required"),
                "the v1 bundle requires every declared component artifact",
            ));
        }
    }
    for kind in required_artifact_kinds() {
        if !kinds.contains(&kind) {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::MissingRequiredArtifact,
                "artifacts",
                format!("required artifact kind {kind:?} is missing"),
            ));
        }
    }

    validate_measurements(
        &bundle.mechanism_ledger.measurements,
        "mechanism_ledger.measurements",
        &uris,
        &mut issues,
    );
    validate_metric_measurements(
        &bundle.metrics.measurements,
        "metrics.measurements",
        &uris,
        &mut issues,
    );
    for non_claim in bundle
        .non_claims
        .iter()
        .chain(bundle.report.non_claims.iter())
    {
        if non_claim.trim().is_empty() {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::EmptyNonClaim,
                "non_claims",
                "non-claim entries must not be empty",
            ));
        }
    }

    ExperimentBundleValidation {
        valid: issues.is_empty(),
        issues,
        claim_boundary: bundle.claim_boundary,
    }
}

/// Bundle validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExperimentBundleValidationIssueKind {
    /// Required identity is empty.
    EmptyIdentity,
    /// Schema version is not supported.
    UnsupportedSchemaVersion,
    /// Claim boundary exceeds the authorized ceiling.
    ClaimBoundaryEscalation,
    /// Bundle or report non-claims are absent.
    MissingNonClaim,
    /// A non-claim entry is empty.
    EmptyNonClaim,
    /// Artifact URI is not portable.
    InvalidArtifactUri,
    /// Artifact URI is duplicated.
    DuplicateArtifactUri,
    /// Artifact kind is duplicated.
    DuplicateArtifactKind,
    /// Component artifact digest does not match the serialized component.
    DigestBindingMismatch,
    /// Required artifact is absent.
    MissingRequiredArtifact,
    /// Artifact was incorrectly marked optional.
    OptionalRequiredArtifact,
    /// Digest is malformed.
    InvalidDigest,
    /// Measurement id is empty or duplicated.
    InvalidMeasurementId,
    /// Measurement status and value are inconsistent.
    InvalidMeasurementState,
    /// Measurement kind and value variant are incompatible.
    IncompatibleMeasurementValue,
    /// Measurement source is absent or unknown.
    InvalidMeasurementSource,
}

/// Bundle validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentBundleValidationIssue {
    /// Issue kind.
    pub kind: ExperimentBundleValidationIssueKind,
    /// Structured field path.
    pub path: String,
    /// Human-readable message.
    pub message: String,
}

/// Bundle validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentBundleValidation {
    /// True when no issues were found.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<ExperimentBundleValidationIssue>,
    /// Claim boundary represented by the validated bundle.
    pub claim_boundary: ClaimBoundary,
}

/// Serialize an experiment bundle to deterministic JSON.
pub fn serialize_experiment_bundle_json(bundle: &ExperimentBundle) -> Result<String> {
    serde_json::to_string(bundle).map_err(|error| {
        ZkBenchError::serialization("serialize_experiment_bundle_json", error.to_string())
    })
}

/// Deserialize an experiment bundle from JSON.
pub fn deserialize_experiment_bundle_json(json: &str) -> Result<ExperimentBundle> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_experiment_bundle_json", error.to_string())
    })
}

/// Compute the deterministic digest of a complete experiment bundle.
pub fn compute_experiment_bundle_digest(bundle: &ExperimentBundle) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        bundle,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    )
}

/// Shipped task adapter for generated local Benchmark Instances.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalJsonExperimentTask {
    descriptor: ExperimentTaskDescriptor,
    config: GeneratorConfig,
}

impl LocalJsonExperimentTask {
    /// Construct a task from a deterministic generator configuration.
    pub fn new(config: GeneratorConfig) -> Self {
        Self {
            descriptor: ExperimentTaskDescriptor {
                task_id: "generated-benchmark-instance-task".to_string(),
                plugin_id: LOCAL_JSON_EXPERIMENT_PLUGIN_ID.to_string(),
                description: "Generate one deterministic local Benchmark Instance".to_string(),
            },
            config,
        }
    }
}

impl Default for LocalJsonExperimentTask {
    fn default() -> Self {
        Self::new(GeneratorConfig::baseline_fsm())
    }
}

impl ExperimentTask for LocalJsonExperimentTask {
    fn descriptor(&self) -> &ExperimentTaskDescriptor {
        &self.descriptor
    }

    fn prepare(&self) -> Result<ExperimentTaskInput> {
        let instance = generate_instance(self.config.clone(), InstanceParams::default())?;
        let config_bytes = canonical_json_bytes(&self.config)?;
        let canonical_json = String::from_utf8(config_bytes.clone())
            .map_err(|error| ZkBenchError::serialization("experiment.config", error.to_string()))?;
        let config = ExperimentConfig {
            config_id: format!("{}_config", self.descriptor.task_id),
            schema_version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
            plugin_id: self.descriptor.plugin_id.clone(),
            canonical_json,
            digest: compute_artifact_digest_bytes(
                &config_bytes,
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Manifest),
            ),
        };
        let data_digest = compute_artifact_digest(
            &instance,
            Some(ArtifactKind::GeneratedInstance),
            Some(ArtifactRole::Input),
        )?;
        Ok(ExperimentTaskInput {
            descriptor: self.descriptor.clone(),
            config,
            data_version: ExperimentDataVersion {
                source_id: "zkbench-core.generated_benchmark_instance".to_string(),
                version: instance.generation_provenance.generator_version.clone(),
                digest: data_digest,
                provenance: instance.generation_provenance.generated_at.clone(),
            },
            instance,
        })
    }
}

/// Shipped model adapter for local semantic replay.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalJsonExperimentModel {
    model_version: ExperimentModelVersion,
}

impl LocalJsonExperimentModel {
    /// Construct the local JSON model/runtime identity.
    pub fn new() -> Result<Self> {
        let identity = (
            "local_json_adapter_v0",
            "phase-f-local-replay-v0",
            "local_semantic_oracle",
        );
        Ok(Self {
            model_version: ExperimentModelVersion {
                model_id: identity.0.to_string(),
                version: identity.1.to_string(),
                runtime: identity.2.to_string(),
                artifact_digest: compute_artifact_digest(
                    &identity,
                    Some(ArtifactKind::Other),
                    Some(ArtifactRole::Manifest),
                )?,
            },
        })
    }
}

impl ExperimentModel for LocalJsonExperimentModel {
    fn model_version(&self) -> &ExperimentModelVersion {
        &self.model_version
    }

    fn execute(&self, input: &ExperimentTaskInput) -> Result<ExperimentModelRun> {
        let manifest = build_local_replay_manifest_for_instance(&input.instance)?;
        let replay_result = LocalJsonAdapter::default().replay(&manifest)?;
        let artifacts = vec![
            experiment_artifact(
                "replay/manifest.json",
                ExperimentArtifactKind::ReplayManifest,
                &manifest,
                true,
            )?,
            experiment_artifact(
                "replay/result.json",
                ExperimentArtifactKind::ReplayResult,
                &replay_result,
                true,
            )?,
        ];
        Ok(ExperimentModelRun {
            model_version: self.model_version.clone(),
            replay_manifest: manifest,
            replay_result,
            artifacts,
        })
    }
}

/// Shipped sparse mechanism collector for local replay.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct LocalReplayMechanismCollector;

impl MechanismCollector for LocalReplayMechanismCollector {
    fn collector_id(&self) -> &str {
        "local-replay-mechanism-collector-v1"
    }

    fn collect(
        &self,
        _input: &ExperimentTaskInput,
        run: &ExperimentModelRun,
    ) -> Result<MechanismLedger> {
        let trace_count = run.replay_result.trace_results.len() as u64;
        let transition_count = run
            .replay_result
            .trace_results
            .iter()
            .filter(|trace| matches!(trace.local_oracle_outcome, OracleOutcome::Accepted))
            .count() as u64;
        Ok(MechanismLedger {
            schema_version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
            collector_id: self.collector_id().to_string(),
            measurements: vec![
                MechanismMeasurement {
                    measurement_id: "trace_outcome_count".to_string(),
                    kind: MechanismMeasurementKind::TraceOutcome,
                    status: MeasurementStatus::Collected,
                    value: Some(MeasurementValue::Count(trace_count)),
                    unit: Some("traces".to_string()),
                    source_artifact_uri: Some("replay/result.json".to_string()),
                    reason: None,
                },
                MechanismMeasurement {
                    measurement_id: "accepted_state_transition_count".to_string(),
                    kind: MechanismMeasurementKind::StateTransition,
                    status: MeasurementStatus::Collected,
                    value: Some(MeasurementValue::Count(transition_count)),
                    unit: Some("traces".to_string()),
                    source_artifact_uri: Some("replay/result.json".to_string()),
                    reason: None,
                },
                unsupported_mechanism(
                    "activation_path",
                    MechanismMeasurementKind::Activation,
                    "local JSON replay exposes no model activation stream",
                ),
                unsupported_mechanism(
                    "attention_weights",
                    MechanismMeasurementKind::Attention,
                    "local JSON replay exposes no attention stream",
                ),
                unsupported_mechanism(
                    "causal_effect",
                    MechanismMeasurementKind::CausalEffect,
                    "no intervention-capable model runtime is attached",
                ),
            ],
            claim_boundary: EXPERIMENT_BUNDLE_CLAIM_BOUNDARY,
            notes: vec![
                "Mechanism ledger is intentionally sparse for the local semantic replay adapter."
                    .to_string(),
                "Unsupported mechanism fields remain explicit for future collector adapters."
                    .to_string(),
            ],
        })
    }
}

/// Shipped evaluator for local replay results.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct LocalReplayEvaluator;

impl Evaluator for LocalReplayEvaluator {
    fn evaluator_id(&self) -> &str {
        "local-replay-evaluator-v1"
    }

    fn evaluate(
        &self,
        _input: &ExperimentTaskInput,
        run: &ExperimentModelRun,
        _mechanisms: &MechanismLedger,
    ) -> Result<ExperimentEvaluation> {
        let mut accepted = 0_u64;
        let mut rejected = 0_u64;
        let mut inconclusive = 0_u64;
        let mut capability_gap = 0_u64;
        for trace in &run.replay_result.trace_results {
            match trace.local_oracle_outcome {
                OracleOutcome::Accepted => accepted += 1,
                OracleOutcome::Rejected { .. } => rejected += 1,
                OracleOutcome::Inconclusive { .. } => inconclusive += 1,
                OracleOutcome::CapabilityGap { .. } => capability_gap += 1,
            }
        }
        let source = Some("replay/result.json".to_string());
        let metric = |metric_id: &str, value: MeasurementValue| MetricMeasurement {
            metric_id: metric_id.to_string(),
            kind: MetricKind::Count,
            status: MeasurementStatus::Collected,
            value: Some(value),
            unit: Some("traces".to_string()),
            source_artifact_uri: source.clone(),
            reason: None,
        };
        let metrics = ExperimentMetrics {
            schema_version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
            evaluator_id: self.evaluator_id().to_string(),
            measurements: vec![
                metric(
                    "trace_count",
                    MeasurementValue::Count(run.replay_result.trace_results.len() as u64),
                ),
                metric("accepted_trace_count", MeasurementValue::Count(accepted)),
                metric("rejected_trace_count", MeasurementValue::Count(rejected)),
                metric(
                    "inconclusive_trace_count",
                    MeasurementValue::Count(inconclusive),
                ),
                metric(
                    "capability_gap_count",
                    MeasurementValue::Count(capability_gap),
                ),
                metric(
                    "evidence_record_count",
                    MeasurementValue::Count(run.replay_result.evidence_records.len() as u64),
                ),
            ],
            claim_boundary: EXPERIMENT_BUNDLE_CLAIM_BOUNDARY,
            notes: vec![
                "Metrics summarize local replay only; no external backend metrics were collected."
                    .to_string(),
            ],
        };
        let report = ExperimentReport {
            schema_version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
            title: "Composed ZK Benchmark OS local experiment".to_string(),
            summary: format!(
                "Local replay completed with {} traces and {} evidence records.",
                run.replay_result.trace_results.len(),
                run.replay_result.evidence_records.len()
            ),
            claim_boundary: EXPERIMENT_BUNDLE_CLAIM_BOUNDARY,
            non_claims: required_non_claims(),
            notes: vec![
                "This report is a deterministic local artifact summary, not a backend benchmark report."
                    .to_string(),
            ],
        };
        Ok(ExperimentEvaluation { metrics, report })
    }
}

/// Shipped static local JSON plugin.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalJsonExperimentPlugin {
    descriptor: ExperimentPluginDescriptor,
    task: LocalJsonExperimentTask,
    model: LocalJsonExperimentModel,
    collector: LocalReplayMechanismCollector,
    evaluator: LocalReplayEvaluator,
}

impl LocalJsonExperimentPlugin {
    /// Construct a local JSON plugin for a deterministic generator config.
    pub fn new(config: GeneratorConfig) -> Result<Self> {
        Ok(Self {
            descriptor: local_json_experiment_plugin_descriptor(),
            task: LocalJsonExperimentTask::new(config),
            model: LocalJsonExperimentModel::new()?,
            collector: LocalReplayMechanismCollector,
            evaluator: LocalReplayEvaluator,
        })
    }

    /// Construct the baseline local JSON plugin.
    pub fn baseline() -> Result<Self> {
        Self::new(GeneratorConfig::baseline_fsm())
    }
}

impl ExperimentPlugin for LocalJsonExperimentPlugin {
    fn descriptor(&self) -> &ExperimentPluginDescriptor {
        &self.descriptor
    }

    fn run(&self) -> Result<ExperimentBundle> {
        execute_experiment(&self.task, &self.model, &self.collector, &self.evaluator)
    }
}

fn bundle_id(input: &ExperimentTaskInput, run: &ExperimentModelRun) -> Result<String> {
    let material = (
        input.descriptor.task_id.as_str(),
        input.instance.id.as_str(),
        run.model_version.model_id.as_str(),
        run.model_version.version.as_str(),
    );
    let material_json = serde_json::to_string(&material)
        .map_err(|error| ZkBenchError::serialization("experiment.bundle_id", error.to_string()))?;
    let digest = compute_artifact_digest_bytes(
        material_json.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    );
    Ok(format!("experiment_{}", digest.hex_digest))
}

fn build_bundle_artifacts(
    bundle: &ExperimentBundle,
    run: &ExperimentModelRun,
) -> Result<Vec<ExperimentArtifactRef>> {
    let mut artifacts = vec![
        experiment_artifact(
            "config/experiment-config.json",
            ExperimentArtifactKind::Config,
            &bundle.config,
            true,
        )?,
        experiment_artifact(
            "data/data-version.json",
            ExperimentArtifactKind::DataVersion,
            &bundle.data_version,
            true,
        )?,
        experiment_artifact(
            "model/model-version.json",
            ExperimentArtifactKind::ModelVersion,
            &bundle.model_version,
            true,
        )?,
        experiment_artifact(
            "mechanism/mechanism-ledger.json",
            ExperimentArtifactKind::MechanismLedger,
            &bundle.mechanism_ledger,
            true,
        )?,
        experiment_artifact(
            "metrics/metrics.json",
            ExperimentArtifactKind::Metrics,
            &bundle.metrics,
            true,
        )?,
        experiment_artifact(
            "report/report.json",
            ExperimentArtifactKind::Report,
            &bundle.report,
            true,
        )?,
    ];
    artifacts.extend(run.artifacts.clone());
    Ok(artifacts)
}

fn experiment_artifact<T: Serialize>(
    uri: &str,
    kind: ExperimentArtifactKind,
    value: &T,
    required: bool,
) -> Result<ExperimentArtifactRef> {
    Ok(ExperimentArtifactRef {
        uri: uri.to_string(),
        kind,
        digest: compute_artifact_digest(
            value,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?,
        required,
    })
}

fn required_artifact_kinds() -> [ExperimentArtifactKind; 8] {
    [
        ExperimentArtifactKind::Config,
        ExperimentArtifactKind::DataVersion,
        ExperimentArtifactKind::ModelVersion,
        ExperimentArtifactKind::MechanismLedger,
        ExperimentArtifactKind::Metrics,
        ExperimentArtifactKind::Report,
        ExperimentArtifactKind::ReplayManifest,
        ExperimentArtifactKind::ReplayResult,
    ]
}

fn required_non_claims() -> Vec<String> {
    vec![
        "Local replay is not official benchmark evidence.".to_string(),
        "No external backend command, network access, or model download occurred.".to_string(),
        "Mechanism measurements are sparse and do not establish interpretability, introspection, or causal validity.".to_string(),
        "This bundle does not mutate the accepted Evidence Ledger or authorize runtime action.".to_string(),
    ]
}

fn unsupported_mechanism(
    measurement_id: &str,
    kind: MechanismMeasurementKind,
    reason: &str,
) -> MechanismMeasurement {
    MechanismMeasurement {
        measurement_id: measurement_id.to_string(),
        kind,
        status: MeasurementStatus::Unsupported,
        value: None,
        unit: None,
        source_artifact_uri: None,
        reason: Some(reason.to_string()),
    }
}

fn validate_measurements(
    measurements: &[MechanismMeasurement],
    prefix: &str,
    artifact_uris: &BTreeSet<String>,
    issues: &mut Vec<ExperimentBundleValidationIssue>,
) {
    let mut ids = BTreeSet::new();
    for (index, measurement) in measurements.iter().enumerate() {
        let path = format!("{prefix}[{index}]");
        if measurement.measurement_id.trim().is_empty() || !ids.insert(&measurement.measurement_id)
        {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::InvalidMeasurementId,
                format!("{path}.measurement_id"),
                "measurement id must be non-empty and unique",
            ));
        }
        validate_measurement_state(
            measurement.status,
            &measurement.value,
            &measurement.reason,
            &measurement.source_artifact_uri,
            &path,
            artifact_uris,
            issues,
        );
        if !mechanism_value_matches_kind(measurement.kind, &measurement.value) {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::IncompatibleMeasurementValue,
                format!("{path}.value"),
                "mechanism measurement kind is incompatible with its value variant",
            ));
        }
    }
}

fn validate_metric_measurements(
    measurements: &[MetricMeasurement],
    prefix: &str,
    artifact_uris: &BTreeSet<String>,
    issues: &mut Vec<ExperimentBundleValidationIssue>,
) {
    let mut ids = BTreeSet::new();
    for (index, measurement) in measurements.iter().enumerate() {
        let path = format!("{prefix}[{index}]");
        if measurement.metric_id.trim().is_empty() || !ids.insert(&measurement.metric_id) {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::InvalidMeasurementId,
                format!("{path}.metric_id"),
                "metric id must be non-empty and unique",
            ));
        }
        validate_measurement_state(
            measurement.status,
            &measurement.value,
            &measurement.reason,
            &measurement.source_artifact_uri,
            &path,
            artifact_uris,
            issues,
        );
        if !metric_value_matches_kind(measurement.kind, &measurement.value) {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::IncompatibleMeasurementValue,
                format!("{path}.value"),
                "metric kind is incompatible with its value variant",
            ));
        }
    }
}

fn validate_measurement_state(
    status: MeasurementStatus,
    value: &Option<MeasurementValue>,
    reason: &Option<String>,
    source_artifact_uri: &Option<String>,
    path: &str,
    artifact_uris: &BTreeSet<String>,
    issues: &mut Vec<ExperimentBundleValidationIssue>,
) {
    match status {
        MeasurementStatus::Collected => {
            if value.is_none() || source_artifact_uri.is_none() {
                issues.push(issue(
                    ExperimentBundleValidationIssueKind::InvalidMeasurementState,
                    path,
                    "collected measurements require a value and source artifact URI",
                ));
            }
            if reason.is_some() {
                issues.push(issue(
                    ExperimentBundleValidationIssueKind::InvalidMeasurementState,
                    path,
                    "collected measurements must not carry a failure/absence reason",
                ));
            }
        }
        MeasurementStatus::NotCollected
        | MeasurementStatus::Unsupported
        | MeasurementStatus::Failed => {
            if value.is_some() || reason.as_deref().unwrap_or("").trim().is_empty() {
                issues.push(issue(
                    ExperimentBundleValidationIssueKind::InvalidMeasurementState,
                    path,
                    "non-collected measurements require no value and a reason",
                ));
            }
            if source_artifact_uri.is_some() {
                issues.push(issue(
                    ExperimentBundleValidationIssueKind::InvalidMeasurementState,
                    path,
                    "non-collected measurements must not claim a source artifact",
                ));
            }
        }
    }
    if let Some(source) = source_artifact_uri {
        if !artifact_uris.contains(source) {
            issues.push(issue(
                ExperimentBundleValidationIssueKind::InvalidMeasurementSource,
                format!("{path}.source_artifact_uri"),
                "measurement source artifact URI is not declared by the bundle",
            ));
        }
    }
}

fn mechanism_value_matches_kind(
    kind: MechanismMeasurementKind,
    value: &Option<MeasurementValue>,
) -> bool {
    let Some(value) = value else {
        return true;
    };
    match kind {
        MechanismMeasurementKind::TraceOutcome => matches!(
            value,
            MeasurementValue::Count(_)
                | MeasurementValue::Integer(_)
                | MeasurementValue::Text(_)
                | MeasurementValue::Digest(_)
        ),
        MechanismMeasurementKind::StateTransition => {
            matches!(
                value,
                MeasurementValue::Count(_) | MeasurementValue::Integer(_)
            )
        }
        MechanismMeasurementKind::Activation
        | MechanismMeasurementKind::Attention
        | MechanismMeasurementKind::CausalEffect
        | MechanismMeasurementKind::Other => true,
    }
}

fn metric_value_matches_kind(kind: MetricKind, value: &Option<MeasurementValue>) -> bool {
    let Some(value) = value else {
        return true;
    };
    match kind {
        MetricKind::Count => matches!(value, MeasurementValue::Count(_)),
        MetricKind::Integer | MetricKind::DurationMillis => {
            matches!(
                value,
                MeasurementValue::Integer(_) | MeasurementValue::Count(_)
            )
        }
        MetricKind::RatioBasisPoints => matches!(value, MeasurementValue::RatioBasisPoints(_)),
        MetricKind::StatusLabel => matches!(value, MeasurementValue::Text(_)),
    }
}

fn validate_digest(
    digest: &ArtifactDigest,
    path: &str,
    issues: &mut Vec<ExperimentBundleValidationIssue>,
) {
    let valid_hex = digest.hex_digest.len() == 64
        && digest
            .hex_digest
            .chars()
            .all(|character| character.is_ascii_hexdigit() && !character.is_ascii_uppercase());
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 || !valid_hex || digest.byte_len == 0 {
        issues.push(issue(
            ExperimentBundleValidationIssueKind::InvalidDigest,
            path,
            "experiment artifacts require a non-empty SHA-256 digest with lowercase hex",
        ));
    }
}

fn validate_component_artifact_binding<T: Serialize>(
    bundle: &ExperimentBundle,
    kind: ExperimentArtifactKind,
    component: &T,
    path: &str,
    issues: &mut Vec<ExperimentBundleValidationIssue>,
) {
    let Some(artifact) = bundle
        .artifacts
        .iter()
        .find(|artifact| artifact.kind == kind)
    else {
        return;
    };
    let Ok(expected) = compute_artifact_digest(
        component,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    ) else {
        issues.push(issue(
            ExperimentBundleValidationIssueKind::DigestBindingMismatch,
            path,
            "component digest could not be recomputed",
        ));
        return;
    };
    if artifact.digest != expected {
        issues.push(issue(
            ExperimentBundleValidationIssueKind::DigestBindingMismatch,
            path,
            "artifact digest does not match the serialized component",
        ));
    }
}

fn issue(
    kind: ExperimentBundleValidationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) -> ExperimentBundleValidationIssue {
    ExperimentBundleValidationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    }
}

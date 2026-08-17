//! Adaptive observability and fixed experiment artifact contracts.
//!
//! State slice: benchmark-os-experiment-unit-adaptive-observability-v1.
//! Integrity extension: benchmark-os-observability-integrity-hardening-v1.
//! Payload readback slice: benchmark-os-observability-payload-readback-v1.
//! Artifact identity slice: benchmark-os-observability-artifact-identity-v1.
//! Legacy migration slice: benchmark-os-observability-v1-to-v2-upgrade-v1.
//! Ledger transport slice: benchmark-os-observability-ledger-transport-v1.
//! Bundle assembly slice: benchmark-os-observability-bundle-assembly-v1.
//! Slot access slice: benchmark-os-observability-slot-access-v1.
//! Module manifest slice: benchmark-os-observability-module-manifest-v1.
//! Slot order slice: benchmark-os-observability-slot-order-v1.
//! Local projection binding access slice: benchmark-os-local-json-projection-binding-access-v1.
//! Local inner artifact access slice: benchmark-os-local-inner-artifact-access-v1.
//! Local projection single-source access slice: benchmark-os-local-json-projection-single-source-access-v1.
//! Lifecycle transaction slice: benchmark-os-observability-run-lifecycle-transaction-v1.
//! Artifact policy slice: benchmark-os-observability-run-artifact-policy-v1.
//! Shared artifact-reference policy locality slice: benchmark-os-plugin-composition-artifact-reference-policy-locality-v1.
//! Local JSON composition output handoff slice: benchmark-os-local-json-composition-output-handoff-validation-v1.
//! Scheduler budget transition validation slice: benchmark-os-observability-scheduler-budget-transition-v1.
//! Append-only ledger precondition slice: benchmark-os-observability-append-only-ledger-precondition-v1.
//! Durable composition-adapter attribution slice:
//! benchmark-os-observability-composition-adapter-durable-attribution-v1.
//!
//! This module is metadata-only. It defines replaceable interfaces, a fixed
//! nine-slot run bundle, deterministic observability allocation, provenance,
//! append-only mechanism history, and metric meta-evaluation. It does not run
//! models, access the network, retain secrets, or promote evidence.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, compute_artifact_digest_bytes, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
};
use crate::experiment::{
    compute_experiment_bundle_digest, deserialize_experiment_bundle_json,
    serialize_experiment_bundle_json, validate_experiment_bundle,
    ExperimentArtifactKind as LocalArtifactKind, ExperimentBundle as LocalExperimentBundle,
    ExperimentPlugin, ExperimentPluginDescriptor,
};
use crate::experiment_plugin_catalog::ExperimentPluginFactoryCatalog;
use crate::generator::GeneratorConfig;
/// Fixed schema version for the nine-slot run bundle.
pub const EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION: &str = "experiment-unit-artifact-bundle-v2";
/// Legacy schema accepted only by the explicit v1-to-v2 migration Adapter.
pub const LEGACY_EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION: &str = "experiment-unit-artifact-bundle-v1";
/// Fixed schema version for the append-only mechanism ledger.
pub const ADAPTIVE_MECHANISM_LEDGER_SCHEMA_VERSION: &str = "adaptive-mechanism-ledger-v2";
/// Fixed schema version for metric meta-evaluation.
pub const METRIC_META_EVALUATION_SCHEMA_VERSION: &str = "metric-meta-evaluation-v2";
/// Fixed schema version for the append-only metric meta-evaluation ledger.
pub const METRIC_META_EVALUATION_LEDGER_SCHEMA_VERSION: &str = "metric-meta-evaluation-ledger-v1";
/// Integer score scale used by scheduler inputs and outputs.
pub const OBSERVABILITY_SCORE_SCALE: u16 = 1_000;

/// Provenance attached to every artifact reference and observation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentProvenance {
    /// Actor, agent, or process identity.
    pub who: String,
    /// Activity that produced this record.
    pub what: String,
    /// Deterministic logical time or declared timestamp.
    pub when: String,
    /// Implementation version.
    pub version: String,
    /// Source revision or explicit local-state marker.
    pub source_revision: String,
}

impl ExperimentProvenance {
    /// Validate the who/what/when/version/source fields.
    pub fn validate(&self, path: &str) -> Result<()> {
        for (field, value) in [
            ("who", &self.who),
            ("what", &self.what),
            ("when", &self.when),
            ("version", &self.version),
            ("source_revision", &self.source_revision),
        ] {
            if value.trim().is_empty() {
                return Err(ZkBenchError::validation(
                    format!("{path}.{field}"),
                    "provenance value must not be empty",
                ));
            }
        }
        Ok(())
    }
}

/// Identity of a replaceable implementation behind an interface.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ModuleDescriptor {
    /// Stable logical module id.
    pub module_id: String,
    /// Concrete implementation id.
    pub implementation_id: String,
    /// Implementation version.
    pub version: String,
    /// Source revision.
    pub source_revision: String,
}

impl ModuleDescriptor {
    /// Validate module identity and version.
    pub fn validate(&self, path: &str) -> Result<()> {
        for (field, value) in [
            ("module_id", &self.module_id),
            ("implementation_id", &self.implementation_id),
            ("version", &self.version),
            ("source_revision", &self.source_revision),
        ] {
            if value.trim().is_empty() {
                return Err(ZkBenchError::validation(
                    format!("{path}.{field}"),
                    "module descriptor value must not be empty",
                ));
            }
        }
        Ok(())
    }
}

/// Validate the ordered module manifest carried by a run or composition.
///
/// The wire shape remains `Vec<ModuleDescriptor>`, but all callers share one
/// admission Interface for non-empty manifests, descriptor validity, and
/// unique logical module ids. This keeps implementation replacement explicit
/// without forcing serialized consumers to adopt a new wrapper type.
pub fn validate_module_manifest(modules: &[ModuleDescriptor], path: &str) -> Result<()> {
    if modules.is_empty() {
        return Err(ZkBenchError::validation(
            path,
            "module manifest must contain at least one descriptor",
        ));
    }
    let mut module_ids = BTreeSet::new();
    for (index, module) in modules.iter().enumerate() {
        let module_path = format!("{}[{}]", path, index);
        module.validate(&module_path)?;
        if !module_ids.insert(module.module_id.clone()) {
            return Err(ZkBenchError::validation(
                format!("{}.module_id", module_path),
                "logical module id is duplicated",
            ));
        }
    }
    Ok(())
}

/// The fixed artifact slots emitted by every experiment run.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExperimentArtifactKind {
    /// Frozen experiment configuration.
    Config,
    /// Task instance and task implementation identity.
    Task,
    /// Prompt or prompt digest.
    Prompt,
    /// Response or response digest.
    Response,
    /// Evaluation and metric results.
    Evaluation,
    /// Mechanism observation for this run.
    MechanismRecord,
    /// Run metadata and lifecycle status.
    Metadata,
    /// Redacted or structured logs.
    Logs,
    /// Human and machine-readable report.
    Report,
}

impl ExperimentArtifactKind {
    /// Number of required artifact slots in every experiment run.
    pub const SLOT_COUNT: usize = 9;

    /// Canonical serialized and validation order for the fixed slots.
    pub const ALL: [Self; Self::SLOT_COUNT] = [
        Self::Config,
        Self::Task,
        Self::Prompt,
        Self::Response,
        Self::Evaluation,
        Self::MechanismRecord,
        Self::Metadata,
        Self::Logs,
        Self::Report,
    ];

    /// Stable field name used in validation paths and reports.
    pub const fn field_name(self) -> &'static str {
        match self {
            Self::Config => "config",
            Self::Task => "task",
            Self::Prompt => "prompt",
            Self::Response => "response",
            Self::Evaluation => "evaluation",
            Self::MechanismRecord => "mechanism_record",
            Self::Metadata => "metadata",
            Self::Logs => "logs",
            Self::Report => "report",
        }
    }
}

/// Digest-bound artifact reference with first-class provenance.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentArtifactRef {
    /// Portable relative artifact URI.
    pub uri: String,
    /// Fixed bundle slot.
    pub kind: ExperimentArtifactKind,
    /// Experiment identity that owns this artifact.
    pub experiment_id: String,
    /// Run identity that owns this artifact.
    pub run_id: String,
    /// Digest over the exact artifact payload.
    pub digest: ArtifactDigest,
    /// Provenance for this artifact.
    pub provenance: ExperimentProvenance,
}

impl ExperimentArtifactRef {
    /// Validate portable identity, digest metadata, and provenance before an
    /// artifact is handed to a downstream Adapter.
    pub fn validate(&self, path: &str) -> Result<()> {
        require_text(&self.uri, format!("{path}.uri"))?;
        require_text(&self.experiment_id, format!("{path}.experiment_id"))?;
        require_text(&self.run_id, format!("{path}.run_id"))?;
        if self.uri.starts_with('/') || self.uri.contains("..") {
            return Err(ZkBenchError::validation(
                format!("{path}.uri"),
                "artifact URI must be a portable relative path",
            ));
        }
        if self.digest.algorithm != ArtifactDigestAlgorithm::Sha256
            || self.digest.kind != Some(ArtifactKind::Other)
            || self.digest.role != Some(ArtifactRole::Manifest)
            || self.digest.hex_digest.len() != 64
            || !self
                .digest
                .hex_digest
                .chars()
                .all(|character| character.is_ascii_hexdigit() && !character.is_ascii_uppercase())
        {
            return Err(ZkBenchError::validation(
                format!("{path}.digest"),
                "artifact digest must be lowercase SHA-256 metadata",
            ));
        }
        self.provenance.validate(&format!("{path}.provenance"))?;
        if self.provenance.source_revision.trim().is_empty() {
            return Err(ZkBenchError::validation(
                format!("{path}.provenance.source_revision"),
                "artifact source revision is required",
            ));
        }
        Ok(())
    }

    /// Validate the artifact against the active experiment and run.
    pub fn validate_for(&self, path: &str, experiment_id: &str, run_id: &str) -> Result<()> {
        self.validate(path)?;
        if self.experiment_id != experiment_id {
            return Err(ZkBenchError::validation(
                format!("{path}.experiment_id"),
                "artifact experiment identity does not match the active run",
            ));
        }
        if self.run_id != run_id {
            return Err(ZkBenchError::validation(
                format!("{path}.run_id"),
                "artifact run identity does not match the active run",
            ));
        }
        Ok(())
    }
}

/// Create a digest-bound artifact reference from the exact serialized payload.
pub fn create_experiment_artifact_ref<T: Serialize>(
    uri: impl Into<String>,
    kind: ExperimentArtifactKind,
    payload: &T,
    experiment_id: &str,
    run_id: &str,
    provenance: ExperimentProvenance,
) -> Result<ExperimentArtifactRef> {
    let artifact = ExperimentArtifactRef {
        uri: uri.into(),
        kind,
        experiment_id: experiment_id.to_string(),
        run_id: run_id.to_string(),
        digest: compute_artifact_digest(
            payload,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?,
        provenance,
    };
    artifact.validate_for("artifact", experiment_id, run_id)?;
    Ok(artifact)
}

/// Validate a typed payload against the artifact reference that claims to
/// contain it. This is the payload-aware counterpart to structural manifest
/// validation and is safe for serialized readback callers.
pub fn validate_experiment_artifact_payload<T: Serialize>(
    artifact: &ExperimentArtifactRef,
    expected_kind: ExperimentArtifactKind,
    payload: &T,
    experiment_id: &str,
    run_id: &str,
    path: &str,
) -> Result<()> {
    artifact.validate_for(path, experiment_id, run_id)?;
    if artifact.kind != expected_kind {
        return Err(ZkBenchError::validation(
            format!("{path}.kind"),
            format!("expected {expected_kind:?}, got {:?}", artifact.kind),
        ));
    }
    let expected_digest = compute_artifact_digest(
        payload,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    )?;
    if artifact.digest != expected_digest {
        return Err(ZkBenchError::validation(
            format!("{path}.digest"),
            "artifact payload digest does not match the declared digest",
        ));
    }
    Ok(())
}

/// Fixed nine-slot artifact bundle. No slot is optional.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentArtifactBundle {
    /// Stable bundle id.
    pub bundle_id: String,
    /// Experiment id.
    pub experiment_id: String,
    /// Run id.
    pub run_id: String,
    /// Bundle schema version.
    pub schema_version: String,
    /// Configuration artifact.
    pub config: ExperimentArtifactRef,
    /// Task artifact.
    pub task: ExperimentArtifactRef,
    /// Prompt artifact.
    pub prompt: ExperimentArtifactRef,
    /// Response artifact.
    pub response: ExperimentArtifactRef,
    /// Evaluation artifact.
    pub evaluation: ExperimentArtifactRef,
    /// Mechanism record artifact.
    pub mechanism_record: ExperimentArtifactRef,
    /// Metadata artifact.
    pub metadata: ExperimentArtifactRef,
    /// Logs artifact.
    pub logs: ExperimentArtifactRef,
    /// Report artifact.
    pub report: ExperimentArtifactRef,
    /// This contract remains a local design/metadata claim.
    pub claim_boundary: ClaimBoundary,
}

impl ExperimentArtifactBundle {
    /// Return the canonical reference for one fixed bundle slot.
    ///
    /// The enum is the only caller-facing selector. Keeping this lookup on
    /// the bundle prevents composition Adapters from reimplementing the
    /// nine-slot mapping in separate private matchers.
    pub fn artifact(&self, kind: ExperimentArtifactKind) -> &ExperimentArtifactRef {
        match kind {
            ExperimentArtifactKind::Config => &self.config,
            ExperimentArtifactKind::Task => &self.task,
            ExperimentArtifactKind::Prompt => &self.prompt,
            ExperimentArtifactKind::Response => &self.response,
            ExperimentArtifactKind::Evaluation => &self.evaluation,
            ExperimentArtifactKind::MechanismRecord => &self.mechanism_record,
            ExperimentArtifactKind::Metadata => &self.metadata,
            ExperimentArtifactKind::Logs => &self.logs,
            ExperimentArtifactKind::Report => &self.report,
        }
    }

    /// Return all fixed slots in the canonical order owned by the slot kind
    /// Interface.
    pub fn artifacts_in_order(
        &self,
    ) -> [(ExperimentArtifactKind, &ExperimentArtifactRef); ExperimentArtifactKind::SLOT_COUNT]
    {
        ExperimentArtifactKind::ALL.map(|kind| (kind, self.artifact(kind)))
    }
}

/// Assemble the fixed nine-slot bundle through one private policy Seam.
///
/// All Implementations supply the nine typed references in slot order. This
/// Module owns schema version, bundle identity, claim ceiling, slot mapping,
/// and final validation so a future wire-schema change has one edit point.
pub(crate) fn assemble_experiment_artifact_bundle(
    bundle_id: impl Into<String>,
    experiment_id: impl Into<String>,
    run_id: impl Into<String>,
    artifacts: [ExperimentArtifactRef; 9],
) -> Result<ExperimentArtifactBundle> {
    let [config, task, prompt, response, evaluation, mechanism_record, metadata, logs, report] =
        artifacts;
    let bundle = ExperimentArtifactBundle {
        bundle_id: bundle_id.into(),
        experiment_id: experiment_id.into(),
        run_id: run_id.into(),
        schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
        config,
        task,
        prompt,
        response,
        evaluation,
        mechanism_record,
        metadata,
        logs,
        report,
        claim_boundary: ClaimBoundary::Level0DesignNote,
    };
    validate_experiment_artifact_bundle(&bundle)?;
    Ok(bundle)
}

/// The pre-identity v1 reference shape retained solely for explicit migration.
///
/// This is intentionally private: callers must use the named migration seam
/// rather than deserialize a legacy record as if it were a current artifact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct LegacyExperimentArtifactRefV1 {
    uri: String,
    kind: ExperimentArtifactKind,
    digest: ArtifactDigest,
    provenance: ExperimentProvenance,
}

/// The pre-identity v1 outer bundle shape.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct LegacyExperimentArtifactBundleV1 {
    bundle_id: String,
    experiment_id: String,
    run_id: String,
    schema_version: String,
    config: LegacyExperimentArtifactRefV1,
    task: LegacyExperimentArtifactRefV1,
    prompt: LegacyExperimentArtifactRefV1,
    response: LegacyExperimentArtifactRefV1,
    evaluation: LegacyExperimentArtifactRefV1,
    mechanism_record: LegacyExperimentArtifactRefV1,
    metadata: LegacyExperimentArtifactRefV1,
    logs: LegacyExperimentArtifactRefV1,
    report: LegacyExperimentArtifactRefV1,
    claim_boundary: ClaimBoundary,
}

/// Validate the fixed slots, identity, provenance, digests, and claim ceiling.
pub fn validate_experiment_artifact_bundle(bundle: &ExperimentArtifactBundle) -> Result<()> {
    require_text(&bundle.bundle_id, "bundle.bundle_id")?;
    require_text(&bundle.experiment_id, "bundle.experiment_id")?;
    require_text(&bundle.run_id, "bundle.run_id")?;
    if bundle.schema_version != EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION {
        return Err(ZkBenchError::validation(
            "bundle.schema_version",
            format!(
                "expected {EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION}, got {}",
                bundle.schema_version
            ),
        ));
    }
    if bundle.claim_boundary != ClaimBoundary::Level0DesignNote {
        return Err(ZkBenchError::ClaimBoundary {
            message: "adaptive observability metadata remains Level0DesignNote".to_string(),
        });
    }

    let mut uris = BTreeSet::new();
    for (expected_kind, artifact) in bundle.artifacts_in_order() {
        let slot = expected_kind.field_name();
        if artifact.kind != expected_kind {
            return Err(ZkBenchError::validation(
                format!("bundle.{slot}.kind"),
                format!("expected {expected_kind:?}, got {:?}", artifact.kind),
            ));
        }
        if !uris.insert(artifact.uri.clone()) {
            return Err(ZkBenchError::validation(
                format!("bundle.{slot}.uri"),
                "artifact URI is duplicated",
            ));
        }
        artifact.validate_for(
            &format!("bundle.{slot}"),
            &bundle.experiment_id,
            &bundle.run_id,
        )?;
    }
    Ok(())
}

/// Serialize a validated bundle using the repository's version-locked JSON
/// field order. The bytes are suitable for archival or transport.
pub fn serialize_experiment_artifact_bundle_json(
    bundle: &ExperimentArtifactBundle,
) -> Result<String> {
    validate_experiment_artifact_bundle(bundle)?;
    serde_json::to_string(bundle)
        .map_err(|error| ZkBenchError::serialization("experiment_bundle.json", error.to_string()))
}

/// Deserialize and validate one fixed-shape experiment bundle.
pub fn deserialize_experiment_artifact_bundle_json(json: &str) -> Result<ExperimentArtifactBundle> {
    let bundle: ExperimentArtifactBundle = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::serialization("experiment_bundle.json", error.to_string())
    })?;
    validate_experiment_artifact_bundle(&bundle)?;
    Ok(bundle)
}

/// Upgrade one canonical v1 outer bundle to the current v2 identity contract.
///
/// The migration is explicit and fail-closed. It accepts only the exact v1
/// schema, requires canonical v1 JSON, copies the enclosing experiment/run
/// identity into all nine references, preserves every URI, kind, digest, and
/// provenance field, and validates the resulting v2 bundle. It never reads or
/// rewrites payloads. The ordinary v2 deserializer deliberately does not call
/// this Adapter implicitly.
pub fn upgrade_experiment_artifact_bundle_v1_json(json: &str) -> Result<ExperimentArtifactBundle> {
    let legacy: LegacyExperimentArtifactBundleV1 = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::serialization("experiment_bundle.v1.json", error.to_string())
    })?;
    if legacy.schema_version != LEGACY_EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION {
        return Err(ZkBenchError::validation(
            "bundle.schema_version",
            format!(
                "expected {LEGACY_EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION}, got {}",
                legacy.schema_version
            ),
        ));
    }
    let canonical = serde_json::to_string(&legacy).map_err(|error| {
        ZkBenchError::serialization("experiment_bundle.v1.json", error.to_string())
    })?;
    if json != canonical {
        return Err(ZkBenchError::validation(
            "bundle",
            "legacy v1 JSON must use the canonical serialized form",
        ));
    }

    require_text(&legacy.bundle_id, "bundle.bundle_id")?;
    require_text(&legacy.experiment_id, "bundle.experiment_id")?;
    require_text(&legacy.run_id, "bundle.run_id")?;
    if legacy.claim_boundary != ClaimBoundary::Level0DesignNote {
        return Err(ZkBenchError::ClaimBoundary {
            message: "adaptive observability metadata remains Level0DesignNote".to_string(),
        });
    }

    let experiment_id = legacy.experiment_id.clone();
    let run_id = legacy.run_id.clone();
    let bundle = ExperimentArtifactBundle {
        bundle_id: legacy.bundle_id,
        experiment_id: experiment_id.clone(),
        run_id: run_id.clone(),
        schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
        config: upgrade_experiment_artifact_ref_v1(
            legacy.config,
            &experiment_id,
            &run_id,
            "bundle.config",
        )?,
        task: upgrade_experiment_artifact_ref_v1(
            legacy.task,
            &experiment_id,
            &run_id,
            "bundle.task",
        )?,
        prompt: upgrade_experiment_artifact_ref_v1(
            legacy.prompt,
            &experiment_id,
            &run_id,
            "bundle.prompt",
        )?,
        response: upgrade_experiment_artifact_ref_v1(
            legacy.response,
            &experiment_id,
            &run_id,
            "bundle.response",
        )?,
        evaluation: upgrade_experiment_artifact_ref_v1(
            legacy.evaluation,
            &experiment_id,
            &run_id,
            "bundle.evaluation",
        )?,
        mechanism_record: upgrade_experiment_artifact_ref_v1(
            legacy.mechanism_record,
            &experiment_id,
            &run_id,
            "bundle.mechanism_record",
        )?,
        metadata: upgrade_experiment_artifact_ref_v1(
            legacy.metadata,
            &experiment_id,
            &run_id,
            "bundle.metadata",
        )?,
        logs: upgrade_experiment_artifact_ref_v1(
            legacy.logs,
            &experiment_id,
            &run_id,
            "bundle.logs",
        )?,
        report: upgrade_experiment_artifact_ref_v1(
            legacy.report,
            &experiment_id,
            &run_id,
            "bundle.report",
        )?,
        claim_boundary: legacy.claim_boundary,
    };
    validate_experiment_artifact_bundle(&bundle)?;
    Ok(bundle)
}

fn upgrade_experiment_artifact_ref_v1(
    legacy: LegacyExperimentArtifactRefV1,
    experiment_id: &str,
    run_id: &str,
    path: &str,
) -> Result<ExperimentArtifactRef> {
    let upgraded = ExperimentArtifactRef {
        uri: legacy.uri,
        kind: legacy.kind,
        experiment_id: experiment_id.to_string(),
        run_id: run_id.to_string(),
        digest: legacy.digest,
        provenance: legacy.provenance,
    };
    upgraded.validate_for(path, experiment_id, run_id)?;
    Ok(upgraded)
}

/// Compute the digest of the validated serialized bundle manifest.
pub fn compute_experiment_artifact_bundle_digest(
    bundle: &ExperimentArtifactBundle,
) -> Result<ArtifactDigest> {
    let json = serialize_experiment_artifact_bundle_json(bundle)?;
    Ok(compute_artifact_digest_bytes(
        json.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    ))
}

/// Collection tier allocated for one run.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ObservabilityTier {
    /// Minimal metadata, always enabled.
    Tier0,
    /// Sampled light mechanism data.
    Tier1,
    /// Anomaly-triggered deep dive.
    Tier2,
    /// Reserved gold case.
    Tier3,
}

/// Signals used by the scheduler, all on a 0..=1000 scale.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObservabilitySignals {
    /// Novelty signal.
    pub novelty_milli: u16,
    /// Uncertainty signal.
    pub uncertainty_milli: u16,
    /// Failure or anomaly signal.
    pub failure_milli: u16,
}

impl ObservabilitySignals {
    /// Validate bounded scheduler signals.
    pub fn validate(&self) -> Result<()> {
        for (name, value) in [
            ("novelty_milli", self.novelty_milli),
            ("uncertainty_milli", self.uncertainty_milli),
            ("failure_milli", self.failure_milli),
        ] {
            if value > OBSERVABILITY_SCORE_SCALE {
                return Err(ZkBenchError::validation(
                    format!("observability.signals.{name}"),
                    format!("score must be <= {OBSERVABILITY_SCORE_SCALE}"),
                ));
            }
        }
        Ok(())
    }
}

/// Remaining observability budget.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObservabilityBudget {
    /// Remaining Tier1 samples.
    pub tier1_samples_remaining: u32,
    /// Remaining Tier2 deep dives.
    pub tier2_deep_dives_remaining: u32,
    /// Remaining Tier3 gold cases.
    pub tier3_gold_cases_remaining: u32,
}

impl ObservabilityBudget {
    /// Verify that one scheduler allocation consumes exactly the selected tier.
    fn validate_allocation(before: &Self, after: &Self, tier: ObservabilityTier) -> Result<()> {
        let mut expected = before.clone();
        match tier {
            ObservabilityTier::Tier0 => {}
            ObservabilityTier::Tier1 => {
                expected.tier1_samples_remaining = before
                    .tier1_samples_remaining
                    .checked_sub(1)
                    .ok_or_else(|| {
                        ZkBenchError::validation(
                            "observability.budget",
                            "scheduler selected Tier1 without remaining budget",
                        )
                    })?;
            }
            ObservabilityTier::Tier2 => {
                expected.tier2_deep_dives_remaining = before
                    .tier2_deep_dives_remaining
                    .checked_sub(1)
                    .ok_or_else(|| {
                        ZkBenchError::validation(
                            "observability.budget",
                            "scheduler selected Tier2 without remaining budget",
                        )
                    })?;
            }
            ObservabilityTier::Tier3 => {
                expected.tier3_gold_cases_remaining = before
                    .tier3_gold_cases_remaining
                    .checked_sub(1)
                    .ok_or_else(|| {
                        ZkBenchError::validation(
                            "observability.budget",
                            "scheduler selected Tier3 without remaining budget",
                        )
                    })?;
            }
        }
        if after != &expected {
            return Err(ZkBenchError::validation(
                "observability.budget",
                "scheduler allocation must consume exactly the selected tier",
            ));
        }
        Ok(())
    }

    fn consume(&mut self, tier: ObservabilityTier) {
        match tier {
            ObservabilityTier::Tier0 => {}
            ObservabilityTier::Tier1 => self.tier1_samples_remaining -= 1,
            ObservabilityTier::Tier2 => self.tier2_deep_dives_remaining -= 1,
            ObservabilityTier::Tier3 => self.tier3_gold_cases_remaining -= 1,
        }
    }
}

/// Scheduler reason retained with the allocation decision.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ObservabilityReason {
    /// Novelty crossed a decision threshold.
    Novelty,
    /// Uncertainty crossed a decision threshold.
    Uncertainty,
    /// Failure crossed a decision threshold.
    Failure,
    /// Gold-case rule fired.
    GoldCase,
    /// No higher tier was eligible or budget remained.
    Tier0Fallback,
}

/// Deterministic allocation decision.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObservabilityDecision {
    /// Selected tier.
    pub tier: ObservabilityTier,
    /// Weighted priority score.
    pub priority_milli: u16,
    /// Signals used by the decision.
    pub signals: ObservabilitySignals,
    /// Reasons retained for audit.
    #[serde(default)]
    pub reasons: Vec<ObservabilityReason>,
}

impl ObservabilityDecision {
    /// Validate decision-local bounds before a policy-specific check.
    pub fn validate(&self, path: &str) -> Result<()> {
        self.signals.validate()?;
        if self.priority_milli > OBSERVABILITY_SCORE_SCALE {
            return Err(ZkBenchError::validation(
                format!("{path}.priority_milli"),
                format!("priority must be <= {OBSERVABILITY_SCORE_SCALE}"),
            ));
        }
        Ok(())
    }
}

/// Replaceable scheduler seam.
pub trait ObservabilityScheduler: Send + Sync {
    /// Implementation identity and policy version.
    fn descriptor(&self) -> ModuleDescriptor;
    /// Validate a decision produced by this scheduler implementation.
    fn validate_decision(&self, decision: &ObservabilityDecision) -> Result<()> {
        decision.validate("observability.decision")
    }
    /// Allocate one tier and consume only the selected budget.
    fn allocate(
        &self,
        signals: ObservabilitySignals,
        budget: &mut ObservabilityBudget,
    ) -> Result<ObservabilityDecision>;
}

/// Reference scheduler adapter. It is deterministic policy, not evidence.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct WeightedObservabilityScheduler {
    /// Novelty weight.
    pub novelty_weight_milli: u16,
    /// Uncertainty weight.
    pub uncertainty_weight_milli: u16,
    /// Failure weight.
    pub failure_weight_milli: u16,
}

impl Default for WeightedObservabilityScheduler {
    fn default() -> Self {
        Self {
            novelty_weight_milli: 350,
            uncertainty_weight_milli: 300,
            failure_weight_milli: 350,
        }
    }
}

impl ObservabilityScheduler for WeightedObservabilityScheduler {
    fn descriptor(&self) -> ModuleDescriptor {
        ModuleDescriptor {
            module_id: "observability-scheduler".to_string(),
            implementation_id: "weighted-observability-scheduler-v1".to_string(),
            version: format!(
                "weights-{}-{}-{}",
                self.novelty_weight_milli, self.uncertainty_weight_milli, self.failure_weight_milli
            ),
            source_revision: "experiment-unit-adaptive-observability-v1".to_string(),
        }
    }

    fn allocate(
        &self,
        signals: ObservabilitySignals,
        budget: &mut ObservabilityBudget,
    ) -> Result<ObservabilityDecision> {
        signals.validate()?;
        let weight_sum = self.novelty_weight_milli as u32
            + self.uncertainty_weight_milli as u32
            + self.failure_weight_milli as u32;
        if weight_sum == 0 {
            return Err(ZkBenchError::validation(
                "observability.scheduler.weights",
                "at least one weight must be non-zero",
            ));
        }
        let priority = ((signals.novelty_milli as u32 * self.novelty_weight_milli as u32
            + signals.uncertainty_milli as u32 * self.uncertainty_weight_milli as u32
            + signals.failure_milli as u32 * self.failure_weight_milli as u32)
            / weight_sum)
            .min(OBSERVABILITY_SCORE_SCALE as u32) as u16;
        let mut reasons = Vec::new();
        if signals.novelty_milli >= 700 {
            reasons.push(ObservabilityReason::Novelty);
        }
        if signals.uncertainty_milli >= 700 {
            reasons.push(ObservabilityReason::Uncertainty);
        }
        if signals.failure_milli >= 700 {
            reasons.push(ObservabilityReason::Failure);
        }

        let tier = if budget.tier3_gold_cases_remaining > 0
            && (priority >= 900 || (signals.novelty_milli >= 900 && signals.failure_milli >= 900))
        {
            reasons.push(ObservabilityReason::GoldCase);
            ObservabilityTier::Tier3
        } else if budget.tier2_deep_dives_remaining > 0
            && (priority >= 700 || signals.failure_milli >= 800)
        {
            ObservabilityTier::Tier2
        } else if budget.tier1_samples_remaining > 0 && priority >= 300 {
            ObservabilityTier::Tier1
        } else {
            reasons.push(ObservabilityReason::Tier0Fallback);
            ObservabilityTier::Tier0
        };
        budget.consume(tier);
        Ok(ObservabilityDecision {
            tier,
            priority_milli: priority,
            signals,
            reasons,
        })
    }

    fn validate_decision(&self, decision: &ObservabilityDecision) -> Result<()> {
        decision.validate("observability.decision")?;
        let expected_priority = self.priority(decision.signals);
        if decision.priority_milli != expected_priority {
            return Err(ZkBenchError::validation(
                "observability.decision.priority_milli",
                format!(
                    "weighted priority does not match scheduler inputs: expected {expected_priority}, got {}",
                    decision.priority_milli
                ),
            ));
        }
        let mut expected_reasons = Vec::new();
        if decision.signals.novelty_milli >= 700 {
            expected_reasons.push(ObservabilityReason::Novelty);
        }
        if decision.signals.uncertainty_milli >= 700 {
            expected_reasons.push(ObservabilityReason::Uncertainty);
        }
        if decision.signals.failure_milli >= 700 {
            expected_reasons.push(ObservabilityReason::Failure);
        }
        if decision.tier == ObservabilityTier::Tier3 {
            let gold_rule = decision.priority_milli >= 900
                || (decision.signals.novelty_milli >= 900 && decision.signals.failure_milli >= 900);
            if !gold_rule {
                return Err(ZkBenchError::validation(
                    "observability.decision.tier",
                    "Tier3 decision does not satisfy the gold-case rule",
                ));
            }
            expected_reasons.push(ObservabilityReason::GoldCase);
        }
        if decision.tier == ObservabilityTier::Tier0 {
            expected_reasons.push(ObservabilityReason::Tier0Fallback);
        }
        if decision
            .reasons
            .iter()
            .any(|reason| !expected_reasons.contains(reason))
            || decision.reasons.len() != expected_reasons.len()
            || expected_reasons
                .iter()
                .any(|reason| !decision.reasons.contains(reason))
        {
            return Err(ZkBenchError::validation(
                "observability.decision.reasons",
                "decision reasons do not match the weighted scheduler rules",
            ));
        }
        Ok(())
    }
}

impl WeightedObservabilityScheduler {
    fn priority(&self, signals: ObservabilitySignals) -> u16 {
        let weight_sum = self.novelty_weight_milli as u32
            + self.uncertainty_weight_milli as u32
            + self.failure_weight_milli as u32;
        if weight_sum == 0 {
            return 0;
        }
        ((signals.novelty_milli as u32 * self.novelty_weight_milli as u32
            + signals.uncertainty_milli as u32 * self.uncertainty_weight_milli as u32
            + signals.failure_milli as u32 * self.failure_weight_milli as u32)
            / weight_sum)
            .min(OBSERVABILITY_SCORE_SCALE as u32) as u16
    }
}

/// Status of one mechanism record.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MechanismRecordStatus {
    /// Tier0 metadata only.
    MetadataOnly,
    /// Tier1 sampled record.
    Sampled,
    /// Tier2 deep dive.
    DeepDive,
    /// Tier3 gold case.
    GoldCase,
    /// Collection failed; failure is retained.
    Failed,
}

/// One mechanism record appended to the mechanism ledger.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MechanismRecord {
    /// Stable record id.
    pub record_id: String,
    /// Experiment id.
    pub experiment_id: String,
    /// Run id.
    pub run_id: String,
    /// Allocated tier.
    pub tier: ObservabilityTier,
    /// Collection status.
    pub status: MechanismRecordStatus,
    /// Collector descriptor, absent for Tier0 metadata-only records.
    #[serde(default)]
    pub collector: Option<ModuleDescriptor>,
    /// Digest of the retained mechanism payload, if one exists.
    #[serde(default)]
    pub payload_digest: Option<ArtifactDigest>,
    /// Required explanation when collection failed.
    #[serde(default)]
    pub failure_reason: Option<String>,
    /// Scheduler decision.
    pub decision: ObservabilityDecision,
    /// Record provenance.
    pub provenance: ExperimentProvenance,
}

impl MechanismRecord {
    /// Validate tier/status/collector/provenance invariants.
    pub fn validate(&self, path: &str) -> Result<()> {
        require_text(&self.record_id, format!("{path}.record_id"))?;
        require_text(&self.experiment_id, format!("{path}.experiment_id"))?;
        require_text(&self.run_id, format!("{path}.run_id"))?;
        self.provenance.validate(&format!("{path}.provenance"))?;
        self.decision.validate(&format!("{path}.decision"))?;
        if self.decision.tier != self.tier {
            return Err(ZkBenchError::validation(
                format!("{path}.decision.tier"),
                "mechanism record tier must match scheduler decision",
            ));
        }
        let expected_status = match self.tier {
            ObservabilityTier::Tier0 => MechanismRecordStatus::MetadataOnly,
            ObservabilityTier::Tier1 => MechanismRecordStatus::Sampled,
            ObservabilityTier::Tier2 => MechanismRecordStatus::DeepDive,
            ObservabilityTier::Tier3 => MechanismRecordStatus::GoldCase,
        };
        if self.status != expected_status && self.status != MechanismRecordStatus::Failed {
            return Err(ZkBenchError::validation(
                format!("{path}.status"),
                "mechanism status must match its allocated tier",
            ));
        }
        if self.status == MechanismRecordStatus::Failed {
            if self
                .failure_reason
                .as_deref()
                .unwrap_or("")
                .trim()
                .is_empty()
            {
                return Err(ZkBenchError::validation(
                    format!("{path}.failure_reason"),
                    "failed mechanism records require a failure reason",
                ));
            }
        } else if self.failure_reason.is_some() {
            return Err(ZkBenchError::validation(
                format!("{path}.failure_reason"),
                "non-failed mechanism records must not carry a failure reason",
            ));
        }
        if self.tier == ObservabilityTier::Tier0 && self.collector.is_some() {
            return Err(ZkBenchError::validation(
                format!("{path}.collector"),
                "Tier0 metadata-only records must not carry a collector",
            ));
        }
        if let Some(payload_digest) = &self.payload_digest {
            validate_artifact_digest_metadata(payload_digest, &format!("{path}.payload_digest"))?;
        }
        if self.tier == ObservabilityTier::Tier0 && self.payload_digest.is_some() {
            return Err(ZkBenchError::validation(
                format!("{path}.payload_digest"),
                "Tier0 metadata-only records must not carry a mechanism payload",
            ));
        }
        if self.status != MechanismRecordStatus::Failed
            && self.tier != ObservabilityTier::Tier0
            && self.collector.is_none()
        {
            return Err(ZkBenchError::validation(
                format!("{path}.collector"),
                "sampled, deep, and gold records require a collector",
            ));
        }
        if let Some(collector) = &self.collector {
            collector.validate(&format!("{path}.collector"))?;
        }
        Ok(())
    }
}

/// Append-only mechanism ledger with a digest chain.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MechanismLedger {
    /// Ledger schema version.
    pub schema_version: String,
    /// Experiment id shared by all records.
    pub experiment_id: String,
    /// Historical entries. New evidence appends.
    #[serde(default)]
    pub entries: Vec<MechanismLedgerEntry>,
    /// Digest of the final entry.
    #[serde(default)]
    pub tip_digest: Option<ArtifactDigest>,
}

/// One digest-bound append-only ledger entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MechanismLedgerEntry {
    /// Zero-based sequence number.
    pub sequence_number: u64,
    /// Digest of the previous entry.
    #[serde(default)]
    pub previous_digest: Option<ArtifactDigest>,
    /// Mechanism record.
    pub record: MechanismRecord,
    /// Digest over sequence, previous digest, and record.
    pub entry_digest: ArtifactDigest,
}

impl MechanismLedger {
    /// Create an empty ledger.
    pub fn new(experiment_id: impl Into<String>) -> Self {
        Self {
            schema_version: ADAPTIVE_MECHANISM_LEDGER_SCHEMA_VERSION.to_string(),
            experiment_id: experiment_id.into(),
            entries: Vec::new(),
            tip_digest: None,
        }
    }

    /// Append one record without replacing prior entries.
    pub fn append(&mut self, record: MechanismRecord) -> Result<()> {
        self.validate()?;
        record.validate("mechanism_ledger.record")?;
        if record.experiment_id != self.experiment_id {
            return Err(ZkBenchError::validation(
                "mechanism_ledger.record.experiment_id",
                "record experiment_id does not match ledger",
            ));
        }
        let sequence_number = self.entries.len() as u64;
        let previous_digest = self.entries.last().map(|entry| entry.entry_digest.clone());
        let preimage = (sequence_number, previous_digest.as_ref(), &record);
        let entry_digest = compute_artifact_digest(
            &preimage,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?;
        self.entries.push(MechanismLedgerEntry {
            sequence_number,
            previous_digest,
            record,
            entry_digest: entry_digest.clone(),
        });
        self.tip_digest = Some(entry_digest);
        Ok(())
    }

    /// Validate schema, ordering, identity, and the append digest chain.
    pub fn validate(&self) -> Result<()> {
        require_text(&self.experiment_id, "mechanism_ledger.experiment_id")?;
        if self.schema_version != ADAPTIVE_MECHANISM_LEDGER_SCHEMA_VERSION {
            return Err(ZkBenchError::validation(
                "mechanism_ledger.schema_version",
                "unsupported mechanism ledger schema version",
            ));
        }
        let mut previous_digest = None;
        for (index, entry) in self.entries.iter().enumerate() {
            if entry.sequence_number != index as u64 {
                return Err(ZkBenchError::validation(
                    format!("mechanism_ledger.entries[{index}].sequence_number"),
                    "sequence number does not match append position",
                ));
            }
            if entry.previous_digest != previous_digest {
                return Err(ZkBenchError::validation(
                    format!("mechanism_ledger.entries[{index}].previous_digest"),
                    "previous digest does not match prior entry",
                ));
            }
            entry
                .record
                .validate(&format!("mechanism_ledger.entries[{index}].record"))?;
            if entry.record.experiment_id != self.experiment_id {
                return Err(ZkBenchError::validation(
                    format!("mechanism_ledger.entries[{index}].record.experiment_id"),
                    "record experiment_id does not match ledger",
                ));
            }
            let expected = compute_artifact_digest(
                &(
                    entry.sequence_number,
                    entry.previous_digest.as_ref(),
                    &entry.record,
                ),
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Manifest),
            )?;
            if entry.entry_digest != expected {
                return Err(ZkBenchError::validation(
                    format!("mechanism_ledger.entries[{index}].entry_digest"),
                    "entry digest does not match append preimage",
                ));
            }
            previous_digest = Some(entry.entry_digest.clone());
        }
        if self.tip_digest != previous_digest {
            return Err(ZkBenchError::validation(
                "mechanism_ledger.tip_digest",
                "tip digest does not match final entry",
            ));
        }
        Ok(())
    }
}

/// Serialize a validated mechanism ledger using its canonical JSON form.
pub fn serialize_mechanism_ledger_json(ledger: &MechanismLedger) -> Result<String> {
    ledger.validate()?;
    serde_json::to_string(ledger)
        .map_err(|error| ZkBenchError::serialization("mechanism_ledger.json", error.to_string()))
}

/// Deserialize and validate one canonical mechanism ledger.
pub fn deserialize_mechanism_ledger_json(json: &str) -> Result<MechanismLedger> {
    let ledger: MechanismLedger = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("mechanism_ledger.json", error.to_string())
    })?;
    let canonical_json = serialize_mechanism_ledger_json(&ledger)?;
    if json != canonical_json {
        return Err(ZkBenchError::validation(
            "mechanism_ledger.json",
            "ledger bytes are not the canonical serialization",
        ));
    }
    Ok(ledger)
}

/// Minimal context passed through the Task seam.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TaskContext {
    /// Experiment identity for artifacts materialized by the Task.
    pub experiment_id: String,
    /// Run identity for artifacts materialized by the Task.
    pub run_id: String,
    /// Stable task id.
    pub task_id: String,
    /// Digest of the frozen task/config input.
    pub input_digest: ArtifactDigest,
    /// Task provenance.
    pub provenance: ExperimentProvenance,
}

/// Output of a Task implementation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TaskOutput {
    /// Task artifact reference.
    pub task_artifact: ExperimentArtifactRef,
    /// Prompt artifact reference.
    pub prompt_artifact: ExperimentArtifactRef,
}

/// Context passed to a ResponseProducer implementation.
pub struct ResponseContext<'a> {
    /// Experiment identity for the response artifact.
    pub experiment_id: &'a str,
    /// Run identity for the response artifact.
    pub run_id: &'a str,
    /// Task artifact.
    pub task: &'a ExperimentArtifactRef,
    /// Prompt artifact.
    pub prompt: &'a ExperimentArtifactRef,
    /// Run provenance.
    pub provenance: &'a ExperimentProvenance,
}

/// Output of a ResponseProducer implementation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ResponseOutput {
    /// Response artifact reference.
    pub response_artifact: ExperimentArtifactRef,
}

/// Replaceable response-production seam. This may be a fixture or a future
/// authorized runtime adapter; this contract itself performs no execution.
pub trait ResponseProducer: Send + Sync {
    /// Implementation identity.
    fn descriptor(&self) -> &ModuleDescriptor;
    /// Materialize one response artifact from the task and prompt.
    fn produce(&self, context: ResponseContext<'_>) -> Result<ResponseOutput>;
}

/// Replaceable experiment runner seam that must emit the fixed bundle shape.
pub trait ExperimentRunner: Send + Sync {
    /// Execute one configured run and return all nine artifact slots.
    fn run(&mut self) -> Result<ExperimentArtifactBundle>;
}

/// Replaceable Task seam.
pub trait Task: Send + Sync {
    /// Implementation identity.
    fn descriptor(&self) -> &ModuleDescriptor;
    /// Materialize the task and prompt artifacts.
    fn materialize(&self, context: &TaskContext) -> Result<TaskOutput>;
}

/// Context passed to a Metric implementation.
pub struct MetricContext<'a> {
    /// Task artifact reference.
    pub task: &'a ExperimentArtifactRef,
    /// Response artifact reference.
    pub response: &'a ExperimentArtifactRef,
}

/// One metric observation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetricObservation {
    /// Metric implementation.
    pub metric: ModuleDescriptor,
    /// Whether measurement was obtained.
    pub status: MetricObservationStatus,
    /// Optional scalar value in the metric's declared unit.
    #[serde(default)]
    pub value: Option<i64>,
    /// Metric provenance.
    pub provenance: ExperimentProvenance,
}

impl MetricObservation {
    /// Validate metric identity, measurement state, and provenance.
    pub fn validate(&self, path: &str) -> Result<()> {
        self.metric.validate(&format!("{path}.metric"))?;
        self.provenance.validate(&format!("{path}.provenance"))?;
        match (self.status, self.value.is_some()) {
            (MetricObservationStatus::Measured, false) => Err(ZkBenchError::validation(
                format!("{path}.value"),
                "measured observations require a scalar value",
            )),
            (MetricObservationStatus::Unavailable, true)
            | (MetricObservationStatus::Failed, true) => Err(ZkBenchError::validation(
                format!("{path}.value"),
                "unavailable and failed observations must not carry a scalar value",
            )),
            _ => Ok(()),
        }
    }
}

/// Metric measurement status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MetricObservationStatus {
    /// Measurement exists.
    Measured,
    /// Metric does not apply.
    Unavailable,
    /// Metric implementation failed.
    Failed,
}

/// Replaceable Metric seam.
pub trait Metric: Send + Sync {
    /// Implementation identity.
    fn descriptor(&self) -> &ModuleDescriptor;
    /// Measure a task/response pair.
    fn measure(&self, context: MetricContext<'_>) -> Result<MetricObservation>;
}

/// Context passed to an Evaluator implementation.
pub struct EvaluationContext<'a> {
    /// Task artifact.
    pub task: &'a ExperimentArtifactRef,
    /// Response artifact.
    pub response: &'a ExperimentArtifactRef,
    /// Metric observations.
    pub metrics: &'a [MetricObservation],
}

/// Explicit result class so negative and inconclusive results remain data,
/// rather than being inferred from free-form report text.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ExperimentOutcome {
    /// The declared result direction was observed.
    Positive,
    /// The declared result direction was not observed.
    Negative,
    /// The run completed but did not resolve the hypothesis.
    Inconclusive,
    /// The run or evaluation failed.
    Failed,
    /// The experiment was recorded without an execution result.
    NotRun,
}

/// Evaluation record produced by an Evaluator.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvaluationRecord {
    /// Evaluator implementation.
    pub evaluator: ModuleDescriptor,
    /// Result status, including negative or inconclusive outcomes.
    pub status: String,
    /// Typed result class retained in the fixed evaluation artifact.
    pub outcome: ExperimentOutcome,
    /// Metric observations included in this evaluation.
    pub metrics: Vec<MetricObservation>,
    /// Evaluation provenance.
    pub provenance: ExperimentProvenance,
}

impl EvaluationRecord {
    /// Validate evaluator identity, typed outcome/status agreement, unique
    /// metric observations, and provenance.
    pub fn validate(&self, path: &str) -> Result<()> {
        self.evaluator.validate(&format!("{path}.evaluator"))?;
        require_text(&self.status, format!("{path}.status"))?;
        self.provenance.validate(&format!("{path}.provenance"))?;
        let status_allowed = match self.outcome {
            ExperimentOutcome::Positive => self.status == "positive_result",
            ExperimentOutcome::Negative => self.status == "negative_result",
            ExperimentOutcome::Inconclusive => self.status == "inconclusive",
            ExperimentOutcome::Failed => self.status == "failed",
            ExperimentOutcome::NotRun => self.status == "not_run",
        };
        if !status_allowed {
            return Err(ZkBenchError::validation(
                format!("{path}.status"),
                "evaluation status does not match its typed outcome",
            ));
        }
        let mut metric_ids = BTreeSet::new();
        for (index, metric) in self.metrics.iter().enumerate() {
            metric.validate(&format!("{path}.metrics[{index}]"))?;
            let identity = (
                metric.metric.module_id.as_str(),
                metric.metric.implementation_id.as_str(),
                metric.metric.version.as_str(),
                metric.metric.source_revision.as_str(),
            );
            if !metric_ids.insert(identity) {
                return Err(ZkBenchError::validation(
                    format!("{path}.metrics[{index}].metric"),
                    "evaluation metric identity is duplicated",
                ));
            }
        }
        Ok(())
    }
}

/// Replaceable Evaluator seam.
pub trait Evaluator: Send + Sync {
    /// Implementation identity.
    fn descriptor(&self) -> &ModuleDescriptor;
    /// Evaluate the response using swappable Metric observations.
    fn evaluate(&self, context: EvaluationContext<'_>) -> Result<EvaluationRecord>;
}

/// Context passed to a MechanismCollector implementation.
pub struct MechanismCollectionContext<'a> {
    /// Experiment id for the record being collected.
    pub experiment_id: &'a str,
    /// Run id for the record being collected.
    pub run_id: &'a str,
    /// Task artifact.
    pub task: &'a ExperimentArtifactRef,
    /// Response artifact.
    pub response: &'a ExperimentArtifactRef,
    /// Evaluation record.
    pub evaluation: &'a EvaluationRecord,
    /// Scheduler decision.
    pub decision: &'a ObservabilityDecision,
}

/// Replaceable MechanismCollector seam.
pub trait MechanismCollector: Send + Sync {
    /// Implementation identity.
    fn descriptor(&self) -> &ModuleDescriptor;
    /// Collect only the tier authorized by the scheduler.
    fn collect(&self, context: MechanismCollectionContext<'_>) -> Result<MechanismRecord>;
}

/// Immutable identity and hypothesis for one experiment run.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentRunSpec {
    /// Stable bundle id.
    pub bundle_id: String,
    /// Stable experiment id shared by replications.
    pub experiment_id: String,
    /// Stable run id within the experiment.
    pub run_id: String,
    /// Explicit hypothesis or research question.
    pub hypothesis: String,
    /// Whether this run is an explicitly identified replication.
    pub replication: bool,
    /// Frozen task context.
    pub task_context: TaskContext,
    /// Signals supplied to the scheduler before collection.
    pub signals: ObservabilitySignals,
    /// Run provenance.
    pub provenance: ExperimentProvenance,
}

impl ExperimentRunSpec {
    /// Validate identities, hypothesis, task context, signals, and provenance.
    pub fn validate(&self) -> Result<()> {
        for (path, value) in [
            ("run_spec.bundle_id", &self.bundle_id),
            ("run_spec.experiment_id", &self.experiment_id),
            ("run_spec.run_id", &self.run_id),
            ("run_spec.hypothesis", &self.hypothesis),
            (
                "run_spec.task_context.experiment_id",
                &self.task_context.experiment_id,
            ),
            ("run_spec.task_context.run_id", &self.task_context.run_id),
            ("run_spec.task_context.task_id", &self.task_context.task_id),
        ] {
            require_text(value, path)?;
        }
        self.signals.validate()?;
        self.provenance.validate("run_spec.provenance")?;
        self.task_context
            .provenance
            .validate("run_spec.task_context.provenance")?;
        if self.task_context.experiment_id != self.experiment_id {
            return Err(ZkBenchError::validation(
                "run_spec.task_context.experiment_id",
                "task context experiment identity does not match the run",
            ));
        }
        if self.task_context.run_id != self.run_id {
            return Err(ZkBenchError::validation(
                "run_spec.task_context.run_id",
                "task context run identity does not match the run",
            ));
        }
        Ok(())
    }
}

/// Payload stored in the fixed config slot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentRunConfig {
    /// Config schema version.
    pub schema_version: String,
    /// Immutable run spec.
    pub run_spec: ExperimentRunSpec,
    /// Budget before this run's allocation.
    pub initial_budget: ObservabilityBudget,
    /// Module descriptors frozen for this run.
    pub modules: Vec<ModuleDescriptor>,
}

/// Payload stored in the fixed metadata slot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentRunMetadata {
    /// Metadata schema version.
    pub schema_version: String,
    /// Experiment id.
    pub experiment_id: String,
    /// Run id.
    pub run_id: String,
    /// Hypothesis copied into the run metadata slot.
    pub hypothesis: String,
    /// Replication marker from the frozen run spec.
    pub replication: bool,
    /// Lifecycle status.
    pub lifecycle: String,
    /// Scheduler decision.
    pub observability: ObservabilityDecision,
    /// Budget after this run's allocation.
    pub remaining_budget: ObservabilityBudget,
    /// Module descriptors used by this run.
    pub modules: Vec<ModuleDescriptor>,
    /// Claim ceiling for this metadata-only contract.
    pub claim_boundary: ClaimBoundary,
    /// Metadata provenance.
    pub provenance: ExperimentProvenance,
}

/// Payload stored in the fixed logs slot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentRunLogs {
    /// Logs schema version.
    pub schema_version: String,
    /// Declared retention policy.
    pub retention_policy: String,
    /// Structured metadata-only log entries.
    pub entries: Vec<String>,
    /// Log provenance.
    pub provenance: ExperimentProvenance,
}

/// Payload stored in the fixed report slot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentRunReport {
    /// Report schema version.
    pub schema_version: String,
    /// Experiment id.
    pub experiment_id: String,
    /// Run id.
    pub run_id: String,
    /// Typed result class.
    pub outcome: ExperimentOutcome,
    /// Evaluator status label.
    pub status: String,
    /// Explicit first-class negative-result marker.
    pub negative_result: bool,
    /// Limitations and non-claims.
    pub limitations: Vec<String>,
    /// Claim ceiling.
    pub claim_boundary: ClaimBoundary,
    /// Report provenance.
    pub provenance: ExperimentProvenance,
}

impl ExperimentRunReport {
    /// Validate report identity, typed result semantics, limitations, and
    /// provenance without asserting scientific validity.
    pub fn validate(&self, path: &str) -> Result<()> {
        require_text(&self.schema_version, format!("{path}.schema_version"))?;
        if self.schema_version != EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION {
            return Err(ZkBenchError::validation(
                format!("{path}.schema_version"),
                format!(
                    "expected {EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION}, got {}",
                    self.schema_version
                ),
            ));
        }
        require_text(&self.experiment_id, format!("{path}.experiment_id"))?;
        require_text(&self.run_id, format!("{path}.run_id"))?;
        require_text(&self.status, format!("{path}.status"))?;
        let status_allowed = match self.outcome {
            ExperimentOutcome::Positive => self.status == "positive_result",
            ExperimentOutcome::Negative => self.status == "negative_result",
            ExperimentOutcome::Inconclusive => self.status == "inconclusive",
            ExperimentOutcome::Failed => self.status == "failed",
            ExperimentOutcome::NotRun => self.status == "not_run",
        };
        if !status_allowed {
            return Err(ZkBenchError::validation(
                format!("{path}.status"),
                "report status does not match its typed outcome",
            ));
        }
        if self.negative_result != (self.outcome == ExperimentOutcome::Negative) {
            return Err(ZkBenchError::validation(
                format!("{path}.negative_result"),
                "negative-result marker does not match its typed outcome",
            ));
        }
        if self.claim_boundary != ClaimBoundary::Level0DesignNote {
            return Err(ZkBenchError::ClaimBoundary {
                message: "experiment reports remain Level0DesignNote metadata".to_string(),
            });
        }
        if self.limitations.is_empty() {
            return Err(ZkBenchError::validation(
                format!("{path}.limitations"),
                "report must declare at least one limitation",
            ));
        }
        for (index, limitation) in self.limitations.iter().enumerate() {
            require_text(limitation, format!("{path}.limitations[{index}]"))?;
        }
        self.provenance.validate(&format!("{path}.provenance"))?;
        Ok(())
    }

    /// Validate intrinsic report fields and bind the report to the active run.
    pub fn validate_for(&self, path: &str, experiment_id: &str, run_id: &str) -> Result<()> {
        self.validate(path)?;
        if self.experiment_id != experiment_id {
            return Err(ZkBenchError::validation(
                format!("{path}.experiment_id"),
                "report experiment identity does not match the active run",
            ));
        }
        if self.run_id != run_id {
            return Err(ZkBenchError::validation(
                format!("{path}.run_id"),
                "report run identity does not match the active run",
            ));
        }
        Ok(())
    }
}

/// Validate a report payload and bind it to the report artifact reference,
/// including the active experiment/run identity and exact serialized digest.
pub fn validate_experiment_report_artifact(
    artifact: &ExperimentArtifactRef,
    report: &ExperimentRunReport,
    experiment_id: &str,
    run_id: &str,
    path: &str,
) -> Result<()> {
    report.validate_for(&format!("{path}.payload"), experiment_id, run_id)?;
    validate_experiment_artifact_payload(
        artifact,
        ExperimentArtifactKind::Report,
        report,
        experiment_id,
        run_id,
        path,
    )
}

/// Shared identity and provenance policy for fixed-slot artifact references.
///
/// Generic and local runners retain their adapter-specific payloads, while
/// this private policy owns the repeated reference construction and typed
/// report binding. That keeps artifact identity, provenance, and report digest
/// ordering in one testable Interface without changing the serialized slots.
pub(crate) struct ExperimentArtifactReferencePolicy {
    experiment_id: String,
    run_id: String,
    provenance: ExperimentProvenance,
}

impl ExperimentArtifactReferencePolicy {
    pub(crate) fn new(
        experiment_id: impl Into<String>,
        run_id: impl Into<String>,
        provenance: ExperimentProvenance,
    ) -> Result<Self> {
        let policy = Self {
            experiment_id: experiment_id.into(),
            run_id: run_id.into(),
            provenance,
        };
        require_text(&policy.experiment_id, "artifact_policy.experiment_id")?;
        require_text(&policy.run_id, "artifact_policy.run_id")?;
        policy.provenance.validate("artifact_policy.provenance")?;
        Ok(policy)
    }

    pub(crate) fn reference<T: Serialize>(
        &self,
        uri: impl Into<String>,
        kind: ExperimentArtifactKind,
        payload: &T,
    ) -> Result<ExperimentArtifactRef> {
        create_experiment_artifact_ref(
            uri,
            kind,
            payload,
            &self.experiment_id,
            &self.run_id,
            self.provenance.clone(),
        )
    }

    pub(crate) fn report(
        &self,
        payload: &ExperimentRunReport,
        path: &str,
    ) -> Result<ExperimentArtifactRef> {
        let artifact =
            self.reference("run/report.json", ExperimentArtifactKind::Report, payload)?;
        validate_experiment_report_artifact(
            &artifact,
            payload,
            &self.experiment_id,
            &self.run_id,
            path,
        )?;
        Ok(artifact)
    }
}

/// Deserialize one canonical report payload and validate it against a bundle's
/// report reference. The manifest validator alone cannot inspect this payload.
pub fn deserialize_experiment_report_json(
    json: &str,
    bundle: &ExperimentArtifactBundle,
) -> Result<ExperimentRunReport> {
    let report: ExperimentRunReport = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::serialization("experiment_report.json", error.to_string())
    })?;
    let canonical_json = serde_json::to_string(&report).map_err(|error| {
        ZkBenchError::serialization("experiment_report.json", error.to_string())
    })?;
    if json != canonical_json {
        return Err(ZkBenchError::validation(
            "experiment_report.json",
            "report bytes are not the canonical serialization",
        ));
    }
    validate_experiment_report_artifact(
        &bundle.report,
        &report,
        &bundle.experiment_id,
        &bundle.run_id,
        "bundle.report",
    )?;
    Ok(report)
}

/// Concrete composition adapter for the fixed nine-slot experiment bundle.
///
/// The adapter owns only contract composition and scheduler budget state. It
/// delegates task, response, metric, evaluation, and mechanism behavior to
/// swappable adapters at their seams.
pub struct ComposedExperimentRunner {
    /// Immutable run identity and hypothesis.
    pub spec: ExperimentRunSpec,
    /// Task adapter.
    pub task: Box<dyn Task>,
    /// Response adapter.
    pub response_producer: Box<dyn ResponseProducer>,
    /// Metric adapters.
    pub metrics: Vec<Box<dyn Metric>>,
    /// Evaluator adapter.
    pub evaluator: Box<dyn Evaluator>,
    /// Mechanism collector adapter.
    pub collector: Box<dyn MechanismCollector>,
    /// Observability scheduler adapter.
    pub scheduler: Box<dyn ObservabilityScheduler>,
    /// Mutable campaign-local budget.
    pub budget: ObservabilityBudget,
    /// Append-only mechanism ledger for this fixed run.
    mechanism_ledger: Option<MechanismLedger>,
}

/// Private tentative state for one observability run lifecycle.
///
/// Scheduler allocation and ledger append operations target this transaction,
/// never the runner's retained state. Callers commit only after the complete
/// nine-slot bundle and its payload projections validate.
struct ObservabilityRunLifecycleTransaction {
    next_budget: ObservabilityBudget,
    next_ledger: MechanismLedger,
}

impl ObservabilityRunLifecycleTransaction {
    fn new(current_budget: &ObservabilityBudget, experiment_id: &str) -> Self {
        Self {
            next_budget: current_budget.clone(),
            next_ledger: MechanismLedger::new(experiment_id),
        }
    }

    fn allocate(
        &mut self,
        scheduler: &dyn ObservabilityScheduler,
        signals: ObservabilitySignals,
    ) -> Result<ObservabilityDecision> {
        let before = self.next_budget.clone();
        let decision = scheduler.allocate(signals, &mut self.next_budget)?;
        scheduler.validate_decision(&decision)?;
        ObservabilityBudget::validate_allocation(&before, &self.next_budget, decision.tier)?;
        Ok(decision)
    }

    fn append_mechanism(&mut self, mechanism: MechanismRecord) -> Result<()> {
        self.next_ledger.append(mechanism)?;
        self.next_ledger.validate()
    }

    fn remaining_budget(&self) -> &ObservabilityBudget {
        &self.next_budget
    }

    fn commit(
        self,
        budget: &mut ObservabilityBudget,
        mechanism_ledger: &mut Option<MechanismLedger>,
    ) {
        *budget = self.next_budget;
        *mechanism_ledger = Some(self.next_ledger);
    }
}

impl ComposedExperimentRunner {
    /// Construct a runner after validating all module identities and the run
    /// spec. No execution or external access occurs here.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        spec: ExperimentRunSpec,
        task: Box<dyn Task>,
        response_producer: Box<dyn ResponseProducer>,
        metrics: Vec<Box<dyn Metric>>,
        evaluator: Box<dyn Evaluator>,
        collector: Box<dyn MechanismCollector>,
        scheduler: Box<dyn ObservabilityScheduler>,
        budget: ObservabilityBudget,
    ) -> Result<Self> {
        spec.validate()?;
        task.descriptor().validate("runner.task")?;
        response_producer
            .descriptor()
            .validate("runner.response_producer")?;
        for (index, metric) in metrics.iter().enumerate() {
            metric
                .descriptor()
                .validate(&format!("runner.metrics[{index}]"))?;
        }
        evaluator.descriptor().validate("runner.evaluator")?;
        collector.descriptor().validate("runner.collector")?;
        scheduler.descriptor().validate("runner.scheduler")?;
        let runner = Self {
            spec,
            task,
            response_producer,
            metrics,
            evaluator,
            collector,
            scheduler,
            budget,
            mechanism_ledger: None,
        };
        runner.module_descriptors()?;
        Ok(runner)
    }

    /// Return the budget after the most recent run allocation.
    pub fn remaining_budget(&self) -> &ObservabilityBudget {
        &self.budget
    }

    /// Return the append-only mechanism ledger after a successful run.
    pub fn mechanism_ledger(&self) -> Option<&MechanismLedger> {
        self.mechanism_ledger.as_ref()
    }

    fn module_descriptors(&self) -> Result<Vec<ModuleDescriptor>> {
        let mut modules = vec![
            self.task.descriptor().clone(),
            self.response_producer.descriptor().clone(),
        ];
        modules.extend(
            self.metrics
                .iter()
                .map(|metric| metric.descriptor().clone()),
        );
        modules.push(self.evaluator.descriptor().clone());
        modules.push(self.collector.descriptor().clone());
        modules.push(self.scheduler.descriptor());
        validate_module_manifest(&modules, "runner.modules")?;
        Ok(modules)
    }
}

impl ExperimentRunner for ComposedExperimentRunner {
    fn run(&mut self) -> Result<ExperimentArtifactBundle> {
        if self.mechanism_ledger.is_some() {
            return Err(ZkBenchError::validation(
                "runner",
                "runner instances are one-shot for their fixed run id",
            ));
        }
        self.spec.validate()?;
        let artifact_policy = ExperimentArtifactReferencePolicy::new(
            self.spec.experiment_id.clone(),
            self.spec.run_id.clone(),
            self.spec.provenance.clone(),
        )?;
        let initial_budget = self.budget.clone();
        let modules = self.module_descriptors()?;
        let config_payload = ExperimentRunConfig {
            schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
            run_spec: self.spec.clone(),
            initial_budget,
            modules: modules.clone(),
        };
        let config = artifact_policy.reference(
            "run/config.json",
            ExperimentArtifactKind::Config,
            &config_payload,
        )?;

        let task_output = self.task.materialize(&self.spec.task_context)?;
        require_artifact_kind(
            &task_output.task_artifact,
            ExperimentArtifactKind::Task,
            "runner.task_artifact",
        )?;
        task_output.task_artifact.validate_for(
            "runner.task_artifact",
            &self.spec.experiment_id,
            &self.spec.run_id,
        )?;
        require_artifact_kind(
            &task_output.prompt_artifact,
            ExperimentArtifactKind::Prompt,
            "runner.prompt_artifact",
        )?;
        task_output.prompt_artifact.validate_for(
            "runner.prompt_artifact",
            &self.spec.experiment_id,
            &self.spec.run_id,
        )?;
        let response_output = self.response_producer.produce(ResponseContext {
            experiment_id: &self.spec.experiment_id,
            run_id: &self.spec.run_id,
            task: &task_output.task_artifact,
            prompt: &task_output.prompt_artifact,
            provenance: &self.spec.provenance,
        })?;
        require_artifact_kind(
            &response_output.response_artifact,
            ExperimentArtifactKind::Response,
            "runner.response_artifact",
        )?;
        response_output.response_artifact.validate_for(
            "runner.response_artifact",
            &self.spec.experiment_id,
            &self.spec.run_id,
        )?;

        let mut observations = Vec::with_capacity(self.metrics.len());
        for (index, metric) in self.metrics.iter().enumerate() {
            let observation = metric.measure(MetricContext {
                task: &task_output.task_artifact,
                response: &response_output.response_artifact,
            })?;
            if observation.metric != *metric.descriptor() {
                return Err(ZkBenchError::validation(
                    format!("runner.metrics[{index}].metric"),
                    "metric observation identity does not match its adapter",
                ));
            }
            observation.validate(&format!("runner.metrics[{index}]"))?;
            observations.push(observation);
        }

        let evaluation = self.evaluator.evaluate(EvaluationContext {
            task: &task_output.task_artifact,
            response: &response_output.response_artifact,
            metrics: &observations,
        })?;
        if evaluation.evaluator != *self.evaluator.descriptor() {
            return Err(ZkBenchError::validation(
                "runner.evaluation.evaluator",
                "evaluation identity does not match its adapter",
            ));
        }
        evaluation.validate("runner.evaluation")?;
        if evaluation.metrics != observations {
            return Err(ZkBenchError::validation(
                "runner.evaluation.metrics",
                "evaluator must retain the metric observations it received",
            ));
        }
        let mut lifecycle =
            ObservabilityRunLifecycleTransaction::new(&self.budget, &self.spec.experiment_id);
        let decision = lifecycle.allocate(&*self.scheduler, self.spec.signals)?;
        let mechanism = self.collector.collect(MechanismCollectionContext {
            experiment_id: &self.spec.experiment_id,
            run_id: &self.spec.run_id,
            task: &task_output.task_artifact,
            response: &response_output.response_artifact,
            evaluation: &evaluation,
            decision: &decision,
        })?;
        if mechanism.experiment_id != self.spec.experiment_id {
            return Err(ZkBenchError::validation(
                "runner.mechanism.experiment_id",
                "mechanism record experiment identity does not match the run",
            ));
        }
        if mechanism.run_id != self.spec.run_id {
            return Err(ZkBenchError::validation(
                "runner.mechanism.run_id",
                "mechanism record run identity does not match the run",
            ));
        }
        if mechanism.decision != decision {
            return Err(ZkBenchError::validation(
                "runner.mechanism.decision",
                "mechanism record must retain the scheduler decision",
            ));
        }
        if mechanism.tier != ObservabilityTier::Tier0
            && mechanism.collector.as_ref() != Some(self.collector.descriptor())
        {
            return Err(ZkBenchError::validation(
                "runner.mechanism.collector",
                "mechanism record collector identity does not match its adapter",
            ));
        }
        mechanism.validate("runner.mechanism")?;
        lifecycle.append_mechanism(mechanism.clone())?;
        let next_budget = lifecycle.remaining_budget().clone();

        let metadata_payload = ExperimentRunMetadata {
            schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
            experiment_id: self.spec.experiment_id.clone(),
            run_id: self.spec.run_id.clone(),
            hypothesis: self.spec.hypothesis.clone(),
            replication: self.spec.replication,
            lifecycle: "completed".to_string(),
            observability: decision.clone(),
            remaining_budget: next_budget.clone(),
            modules: modules.clone(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            provenance: self.spec.provenance.clone(),
        };
        let logs_payload = ExperimentRunLogs {
            schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
            retention_policy: "metadata-only; payload retention is adapter-declared".to_string(),
            entries: vec![
                "task-materialized".to_string(),
                "response-bound".to_string(),
                "evaluation-recorded".to_string(),
                format!("observability-{:?}", decision.tier),
            ],
            provenance: self.spec.provenance.clone(),
        };
        let report_payload = ExperimentRunReport {
            schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
            experiment_id: self.spec.experiment_id.clone(),
            run_id: self.spec.run_id.clone(),
            outcome: evaluation.outcome,
            status: evaluation.status.clone(),
            negative_result: evaluation.outcome == ExperimentOutcome::Negative,
            limitations: vec![
                "metadata-only contract".to_string(),
                "not accepted evidence".to_string(),
                "not a benchmark or interpretability claim".to_string(),
            ],
            claim_boundary: ClaimBoundary::Level0DesignNote,
            provenance: self.spec.provenance.clone(),
        };
        let report = artifact_policy.report(&report_payload, "runner.report")?;

        let bundle = assemble_experiment_artifact_bundle(
            self.spec.bundle_id.clone(),
            self.spec.experiment_id.clone(),
            self.spec.run_id.clone(),
            [
                config,
                task_output.task_artifact,
                task_output.prompt_artifact,
                response_output.response_artifact,
                artifact_policy.reference(
                    "run/evaluation.json",
                    ExperimentArtifactKind::Evaluation,
                    &evaluation,
                )?,
                artifact_policy.reference(
                    "run/mechanism-record.json",
                    ExperimentArtifactKind::MechanismRecord,
                    &mechanism,
                )?,
                artifact_policy.reference(
                    "run/metadata.json",
                    ExperimentArtifactKind::Metadata,
                    &metadata_payload,
                )?,
                artifact_policy.reference(
                    "run/logs.json",
                    ExperimentArtifactKind::Logs,
                    &logs_payload,
                )?,
                report,
            ],
        )?;
        lifecycle.commit(&mut self.budget, &mut self.mechanism_ledger);
        Ok(bundle)
    }
}

/// Concrete local composition adapter for the two experiment contracts.
///
/// It executes the registered local JSON plugin once, projects its typed
/// Level1LocalReplay bundle into the fixed nine-slot observability manifest,
/// allocates one deterministic observability tier, and appends the resulting
/// mechanism record to a digest-chained local ledger. The outer manifest stays
/// Level0DesignNote because it is a composition and retention contract, not
/// new scientific evidence.
///
/// State slice: benchmark-os-canonical-artifact-projection-v1.
/// Transport extension: benchmark-os-composition-config-transport-v1.
/// Packet extension: benchmark-os-composition-transport-readback-v1.
pub const LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION: &str =
    "benchmark-os-canonical-artifact-projection-v1";
/// Schema for the canonical local composition config payload.
pub const LOCAL_JSON_COMPOSITION_CONFIG_SCHEMA_VERSION: &str =
    "benchmark-os-local-json-composition-config-v1";
/// Stable identity of the local inner-to-outer bridge adapter.
pub const LOCAL_JSON_COMPOSITION_ADAPTER_ID: &str = "local-json-observability-bridge-v1";
/// Stable logical module id for the local composition Adapter itself.
pub const LOCAL_JSON_COMPOSITION_ADAPTER_MODULE_ID: &str = "local-json-composition-adapter";
/// Source revision marker for newly emitted local composition descriptors.
pub const LOCAL_JSON_COMPOSITION_ADAPTER_SOURCE_REVISION: &str =
    "benchmark-os-observability-composition-adapter-durable-attribution-v1";

/// Return the stable descriptor retained by newly emitted local configs.
pub fn local_json_composition_adapter_descriptor() -> ModuleDescriptor {
    ModuleDescriptor {
        module_id: LOCAL_JSON_COMPOSITION_ADAPTER_MODULE_ID.to_string(),
        implementation_id: LOCAL_JSON_COMPOSITION_ADAPTER_ID.to_string(),
        version: "1".to_string(),
        source_revision: LOCAL_JSON_COMPOSITION_ADAPTER_SOURCE_REVISION.to_string(),
    }
}

fn validate_local_json_composition_adapter_descriptor(
    descriptor: &ModuleDescriptor,
    path: &str,
) -> Result<()> {
    descriptor.validate(path)?;
    if descriptor.module_id != LOCAL_JSON_COMPOSITION_ADAPTER_MODULE_ID {
        return Err(ZkBenchError::validation(
            format!("{path}.module_id"),
            "local composition adapter descriptor has an unsupported module id",
        ));
    }
    if descriptor.implementation_id != LOCAL_JSON_COMPOSITION_ADAPTER_ID {
        return Err(ZkBenchError::validation(
            format!("{path}.implementation_id"),
            "local composition adapter descriptor does not match adapter_id",
        ));
    }
    Ok(())
}

/// Relationship between an outer slot and its inner source artifacts.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LocalJsonProjectionRelation {
    /// One or more inner artifacts are carried into the outer slot.
    Direct,
    /// Multiple inner identities are represented by one outer slot.
    Composed,
    /// The outer slot is generated from the inner run and outer policy.
    Derived,
    /// The slot intentionally has no inner source at the selected tier.
    Absent,
}

/// Inner artifact identity retained by the local composition bridge.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalJsonSourceArtifactRef {
    /// Inner artifact category.
    pub kind: LocalArtifactKind,
    /// Inner artifact URI.
    pub uri: String,
    /// Digest over the inner artifact payload.
    pub digest: ArtifactDigest,
}

/// Deterministic source-to-target binding for one outer artifact slot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalJsonArtifactBinding {
    /// Outer fixed bundle slot.
    pub outer_kind: ExperimentArtifactKind,
    /// Outer artifact URI.
    pub outer_uri: String,
    /// Declared relationship between the inner and outer records.
    pub relation: LocalJsonProjectionRelation,
    /// Inner source artifacts. Empty only for derived or absent slots.
    pub inner_artifacts: Vec<LocalJsonSourceArtifactRef>,
    /// Expected outer digest when the projected payload is deterministic from
    /// the inner source set alone. Policy-generated slots remain unbound here.
    #[serde(default)]
    pub outer_digest: Option<ArtifactDigest>,
}

impl LocalJsonArtifactBinding {
    /// Return the one inner source required by a direct task, prompt, or
    /// response projection.
    pub fn single_inner_artifact(&self) -> Result<&LocalJsonSourceArtifactRef> {
        let mut matches = self.inner_artifacts.iter();
        let artifact = matches.next().ok_or_else(|| {
            ZkBenchError::validation(
                "local_json_projection.binding.inner_artifacts",
                "projection requires one inner source",
            )
        })?;
        if matches.next().is_some() {
            return Err(ZkBenchError::validation(
                "local_json_projection.binding.inner_artifacts",
                "projection inner source is duplicated",
            ));
        }
        Ok(artifact)
    }
}

/// Canonical identity map between one local experiment bundle and its outer
/// observability bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalJsonArtifactProjection {
    /// Projection schema version.
    pub schema_version: String,
    /// Stable bridge adapter identity.
    pub adapter_id: String,
    /// Inner bundle identity.
    pub inner_bundle_id: String,
    /// Digest over the complete inner bundle.
    pub inner_bundle_digest: ArtifactDigest,
    /// Claim ceiling of this bridge record.
    pub claim_boundary: ClaimBoundary,
    /// Fixed, deterministic outer-slot order.
    pub bindings: Vec<LocalJsonArtifactBinding>,
}

impl LocalJsonArtifactProjection {
    /// Build the fixed projection for one inner bundle and selected tier.
    pub fn from_inner_bundle(
        bundle: &LocalExperimentBundle,
        tier: ObservabilityTier,
    ) -> Result<Self> {
        let source =
            |kind: LocalArtifactKind, path: &str| local_json_source_artifact(bundle, kind, path);
        let config = source(LocalArtifactKind::Config, "projection.config")?;
        let data = source(LocalArtifactKind::DataVersion, "projection.data_version")?;
        let manifest = source(
            LocalArtifactKind::ReplayManifest,
            "projection.replay_manifest",
        )?;
        let result = source(LocalArtifactKind::ReplayResult, "projection.replay_result")?;
        let mechanism = source(
            LocalArtifactKind::MechanismLedger,
            "projection.mechanism_ledger",
        )?;
        let metrics = source(LocalArtifactKind::Metrics, "projection.metrics")?;
        let report = source(LocalArtifactKind::Report, "projection.report")?;

        let task_payload = LocalJsonTaskArtifactPayload {
            schema_version: LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION.to_string(),
            plugin_id: bundle.config.plugin_id.clone(),
            source: data.clone(),
        };
        let prompt_payload = LocalJsonPromptArtifactPayload {
            schema_version: LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION.to_string(),
            source: manifest.clone(),
        };
        let response_payload = LocalJsonResponseArtifactPayload {
            schema_version: LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION.to_string(),
            source: result.clone(),
        };
        let evaluation_payload = LocalJsonEvaluationArtifactPayload {
            schema_version: LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION.to_string(),
            sources: vec![metrics.clone(), report.clone()],
        };

        Ok(Self {
            schema_version: LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION.to_string(),
            adapter_id: LOCAL_JSON_COMPOSITION_ADAPTER_ID.to_string(),
            inner_bundle_id: bundle.bundle_id.clone(),
            inner_bundle_digest: compute_experiment_bundle_digest(bundle)?,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            bindings: vec![
                LocalJsonArtifactBinding {
                    outer_kind: ExperimentArtifactKind::Config,
                    outer_uri: "run/config.json".to_string(),
                    relation: LocalJsonProjectionRelation::Composed,
                    inner_artifacts: vec![config],
                    outer_digest: None,
                },
                LocalJsonArtifactBinding {
                    outer_kind: ExperimentArtifactKind::Task,
                    outer_uri: "run/task.json".to_string(),
                    relation: LocalJsonProjectionRelation::Derived,
                    inner_artifacts: vec![data],
                    outer_digest: Some(compute_artifact_digest(
                        &task_payload,
                        Some(ArtifactKind::Other),
                        Some(ArtifactRole::Manifest),
                    )?),
                },
                LocalJsonArtifactBinding {
                    outer_kind: ExperimentArtifactKind::Prompt,
                    outer_uri: "run/prompt.json".to_string(),
                    relation: LocalJsonProjectionRelation::Derived,
                    inner_artifacts: vec![manifest],
                    outer_digest: Some(compute_artifact_digest(
                        &prompt_payload,
                        Some(ArtifactKind::Other),
                        Some(ArtifactRole::Manifest),
                    )?),
                },
                LocalJsonArtifactBinding {
                    outer_kind: ExperimentArtifactKind::Response,
                    outer_uri: "run/response.json".to_string(),
                    relation: LocalJsonProjectionRelation::Derived,
                    inner_artifacts: vec![result],
                    outer_digest: Some(compute_artifact_digest(
                        &response_payload,
                        Some(ArtifactKind::Other),
                        Some(ArtifactRole::Manifest),
                    )?),
                },
                LocalJsonArtifactBinding {
                    outer_kind: ExperimentArtifactKind::Evaluation,
                    outer_uri: "run/evaluation.json".to_string(),
                    relation: LocalJsonProjectionRelation::Composed,
                    inner_artifacts: vec![metrics, report],
                    outer_digest: Some(compute_artifact_digest(
                        &evaluation_payload,
                        Some(ArtifactKind::Other),
                        Some(ArtifactRole::Manifest),
                    )?),
                },
                LocalJsonArtifactBinding {
                    outer_kind: ExperimentArtifactKind::MechanismRecord,
                    outer_uri: "run/mechanism-record.json".to_string(),
                    relation: if tier == ObservabilityTier::Tier0 {
                        LocalJsonProjectionRelation::Absent
                    } else {
                        LocalJsonProjectionRelation::Derived
                    },
                    inner_artifacts: if tier == ObservabilityTier::Tier0 {
                        Vec::new()
                    } else {
                        vec![mechanism]
                    },
                    outer_digest: None,
                },
                LocalJsonArtifactBinding {
                    outer_kind: ExperimentArtifactKind::Metadata,
                    outer_uri: "run/metadata.json".to_string(),
                    relation: LocalJsonProjectionRelation::Derived,
                    inner_artifacts: Vec::new(),
                    outer_digest: None,
                },
                LocalJsonArtifactBinding {
                    outer_kind: ExperimentArtifactKind::Logs,
                    outer_uri: "run/logs.json".to_string(),
                    relation: LocalJsonProjectionRelation::Derived,
                    inner_artifacts: Vec::new(),
                    outer_digest: None,
                },
                LocalJsonArtifactBinding {
                    outer_kind: ExperimentArtifactKind::Report,
                    outer_uri: "run/report.json".to_string(),
                    relation: LocalJsonProjectionRelation::Derived,
                    inner_artifacts: Vec::new(),
                    outer_digest: None,
                },
            ],
        })
    }

    /// Return one fixed-slot binding.
    pub fn binding(&self, kind: ExperimentArtifactKind) -> Result<&LocalJsonArtifactBinding> {
        let mut matches = self
            .bindings
            .iter()
            .filter(|binding| binding.outer_kind == kind);
        let binding = matches.next().ok_or_else(|| {
            ZkBenchError::validation(
                "local_json_projection.bindings",
                format!("missing binding for outer slot {kind:?}"),
            )
        })?;
        if matches.next().is_some() {
            return Err(ZkBenchError::validation(
                "local_json_projection.bindings",
                format!("binding for outer slot {kind:?} is duplicated"),
            ));
        }
        Ok(binding)
    }

    /// Return the exactly-one inner source for a direct outer slot.
    pub fn single_inner_artifact(
        &self,
        kind: ExperimentArtifactKind,
    ) -> Result<&LocalJsonSourceArtifactRef> {
        self.binding(kind)?.single_inner_artifact()
    }

    /// Validate the complete source map against the supplied inner bundle.
    pub fn validate(&self, bundle: &LocalExperimentBundle, tier: ObservabilityTier) -> Result<()> {
        require_text(&self.schema_version, "local_json_projection.schema_version")?;
        if self.schema_version != LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION {
            return Err(ZkBenchError::validation(
                "local_json_projection.schema_version",
                "unsupported local artifact projection schema version",
            ));
        }
        if self.adapter_id != LOCAL_JSON_COMPOSITION_ADAPTER_ID {
            return Err(ZkBenchError::validation(
                "local_json_projection.adapter_id",
                "unsupported local composition adapter",
            ));
        }
        if self.claim_boundary != ClaimBoundary::Level0DesignNote {
            return Err(ZkBenchError::ClaimBoundary {
                message: "local artifact projection remains Level0DesignNote".to_string(),
            });
        }
        if self.inner_bundle_id != bundle.bundle_id {
            return Err(ZkBenchError::validation(
                "local_json_projection.inner_bundle_id",
                "projection inner bundle id does not match supplied bundle",
            ));
        }
        let expected_digest = compute_experiment_bundle_digest(bundle)?;
        if self.inner_bundle_digest != expected_digest {
            return Err(ZkBenchError::validation(
                "local_json_projection.inner_bundle_digest",
                "projection inner bundle digest does not match supplied bundle",
            ));
        }
        let expected = Self::from_inner_bundle(bundle, tier)?;
        if self != &expected {
            return Err(ZkBenchError::validation(
                "local_json_projection.bindings",
                "projection bindings do not match the canonical local mapping",
            ));
        }
        Ok(())
    }
}

/// Canonical config payload for the local inner-to-outer bridge.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalJsonCompositionConfig {
    /// Composition-config schema version.
    pub schema_version: String,
    /// Stable bridge adapter identity.
    pub adapter_id: String,
    /// Descriptor of the Adapter that emitted this config.
    ///
    /// New configs always carry this identity. `None` is accepted only for
    /// legacy v1 JSON that predates durable composition-adapter attribution.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub adapter_descriptor: Option<ModuleDescriptor>,
    /// Outer experiment identity.
    pub experiment_id: String,
    /// Outer run identity.
    pub run_id: String,
    /// Inner bundle identity.
    pub inner_bundle_id: String,
    /// Digest over the inner bundle.
    pub inner_bundle_digest: ArtifactDigest,
    /// Signals frozen before scheduler allocation.
    pub signals: ObservabilitySignals,
    /// Budget before scheduler allocation.
    pub initial_budget: ObservabilityBudget,
    /// Scheduler decision frozen into the bridge record.
    pub decision: ObservabilityDecision,
    /// Module identities used by the outer composition.
    pub modules: Vec<ModuleDescriptor>,
    /// Canonical source-to-target artifact projection.
    pub projection: LocalJsonArtifactProjection,
}

impl LocalJsonCompositionConfig {
    /// Validate identity, scheduler decision, module descriptors, and source
    /// projection without executing any adapter.
    pub fn validate(&self, inner: &LocalExperimentBundle) -> Result<()> {
        if self.schema_version != LOCAL_JSON_COMPOSITION_CONFIG_SCHEMA_VERSION {
            return Err(ZkBenchError::validation(
                "local_json_composition_config.schema_version",
                "unsupported local composition config schema version",
            ));
        }
        if self.adapter_id != LOCAL_JSON_COMPOSITION_ADAPTER_ID {
            return Err(ZkBenchError::validation(
                "local_json_composition_config.adapter_id",
                "unsupported local composition adapter",
            ));
        }
        if let Some(adapter_descriptor) = &self.adapter_descriptor {
            validate_local_json_composition_adapter_descriptor(
                adapter_descriptor,
                "local_json_composition_config.adapter_descriptor",
            )?;
        }
        require_text(
            &self.experiment_id,
            "local_json_composition_config.experiment_id",
        )?;
        require_text(&self.run_id, "local_json_composition_config.run_id")?;
        if self.inner_bundle_id != inner.bundle_id
            || self.inner_bundle_digest != compute_experiment_bundle_digest(inner)?
            || self.projection.inner_bundle_id != self.inner_bundle_id
            || self.projection.inner_bundle_digest != self.inner_bundle_digest
        {
            return Err(ZkBenchError::validation(
                "local_json_composition_config.inner_bundle",
                "composition config is not bound to the supplied inner bundle",
            ));
        }
        self.signals.validate()?;
        self.decision
            .validate("local_json_composition_config.decision")?;
        validate_module_manifest(&self.modules, "local_json_composition_config.modules")?;
        self.projection.validate(inner, self.decision.tier)
    }
}

/// Validated in-memory handoff for the local inner/config/outer composition.
///
/// The fields stay private so callers cannot separate the three values without
/// first passing through the complete projection validator.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedLocalJsonCompositionOutput {
    inner: LocalExperimentBundle,
    config: LocalJsonCompositionConfig,
    outer: ExperimentArtifactBundle,
}

impl ValidatedLocalJsonCompositionOutput {
    /// Validate and bind the complete local composition handoff.
    pub fn new(
        inner: LocalExperimentBundle,
        config: LocalJsonCompositionConfig,
        outer: ExperimentArtifactBundle,
    ) -> Result<Self> {
        validate_local_json_artifact_projection(&inner, &outer, &config)?;
        Ok(Self {
            inner,
            config,
            outer,
        })
    }

    /// Return the validated inner local replay bundle.
    pub fn inner(&self) -> &LocalExperimentBundle {
        &self.inner
    }

    /// Return the validated composition config.
    pub fn config(&self) -> &LocalJsonCompositionConfig {
        &self.config
    }

    /// Return the validated outer observability bundle.
    pub fn outer(&self) -> &ExperimentArtifactBundle {
        &self.outer
    }

    /// Decompose the validated handoff after validation has already occurred.
    pub fn into_parts(
        self,
    ) -> (
        LocalExperimentBundle,
        LocalJsonCompositionConfig,
        ExperimentArtifactBundle,
    ) {
        (self.inner, self.config, self.outer)
    }

    /// Preserve the historical runner output shape.
    pub fn into_outer(self) -> ExperimentArtifactBundle {
        self.outer
    }
}

/// Validate the inner bundle, composition config, outer bundle, and every
/// source-to-target digest binding together.
pub fn validate_local_json_artifact_projection(
    inner: &LocalExperimentBundle,
    outer: &ExperimentArtifactBundle,
    config: &LocalJsonCompositionConfig,
) -> Result<()> {
    let inner_validation = crate::experiment::validate_experiment_bundle(inner);
    if !inner_validation.valid {
        return Err(ZkBenchError::validation(
            "local_json_projection.inner_bundle",
            format!(
                "inner local bundle is invalid: {:?}",
                inner_validation.issues
            ),
        ));
    }
    config.validate(inner)?;
    validate_experiment_artifact_bundle(outer)?;
    if outer.experiment_id != config.experiment_id
        || outer.run_id != config.run_id
        || outer.bundle_id != format!("observability_{}", config.inner_bundle_id)
    {
        return Err(ZkBenchError::validation(
            "local_json_projection.outer_identity",
            "outer bundle identity does not match the composition config",
        ));
    }
    let expected_config_digest = compute_artifact_digest(
        config,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    )?;
    if outer.config.digest != expected_config_digest {
        return Err(ZkBenchError::validation(
            "local_json_projection.outer_config_digest",
            "outer config digest does not match the canonical composition config",
        ));
    }
    for binding in &config.projection.bindings {
        let target = outer.artifact(binding.outer_kind);
        if target.uri != binding.outer_uri {
            return Err(ZkBenchError::validation(
                "local_json_projection.outer_uri",
                format!("outer URI drift for {:?}", binding.outer_kind),
            ));
        }
        if let Some(expected_digest) = &binding.outer_digest {
            if target.digest != *expected_digest {
                return Err(ZkBenchError::validation(
                    "local_json_projection.outer_digest",
                    format!("outer digest drift for {:?}", binding.outer_kind),
                ));
            }
        }
    }
    Ok(())
}

/// Serialize the canonical local composition config for artifact transport.
pub fn serialize_local_json_composition_config_json(
    config: &LocalJsonCompositionConfig,
) -> Result<String> {
    serde_json::to_string(config).map_err(|error| {
        ZkBenchError::serialization("local_json_composition_config.json", error.to_string())
    })
}

/// Deserialize one local composition config transport artifact.
pub fn deserialize_local_json_composition_config_json(
    json: &str,
) -> Result<LocalJsonCompositionConfig> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("local_json_composition_config.json", error.to_string())
    })
}

/// Compute the digest of the version-locked canonical config serialization.
pub fn compute_local_json_composition_config_digest(
    config: &LocalJsonCompositionConfig,
) -> Result<ArtifactDigest> {
    let json = serialize_local_json_composition_config_json(config)?;
    Ok(compute_artifact_digest_bytes(
        json.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    ))
}

/// Validate a transported composition config against its inner and outer
/// bundles. The raw JSON bytes must be the exact bytes named by `outer.config`.
pub fn validate_serialized_local_json_composition(
    config_json: &str,
    inner: &LocalExperimentBundle,
    outer: &ExperimentArtifactBundle,
) -> Result<LocalJsonCompositionConfig> {
    let config = deserialize_local_json_composition_config_json(config_json)?;
    let transport_digest = compute_artifact_digest_bytes(
        config_json.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    );
    if outer.config.digest != transport_digest {
        return Err(ZkBenchError::validation(
            "local_json_composition_config.transport_digest",
            "transported config bytes do not match outer.config.digest",
        ));
    }
    let canonical_digest = compute_local_json_composition_config_digest(&config)?;
    if transport_digest != canonical_digest {
        return Err(ZkBenchError::validation(
            "local_json_composition_config.canonical_bytes",
            "transported config bytes are not the canonical serialization",
        ));
    }
    validate_local_json_artifact_projection(inner, outer, &config)?;
    Ok(config)
}

/// Validate the complete local composition packet from its three transport
/// artifacts: inner bundle, canonical config, and outer bundle.
pub fn validate_serialized_local_json_composition_transport(
    inner_json: &str,
    config_json: &str,
    outer_json: &str,
) -> Result<(
    LocalExperimentBundle,
    LocalJsonCompositionConfig,
    ExperimentArtifactBundle,
)> {
    let inner = deserialize_experiment_bundle_json(inner_json)?;
    let inner_validation = validate_experiment_bundle(&inner);
    if !inner_validation.valid {
        return Err(ZkBenchError::validation(
            "local_json_composition_transport.inner_bundle",
            format!("inner bundle is invalid: {:?}", inner_validation.issues),
        ));
    }
    let canonical_inner_json = serialize_experiment_bundle_json(&inner)?;
    if inner_json != canonical_inner_json {
        return Err(ZkBenchError::validation(
            "local_json_composition_transport.inner_bytes",
            "inner bundle bytes are not the canonical serialization",
        ));
    }

    let outer = deserialize_experiment_artifact_bundle_json(outer_json)?;
    let canonical_outer_json = serialize_experiment_artifact_bundle_json(&outer)?;
    if outer_json != canonical_outer_json {
        return Err(ZkBenchError::validation(
            "local_json_composition_transport.outer_bytes",
            "outer bundle bytes are not the canonical serialization",
        ));
    }
    let config = validate_serialized_local_json_composition(config_json, &inner, &outer)?;
    Ok((inner, config, outer))
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
struct LocalJsonTaskArtifactPayload {
    schema_version: String,
    plugin_id: String,
    source: LocalJsonSourceArtifactRef,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
struct LocalJsonPromptArtifactPayload {
    schema_version: String,
    source: LocalJsonSourceArtifactRef,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
struct LocalJsonResponseArtifactPayload {
    schema_version: String,
    source: LocalJsonSourceArtifactRef,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
struct LocalJsonEvaluationArtifactPayload {
    schema_version: String,
    sources: Vec<LocalJsonSourceArtifactRef>,
}

fn local_json_source_artifact(
    bundle: &LocalExperimentBundle,
    kind: LocalArtifactKind,
    path: &str,
) -> Result<LocalJsonSourceArtifactRef> {
    let artifact = local_inner_artifact(bundle, kind, path)?;
    Ok(LocalJsonSourceArtifactRef {
        kind: artifact.kind,
        uri: artifact.uri.clone(),
        digest: artifact.digest.clone(),
    })
}

pub struct LocalJsonExperimentRunner {
    plugin: Box<dyn ExperimentPlugin>,
    experiment_id: String,
    run_id: String,
    signals: ObservabilitySignals,
    provenance: ExperimentProvenance,
    scheduler: Box<dyn ObservabilityScheduler>,
    budget: ObservabilityBudget,
    mechanism_ledger: Option<MechanismLedger>,
    composition_config: Option<LocalJsonCompositionConfig>,
}

impl LocalJsonExperimentRunner {
    /// Construct a one-shot runner using the reference weighted scheduler.
    pub fn new(
        config: GeneratorConfig,
        experiment_id: impl Into<String>,
        run_id: impl Into<String>,
        signals: ObservabilitySignals,
        provenance: ExperimentProvenance,
        budget: ObservabilityBudget,
    ) -> Result<Self> {
        Self::new_with_scheduler(
            config,
            experiment_id,
            run_id,
            signals,
            provenance,
            budget,
            Box::new(WeightedObservabilityScheduler::default()),
        )
    }

    /// Construct a one-shot runner with an explicit scheduler adapter.
    pub fn new_with_scheduler(
        config: GeneratorConfig,
        experiment_id: impl Into<String>,
        run_id: impl Into<String>,
        signals: ObservabilitySignals,
        provenance: ExperimentProvenance,
        budget: ObservabilityBudget,
        scheduler: Box<dyn ObservabilityScheduler>,
    ) -> Result<Self> {
        let plugin = ExperimentPluginFactoryCatalog::local_json(config)?
            .instantiate(crate::experiment::LOCAL_JSON_EXPERIMENT_PLUGIN_ID)?;
        Self::new_with_plugin(
            plugin,
            experiment_id,
            run_id,
            signals,
            provenance,
            budget,
            scheduler,
        )
    }

    /// Construct a one-shot runner from an explicit experiment plugin
    /// Adapter. The plugin must emit the existing local experiment bundle
    /// contract; projection, provenance, claim ceilings, and transaction
    /// invariants remain owned by this outer runner.
    pub fn new_with_plugin(
        plugin: Box<dyn ExperimentPlugin>,
        experiment_id: impl Into<String>,
        run_id: impl Into<String>,
        signals: ObservabilitySignals,
        provenance: ExperimentProvenance,
        budget: ObservabilityBudget,
        scheduler: Box<dyn ObservabilityScheduler>,
    ) -> Result<Self> {
        let experiment_id = experiment_id.into();
        let run_id = run_id.into();
        require_text(&experiment_id, "local_json_runner.experiment_id")?;
        require_text(&run_id, "local_json_runner.run_id")?;
        signals.validate()?;
        provenance.validate("local_json_runner.provenance")?;
        plugin.descriptor().validate("local_json_runner.plugin")?;
        scheduler
            .descriptor()
            .validate("local_json_runner.scheduler")?;
        Ok(Self {
            plugin,
            experiment_id,
            run_id,
            signals,
            provenance,
            scheduler,
            budget,
            mechanism_ledger: None,
            composition_config: None,
        })
    }

    /// Return the budget after a successful run.
    pub fn remaining_budget(&self) -> &ObservabilityBudget {
        &self.budget
    }

    /// Return the local append-only mechanism ledger after a successful run.
    pub fn mechanism_ledger(&self) -> Option<&MechanismLedger> {
        self.mechanism_ledger.as_ref()
    }

    /// Return the canonical inner-to-outer config emitted by the last run.
    pub fn composition_config(&self) -> Option<&LocalJsonCompositionConfig> {
        self.composition_config.as_ref()
    }
}

impl LocalJsonExperimentRunner {
    /// Run the local composition and return the validated inner/config/outer
    /// handoff while retaining the existing one-shot transaction semantics.
    pub fn run_validated_output(&mut self) -> Result<ValidatedLocalJsonCompositionOutput> {
        if self.mechanism_ledger.is_some() {
            return Err(ZkBenchError::validation(
                "local_json_runner",
                "runner instances are one-shot for their fixed run id",
            ));
        }

        let validated = self.plugin.run_validated_output()?;
        let (plugin_descriptor, inner_bundle) = validated.into_parts();
        let artifact_policy = ExperimentArtifactReferencePolicy::new(
            self.experiment_id.clone(),
            self.run_id.clone(),
            self.provenance.clone(),
        )?;
        let inner_digest = compute_experiment_bundle_digest(&inner_bundle)?;
        let initial_budget = self.budget.clone();
        let modules = local_json_composition_modules(
            &inner_bundle,
            &plugin_descriptor,
            &self.provenance,
            &*self.scheduler,
        )?;
        let mut lifecycle =
            ObservabilityRunLifecycleTransaction::new(&self.budget, &self.experiment_id);
        let decision = lifecycle.allocate(&*self.scheduler, self.signals)?;
        let projection =
            LocalJsonArtifactProjection::from_inner_bundle(&inner_bundle, decision.tier)?;
        let composition_config = LocalJsonCompositionConfig {
            schema_version: LOCAL_JSON_COMPOSITION_CONFIG_SCHEMA_VERSION.to_string(),
            adapter_id: LOCAL_JSON_COMPOSITION_ADAPTER_ID.to_string(),
            adapter_descriptor: Some(local_json_composition_adapter_descriptor()),
            experiment_id: self.experiment_id.clone(),
            run_id: self.run_id.clone(),
            inner_bundle_id: inner_bundle.bundle_id.clone(),
            inner_bundle_digest: inner_digest,
            signals: self.signals,
            initial_budget,
            decision: decision.clone(),
            modules: modules.clone(),
            projection,
        };
        composition_config.validate(&inner_bundle)?;
        let config = artifact_policy.reference(
            "run/config.json",
            ExperimentArtifactKind::Config,
            &composition_config,
        )?;
        config.validate_for(
            "local_json_runner.config",
            &self.experiment_id,
            &self.run_id,
        )?;

        let task_source = composition_config
            .projection
            .single_inner_artifact(ExperimentArtifactKind::Task)?
            .clone();
        let task_artifact = artifact_policy.reference(
            "run/task.json",
            ExperimentArtifactKind::Task,
            &LocalJsonTaskArtifactPayload {
                schema_version: LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION.to_string(),
                plugin_id: inner_bundle.config.plugin_id.clone(),
                source: task_source,
            },
        )?;
        task_artifact.validate_for(
            "local_json_runner.task_artifact",
            &self.experiment_id,
            &self.run_id,
        )?;
        let prompt_source = composition_config
            .projection
            .single_inner_artifact(ExperimentArtifactKind::Prompt)?
            .clone();
        let prompt_artifact = artifact_policy.reference(
            "run/prompt.json",
            ExperimentArtifactKind::Prompt,
            &LocalJsonPromptArtifactPayload {
                schema_version: LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION.to_string(),
                source: prompt_source,
            },
        )?;
        prompt_artifact.validate_for(
            "local_json_runner.prompt_artifact",
            &self.experiment_id,
            &self.run_id,
        )?;
        let response_source = composition_config
            .projection
            .single_inner_artifact(ExperimentArtifactKind::Response)?
            .clone();
        let response_artifact = artifact_policy.reference(
            "run/response.json",
            ExperimentArtifactKind::Response,
            &LocalJsonResponseArtifactPayload {
                schema_version: LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION.to_string(),
                source: response_source,
            },
        )?;
        response_artifact.validate_for(
            "local_json_runner.response_artifact",
            &self.experiment_id,
            &self.run_id,
        )?;

        let mechanism = local_json_mechanism_record(
            &inner_bundle,
            &self.experiment_id,
            &self.run_id,
            decision,
            &self.provenance,
        )?;
        lifecycle.append_mechanism(mechanism.clone())?;
        let next_budget = lifecycle.remaining_budget().clone();

        let evaluation = artifact_policy.reference(
            "run/evaluation.json",
            ExperimentArtifactKind::Evaluation,
            &LocalJsonEvaluationArtifactPayload {
                schema_version: LOCAL_JSON_ARTIFACT_PROJECTION_SCHEMA_VERSION.to_string(),
                sources: composition_config
                    .projection
                    .binding(ExperimentArtifactKind::Evaluation)?
                    .inner_artifacts
                    .clone(),
            },
        )?;
        let metadata_payload = ExperimentRunMetadata {
            schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
            experiment_id: self.experiment_id.clone(),
            run_id: self.run_id.clone(),
            hypothesis: "local JSON replay composition".to_string(),
            replication: false,
            lifecycle: "completed_local_composition".to_string(),
            observability: mechanism.decision.clone(),
            remaining_budget: next_budget.clone(),
            modules,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            provenance: self.provenance.clone(),
        };
        let logs_payload = ExperimentRunLogs {
            schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
            retention_policy: "metadata-only; inner local bundle remains caller-owned".to_string(),
            entries: vec![
                "inner-local-plugin-completed".to_string(),
                "observability-decision-recorded".to_string(),
                "mechanism-ledger-entry-appended".to_string(),
            ],
            provenance: self.provenance.clone(),
        };
        let report_payload = ExperimentRunReport {
            schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
            experiment_id: self.experiment_id.clone(),
            run_id: self.run_id.clone(),
            outcome: ExperimentOutcome::Inconclusive,
            status: "inconclusive".to_string(),
            negative_result: false,
            limitations: vec![
                "outer manifest is a metadata-only composition contract".to_string(),
                "inner local replay is not official benchmark evidence".to_string(),
                "mechanism coverage is sparse and adapter-limited".to_string(),
            ],
            claim_boundary: ClaimBoundary::Level0DesignNote,
            provenance: self.provenance.clone(),
        };
        let report = artifact_policy.report(&report_payload, "local_json_composition.report")?;

        let bundle = assemble_experiment_artifact_bundle(
            format!("observability_{}", inner_bundle.bundle_id),
            self.experiment_id.clone(),
            self.run_id.clone(),
            [
                config,
                task_artifact,
                prompt_artifact,
                response_artifact,
                evaluation,
                artifact_policy.reference(
                    "run/mechanism-record.json",
                    ExperimentArtifactKind::MechanismRecord,
                    &mechanism,
                )?,
                artifact_policy.reference(
                    "run/metadata.json",
                    ExperimentArtifactKind::Metadata,
                    &metadata_payload,
                )?,
                artifact_policy.reference(
                    "run/logs.json",
                    ExperimentArtifactKind::Logs,
                    &logs_payload,
                )?,
                report,
            ],
        )?;
        let output =
            ValidatedLocalJsonCompositionOutput::new(inner_bundle, composition_config, bundle)?;
        lifecycle.commit(&mut self.budget, &mut self.mechanism_ledger);
        self.composition_config = Some(output.config().clone());
        Ok(output)
    }
}

impl ExperimentRunner for LocalJsonExperimentRunner {
    fn run(&mut self) -> Result<ExperimentArtifactBundle> {
        Ok(self.run_validated_output()?.into_outer())
    }
}

fn local_artifact_digest(
    bundle: &LocalExperimentBundle,
    kind: LocalArtifactKind,
    path: &str,
) -> Result<ArtifactDigest> {
    Ok(local_inner_artifact(bundle, kind, path)?.digest.clone())
}

fn local_inner_artifact<'a>(
    bundle: &'a LocalExperimentBundle,
    kind: LocalArtifactKind,
    path: &str,
) -> Result<&'a crate::experiment::ExperimentArtifactRef> {
    bundle.artifact(kind).map_err(|error| match error {
        ZkBenchError::Validation { message, .. } => ZkBenchError::validation(path, message),
        error => error,
    })
}

fn local_json_composition_modules(
    bundle: &LocalExperimentBundle,
    plugin: &ExperimentPluginDescriptor,
    provenance: &ExperimentProvenance,
    scheduler: &dyn ObservabilityScheduler,
) -> Result<Vec<ModuleDescriptor>> {
    let descriptor = |module_id: &str, implementation_id: String| ModuleDescriptor {
        module_id: module_id.to_string(),
        implementation_id,
        version: provenance.version.clone(),
        source_revision: provenance.source_revision.clone(),
    };
    let modules = vec![
        ModuleDescriptor {
            module_id: "experiment-source".to_string(),
            implementation_id: plugin.plugin_id.clone(),
            version: plugin.version.clone(),
            source_revision: provenance.source_revision.clone(),
        },
        descriptor("task", bundle.config.plugin_id.clone()),
        descriptor("model", bundle.model_version.model_id.clone()),
        descriptor(
            "mechanism-collector",
            bundle.mechanism_ledger.collector_id.clone(),
        ),
        descriptor("evaluator", bundle.metrics.evaluator_id.clone()),
        scheduler.descriptor(),
    ];
    validate_module_manifest(&modules, "local_json_runner.modules")?;
    Ok(modules)
}

fn local_json_mechanism_record(
    bundle: &LocalExperimentBundle,
    experiment_id: &str,
    run_id: &str,
    decision: ObservabilityDecision,
    provenance: &ExperimentProvenance,
) -> Result<MechanismRecord> {
    let collector = if decision.tier == ObservabilityTier::Tier0 {
        None
    } else {
        Some(ModuleDescriptor {
            module_id: "mechanism-collector".to_string(),
            implementation_id: bundle.mechanism_ledger.collector_id.clone(),
            version: provenance.version.clone(),
            source_revision: provenance.source_revision.clone(),
        })
    };
    let payload_digest = if decision.tier == ObservabilityTier::Tier0 {
        None
    } else {
        Some(local_artifact_digest(
            bundle,
            LocalArtifactKind::MechanismLedger,
            "local_json_runner.mechanism",
        )?)
    };
    let status = match decision.tier {
        ObservabilityTier::Tier0 => MechanismRecordStatus::MetadataOnly,
        ObservabilityTier::Tier1 => MechanismRecordStatus::Sampled,
        ObservabilityTier::Tier2 => MechanismRecordStatus::DeepDive,
        ObservabilityTier::Tier3 => MechanismRecordStatus::GoldCase,
    };
    Ok(MechanismRecord {
        record_id: format!("{run_id}-mechanism"),
        experiment_id: experiment_id.to_string(),
        run_id: run_id.to_string(),
        tier: decision.tier,
        status,
        collector,
        payload_digest,
        failure_reason: None,
        decision,
        provenance: provenance.clone(),
    })
}

/// Metric stability classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MetricStability {
    /// Stable under the declared replication test.
    Stable,
    /// Unstable under the declared replication test.
    Unstable,
    /// Not tested yet.
    Untested,
}

/// Metric downstream-predictiveness classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DownstreamPredictiveness {
    /// Predicts the declared downstream target under the frozen test.
    Predictive,
    /// Tested and not predictive.
    NotPredictive,
    /// Not tested yet.
    Untested,
}

/// Metric noise classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MetricNoise {
    /// Low observed noise.
    Low,
    /// Medium observed noise.
    Medium,
    /// High observed noise.
    High,
    /// Not characterized.
    Unknown,
}

/// Immutable assessment basis for one metric judgment.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetricMetaEvaluationBasis {
    /// Frozen comparison rule identity.
    pub comparison_rule_id: String,
    /// Held-out downstream target identity.
    pub held_out_target_id: String,
    /// Replication or assessment experiment identity.
    pub replication_id: String,
    /// Ordered source artifacts used to make this judgment.
    pub source_artifacts: Vec<ExperimentArtifactRef>,
}

impl MetricMetaEvaluationBasis {
    /// Validate every identity and source reference in the immutable basis.
    pub fn validate(&self, path: &str) -> Result<()> {
        for (field, value) in [
            ("comparison_rule_id", &self.comparison_rule_id),
            ("held_out_target_id", &self.held_out_target_id),
            ("replication_id", &self.replication_id),
        ] {
            require_text(value, format!("{path}.{field}"))?;
        }
        if self.source_artifacts.is_empty() {
            return Err(ZkBenchError::validation(
                format!("{path}.source_artifacts"),
                "assessment bases require at least one source artifact",
            ));
        }
        let mut source_uris = BTreeSet::new();
        for (index, source) in self.source_artifacts.iter().enumerate() {
            let source_path = format!("{path}.source_artifacts[{index}]");
            source.validate(&source_path)?;
            if !source_uris.insert(source.uri.clone()) {
                return Err(ZkBenchError::validation(
                    format!("{source_path}.uri"),
                    "source artifact URI is duplicated",
                ));
            }
        }
        Ok(())
    }
}

/// Explicit, digest-bound meta-evaluation record for one Metric implementation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetricMetaEvaluation {
    /// Metric identity.
    pub metric: ModuleDescriptor,
    /// Immutable rule, target, replication, and source-artifact basis.
    pub assessment_basis: MetricMetaEvaluationBasis,
    /// Digest over the canonical assessment basis.
    pub assessment_basis_digest: ArtifactDigest,
    /// Stability judgment.
    pub stability: MetricStability,
    /// Downstream predictive judgment.
    pub downstream_predictiveness: DownstreamPredictiveness,
    /// Noise judgment.
    pub noise: MetricNoise,
    /// Optional noise score on the common scale.
    #[serde(default)]
    pub noise_milli: Option<u16>,
    /// Observation count.
    pub observation_count: u64,
    /// Replication count.
    pub replication_count: u64,
    /// Meta-evaluation provenance.
    pub provenance: ExperimentProvenance,
}

impl MetricMetaEvaluation {
    /// Validate explicit scope, digest binding, stability, predictive, and
    /// noise metadata.
    pub fn validate(&self, path: &str) -> Result<()> {
        self.metric.validate(&format!("{path}.metric"))?;
        self.assessment_basis
            .validate(&format!("{path}.assessment_basis"))?;
        validate_artifact_digest_metadata(
            &self.assessment_basis_digest,
            &format!("{path}.assessment_basis_digest"),
        )?;
        let expected_basis_digest = compute_artifact_digest(
            &self.assessment_basis,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?;
        if self.assessment_basis_digest != expected_basis_digest {
            return Err(ZkBenchError::validation(
                format!("{path}.assessment_basis_digest"),
                "assessment basis digest does not match the canonical basis",
            ));
        }
        self.provenance.validate(&format!("{path}.provenance"))?;
        if self
            .noise_milli
            .is_some_and(|value| value > OBSERVABILITY_SCORE_SCALE)
        {
            return Err(ZkBenchError::validation(
                format!("{path}.noise_milli"),
                "noise score exceeds the common scale",
            ));
        }
        if self.stability == MetricStability::Untested && self.replication_count > 0 {
            return Err(ZkBenchError::validation(
                format!("{path}.stability"),
                "untested metrics cannot report replications",
            ));
        }
        if self.stability != MetricStability::Untested && self.replication_count == 0 {
            return Err(ZkBenchError::validation(
                format!("{path}.replication_count"),
                "tested stability judgments require at least one replication",
            ));
        }
        if self.downstream_predictiveness != DownstreamPredictiveness::Untested
            && self.observation_count == 0
        {
            return Err(ZkBenchError::validation(
                format!("{path}.observation_count"),
                "tested downstream judgments require observations",
            ));
        }
        Ok(())
    }
}

/// Append-only metric meta-evaluation ledger.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetaEvaluationLedger {
    /// Schema version.
    pub schema_version: String,
    /// Historical judgments. New judgments append.
    #[serde(default)]
    pub entries: Vec<MetaEvaluationLedgerEntry>,
    /// Digest of the final entry.
    #[serde(default)]
    pub tip_digest: Option<ArtifactDigest>,
}

/// One digest-bound append-only metric meta-evaluation entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetaEvaluationLedgerEntry {
    /// Zero-based sequence number.
    pub sequence_number: u64,
    /// Digest of the previous entry.
    #[serde(default)]
    pub previous_digest: Option<ArtifactDigest>,
    /// Digest-bound metric judgment.
    pub evaluation: MetricMetaEvaluation,
    /// Digest over sequence, previous digest, and evaluation.
    pub entry_digest: ArtifactDigest,
}

impl Default for MetaEvaluationLedger {
    fn default() -> Self {
        Self {
            schema_version: METRIC_META_EVALUATION_LEDGER_SCHEMA_VERSION.to_string(),
            entries: Vec::new(),
            tip_digest: None,
        }
    }
}

impl MetaEvaluationLedger {
    /// Append a new judgment without replacing prior judgments.
    pub fn append(&mut self, evaluation: MetricMetaEvaluation) -> Result<()> {
        self.validate()?;
        evaluation.validate("meta_evaluation.evaluation")?;
        let sequence_number = self.entries.len() as u64;
        let previous_digest = self.entries.last().map(|entry| entry.entry_digest.clone());
        let preimage = (sequence_number, previous_digest.as_ref(), &evaluation);
        let entry_digest = compute_artifact_digest(
            &preimage,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?;
        self.entries.push(MetaEvaluationLedgerEntry {
            sequence_number,
            previous_digest,
            evaluation,
            entry_digest: entry_digest.clone(),
        });
        self.tip_digest = Some(entry_digest);
        Ok(())
    }

    /// Validate schema, historical entries, and the append digest chain.
    pub fn validate(&self) -> Result<()> {
        if self.schema_version != METRIC_META_EVALUATION_LEDGER_SCHEMA_VERSION {
            return Err(ZkBenchError::validation(
                "meta_evaluation.schema_version",
                "unsupported metric meta-evaluation schema version",
            ));
        }
        let mut previous_digest = None;
        for (index, entry) in self.entries.iter().enumerate() {
            if entry.sequence_number != index as u64 {
                return Err(ZkBenchError::validation(
                    format!("meta_evaluation.entries[{index}].sequence_number"),
                    "sequence number does not match append position",
                ));
            }
            if entry.previous_digest != previous_digest {
                return Err(ZkBenchError::validation(
                    format!("meta_evaluation.entries[{index}].previous_digest"),
                    "previous digest does not match prior entry",
                ));
            }
            entry
                .evaluation
                .validate(&format!("meta_evaluation.entries[{index}].evaluation"))?;
            let expected = compute_artifact_digest(
                &(
                    entry.sequence_number,
                    entry.previous_digest.as_ref(),
                    &entry.evaluation,
                ),
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Manifest),
            )?;
            if entry.entry_digest != expected {
                return Err(ZkBenchError::validation(
                    format!("meta_evaluation.entries[{index}].entry_digest"),
                    "entry digest does not match append preimage",
                ));
            }
            previous_digest = Some(entry.entry_digest.clone());
        }
        if self.tip_digest != previous_digest {
            return Err(ZkBenchError::validation(
                "meta_evaluation.tip_digest",
                "tip digest does not match final entry",
            ));
        }
        Ok(())
    }
}

/// Serialize a validated metric meta-evaluation ledger using its canonical
/// JSON form.
pub fn serialize_meta_evaluation_ledger_json(ledger: &MetaEvaluationLedger) -> Result<String> {
    ledger.validate()?;
    serde_json::to_string(ledger).map_err(|error| {
        ZkBenchError::serialization("meta_evaluation_ledger.json", error.to_string())
    })
}

/// Deserialize and validate one canonical metric meta-evaluation ledger.
pub fn deserialize_meta_evaluation_ledger_json(json: &str) -> Result<MetaEvaluationLedger> {
    let ledger: MetaEvaluationLedger = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("meta_evaluation_ledger.json", error.to_string())
    })?;
    let canonical_json = serialize_meta_evaluation_ledger_json(&ledger)?;
    if json != canonical_json {
        return Err(ZkBenchError::validation(
            "meta_evaluation_ledger.json",
            "ledger bytes are not the canonical serialization",
        ));
    }
    Ok(ledger)
}

fn require_text(value: &str, path: impl Into<String>) -> Result<()> {
    if value.trim().is_empty() {
        return Err(ZkBenchError::validation(path, "value must not be empty"));
    }
    Ok(())
}

fn validate_artifact_digest_metadata(digest: &ArtifactDigest, path: &str) -> Result<()> {
    let valid_hex = digest.hex_digest.len() == 64
        && digest
            .hex_digest
            .chars()
            .all(|character| character.is_ascii_hexdigit() && !character.is_ascii_uppercase());
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 || !valid_hex {
        return Err(ZkBenchError::validation(
            path,
            "digest must be lowercase SHA-256 metadata",
        ));
    }
    Ok(())
}

fn require_artifact_kind(
    artifact: &ExperimentArtifactRef,
    expected: ExperimentArtifactKind,
    path: &str,
) -> Result<()> {
    if artifact.kind != expected {
        return Err(ZkBenchError::validation(
            format!("{path}.kind"),
            format!("expected {expected:?}, got {:?}", artifact.kind),
        ));
    }
    Ok(())
}

#[cfg(test)]
mod bundle_assembly_tests {
    use super::*;

    // State slice: benchmark-os-observability-bundle-assembly-v1.
    fn provenance() -> ExperimentProvenance {
        ExperimentProvenance {
            who: "bundle-assembly-test".to_string(),
            what: "fixed-slot-assembly".to_string(),
            when: "logical-test-time-1".to_string(),
            version: "bundle-assembly-test-v1".to_string(),
            source_revision: "local-test-revision".to_string(),
        }
    }

    fn artifact(kind: ExperimentArtifactKind, uri: &str) -> ExperimentArtifactRef {
        ExperimentArtifactRef {
            uri: uri.to_string(),
            kind,
            experiment_id: "experiment-assembly".to_string(),
            run_id: "run-assembly".to_string(),
            digest: compute_artifact_digest_bytes(
                uri.as_bytes(),
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Manifest),
            ),
            provenance: provenance(),
        }
    }

    fn artifacts() -> [ExperimentArtifactRef; 9] {
        [
            artifact(ExperimentArtifactKind::Config, "config.json"),
            artifact(ExperimentArtifactKind::Task, "task.json"),
            artifact(ExperimentArtifactKind::Prompt, "prompt.json"),
            artifact(ExperimentArtifactKind::Response, "response.json"),
            artifact(ExperimentArtifactKind::Evaluation, "evaluation.json"),
            artifact(
                ExperimentArtifactKind::MechanismRecord,
                "mechanism-record.json",
            ),
            artifact(ExperimentArtifactKind::Metadata, "metadata.json"),
            artifact(ExperimentArtifactKind::Logs, "logs.json"),
            artifact(ExperimentArtifactKind::Report, "report.json"),
        ]
    }

    #[test]
    fn artifact_policy_binds_scope_and_provenance_for_references() {
        // State slice: benchmark-os-observability-run-artifact-policy-v1.
        let policy = ExperimentArtifactReferencePolicy::new(
            "experiment-assembly",
            "run-assembly",
            provenance(),
        )
        .expect("artifact policy should validate its scope");
        let artifact = policy
            .reference(
                "run/logs.json",
                ExperimentArtifactKind::Logs,
                &vec!["metadata-only".to_string()],
            )
            .expect("policy should create a bound artifact reference");

        assert_eq!(artifact.kind, ExperimentArtifactKind::Logs);
        assert_eq!(artifact.experiment_id, "experiment-assembly");
        assert_eq!(artifact.run_id, "run-assembly");
        assert_eq!(artifact.provenance, provenance());
        artifact
            .validate_for(
                "artifact_policy.reference",
                "experiment-assembly",
                "run-assembly",
            )
            .expect("policy reference should retain the declared scope");
    }

    #[test]
    fn artifact_policy_rejects_invalid_scope_and_report_binding() {
        // State slice: benchmark-os-observability-run-artifact-policy-v1.
        assert!(ExperimentArtifactReferencePolicy::new("", "run-assembly", provenance()).is_err());

        let policy = ExperimentArtifactReferencePolicy::new(
            "experiment-assembly",
            "run-assembly",
            provenance(),
        )
        .expect("artifact policy should validate its scope");
        let report = ExperimentRunReport {
            schema_version: EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION.to_string(),
            experiment_id: "experiment-assembly".to_string(),
            run_id: "run-assembly".to_string(),
            outcome: ExperimentOutcome::Inconclusive,
            status: "inconclusive".to_string(),
            negative_result: false,
            limitations: vec!["metadata-only contract".to_string()],
            claim_boundary: ClaimBoundary::Level0DesignNote,
            provenance: provenance(),
        };
        let artifact = policy
            .report(&report, "artifact_policy.report")
            .expect("policy should validate and bind the report");
        assert_eq!(artifact.kind, ExperimentArtifactKind::Report);
        assert_eq!(artifact.uri, "run/report.json");
        assert!(ExperimentArtifactReferencePolicy::new(
            "experiment-assembly",
            "run-assembly",
            ExperimentProvenance {
                who: String::new(),
                ..provenance()
            },
        )
        .is_err());
    }

    #[test]
    fn fixed_slot_assembly_owns_order_identity_and_uniqueness() {
        let bundle = assemble_experiment_artifact_bundle(
            "bundle-assembly",
            "experiment-assembly",
            "run-assembly",
            artifacts(),
        )
        .expect("fixed slot assembly should validate");
        assert_eq!(bundle.schema_version, EXPERIMENT_UNIT_BUNDLE_SCHEMA_VERSION);
        assert_eq!(bundle.config.kind, ExperimentArtifactKind::Config);
        assert_eq!(bundle.task.kind, ExperimentArtifactKind::Task);
        assert_eq!(
            bundle.mechanism_record.kind,
            ExperimentArtifactKind::MechanismRecord
        );
        assert_eq!(bundle.report.kind, ExperimentArtifactKind::Report);
        assert_eq!(bundle.artifact(ExperimentArtifactKind::Task), &bundle.task);
        assert_eq!(
            bundle.artifact(ExperimentArtifactKind::MechanismRecord),
            &bundle.mechanism_record
        );

        let mut wrong_kind = artifacts();
        wrong_kind[1].kind = ExperimentArtifactKind::Config;
        assert!(assemble_experiment_artifact_bundle(
            "bundle-assembly",
            "experiment-assembly",
            "run-assembly",
            wrong_kind,
        )
        .is_err());

        let mut identity_drift = artifacts();
        identity_drift[0].run_id = "different-run".to_string();
        assert!(assemble_experiment_artifact_bundle(
            "bundle-assembly",
            "experiment-assembly",
            "run-assembly",
            identity_drift,
        )
        .is_err());

        let mut duplicate_uri = artifacts();
        duplicate_uri[1].uri = duplicate_uri[0].uri.clone();
        assert!(assemble_experiment_artifact_bundle(
            "bundle-assembly",
            "experiment-assembly",
            "run-assembly",
            duplicate_uri,
        )
        .is_err());
    }
}

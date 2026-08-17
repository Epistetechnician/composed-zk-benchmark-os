//! Static experiment plugin for the synthetic metacognitive contract.
//!
//! State slice: `benchmark-os-experiment-plugin-agnostic-composition-v1`.
//!
//! This adapter proves that the experiment bundle seam has a second typed
//! implementation. It packages only the existing pure-data metacognitive
//! cases and results. It does not execute a model, retain reasoning, access
//! the network, invoke a process, grant authority, or create evidence.

use serde::Serialize;

use crate::adapters::{
    build_metacognitive_monitor_control_case, MetacognitiveMonitorControlCase,
    MetacognitiveMonitorControlObservation, MetacognitiveMonitorControlResult,
    MetacognitiveMonitorControlVariant, METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY,
    METACOGNITIVE_MONITOR_CONTROL_FAMILY_ID, METACOGNITIVE_MONITOR_CONTROL_SCHEMA_VERSION,
};
use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    canonical_json_bytes, compute_artifact_digest, compute_artifact_digest_bytes, ArtifactKind,
    ArtifactRole, BackendOutcome, ClaimBoundary, ExpectedVerdict,
};
use crate::experiment::{
    validate_experiment_bundle, ExperimentArtifactKind, ExperimentArtifactRef, ExperimentBundle,
    ExperimentBundleVersion, ExperimentConfig, ExperimentDataVersion, ExperimentLifecycle,
    ExperimentMetrics, ExperimentModelVersion, ExperimentPlugin, ExperimentPluginDescriptor,
    ExperimentReport, MeasurementStatus, MeasurementValue, MechanismLedger, MechanismMeasurement,
    MechanismMeasurementKind, MetricKind, MetricMeasurement, EXPERIMENT_BUNDLE_SCHEMA_VERSION,
};

/// Static id for the second typed experiment plugin.
pub const METACOGNITIVE_EXPERIMENT_PLUGIN_ID: &str =
    "metacognitive-monitor-control-experiment-plugin-v1";

/// Task seam identity for the synthetic contract.
pub const METACOGNITIVE_EXPERIMENT_TASK_ID: &str = "metacognitive-monitor-control-task-v1";

/// Model seam identity for the pure-data adapter.
pub const METACOGNITIVE_EXPERIMENT_MODEL_ID: &str = "metacognitive-monitor-control-model-v1";

/// Mechanism collector seam identity.
pub const METACOGNITIVE_EXPERIMENT_COLLECTOR_ID: &str =
    "metacognitive-monitor-control-collector-v1";

/// Evaluator seam identity.
pub const METACOGNITIVE_EXPERIMENT_EVALUATOR_ID: &str =
    "metacognitive-monitor-control-evaluator-v1";

/// Descriptor for the synthetic metacognitive plugin.
pub fn metacognitive_experiment_plugin_descriptor() -> ExperimentPluginDescriptor {
    ExperimentPluginDescriptor {
        plugin_id: METACOGNITIVE_EXPERIMENT_PLUGIN_ID.to_string(),
        version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
        task_id: METACOGNITIVE_EXPERIMENT_TASK_ID.to_string(),
        model_id: METACOGNITIVE_EXPERIMENT_MODEL_ID.to_string(),
        collector_id: METACOGNITIVE_EXPERIMENT_COLLECTOR_ID.to_string(),
        evaluator_id: METACOGNITIVE_EXPERIMENT_EVALUATOR_ID.to_string(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

/// Typed pure-data plugin implementation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MetacognitiveMonitorControlExperimentPlugin {
    descriptor: ExperimentPluginDescriptor,
}

impl MetacognitiveMonitorControlExperimentPlugin {
    /// Construct the deterministic synthetic plugin.
    pub fn new() -> Self {
        Self {
            descriptor: metacognitive_experiment_plugin_descriptor(),
        }
    }
}

impl Default for MetacognitiveMonitorControlExperimentPlugin {
    fn default() -> Self {
        Self::new()
    }
}

impl ExperimentPlugin for MetacognitiveMonitorControlExperimentPlugin {
    fn descriptor(&self) -> &ExperimentPluginDescriptor {
        &self.descriptor
    }

    fn run(&self) -> Result<ExperimentBundle> {
        let cases = valid_cases();
        let results = cases.iter().map(build_result).collect::<Result<Vec<_>>>()?;
        let config_payload = MetacognitiveConfigPayload {
            schema_version: METACOGNITIVE_MONITOR_CONTROL_SCHEMA_VERSION,
            plugin_id: METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            family_id: METACOGNITIVE_MONITOR_CONTROL_FAMILY_ID,
            case_count: cases.len() as u64,
        };
        let config_bytes = canonical_json_bytes(&config_payload)?;
        let config = ExperimentConfig {
            config_id: format!("{METACOGNITIVE_EXPERIMENT_PLUGIN_ID}-config"),
            schema_version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
            plugin_id: METACOGNITIVE_EXPERIMENT_PLUGIN_ID.to_string(),
            canonical_json: String::from_utf8(config_bytes.clone()).map_err(|error| {
                ZkBenchError::serialization("metacognitive_experiment.config", error.to_string())
            })?,
            digest: compute_artifact_digest_bytes(
                &config_bytes,
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Manifest),
            ),
        };
        let data_version_payload = MetacognitiveDataVersionPayload {
            source_id: METACOGNITIVE_MONITOR_CONTROL_FAMILY_ID,
            version: METACOGNITIVE_MONITOR_CONTROL_SCHEMA_VERSION,
            case_count: cases.len() as u64,
        };
        let data_version_digest =
            compute_artifact_digest(&cases, Some(ArtifactKind::Other), Some(ArtifactRole::Input))?;
        let model_identity = (
            METACOGNITIVE_EXPERIMENT_MODEL_ID,
            METACOGNITIVE_MONITOR_CONTROL_SCHEMA_VERSION,
            "pure_data_contract",
        );
        let model_version = ExperimentModelVersion {
            model_id: METACOGNITIVE_EXPERIMENT_MODEL_ID.to_string(),
            version: METACOGNITIVE_MONITOR_CONTROL_SCHEMA_VERSION.to_string(),
            runtime: "pure_data_contract".to_string(),
            artifact_digest: compute_artifact_digest(
                &model_identity,
                Some(ArtifactKind::Other),
                Some(ArtifactRole::Manifest),
            )?,
        };

        let accepted = results
            .iter()
            .filter(|result| result.backend_outcome == BackendOutcome::Accepted)
            .count() as u64;
        let rejected = results
            .iter()
            .filter(|result| result.backend_outcome == BackendOutcome::Rejected)
            .count() as u64;
        let capability_gaps = results
            .iter()
            .filter(|result| result.backend_outcome == BackendOutcome::CapabilityGap)
            .count() as u64;
        let mechanisms = MechanismLedger {
            schema_version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
            collector_id: METACOGNITIVE_EXPERIMENT_COLLECTOR_ID.to_string(),
            measurements: vec![
                collected_mechanism(
                    "case_count",
                    MechanismMeasurementKind::TraceOutcome,
                    cases.len() as u64,
                ),
                collected_mechanism(
                    "accepted_case_count",
                    MechanismMeasurementKind::TraceOutcome,
                    accepted,
                ),
                collected_mechanism(
                    "rejected_case_count",
                    MechanismMeasurementKind::TraceOutcome,
                    rejected,
                ),
                collected_mechanism(
                    "capability_gap_count",
                    MechanismMeasurementKind::TraceOutcome,
                    capability_gaps,
                ),
                unsupported_mechanism(
                    "activation_stream",
                    MechanismMeasurementKind::Activation,
                    "pure-data cases expose no model activations",
                ),
                unsupported_mechanism(
                    "causal_effect",
                    MechanismMeasurementKind::CausalEffect,
                    "pure-data cases do not authorize interventions",
                ),
            ],
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec![
                "Synthetic metacognitive cases are metadata-only contract fixtures.".to_string(),
                "Unsupported mechanism fields remain explicit and are not interpretability evidence."
                    .to_string(),
            ],
        };
        let metrics = ExperimentMetrics {
            schema_version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
            evaluator_id: METACOGNITIVE_EXPERIMENT_EVALUATOR_ID.to_string(),
            measurements: vec![
                collected_metric("case_count", cases.len() as u64),
                collected_metric("accepted_case_count", accepted),
                collected_metric("rejected_case_count", rejected),
                collected_metric("capability_gap_count", capability_gaps),
            ],
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec!["Metrics summarize the frozen synthetic contract only.".to_string()],
        };
        let non_claims = non_claims();
        let report = ExperimentReport {
            schema_version: EXPERIMENT_BUNDLE_SCHEMA_VERSION.to_string(),
            title: "Synthetic metacognitive monitoring/control contract".to_string(),
            summary: format!(
                "Evaluated {} frozen pure-data cases: {} accepted, {} rejected, {} capability gaps.",
                cases.len(), accepted, rejected, capability_gaps
            ),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            non_claims: non_claims.clone(),
            notes: vec![
                "This is a deterministic design-note fixture, not a model or introspection result."
                    .to_string(),
            ],
        };
        let bundle_id_material = (
            METACOGNITIVE_EXPERIMENT_PLUGIN_ID,
            data_version_digest.hex_digest.as_str(),
            cases.len() as u64,
        );
        let bundle_id_digest = compute_artifact_digest(
            &bundle_id_material,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?;
        let mut bundle = ExperimentBundle {
            bundle_id: format!("metacognitive_experiment_{}", bundle_id_digest.hex_digest),
            schema_version: ExperimentBundleVersion::default(),
            lifecycle: ExperimentLifecycle::Completed,
            config,
            data_version: ExperimentDataVersion {
                source_id: data_version_payload.source_id.to_string(),
                version: data_version_payload.version.to_string(),
                digest: data_version_digest,
                provenance: "shipped synthetic pure-data cases".to_string(),
            },
            model_version,
            mechanism_ledger: mechanisms,
            metrics,
            report,
            artifacts: Vec::new(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            non_claims,
        };
        bundle.artifacts = vec![
            artifact(
                "config/experiment-config.json",
                ExperimentArtifactKind::Config,
                &bundle.config,
            )?,
            artifact(
                "data/data-version.json",
                ExperimentArtifactKind::DataVersion,
                &bundle.data_version,
            )?,
            artifact(
                "model/model-version.json",
                ExperimentArtifactKind::ModelVersion,
                &bundle.model_version,
            )?,
            artifact(
                "mechanism/mechanism-ledger.json",
                ExperimentArtifactKind::MechanismLedger,
                &bundle.mechanism_ledger,
            )?,
            artifact(
                "metrics/metrics.json",
                ExperimentArtifactKind::Metrics,
                &bundle.metrics,
            )?,
            artifact(
                "report/report.json",
                ExperimentArtifactKind::Report,
                &bundle.report,
            )?,
            artifact(
                "synthetic/cases.json",
                ExperimentArtifactKind::ReplayManifest,
                &cases,
            )?,
            artifact(
                "synthetic/results.json",
                ExperimentArtifactKind::ReplayResult,
                &results,
            )?,
        ];
        let validation = validate_experiment_bundle(&bundle);
        if !validation.valid {
            return Err(ZkBenchError::validation(
                "metacognitive_experiment.bundle",
                format!(
                    "synthetic plugin bundle failed validation: {:?}",
                    validation.issues
                ),
            ));
        }
        Ok(bundle)
    }
}

#[derive(Debug, Serialize)]
struct MetacognitiveConfigPayload {
    schema_version: &'static str,
    plugin_id: &'static str,
    family_id: &'static str,
    case_count: u64,
}

#[derive(Debug, Serialize)]
struct MetacognitiveDataVersionPayload {
    source_id: &'static str,
    version: &'static str,
    case_count: u64,
}

fn valid_cases() -> Vec<MetacognitiveMonitorControlCase> {
    MetacognitiveMonitorControlVariant::ALL
        .into_iter()
        .filter(|variant| *variant != MetacognitiveMonitorControlVariant::MalformedRecord)
        .map(build_metacognitive_monitor_control_case)
        .collect()
}

fn build_result(
    case: &MetacognitiveMonitorControlCase,
) -> Result<MetacognitiveMonitorControlResult> {
    let validation =
        crate::adapters::validate_metacognitive_monitor_control_candidate(&case.candidate);
    if !validation.valid {
        return Err(ZkBenchError::validation(
            "metacognitive_experiment.candidate",
            format!("frozen candidate is invalid: {:?}", validation.issues),
        ));
    }
    let (observation, backend_outcome) = match case.expected_verdict {
        ExpectedVerdict::Accept => (
            MetacognitiveMonitorControlObservation::Passed,
            BackendOutcome::Accepted,
        ),
        ExpectedVerdict::Reject => (
            MetacognitiveMonitorControlObservation::Failed,
            BackendOutcome::Rejected,
        ),
        ExpectedVerdict::CapabilityGap => (
            MetacognitiveMonitorControlObservation::NotRun,
            BackendOutcome::CapabilityGap,
        ),
        ExpectedVerdict::BackendError => (
            MetacognitiveMonitorControlObservation::Malformed,
            BackendOutcome::MalformedArtifact,
        ),
        ExpectedVerdict::Inconclusive | ExpectedVerdict::UnsoundIfAccepted => (
            MetacognitiveMonitorControlObservation::NotRun,
            BackendOutcome::Inconclusive,
        ),
    };
    let result = MetacognitiveMonitorControlResult {
        candidate_digest: case.candidate.digest()?,
        observation,
        backend_outcome,
        claim_boundary: METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY,
        authority_granted: false,
    };
    let result_validation =
        crate::adapters::validate_metacognitive_monitor_control_result(case, &result);
    if !result_validation.valid {
        return Err(ZkBenchError::validation(
            "metacognitive_experiment.result",
            format!("frozen result is invalid: {:?}", result_validation.issues),
        ));
    }
    Ok(result)
}

fn artifact<T: Serialize>(
    uri: &str,
    kind: ExperimentArtifactKind,
    value: &T,
) -> Result<ExperimentArtifactRef> {
    Ok(ExperimentArtifactRef {
        uri: uri.to_string(),
        kind,
        digest: compute_artifact_digest(
            value,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?,
        required: true,
    })
}

fn collected_mechanism(
    measurement_id: &str,
    kind: MechanismMeasurementKind,
    value: u64,
) -> MechanismMeasurement {
    MechanismMeasurement {
        measurement_id: measurement_id.to_string(),
        kind,
        status: MeasurementStatus::Collected,
        value: Some(MeasurementValue::Count(value)),
        unit: Some("cases".to_string()),
        source_artifact_uri: Some("synthetic/results.json".to_string()),
        reason: None,
    }
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

fn collected_metric(metric_id: &str, value: u64) -> MetricMeasurement {
    MetricMeasurement {
        metric_id: metric_id.to_string(),
        kind: MetricKind::Count,
        status: MeasurementStatus::Collected,
        value: Some(MeasurementValue::Count(value)),
        unit: Some("cases".to_string()),
        source_artifact_uri: Some("synthetic/results.json".to_string()),
        reason: None,
    }
}

fn non_claims() -> Vec<String> {
    vec![
        "This plugin is a synthetic pure-data contract, not a model execution.".to_string(),
        "The cases do not establish self-modeling, introspection, interpretability, or causal validity.".to_string(),
        "No network, process, model download, privileged telemetry, or external backend was used.".to_string(),
        "The bundle is not official benchmark evidence and does not mutate the accepted Evidence Ledger.".to_string(),
    ]
}

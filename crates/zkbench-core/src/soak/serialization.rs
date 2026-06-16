//! Deterministic JSON serialization helpers for Phase K artifacts.

use crate::error::{Result, ZkBenchError};

use super::artifact_layout::{SoakArtifactManifest, SoakReportBundle};
use super::config::SoakRunConfig;
use super::failure_corpus::{FailureCorpusIndex, FailureReproductionManifest};
use super::health::SoakHealthReport;
use super::resume::SoakShardCheckpoint;
use super::shard::{SoakShardManifest, SoakShardPlan};
use super::telemetry::SoakTelemetryReport;

/// Serialize a soak run config to pretty JSON.
pub fn serialize_soak_run_config_json(config: &SoakRunConfig) -> Result<String> {
    serialize("serialize_soak_run_config_json", config)
}

/// Deserialize a soak run config from JSON.
pub fn deserialize_soak_run_config_json(json: &str) -> Result<SoakRunConfig> {
    deserialize("deserialize_soak_run_config_json", json)
}

/// Serialize a shard plan to pretty JSON.
pub fn serialize_soak_shard_plan_json(plan: &SoakShardPlan) -> Result<String> {
    serialize("serialize_soak_shard_plan_json", plan)
}

/// Deserialize a shard plan from JSON.
pub fn deserialize_soak_shard_plan_json(json: &str) -> Result<SoakShardPlan> {
    deserialize("deserialize_soak_shard_plan_json", json)
}

/// Serialize a shard manifest to pretty JSON.
pub fn serialize_soak_shard_manifest_json(manifest: &SoakShardManifest) -> Result<String> {
    serialize("serialize_soak_shard_manifest_json", manifest)
}

/// Deserialize a shard manifest from JSON.
pub fn deserialize_soak_shard_manifest_json(json: &str) -> Result<SoakShardManifest> {
    deserialize("deserialize_soak_shard_manifest_json", json)
}

/// Serialize a shard checkpoint to pretty JSON.
pub fn serialize_soak_shard_checkpoint_json(checkpoint: &SoakShardCheckpoint) -> Result<String> {
    serialize("serialize_soak_shard_checkpoint_json", checkpoint)
}

/// Deserialize a shard checkpoint from JSON.
pub fn deserialize_soak_shard_checkpoint_json(json: &str) -> Result<SoakShardCheckpoint> {
    deserialize("deserialize_soak_shard_checkpoint_json", json)
}

/// Serialize telemetry report to pretty JSON.
pub fn serialize_soak_telemetry_report_json(report: &SoakTelemetryReport) -> Result<String> {
    serialize("serialize_soak_telemetry_report_json", report)
}

/// Deserialize telemetry report from JSON.
pub fn deserialize_soak_telemetry_report_json(json: &str) -> Result<SoakTelemetryReport> {
    deserialize("deserialize_soak_telemetry_report_json", json)
}

/// Serialize health report to pretty JSON.
pub fn serialize_soak_health_report_json(report: &SoakHealthReport) -> Result<String> {
    serialize("serialize_soak_health_report_json", report)
}

/// Deserialize health report from JSON.
pub fn deserialize_soak_health_report_json(json: &str) -> Result<SoakHealthReport> {
    deserialize("deserialize_soak_health_report_json", json)
}

/// Serialize failure corpus index to pretty JSON.
pub fn serialize_failure_corpus_index_json(index: &FailureCorpusIndex) -> Result<String> {
    serialize("serialize_failure_corpus_index_json", index)
}

/// Deserialize failure corpus index from JSON.
pub fn deserialize_failure_corpus_index_json(json: &str) -> Result<FailureCorpusIndex> {
    deserialize("deserialize_failure_corpus_index_json", json)
}

/// Serialize failure reproduction manifest to pretty JSON.
pub fn serialize_failure_reproduction_manifest_json(
    manifest: &FailureReproductionManifest,
) -> Result<String> {
    serialize("serialize_failure_reproduction_manifest_json", manifest)
}

/// Deserialize failure reproduction manifest from JSON.
pub fn deserialize_failure_reproduction_manifest_json(
    json: &str,
) -> Result<FailureReproductionManifest> {
    deserialize("deserialize_failure_reproduction_manifest_json", json)
}

/// Serialize soak artifact manifest to pretty JSON.
pub fn serialize_soak_artifact_manifest_json(manifest: &SoakArtifactManifest) -> Result<String> {
    serialize("serialize_soak_artifact_manifest_json", manifest)
}

/// Deserialize soak artifact manifest from JSON.
pub fn deserialize_soak_artifact_manifest_json(json: &str) -> Result<SoakArtifactManifest> {
    deserialize("deserialize_soak_artifact_manifest_json", json)
}

/// Serialize report bundle to pretty JSON.
pub fn serialize_soak_report_bundle_json(bundle: &SoakReportBundle) -> Result<String> {
    serialize("serialize_soak_report_bundle_json", bundle)
}

/// Deserialize report bundle from JSON.
pub fn deserialize_soak_report_bundle_json(json: &str) -> Result<SoakReportBundle> {
    deserialize("deserialize_soak_report_bundle_json", json)
}

fn serialize<T: serde::Serialize>(path: &str, value: &T) -> Result<String> {
    serde_json::to_string_pretty(value)
        .map_err(|error| ZkBenchError::serialization(path, error.to_string()))
}

fn deserialize<T: serde::de::DeserializeOwned>(path: &str, json: &str) -> Result<T> {
    serde_json::from_str(json)
        .map_err(|error| ZkBenchError::deserialization(path, error.to_string()))
}

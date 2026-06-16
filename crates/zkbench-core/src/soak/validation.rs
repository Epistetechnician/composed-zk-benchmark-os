//! Validation helpers for Phase K local soak artifacts.

use crate::error::Result;

use super::artifact_layout::{validate_soak_report_bundle, SoakReportBundleValidation};
use super::config::{validate_soak_run_config, SoakRunConfig};
use super::failure_corpus::{validate_failure_corpus_index, FailureCorpusIndex};
use super::health::{validate_soak_health_report, SoakHealthReport};
use super::resume::{validate_soak_shard_checkpoint, SoakShardCheckpoint};
use super::shard::{
    validate_soak_shard_manifest, validate_soak_shard_plan, SoakShardManifest, SoakShardPlan,
    SoakShardResumeToken, SoakShardValidation,
};
use super::telemetry::{validate_soak_telemetry_report, SoakTelemetryReport};

/// Validate a config.
pub fn validate_config(config: &SoakRunConfig) -> Result<()> {
    validate_soak_run_config(config)
}

/// Validate a shard plan.
pub fn validate_shard_plan(plan: &SoakShardPlan) -> Result<()> {
    validate_soak_shard_plan(plan)
}

/// Validate a shard manifest.
pub fn validate_shard_manifest(manifest: &SoakShardManifest) -> SoakShardValidation {
    validate_soak_shard_manifest(manifest)
}

/// Validate a checkpoint.
pub fn validate_checkpoint(
    checkpoint: &SoakShardCheckpoint,
    expected_config_digest: &str,
    expected_resume_token: &SoakShardResumeToken,
) -> Result<()> {
    validate_soak_shard_checkpoint(checkpoint, expected_config_digest, expected_resume_token)
}

/// Validate telemetry.
pub fn validate_telemetry(report: &SoakTelemetryReport) -> Result<()> {
    validate_soak_telemetry_report(report)
}

/// Validate health report.
pub fn validate_health_report(report: &SoakHealthReport) -> Result<()> {
    validate_soak_health_report(report)
}

/// Validate failure corpus.
pub fn validate_failure_corpus(index: &FailureCorpusIndex) -> Result<()> {
    validate_failure_corpus_index(index)
}

/// Validate report bundle.
pub fn validate_report_bundle(
    bundle: &super::artifact_layout::SoakReportBundle,
) -> SoakReportBundleValidation {
    validate_soak_report_bundle(bundle)
}

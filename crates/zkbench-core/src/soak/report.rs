//! Report bundle helpers for Phase K.

use crate::error::Result;
use crate::evidence::ClaimBoundary;

use super::artifact_layout::{
    soak_artifact_manifest, SoakArtifactDigestSet, SoakArtifactRole, SoakReportBundle,
};
use super::failure_corpus::FailureCorpusIndex;
use super::health::SoakHealthReport;
use super::shard::SoakShardPlan;
use super::telemetry::SoakTelemetryReport;

/// Build a local-only report bundle from shard outputs.
pub fn build_soak_report_bundle(
    bundle_id: impl Into<String>,
    shard_plan: SoakShardPlan,
    telemetry_reports: Vec<SoakTelemetryReport>,
    health_reports: Vec<SoakHealthReport>,
    failure_corpus_indexes: Vec<FailureCorpusIndex>,
) -> Result<SoakReportBundle> {
    let bundle_id = bundle_id.into();
    let artifacts = vec![
        soak_artifact_manifest(
            "soak_run_config",
            SoakArtifactRole::RunConfig,
            "soak_run_config.json",
            &shard_plan.config,
        )?,
        soak_artifact_manifest(
            "shard_plan",
            SoakArtifactRole::ShardPlan,
            "shard_plan.json",
            &shard_plan,
        )?,
    ];
    Ok(SoakReportBundle {
        bundle_id,
        bundle_version: "phase-k-soak-report-bundle-v0".to_string(),
        config: shard_plan.config.clone(),
        shard_manifests: shard_plan.shard_manifests.clone(),
        shard_plan,
        telemetry_reports,
        health_reports,
        failure_corpus_indexes,
        artifact_digest_set: SoakArtifactDigestSet { artifacts },
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Soak report bundle is local-only.".to_string(),
            "Local soak telemetry is not official benchmark evidence.".to_string(),
            "Internal timing telemetry is not ZK backend performance.".to_string(),
        ],
    })
}

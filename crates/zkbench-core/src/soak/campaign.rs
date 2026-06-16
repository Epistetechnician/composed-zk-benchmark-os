//! Phase L long local soak campaigns.
//!
//! A campaign runs every shard of a plan under an explicitly approved,
//! repo-external (or git-ignored) artifact root, attaches reproduction
//! bundles to retained failure packs, and aggregates local-only reports.
//! Campaign outputs are local health artifacts and never benchmark evidence.

use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;

use super::artifact_layout::{
    soak_artifact_manifest, write_soak_report_bundle, SoakArtifactDigestSet, SoakArtifactLayout,
    SoakArtifactRole, SoakReportBundle,
};
use super::failure_corpus::FailureCorpusEntry;
use super::health::{aggregate_soak_health_reports, SoakHealthReport};
use super::reproduction::{attach_reproduction_bundle_to_pack, ReproductionBundleAttachment};
use super::runner::{LocalSoakRunner, LocalSoakRunnerConfig, SoakRunResult};
use super::shard::{SoakShardId, SoakShardPlan};

/// Explicit user approval record required before a long campaign runs.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakCampaignApproval {
    /// Who approved the campaign.
    pub approved_by: String,
    /// Approval statement.
    pub approval_statement: String,
    /// Approval timestamp in unix milliseconds.
    pub approved_at_ms: u64,
}

/// Declared artifact root policy for campaign outputs.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakCampaignArtifactRootPolicy {
    /// Absolute artifact root for all campaign outputs.
    pub artifact_root: PathBuf,
    /// Caller declaration that the root is outside the repo or git-ignored.
    pub declared_outside_repo_or_ignored: bool,
}

/// Campaign configuration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakCampaignConfig {
    /// Campaign id.
    pub campaign_id: String,
    /// Approval record.
    pub approval: SoakCampaignApproval,
    /// Artifact root policy.
    pub artifact_root_policy: SoakCampaignArtifactRootPolicy,
    /// Runner config applied to every shard.
    pub runner_config: LocalSoakRunnerConfig,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Per-shard campaign outcome.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SoakCampaignShardOutcome {
    /// Shard id.
    pub shard_id: SoakShardId,
    /// Run result.
    pub run_result: SoakRunResult,
    /// Reproduction bundles attached to retained failure packs.
    #[serde(default)]
    pub reproduction_bundle_attachments: Vec<ReproductionBundleAttachment>,
}

/// Campaign result.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SoakCampaignResult {
    /// Campaign id.
    pub campaign_id: String,
    /// Shard outcomes.
    pub shard_outcomes: Vec<SoakCampaignShardOutcome>,
    /// Aggregate health report.
    pub aggregate_health_report: SoakHealthReport,
    /// Aggregate report bundle.
    pub report_bundle: SoakReportBundle,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl SoakCampaignResult {
    /// Campaign results never contain ZK backend performance claims.
    pub fn contains_zk_backend_performance_claims(&self) -> bool {
        false
    }
}

/// Validate a campaign configuration.
pub fn validate_soak_campaign_config(config: &SoakCampaignConfig) -> Result<()> {
    if config.campaign_id.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.campaign.campaign_id",
            "campaign id is empty",
        ));
    }
    if config.approval.approved_by.trim().is_empty()
        || config.approval.approval_statement.trim().is_empty()
    {
        return Err(ZkBenchError::soak(
            "soak.campaign.approval",
            "long soak campaigns require an explicit approval record",
        ));
    }
    if !config.artifact_root_policy.artifact_root.is_absolute() {
        return Err(ZkBenchError::soak(
            "soak.campaign.artifact_root",
            "campaign artifact root must be an absolute path",
        ));
    }
    if !config.artifact_root_policy.declared_outside_repo_or_ignored {
        return Err(ZkBenchError::soak(
            "soak.campaign.artifact_root",
            "campaign artifact root must be declared outside the repo or git-ignored",
        ));
    }
    Ok(())
}

/// Run every shard of a plan as one approved local campaign.
pub fn run_soak_campaign(
    config: &SoakCampaignConfig,
    plan: SoakShardPlan,
) -> Result<SoakCampaignResult> {
    validate_soak_campaign_config(config)?;
    let campaign_root = config
        .artifact_root_policy
        .artifact_root
        .join(&config.campaign_id);
    let shard_ids: Vec<SoakShardId> = plan
        .shard_manifests
        .iter()
        .map(|manifest| manifest.shard_id.clone())
        .collect();
    let shard_manifests = plan.shard_manifests.clone();
    let run_config = plan.config.clone();
    let mut runner = LocalSoakRunner::new(plan.clone())
        .with_temp_or_user_output_dir(&campaign_root)
        .with_runner_config(config.runner_config.clone());

    let mut shard_outcomes = Vec::new();
    for shard_id in shard_ids {
        let run_result = runner.run_shard(shard_id.clone())?;
        let attachments = attach_bundles_to_failure_packs(&campaign_root, &shard_id, &run_result)?;
        shard_outcomes.push(SoakCampaignShardOutcome {
            shard_id,
            run_result,
            reproduction_bundle_attachments: attachments,
        });
    }

    let health_reports: Vec<SoakHealthReport> = shard_outcomes
        .iter()
        .map(|outcome| outcome.run_result.health_report.clone())
        .collect();
    let aggregate_health_report =
        aggregate_soak_health_reports(run_config.id.clone(), &health_reports)?;

    let mut artifacts = vec![soak_artifact_manifest(
        format!("aggregate_health_{}", config.campaign_id),
        SoakArtifactRole::AggregateReport,
        "aggregate/aggregate_health_report.json".to_string(),
        &aggregate_health_report,
    )?];
    for outcome in &shard_outcomes {
        let layout = SoakArtifactLayout::for_shard(&outcome.shard_id);
        artifacts.push(soak_artifact_manifest(
            format!("health_{}", outcome.shard_id.value),
            SoakArtifactRole::HealthReport,
            layout.health_report_path.clone(),
            &outcome.run_result.health_report,
        )?);
        artifacts.push(soak_artifact_manifest(
            format!("telemetry_{}", outcome.shard_id.value),
            SoakArtifactRole::Telemetry,
            layout.telemetry_path.clone(),
            &outcome.run_result.telemetry_report,
        )?);
        artifacts.push(soak_artifact_manifest(
            format!("failure_corpus_{}", outcome.shard_id.value),
            SoakArtifactRole::FailureCorpusIndex,
            layout.failure_corpus_index_path.clone(),
            &outcome.run_result.failure_corpus_index,
        )?);
    }

    let report_bundle = SoakReportBundle {
        bundle_id: format!("campaign_{}", config.campaign_id),
        bundle_version: "phase-l-soak-campaign-v0".to_string(),
        config: run_config,
        shard_plan: plan,
        shard_manifests,
        telemetry_reports: shard_outcomes
            .iter()
            .map(|outcome| outcome.run_result.telemetry_report.clone())
            .collect(),
        health_reports,
        failure_corpus_indexes: shard_outcomes
            .iter()
            .map(|outcome| outcome.run_result.failure_corpus_index.clone())
            .collect(),
        artifact_digest_set: SoakArtifactDigestSet { artifacts },
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Campaign report bundle is a local health artifact only.".to_string(),
            "No external execution occurred and no benchmark evidence is included.".to_string(),
        ],
    };
    write_json_aggregate(&campaign_root, &aggregate_health_report)?;
    write_soak_report_bundle(
        campaign_root.join("aggregate/report_bundle"),
        &report_bundle,
    )?;

    Ok(SoakCampaignResult {
        campaign_id: config.campaign_id.clone(),
        shard_outcomes,
        aggregate_health_report,
        report_bundle,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Local soak campaign result is a Level0DesignNote health artifact.".to_string(),
        ],
    })
}

fn attach_bundles_to_failure_packs(
    campaign_root: &Path,
    shard_id: &SoakShardId,
    run_result: &SoakRunResult,
) -> Result<Vec<ReproductionBundleAttachment>> {
    let layout = SoakArtifactLayout::for_shard(shard_id);
    let failure_packs_root = campaign_root.join(&layout.failure_packs_dir);
    let mut attachments = Vec::new();
    for case_result in &run_result.case_results {
        if case_result.failures.is_empty() {
            continue;
        }
        let pack_root = failure_packs_root.join(&case_result.case_id);
        if !pack_root.join("pack.json").exists() {
            continue;
        }
        let entries: Vec<FailureCorpusEntry> = run_result
            .failure_corpus_index
            .entries
            .iter()
            .filter(|entry| entry.source_soak_case_id == case_result.case_id)
            .cloned()
            .collect();
        if entries.is_empty() {
            continue;
        }
        attachments.push(attach_reproduction_bundle_to_pack(&pack_root, &entries)?);
    }
    Ok(attachments)
}

fn write_json_aggregate(campaign_root: &Path, report: &SoakHealthReport) -> Result<()> {
    super::artifact_layout::write_json(
        campaign_root.join("aggregate/aggregate_health_report.json"),
        report,
    )
}

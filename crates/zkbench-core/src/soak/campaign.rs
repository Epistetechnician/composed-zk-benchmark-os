//! Quick local soak campaigns with artifact archival and regression corpus curation.

use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::generator::FamilyKind;
use crate::pack::{
    review_report_bundle, review_soak_report_bundles, ReportBundleReviewFinding,
    ReportBundleReviewPlan, ReportBundleReviewReport, ReportBundleSampleStrategy,
};

use super::config::{SoakConfig, SoakFailure};
use super::regression_corpus::{
    append_regression_entries, entries_from_review_findings, load_regression_corpus,
    save_regression_corpus, RegressionCorpusEntry, RegressionFailureKind,
};
use super::runner::{run_local_soak, SoakExecutionReport};

/// Campaign report schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakCampaignReportVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for SoakCampaignReportVersion {
    fn default() -> Self {
        Self {
            value: "phase-l-soak-campaign-v0".to_string(),
        }
    }
}

/// Configuration for a Phase L soak campaign with artifact archival.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakCampaignConfig {
    /// Stable campaign id used in artifact paths.
    pub campaign_id: String,
    /// Soak configuration for the campaign grid.
    pub soak_config: SoakConfig,
    /// Report-bundle review plan for sampled review.
    pub review_plan: ReportBundleReviewPlan,
    /// Root directory for ignored Phase L artifacts.
    pub artifacts_root: String,
}

/// Per-pack sampled review artifact written under a campaign directory.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PackSampledReview {
    /// Pack id.
    pub pack_id: String,
    /// Relative pack path from the campaign soak root.
    pub pack_root_relative: String,
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Seed.
    pub seed: u64,
    /// Whether the pack passed all review checks.
    pub valid: bool,
    /// Review findings.
    #[serde(default)]
    pub findings: Vec<ReportBundleReviewFinding>,
}

/// Campaign execution report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakCampaignReport {
    /// Schema version.
    pub version: SoakCampaignReportVersion,
    /// Claim boundary for campaign metadata.
    pub claim_boundary: ClaimBoundary,
    /// Campaign id.
    pub campaign_id: String,
    /// Campaign configuration.
    pub config: SoakCampaignConfig,
    /// Soak execution report.
    pub soak_report: SoakExecutionReport,
    /// Sampled report-bundle review report.
    pub review_report: ReportBundleReviewReport,
    /// Number of sampled per-pack review files written.
    pub sampled_report_count: usize,
    /// Number of failure packs archived.
    pub failure_pack_count: usize,
    /// Number of new regression corpus entries added.
    pub corpus_entries_added: usize,
    /// Relative campaign directory from artifacts root.
    pub campaign_relative_path: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Run a quick local soak campaign, archive sampled reports and failure packs, and curate corpus.
pub fn run_soak_campaign(config: &SoakCampaignConfig) -> Result<SoakCampaignReport> {
    validate_campaign_config(config)?;

    let artifacts_root = PathBuf::from(&config.artifacts_root);
    let campaign_dir = artifacts_root.join("campaigns").join(&config.campaign_id);
    if campaign_dir.exists() {
        fs::remove_dir_all(&campaign_dir).map_err(|error| {
            ZkBenchError::benchmark_pack(campaign_dir.display().to_string(), error.to_string())
        })?;
    }
    fs::create_dir_all(&campaign_dir).map_err(|error| {
        ZkBenchError::benchmark_pack(campaign_dir.display().to_string(), error.to_string())
    })?;

    let soak_root = campaign_dir.join("soak");
    let soak_report = run_local_soak(&config.soak_config, &soak_root)?;
    let review_report = review_soak_report_bundles(&soak_root, &soak_report, &config.review_plan)?;

    let sampled_dir = campaign_dir.join("sampled_reports");
    fs::create_dir_all(&sampled_dir).map_err(|error| {
        ZkBenchError::benchmark_pack(sampled_dir.display().to_string(), error.to_string())
    })?;
    let sampled_reviews =
        write_sampled_reports(&soak_root, &soak_report, &config.review_plan, &sampled_dir)?;

    let failure_dir = campaign_dir.join("failure_packs");
    fs::create_dir_all(&failure_dir).map_err(|error| {
        ZkBenchError::benchmark_pack(failure_dir.display().to_string(), error.to_string())
    })?;
    let failure_pack_count =
        archive_failure_packs(&soak_root, &soak_report, &sampled_reviews, &failure_dir)?;

    let campaign_relative_path = format!("campaigns/{}", config.campaign_id);
    write_soak_failure_records(&campaign_dir, &soak_report)?;
    let corpus_entries = build_corpus_entries(
        &config.campaign_id,
        &campaign_relative_path,
        &soak_report,
        &sampled_reviews,
    )?;
    let corpus_path = artifacts_root.join("regression_corpus").join("corpus.json");
    let mut corpus = load_regression_corpus(&corpus_path)?;
    let corpus_entries_added = append_regression_entries(&mut corpus, corpus_entries);
    save_regression_corpus(&corpus, &corpus_path)?;

    let report = SoakCampaignReport {
        version: SoakCampaignReportVersion::default(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        campaign_id: config.campaign_id.clone(),
        config: config.clone(),
        soak_report: soak_report.clone(),
        review_report: review_report.clone(),
        sampled_report_count: sampled_reviews.len(),
        failure_pack_count,
        corpus_entries_added,
        campaign_relative_path,
        notes: vec![
            "Soak campaign artifacts are local failure and review metadata only.".to_string(),
            "Campaign reports are not official benchmark evidence.".to_string(),
        ],
    };

    write_campaign_artifacts(&campaign_dir, &soak_report, &review_report, &report)?;
    write_latest_campaign_pointer(&artifacts_root, &config.campaign_id)?;

    Ok(report)
}

fn validate_campaign_config(config: &SoakCampaignConfig) -> Result<()> {
    if config.campaign_id.trim().is_empty() {
        return Err(ZkBenchError::benchmark_pack(
            "campaign.id",
            "campaign id must not be empty",
        ));
    }
    if config.artifacts_root.trim().is_empty() || config.artifacts_root.contains("..") {
        return Err(ZkBenchError::benchmark_pack(
            "campaign.artifacts_root",
            "artifacts_root must be a non-empty path without parent traversal",
        ));
    }
    Ok(())
}

fn write_sampled_reports(
    soak_root: &Path,
    soak_report: &SoakExecutionReport,
    review_plan: &ReportBundleReviewPlan,
    sampled_dir: &Path,
) -> Result<Vec<PackSampledReview>> {
    let pack_roots = soak_report
        .pack_descriptors
        .iter()
        .map(|descriptor| soak_root.join(&descriptor.pack_root_relative))
        .collect::<Vec<_>>();
    let sampled_roots = sample_pack_roots(&pack_roots, &review_plan.sample_strategy);
    let sampled_set = sampled_roots
        .iter()
        .map(|path| path.to_string_lossy().to_string())
        .collect::<BTreeSet<_>>();

    let mut reviews = Vec::new();
    for descriptor in &soak_report.pack_descriptors {
        let pack_root = soak_root.join(&descriptor.pack_root_relative);
        if !sampled_set.contains(&pack_root.to_string_lossy().to_string()) {
            continue;
        }
        let per_pack = review_report_bundle(&pack_root, review_plan)?;
        let review = PackSampledReview {
            pack_id: descriptor.pack_id.clone(),
            pack_root_relative: descriptor.pack_root_relative.clone(),
            family_kind: descriptor.family_kind,
            seed: descriptor.seed,
            valid: per_pack.valid,
            findings: per_pack.findings,
        };
        let file_name = format!("{}.json", sanitize_filename(&descriptor.pack_id));
        let bytes = serde_json::to_vec_pretty(&review).map_err(|error| {
            ZkBenchError::serialization("campaign.sampled_review", error.to_string())
        })?;
        fs::write(sampled_dir.join(file_name), bytes).map_err(|error| {
            ZkBenchError::benchmark_pack(sampled_dir.display().to_string(), error.to_string())
        })?;
        reviews.push(review);
    }
    Ok(reviews)
}

fn archive_failure_packs(
    soak_root: &Path,
    soak_report: &SoakExecutionReport,
    sampled_reviews: &[PackSampledReview],
    failure_dir: &Path,
) -> Result<usize> {
    let mut failed_pack_ids = sampled_reviews
        .iter()
        .filter(|review| !review.valid)
        .map(|review| review.pack_id.clone())
        .collect::<BTreeSet<_>>();

    for failure in &soak_report.failures {
        failed_pack_ids.insert(format!(
            "phase_l_soak_{}_seed_{}",
            failure.family_kind.id_segment(),
            failure.seed
        ));
    }

    let mut archived = 0usize;
    for descriptor in &soak_report.pack_descriptors {
        if !failed_pack_ids.contains(&descriptor.pack_id) {
            continue;
        }
        let source = soak_root.join(&descriptor.pack_root_relative);
        if !source.is_dir() {
            continue;
        }
        let dest = failure_dir.join(sanitize_filename(&descriptor.pack_id));
        copy_dir_recursive(&source, &dest)?;
        archived += 1;
    }
    Ok(archived)
}

fn build_corpus_entries(
    campaign_id: &str,
    campaign_relative_path: &str,
    soak_report: &SoakExecutionReport,
    sampled_reviews: &[PackSampledReview],
) -> Result<Vec<RegressionCorpusEntry>> {
    let mut entries = Vec::new();

    for review in sampled_reviews.iter().filter(|review| !review.valid) {
        let artifact_relative_path = format!(
            "{campaign_relative_path}/failure_packs/{}",
            sanitize_filename(&review.pack_id)
        );
        entries.extend(entries_from_review_findings(
            campaign_id,
            &review.pack_id,
            review.family_kind,
            review.seed,
            artifact_relative_path,
            &review.findings,
        ));
    }

    for failure in &soak_report.failures {
        entries.push(soak_failure_entry(
            campaign_id,
            campaign_relative_path,
            failure,
        ));
    }

    for descriptor in &soak_report.pack_descriptors {
        if descriptor.mutation_passes_skipped == 0 {
            continue;
        }
        entries.push(RegressionCorpusEntry {
            id: format!("{campaign_id}__{}__mutation_skipped", descriptor.pack_id),
            campaign_id: campaign_id.to_string(),
            pack_id: Some(descriptor.pack_id.clone()),
            family_kind: descriptor.family_kind,
            seed: descriptor.seed,
            failure_kind: RegressionFailureKind::MutationPassSkipped,
            codes: vec!["mutation_pass_skipped".to_string()],
            artifact_relative_path: format!(
                "{campaign_relative_path}/soak/{}",
                descriptor.pack_root_relative
            ),
            notes: vec![format!(
                "mutation passes skipped: {}",
                descriptor.mutation_passes_skipped
            )],
        });
    }

    Ok(entries)
}

fn soak_failure_entry(
    campaign_id: &str,
    campaign_relative_path: &str,
    failure: &SoakFailure,
) -> RegressionCorpusEntry {
    let pack_id = format!(
        "phase_l_soak_{}_seed_{}",
        failure.family_kind.id_segment(),
        failure.seed
    );
    RegressionCorpusEntry {
        id: format!("{campaign_id}__{pack_id}__soak_write_failed"),
        campaign_id: campaign_id.to_string(),
        pack_id: None,
        family_kind: failure.family_kind,
        seed: failure.seed,
        failure_kind: RegressionFailureKind::SoakWriteFailed,
        codes: vec!["soak_write_failed".to_string()],
        artifact_relative_path: format!("{campaign_relative_path}/soak_failures/{pack_id}.json"),
        notes: vec![failure.message.clone()],
    }
}

fn write_soak_failure_records(
    campaign_dir: &Path,
    soak_report: &SoakExecutionReport,
) -> Result<()> {
    if soak_report.failures.is_empty() {
        return Ok(());
    }
    let failures_dir = campaign_dir.join("soak_failures");
    fs::create_dir_all(&failures_dir).map_err(|error| {
        ZkBenchError::benchmark_pack(failures_dir.display().to_string(), error.to_string())
    })?;
    for failure in &soak_report.failures {
        let file_name = format!(
            "phase_l_soak_{}_seed_{}.json",
            failure.family_kind.id_segment(),
            failure.seed
        );
        let bytes = serde_json::to_vec_pretty(failure).map_err(|error| {
            ZkBenchError::serialization("campaign.soak_failure", error.to_string())
        })?;
        fs::write(failures_dir.join(file_name), bytes).map_err(|error| {
            ZkBenchError::benchmark_pack(failures_dir.display().to_string(), error.to_string())
        })?;
    }
    Ok(())
}

fn write_campaign_artifacts(
    campaign_dir: &Path,
    soak_report: &SoakExecutionReport,
    review_report: &ReportBundleReviewReport,
    campaign_report: &SoakCampaignReport,
) -> Result<()> {
    let soak_bytes = serde_json::to_vec_pretty(soak_report)
        .map_err(|error| ZkBenchError::serialization("campaign.soak_report", error.to_string()))?;
    fs::write(campaign_dir.join("soak_execution_report.json"), soak_bytes).map_err(|error| {
        ZkBenchError::benchmark_pack(campaign_dir.display().to_string(), error.to_string())
    })?;

    let review_bytes = serde_json::to_vec_pretty(review_report).map_err(|error| {
        ZkBenchError::serialization("campaign.review_report", error.to_string())
    })?;
    fs::write(campaign_dir.join("report_bundle_review.json"), review_bytes).map_err(|error| {
        ZkBenchError::benchmark_pack(campaign_dir.display().to_string(), error.to_string())
    })?;

    let campaign_bytes = serde_json::to_vec_pretty(campaign_report)
        .map_err(|error| ZkBenchError::serialization("campaign.report", error.to_string()))?;
    fs::write(campaign_dir.join("campaign_report.json"), campaign_bytes).map_err(|error| {
        ZkBenchError::benchmark_pack(campaign_dir.display().to_string(), error.to_string())
    })?;
    Ok(())
}

fn write_latest_campaign_pointer(artifacts_root: &Path, campaign_id: &str) -> Result<()> {
    fs::write(
        artifacts_root.join(".latest_campaign"),
        format!("{campaign_id}\n"),
    )
    .map_err(|error| {
        ZkBenchError::benchmark_pack(
            artifacts_root
                .join(".latest_campaign")
                .display()
                .to_string(),
            error.to_string(),
        )
    })
}

fn sample_pack_roots(
    pack_roots: &[PathBuf],
    strategy: &ReportBundleSampleStrategy,
) -> Vec<PathBuf> {
    match strategy {
        ReportBundleSampleStrategy::All => pack_roots.to_vec(),
        ReportBundleSampleStrategy::First { count } => {
            pack_roots.iter().take(*count).cloned().collect()
        }
        ReportBundleSampleStrategy::EveryNth { stride } => pack_roots
            .iter()
            .enumerate()
            .filter_map(|(index, path)| {
                if index % stride == 0 {
                    Some(path.clone())
                } else {
                    None
                }
            })
            .collect(),
    }
}

fn copy_dir_recursive(source: &Path, dest: &Path) -> Result<()> {
    if dest.exists() {
        fs::remove_dir_all(dest).map_err(|error| {
            ZkBenchError::benchmark_pack(dest.display().to_string(), error.to_string())
        })?;
    }
    fs::create_dir_all(dest).map_err(|error| {
        ZkBenchError::benchmark_pack(dest.display().to_string(), error.to_string())
    })?;
    for entry in fs::read_dir(source).map_err(|error| {
        ZkBenchError::benchmark_pack(source.display().to_string(), error.to_string())
    })? {
        let entry = entry.map_err(|error| {
            ZkBenchError::benchmark_pack(source.display().to_string(), error.to_string())
        })?;
        let file_type = entry.file_type().map_err(|error| {
            ZkBenchError::benchmark_pack(entry.path().display().to_string(), error.to_string())
        })?;
        let target = dest.join(entry.file_name());
        if file_type.is_dir() {
            copy_dir_recursive(&entry.path(), &target)?;
        } else {
            fs::copy(entry.path(), &target).map_err(|error| {
                ZkBenchError::benchmark_pack(target.display().to_string(), error.to_string())
            })?;
        }
    }
    Ok(())
}

fn sanitize_filename(value: &str) -> String {
    value
        .chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() || ch == '_' || ch == '-' {
                ch
            } else {
                '_'
            }
        })
        .collect()
}

/// Serialize a campaign report to pretty JSON.
pub fn serialize_soak_campaign_report_json(report: &SoakCampaignReport) -> Result<String> {
    serde_json::to_string_pretty(report)
        .map_err(|error| ZkBenchError::serialization("campaign.report", error.to_string()))
}

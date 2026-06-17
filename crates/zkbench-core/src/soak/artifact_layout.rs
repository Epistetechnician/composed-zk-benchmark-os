//! Local soak artifact layout and report bundle types.

use std::collections::BTreeSet;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary,
};

use super::config::{validate_soak_run_config, SoakRunConfig};
use super::failure_corpus::{validate_failure_corpus_index, FailureCorpusIndex};
use super::health::{validate_soak_health_report, SoakHealthReport};
use super::shard::{
    validate_soak_shard_manifest, validate_soak_shard_plan, SoakShardId, SoakShardManifest,
    SoakShardPlan,
};
use super::telemetry::{validate_soak_telemetry_report, SoakTelemetryReport};

/// Soak artifact role.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SoakArtifactRole {
    /// Run config.
    RunConfig,
    /// Shard plan.
    ShardPlan,
    /// Shard manifest.
    ShardManifest,
    /// Checkpoint.
    Checkpoint,
    /// Telemetry report.
    Telemetry,
    /// Health report.
    HealthReport,
    /// Failure corpus index.
    FailureCorpusIndex,
    /// Sampled pack.
    SampledPack,
    /// Failure pack.
    FailurePack,
    /// Local summary.
    LocalSummary,
    /// Aggregate report.
    AggregateReport,
    /// Bundle manifest.
    ReportBundle,
}

/// Deterministic artifact layout for one shard.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakArtifactLayout {
    /// Config path.
    pub run_config_path: String,
    /// Shard plan path.
    pub shard_plan_path: String,
    /// Shard root.
    pub shard_root: String,
    /// Shard manifest path.
    pub shard_manifest_path: String,
    /// Checkpoint path.
    pub checkpoint_path: String,
    /// Telemetry path.
    pub telemetry_path: String,
    /// Health report path.
    pub health_report_path: String,
    /// Failure corpus index path.
    pub failure_corpus_index_path: String,
    /// Sampled packs directory.
    pub sampled_packs_dir: String,
    /// Failure packs directory.
    pub failure_packs_dir: String,
    /// Local summary path.
    pub local_summary_path: String,
    /// Aggregate root.
    pub aggregate_root: String,
}

impl SoakArtifactLayout {
    /// Build the documented layout for a shard.
    pub fn for_shard(shard_id: &SoakShardId) -> Self {
        let shard_root = format!("shards/{}", shard_id.value);
        Self {
            run_config_path: "soak_run_config.json".to_string(),
            shard_plan_path: "shard_plan.json".to_string(),
            shard_manifest_path: format!("{shard_root}/shard_manifest.json"),
            checkpoint_path: format!("{shard_root}/checkpoint.json"),
            telemetry_path: format!("{shard_root}/telemetry.json"),
            health_report_path: format!("{shard_root}/health_report.json"),
            failure_corpus_index_path: format!("{shard_root}/failure_corpus_index.json"),
            sampled_packs_dir: format!("{shard_root}/sampled_packs"),
            failure_packs_dir: format!("{shard_root}/failure_packs"),
            local_summary_path: format!("{shard_root}/reports/local_summary.json"),
            aggregate_root: "aggregate".to_string(),
            shard_root,
        }
    }

    /// Return true when all paths are relative and portable.
    pub fn uses_relative_paths_only(&self) -> bool {
        [
            &self.run_config_path,
            &self.shard_plan_path,
            &self.shard_root,
            &self.shard_manifest_path,
            &self.checkpoint_path,
            &self.telemetry_path,
            &self.health_report_path,
            &self.failure_corpus_index_path,
            &self.sampled_packs_dir,
            &self.failure_packs_dir,
            &self.local_summary_path,
            &self.aggregate_root,
        ]
        .iter()
        .all(|path| relative_path_is_portable(path))
    }
}

/// Soak artifact manifest entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakArtifactManifest {
    /// Artifact id.
    pub artifact_id: String,
    /// Role.
    pub role: SoakArtifactRole,
    /// Relative path.
    pub relative_path: String,
    /// Digest.
    #[serde(default)]
    pub digest: Option<ArtifactDigest>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Artifact digest set.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct SoakArtifactDigestSet {
    /// Artifact manifests.
    pub artifacts: Vec<SoakArtifactManifest>,
}

/// Report bundle validation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakReportBundleValidation {
    /// True when no issues were found.
    pub valid: bool,
    /// Issues.
    pub issues: Vec<String>,
}

/// Report bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakReportBundle {
    /// Bundle id.
    pub bundle_id: String,
    /// Bundle version.
    pub bundle_version: String,
    /// Config.
    pub config: SoakRunConfig,
    /// Shard plan.
    pub shard_plan: SoakShardPlan,
    /// Shard manifests.
    pub shard_manifests: Vec<SoakShardManifest>,
    /// Telemetry reports.
    #[serde(default)]
    pub telemetry_reports: Vec<SoakTelemetryReport>,
    /// Health reports.
    #[serde(default)]
    pub health_reports: Vec<SoakHealthReport>,
    /// Failure corpus indexes.
    #[serde(default)]
    pub failure_corpus_indexes: Vec<FailureCorpusIndex>,
    /// Artifact digest set.
    pub artifact_digest_set: SoakArtifactDigestSet,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Validate a report bundle.
pub fn validate_soak_report_bundle(bundle: &SoakReportBundle) -> SoakReportBundleValidation {
    let mut issues = Vec::new();
    if bundle.bundle_id.trim().is_empty() {
        issues.push("report bundle id is empty".to_string());
    }
    if bundle.bundle_version.trim().is_empty() {
        issues.push("report bundle version is empty".to_string());
    }
    if bundle.claim_boundary != ClaimBoundary::Level0DesignNote {
        issues.push("report bundle must remain Level0DesignNote".to_string());
    }
    if let Err(error) = validate_soak_run_config(&bundle.config) {
        issues.push(format!("config invalid: {error}"));
    }
    if bundle.config != bundle.shard_plan.config {
        issues.push("bundle config does not match shard_plan.config".to_string());
    }
    if bundle.shard_plan.claim_boundary != ClaimBoundary::Level0DesignNote {
        issues.push("shard plan must remain Level0DesignNote".to_string());
    }
    if let Err(error) = validate_soak_shard_plan(&bundle.shard_plan) {
        issues.push(format!("shard_plan invalid: {error}"));
    }
    let shard_count = bundle.shard_manifests.len();
    push_bundle_count_issue(
        "shard_plan.shard_manifests",
        bundle.shard_plan.shard_manifests.len(),
        shard_count,
        &mut issues,
    );
    push_bundle_count_issue(
        "telemetry_reports",
        bundle.telemetry_reports.len(),
        shard_count,
        &mut issues,
    );
    push_bundle_count_issue(
        "health_reports",
        bundle.health_reports.len(),
        shard_count,
        &mut issues,
    );
    push_bundle_count_issue(
        "failure_corpus_indexes",
        bundle.failure_corpus_indexes.len(),
        shard_count,
        &mut issues,
    );
    push_bundle_count_issue(
        "artifact_digest_set.telemetry",
        count_artifacts_with_role(bundle, SoakArtifactRole::Telemetry),
        bundle.telemetry_reports.len(),
        &mut issues,
    );
    push_bundle_count_issue(
        "artifact_digest_set.health_reports",
        count_artifacts_with_role(bundle, SoakArtifactRole::HealthReport),
        bundle.health_reports.len(),
        &mut issues,
    );
    push_bundle_count_issue(
        "artifact_digest_set.failure_corpus_indexes",
        count_artifacts_with_role(bundle, SoakArtifactRole::FailureCorpusIndex),
        bundle.failure_corpus_indexes.len(),
        &mut issues,
    );
    for (index, manifest) in bundle.shard_manifests.iter().enumerate() {
        let validation = validate_soak_shard_manifest(manifest);
        if !validation.valid {
            issues.push(format!(
                "shard_manifests[{index}] invalid: {:?}",
                validation.issues
            ));
        }
        if let Some(planned_manifest) = bundle.shard_plan.shard_manifests.get(index) {
            if manifest != planned_manifest {
                issues.push(format!(
                    "shard_manifests[{index}] does not match shard_plan.shard_manifests[{index}]"
                ));
            }
        }
    }
    for (index, report) in bundle.telemetry_reports.iter().enumerate() {
        if let Err(error) = validate_soak_telemetry_report(report) {
            issues.push(format!("telemetry_reports[{index}] invalid: {error}"));
        }
        if let (Some(report_shard_id), Some(manifest)) =
            (&report.shard_id, bundle.shard_manifests.get(index))
        {
            if report_shard_id != &manifest.shard_id {
                issues.push(format!(
                    "telemetry_reports[{index}].shard_id does not match shard_manifests[{index}].shard_id"
                ));
            }
        }
    }
    for (index, report) in bundle.health_reports.iter().enumerate() {
        if let Err(error) = validate_soak_health_report(report) {
            issues.push(format!("health_reports[{index}] invalid: {error}"));
        }
        if let (Some(report_shard_id), Some(manifest)) =
            (&report.shard_id, bundle.shard_manifests.get(index))
        {
            if report_shard_id != &manifest.shard_id {
                issues.push(format!(
                    "health_reports[{index}].shard_id does not match shard_manifests[{index}].shard_id"
                ));
            }
        }
    }
    for (index, failure_corpus) in bundle.failure_corpus_indexes.iter().enumerate() {
        if let Err(error) = validate_failure_corpus_index(failure_corpus) {
            issues.push(format!("failure_corpus_indexes[{index}] invalid: {error}"));
        }
        if let Some(manifest) = bundle.shard_manifests.get(index) {
            for (entry_index, entry) in failure_corpus.entries.iter().enumerate() {
                if entry.reproduction_manifest.shard_id != manifest.shard_id {
                    issues.push(format!(
                        "failure_corpus_indexes[{index}].entries[{entry_index}].reproduction_manifest.shard_id does not match shard_manifests[{index}].shard_id"
                    ));
                }
            }
        }
    }
    let mut artifact_ids = BTreeSet::new();
    let mut artifact_paths = BTreeSet::new();
    for artifact in &bundle.artifact_digest_set.artifacts {
        if !artifact_id_is_portable(&artifact.artifact_id) {
            issues.push(format!(
                "artifact id is not portable: {}",
                artifact.artifact_id
            ));
        }
        if !artifact_ids.insert(artifact.artifact_id.clone()) {
            issues.push(format!("duplicate artifact id: {}", artifact.artifact_id));
        }
        if !artifact_paths.insert(artifact.relative_path.clone()) {
            issues.push(format!(
                "duplicate artifact path: {}",
                artifact.relative_path
            ));
        }
        if artifact.digest.is_none() {
            issues.push(format!(
                "artifact {} is missing digest",
                artifact.artifact_id
            ));
        }
        if !relative_path_is_portable(&artifact.relative_path) {
            issues.push(format!(
                "artifact path is not portable relative: {}",
                artifact.relative_path
            ));
        }
        if artifact.claim_boundary != ClaimBoundary::Level0DesignNote {
            issues.push(format!(
                "artifact {} exceeded Level0DesignNote",
                artifact.artifact_id
            ));
        }
    }
    SoakReportBundleValidation {
        valid: issues.is_empty(),
        issues,
    }
}

fn push_bundle_count_issue(
    path: &'static str,
    actual: usize,
    expected: usize,
    issues: &mut Vec<String>,
) {
    if actual != expected {
        issues.push(format!(
            "{path} count {actual} does not match shard manifest count {expected}"
        ));
    }
}

fn count_artifacts_with_role(bundle: &SoakReportBundle, role: SoakArtifactRole) -> usize {
    bundle
        .artifact_digest_set
        .artifacts
        .iter()
        .filter(|artifact| artifact.role == role)
        .count()
}

/// Write a report bundle to a local directory.
pub fn write_soak_report_bundle(root: impl AsRef<Path>, bundle: &SoakReportBundle) -> Result<()> {
    let root = root.as_ref();
    if root.exists() && !root.is_dir() {
        return Err(ZkBenchError::soak(
            root.display().to_string(),
            "report bundle root exists and is not a directory",
        ));
    }
    if root.exists() && directory_has_entries(root)? {
        return Err(ZkBenchError::soak(
            root.display().to_string(),
            "report bundle root is non-empty",
        ));
    }
    let validation = validate_soak_report_bundle(bundle);
    if !validation.valid {
        return Err(ZkBenchError::soak(
            "soak.report_bundle",
            format!("invalid bundle: {:?}", validation.issues),
        ));
    }
    fs::create_dir_all(root)
        .map_err(|error| ZkBenchError::soak(root.display().to_string(), error.to_string()))?;
    write_json(root.join("soak_report_bundle.json"), bundle)
}

/// Read a report bundle from a local directory.
pub fn read_soak_report_bundle(root: impl AsRef<Path>) -> Result<SoakReportBundle> {
    let path = root.as_ref().join("soak_report_bundle.json");
    let bytes = fs::read(&path)
        .map_err(|error| ZkBenchError::soak(path.display().to_string(), error.to_string()))?;
    serde_json::from_slice(&bytes).map_err(|error| {
        ZkBenchError::deserialization("read_soak_report_bundle", error.to_string())
    })
}

/// Build an artifact manifest with a deterministic digest.
pub fn soak_artifact_manifest<T: Serialize>(
    artifact_id: impl Into<String>,
    role: SoakArtifactRole,
    relative_path: impl Into<String>,
    value: &T,
) -> Result<SoakArtifactManifest> {
    let artifact_id = artifact_id.into();
    if !artifact_id_is_portable(&artifact_id) {
        return Err(ZkBenchError::soak(
            "soak.artifact.artifact_id",
            "soak artifact ids must be non-empty portable identifiers",
        ));
    }
    let relative_path = relative_path.into();
    if !relative_path_is_portable(&relative_path) {
        return Err(ZkBenchError::soak(
            "soak.artifact.relative_path",
            "soak artifact paths must be portable and relative",
        ));
    }
    Ok(SoakArtifactManifest {
        artifact_id,
        role,
        relative_path,
        digest: Some(compute_artifact_digest(
            value,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec!["Soak artifact manifest is local-only.".to_string()],
    })
}

fn artifact_id_is_portable(artifact_id: &str) -> bool {
    !artifact_id.trim().is_empty()
        && !artifact_id.contains('/')
        && !artifact_id.contains('\\')
        && !artifact_id.contains("..")
}

pub(crate) fn relative_path_is_portable(path: &str) -> bool {
    !path.trim().is_empty()
        && !path.starts_with('/')
        && !path.contains("..")
        && !path.contains('\\')
}

pub(crate) fn write_json<T: Serialize>(path: impl AsRef<Path>, value: &T) -> Result<()> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| ZkBenchError::soak(parent.display().to_string(), error.to_string()))?;
    }
    let bytes = serde_json::to_vec_pretty(value)
        .map_err(|error| ZkBenchError::serialization("soak.write_json", error.to_string()))?;
    fs::write(path, bytes)
        .map_err(|error| ZkBenchError::soak(path.display().to_string(), error.to_string()))
}

fn directory_has_entries(path: &Path) -> Result<bool> {
    let mut entries = fs::read_dir(path)
        .map_err(|error| ZkBenchError::soak(path.display().to_string(), error.to_string()))?;
    entries
        .next()
        .transpose()
        .map(|entry| entry.is_some())
        .map_err(|error| ZkBenchError::soak(path.display().to_string(), error.to_string()))
}

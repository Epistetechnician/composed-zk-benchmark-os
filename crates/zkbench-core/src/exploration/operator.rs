//! Provider-free operator workflow for the deterministic exploration campaign.
//!
//! This module is the named state slice
//! `antithesis-inspired-deterministic-exploration-v1-operator-workflow`.
//! It retains only typed local artifacts and makes assessment finalization a
//! one-way explicit operation. It has no network, provider, process, model,
//! evidence-ledger, or claim-escalation surface.

use std::collections::BTreeMap;
use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{compute_artifact_digest_bytes, ClaimBoundary, ResultClassification};
use crate::soak::{
    serialize_failure_corpus_index_json, validate_failure_corpus_index, FailureCorpus,
    FailureCorpusEntry, FailureCorpusIndex,
};

use super::{
    deserialize_baseline_campaign_result_json, is_reproducible_failure_classification,
    reduce_local_replay_failure, serialize_baseline_campaign_result_json, BaselineCampaignConfig,
    BaselineCampaignResult, BaselineCampaignRunner, BaselineComparisonReport, BaselinePolicyKind,
    ExplorationPhase, FailureReductionResult, LocalTargetRun, EXPLORATION_CLAIM_BOUNDARY,
};

/// Operator workflow state slice.
pub const EXPLORATION_OPERATOR_STATE_SLICE: &str =
    "antithesis-inspired-deterministic-exploration-v1-operator-workflow";

/// Operator artifact schema version.
pub const EXPLORATION_OPERATOR_SCHEMA_VERSION: &str = "antithesis-inspired-exploration-operator-v1";

/// Retained campaign configuration.
pub const OPERATOR_CONFIG_PATH: &str = "campaign-config.json";
/// Validation result path.
pub const OPERATOR_VALIDATION_PATH: &str = "validation.json";
/// Finalized result path.
pub const OPERATOR_FINALIZED_PATH: &str = "finalized.json";
/// Canonical report JSON path.
pub const OPERATOR_REPORT_JSON_PATH: &str = "report.json";
/// Canonical report Markdown path.
pub const OPERATOR_REPORT_MARKDOWN_PATH: &str = "report.md";
/// Failure corpus path.
pub const OPERATOR_FAILURE_CORPUS_PATH: &str = "failure-corpus.json";
/// Operator manifest path.
pub const OPERATOR_MANIFEST_PATH: &str = "operator-manifest.json";
/// Minimized replay export directory.
pub const OPERATOR_MINIMIZED_DIR: &str = "minimized";

/// Canonical operator report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationOperatorReport {
    /// Schema version.
    pub schema_version: String,
    /// Campaign id.
    pub campaign_id: String,
    /// Report phase.
    pub phase: ExplorationPhase,
    /// Whether assessment has been finalized.
    pub finalized: bool,
    /// Frozen primary metric id.
    pub metric_id: String,
    /// Validation-selected policy.
    pub validation_winner: BaselinePolicyKind,
    /// Comparison rows.
    pub rows: Vec<super::BaselineComparisonRow>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaims.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ExplorationOperatorReport {
    /// Build a report without exposing assessment data before finalization.
    pub fn from_result(result: &BaselineCampaignResult) -> Result<Self> {
        let comparison = active_comparison(result)?;
        if result.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
            || comparison.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
        {
            return Err(ZkBenchError::validation(
                "exploration.operator.report.claim_boundary",
                "operator reports must remain Level0DesignNote",
            ));
        }
        Ok(Self {
            schema_version: EXPLORATION_OPERATOR_SCHEMA_VERSION.to_string(),
            campaign_id: result.campaign_id.clone(),
            phase: comparison.phase,
            finalized: result.finalized,
            metric_id: comparison.metric_id.clone(),
            validation_winner: result.validation_winner,
            rows: comparison.rows.clone(),
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "This report is local strategy-development metadata only.".to_string(),
                "Assessment rows exist only after explicit one-way finalization.".to_string(),
                "No evidence ledger or benchmark claim is produced.".to_string(),
            ],
        })
    }

    /// Render a deterministic Markdown report.
    pub fn render_markdown(&self) -> String {
        let mut output = String::new();
        output.push_str("# Deterministic exploration campaign report\n\n");
        output.push_str(&format!("- campaign: `{}`\n", self.campaign_id));
        output.push_str(&format!("- phase: `{:?}`\n", self.phase));
        output.push_str(&format!("- finalized: `{}`\n", self.finalized));
        output.push_str(&format!("- metric: `{}`\n", self.metric_id));
        output.push_str(&format!(
            "- validation winner: `{:?}`\n",
            self.validation_winner
        ));
        output.push_str(&format!(
            "- claim boundary: `{:?}`\n\n",
            self.claim_boundary
        ));
        output.push_str("| policy | failures | cases | shards | mutation attempts |\n");
        output.push_str("| --- | ---: | ---: | ---: | ---: |\n");
        for row in &self.rows {
            output.push_str(&format!(
                "| `{:?}` | {} | {} | {} | {} |\n",
                row.kind,
                row.distinct_failure_classification_count,
                row.work_units.case_count,
                row.work_units.shard_count,
                row.work_units.mutation_attempt_count,
            ));
        }
        output.push_str("\nNonclaims:\n\n");
        for note in &self.notes {
            output.push_str(&format!("- {note}\n"));
        }
        output
    }
}

/// One retained operator artifact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationOperatorArtifactRecord {
    /// Portable relative path.
    pub relative_path: String,
    /// Byte length.
    pub byte_len: usize,
    /// SHA-256 digest of exact retained bytes.
    pub sha256: String,
}

/// Retained operator artifact manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationOperatorManifest {
    /// Schema version.
    pub schema_version: String,
    /// Campaign id.
    pub campaign_id: String,
    /// Campaign config digest.
    pub config_digest: String,
    /// Whether assessment is finalized.
    pub finalized: bool,
    /// Exact retained artifacts.
    pub artifacts: Vec<ExplorationOperatorArtifactRecord>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaims.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Export of a minimized local replay failure.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MinimizedReplayExport {
    /// Source failure corpus entry.
    pub failure_entry: FailureCorpusEntry,
    /// Original replay manifest.
    pub replay_manifest: crate::replay::ReplayManifest,
    /// Original replay result.
    pub replay_result: crate::replay::ReplayResult,
    /// Deterministic reduction.
    pub reduction: FailureReductionResult,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Local operator artifact store.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExplorationOperatorStore {
    root: PathBuf,
}

impl ExplorationOperatorStore {
    /// Create or open a bounded local artifact root.
    pub fn new(root: impl Into<PathBuf>) -> Result<Self> {
        let root = root.into();
        validate_operator_root(&root)?;
        if root.exists() {
            let metadata = fs::symlink_metadata(&root)
                .map_err(|error| operator_io_error("exploration.operator.root.metadata", error))?;
            if !metadata.is_dir() || metadata.file_type().is_symlink() {
                return Err(ZkBenchError::validation(
                    "exploration.operator.root",
                    "operator artifact root must be a non-symlink directory",
                ));
            }
        } else {
            fs::create_dir_all(&root)
                .map_err(|error| operator_io_error("exploration.operator.root.create", error))?;
        }
        Ok(Self { root })
    }

    /// Return the artifact root.
    pub fn root(&self) -> &Path {
        &self.root
    }

    /// Read and validate the retained campaign configuration.
    pub fn read_config(&self) -> Result<BaselineCampaignConfig> {
        let json = self.read(OPERATOR_CONFIG_PATH)?;
        let config: BaselineCampaignConfig = serde_json::from_str(&json).map_err(|error| {
            ZkBenchError::deserialization(
                "exploration.operator.config.deserialize",
                error.to_string(),
            )
        })?;
        BaselineCampaignRunner::new(config.clone())?;
        Ok(config)
    }

    /// Run and retain validation artifacts.
    pub fn run_validation(
        &self,
        config: &BaselineCampaignConfig,
    ) -> Result<BaselineCampaignResult> {
        let runner = BaselineCampaignRunner::new(config.clone())?;
        if self.path(OPERATOR_VALIDATION_PATH).exists()
            || self.path(OPERATOR_FINALIZED_PATH).exists()
        {
            return Err(ZkBenchError::validation(
                "exploration.operator.run",
                "campaign artifacts already exist; use resume or finalize",
            ));
        }
        self.write_config(config)?;
        let result = runner.run_validation()?;
        self.write_immutable(
            OPERATOR_VALIDATION_PATH,
            &serialize_baseline_campaign_result_json(&result)?,
        )?;
        self.refresh_derived_artifacts(&result)?;
        Ok(result)
    }

    /// Resume validation from the retained checkpoint.
    pub fn resume_validation(
        &self,
        config: &BaselineCampaignConfig,
    ) -> Result<BaselineCampaignResult> {
        let runner = BaselineCampaignRunner::new(config.clone())?;
        let retained = self.read_result(OPERATOR_VALIDATION_PATH, config)?;
        if retained.finalized {
            return Err(ZkBenchError::validation(
                "exploration.operator.resume",
                "finalized campaigns cannot resume validation",
            ));
        }
        let result = runner.resume_validation(retained.checkpoint.clone())?;
        let json = serialize_baseline_campaign_result_json(&result)?;
        self.write_immutable(OPERATOR_VALIDATION_PATH, &json)?;
        self.refresh_derived_artifacts(&result)?;
        Ok(result)
    }

    /// Finalize assessment exactly once and retain the sealed result.
    pub fn finalize_assessment(
        &self,
        config: &BaselineCampaignConfig,
    ) -> Result<BaselineCampaignResult> {
        let runner = BaselineCampaignRunner::new(config.clone())?;
        if self.path(OPERATOR_FINALIZED_PATH).exists() {
            return Err(ZkBenchError::validation(
                "exploration.operator.finalize",
                "assessment has already been finalized",
            ));
        }
        let validation = self.read_result(OPERATOR_VALIDATION_PATH, config)?;
        let mut result = validation;
        runner.finalize_assessment(&mut result)?;
        self.write_immutable(
            OPERATOR_FINALIZED_PATH,
            &serialize_baseline_campaign_result_json(&result)?,
        )?;
        self.refresh_derived_artifacts(&result)?;
        Ok(result)
    }

    /// Read the finalized result when present, otherwise validation.
    pub fn read_active_result(
        &self,
        config: &BaselineCampaignConfig,
    ) -> Result<BaselineCampaignResult> {
        if self.path(OPERATOR_FINALIZED_PATH).exists() {
            self.read_result(OPERATOR_FINALIZED_PATH, config)
        } else {
            self.read_result(OPERATOR_VALIDATION_PATH, config)
        }
    }

    /// Build and retain the active failure corpus.
    pub fn failure_corpus(&self, config: &BaselineCampaignConfig) -> Result<FailureCorpusIndex> {
        let result = self.read_active_result(config)?;
        let corpus = collect_baseline_failure_corpus(&result)?;
        let json = serialize_failure_corpus_index_json(&corpus)?;
        self.write_replace(OPERATOR_FAILURE_CORPUS_PATH, &json)?;
        self.refresh_manifest(&result)?;
        Ok(corpus)
    }

    /// Export a deterministically minimized replay for one corpus entry.
    pub fn export_minimized_replay(
        &self,
        config: &BaselineCampaignConfig,
        entry_id: &str,
    ) -> Result<MinimizedReplayExport> {
        validate_entry_id(entry_id)?;
        let result = self.read_active_result(config)?;
        let corpus = collect_baseline_failure_corpus(&result)?;
        let entry = corpus
            .entries
            .iter()
            .find(|entry| entry.entry_id == entry_id)
            .cloned()
            .ok_or_else(|| {
                ZkBenchError::validation(
                    "exploration.operator.minimized.entry_id",
                    "failure corpus entry was not found",
                )
            })?;
        let (manifest, replay_result, classification) = find_replay_for_failure(&result, &entry)?;
        let reduction = reduce_local_replay_failure(manifest, replay_result, classification)?;
        let export = MinimizedReplayExport {
            failure_entry: entry,
            replay_manifest: manifest.clone(),
            replay_result: replay_result.clone(),
            reduction,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        };
        let json = serde_json::to_string_pretty(&export).map_err(|error| {
            ZkBenchError::serialization(
                "exploration.operator.minimized.serialize",
                error.to_string(),
            )
        })?;
        let relative_path = format!("{OPERATOR_MINIMIZED_DIR}/{entry_id}.json");
        self.write_replace(&relative_path, &json)?;
        self.refresh_manifest(&result)?;
        Ok(export)
    }

    fn write_config(&self, config: &BaselineCampaignConfig) -> Result<()> {
        let json = serde_json::to_string_pretty(config).map_err(|error| {
            ZkBenchError::serialization("exploration.operator.config.serialize", error.to_string())
        })?;
        self.write_immutable(OPERATOR_CONFIG_PATH, &json)
    }

    fn read_result(
        &self,
        relative_path: &str,
        config: &BaselineCampaignConfig,
    ) -> Result<BaselineCampaignResult> {
        let json = self.read(relative_path)?;
        deserialize_baseline_campaign_result_json(&json, config)
    }

    fn path(&self, relative_path: &str) -> PathBuf {
        self.root.join(relative_path)
    }

    fn read(&self, relative_path: &str) -> Result<String> {
        validate_relative_operator_path(relative_path)?;
        let path = self.path(relative_path);
        reject_symlink(&path, "exploration.operator.read")?;
        fs::read_to_string(path).map_err(|error| {
            operator_io_error(format!("exploration.operator.read.{relative_path}"), error)
        })
    }

    fn write_immutable(&self, relative_path: &str, content: &str) -> Result<()> {
        let path = self.path(relative_path);
        if path.exists() {
            let existing = self.read(relative_path)?;
            if existing != content {
                return Err(ZkBenchError::validation(
                    format!("exploration.operator.immutable.{relative_path}"),
                    "retained artifact differs from deterministic rerun",
                ));
            }
            return Ok(());
        }
        self.write_replace(relative_path, content)
    }

    fn write_replace(&self, relative_path: &str, content: &str) -> Result<()> {
        validate_relative_operator_path(relative_path)?;
        let path = self.path(relative_path);
        if relative_path.starts_with(&format!("{OPERATOR_MINIMIZED_DIR}/")) {
            self.ensure_minimized_directory()?;
        }
        reject_symlink(&path, "exploration.operator.write")?;
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .map_err(|error| operator_io_error("exploration.operator.write.parent", error))?;
        }
        fs::write(&path, content.as_bytes()).map_err(|error| {
            operator_io_error(format!("exploration.operator.write.{relative_path}"), error)
        })
    }

    fn refresh_derived_artifacts(&self, result: &BaselineCampaignResult) -> Result<()> {
        let report = ExplorationOperatorReport::from_result(result)?;
        let report_json = serde_json::to_string_pretty(&report).map_err(|error| {
            ZkBenchError::serialization("exploration.operator.report.serialize", error.to_string())
        })?;
        self.write_replace(OPERATOR_REPORT_JSON_PATH, &report_json)?;
        self.write_replace(OPERATOR_REPORT_MARKDOWN_PATH, &report.render_markdown())?;
        let corpus = collect_baseline_failure_corpus(result)?;
        self.write_replace(
            OPERATOR_FAILURE_CORPUS_PATH,
            &serialize_failure_corpus_index_json(&corpus)?,
        )?;
        self.refresh_manifest(result)
    }

    fn refresh_manifest(&self, result: &BaselineCampaignResult) -> Result<()> {
        let mut relative_paths = vec![
            OPERATOR_CONFIG_PATH.to_string(),
            OPERATOR_VALIDATION_PATH.to_string(),
            OPERATOR_REPORT_JSON_PATH.to_string(),
            OPERATOR_REPORT_MARKDOWN_PATH.to_string(),
            OPERATOR_FAILURE_CORPUS_PATH.to_string(),
        ];
        if result.finalized {
            relative_paths.push(OPERATOR_FINALIZED_PATH.to_string());
        }
        let minimized_dir = self.path(OPERATOR_MINIMIZED_DIR);
        if minimized_dir.exists() {
            let metadata = fs::symlink_metadata(&minimized_dir).map_err(|error| {
                operator_io_error("exploration.operator.manifest.minimized.metadata", error)
            })?;
            if !metadata.is_dir() || metadata.file_type().is_symlink() {
                return Err(ZkBenchError::validation(
                    "exploration.operator.manifest.minimized",
                    "minimized artifact directory must be a non-symlink directory",
                ));
            }
            let entries = fs::read_dir(&minimized_dir).map_err(|error| {
                operator_io_error("exploration.operator.manifest.minimized", error)
            })?;
            for entry in entries {
                let entry = entry.map_err(|error| {
                    operator_io_error("exploration.operator.manifest.entry", error)
                })?;
                let path = entry.path();
                let metadata = fs::symlink_metadata(&path).map_err(|error| {
                    operator_io_error("exploration.operator.manifest.entry.metadata", error)
                })?;
                if !metadata.is_file() || metadata.file_type().is_symlink() {
                    return Err(ZkBenchError::validation(
                        "exploration.operator.manifest.minimized",
                        "minimized artifact directory contains a non-regular file",
                    ));
                }
                let name = path
                    .file_name()
                    .and_then(|name| name.to_str())
                    .ok_or_else(|| {
                        ZkBenchError::validation(
                            "exploration.operator.manifest.minimized",
                            "minimized artifact name is not valid UTF-8",
                        )
                    })?;
                validate_entry_id(name.strip_suffix(".json").unwrap_or(name))?;
                relative_paths.push(format!("{OPERATOR_MINIMIZED_DIR}/{name}"));
            }
        }
        relative_paths.sort();
        let mut artifacts = Vec::new();
        for relative_path in relative_paths {
            let bytes = fs::read(self.path(&relative_path)).map_err(|error| {
                operator_io_error(
                    format!("exploration.operator.manifest.read.{relative_path}"),
                    error,
                )
            })?;
            let digest = compute_artifact_digest_bytes(&bytes, None, None);
            artifacts.push(ExplorationOperatorArtifactRecord {
                relative_path,
                byte_len: bytes.len(),
                sha256: digest.hex_digest,
            });
        }
        let manifest = ExplorationOperatorManifest {
            schema_version: EXPLORATION_OPERATOR_SCHEMA_VERSION.to_string(),
            campaign_id: result.campaign_id.clone(),
            config_digest: result.config_digest.clone(),
            finalized: result.finalized,
            artifacts,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Manifest records local deterministic artifacts only.".to_string(),
                "The manifest itself is excluded from its artifact list.".to_string(),
            ],
        };
        let json = serde_json::to_string_pretty(&manifest).map_err(|error| {
            ZkBenchError::serialization(
                "exploration.operator.manifest.serialize",
                error.to_string(),
            )
        })?;
        self.write_replace(OPERATOR_MANIFEST_PATH, &json)
    }
}

/// Collect and de-duplicate corpus entries across policy replays.
pub fn collect_baseline_failure_corpus(
    result: &BaselineCampaignResult,
) -> Result<FailureCorpusIndex> {
    let mut entries = BTreeMap::new();
    for record in &result.records {
        collect_run_entries(&record.validation_run, &mut entries)?;
        if let Some(assessment) = &record.assessment_run {
            collect_run_entries(assessment, &mut entries)?;
        }
    }
    let mut corpus = FailureCorpus::empty(format!("{}_failure_corpus", result.campaign_id));
    for (_, entry) in entries {
        corpus.push(entry);
    }
    validate_failure_corpus_index(&corpus.index)?;
    Ok(corpus.index)
}

fn collect_run_entries(
    run: &LocalTargetRun,
    entries: &mut BTreeMap<String, FailureCorpusEntry>,
) -> Result<()> {
    for case in &run.case_observations {
        for entry in &case.failure_corpus_entries {
            if let Some(existing) = entries.get(&entry.entry_id) {
                if existing != entry {
                    return Err(ZkBenchError::validation(
                        "exploration.operator.failure_corpus",
                        "same failure entry id has conflicting retained records",
                    ));
                }
            } else {
                entries.insert(entry.entry_id.clone(), entry.clone());
            }
        }
    }
    Ok(())
}

fn active_comparison(result: &BaselineCampaignResult) -> Result<&BaselineComparisonReport> {
    if result.finalized {
        result.assessment_comparison.as_ref().ok_or_else(|| {
            ZkBenchError::validation(
                "exploration.operator.report.assessment",
                "finalized result is missing assessment comparison",
            )
        })
    } else {
        Ok(&result.validation_comparison)
    }
}

fn find_replay_for_failure<'a>(
    result: &'a BaselineCampaignResult,
    entry: &FailureCorpusEntry,
) -> Result<(
    &'a crate::replay::ReplayManifest,
    &'a crate::replay::ReplayResult,
    ResultClassification,
)> {
    let mut runs = Vec::new();
    for record in &result.records {
        runs.push(&record.validation_run);
        if let Some(assessment) = &record.assessment_run {
            runs.push(assessment);
        }
    }
    for run in runs {
        for case in &run.case_observations {
            if case.case_id != entry.source_soak_case_id {
                continue;
            }
            for (manifest, replay_result) in case.replay_manifests.iter().zip(&case.replay_results)
            {
                let manifest_mutation_class = manifest
                    .mutation_provenance
                    .as_ref()
                    .map(|provenance| provenance.mutation_class);
                if manifest_mutation_class != entry.mutation_class {
                    continue;
                }
                let trace = if let Some(trace_id) = &entry.trace_id {
                    replay_result.trace_results.iter().find(|trace| {
                        &trace.trace_id == trace_id
                            && is_reproducible_failure_classification(trace.result_classification)
                    })
                } else {
                    replay_result.trace_results.iter().find(|trace| {
                        is_reproducible_failure_classification(trace.result_classification)
                    })
                };
                if let Some(trace) = trace.filter(|trace| {
                    is_reproducible_failure_classification(trace.result_classification)
                }) {
                    let classification = trace.result_classification;
                    return Ok((manifest, replay_result, classification));
                }
            }
        }
    }
    Err(ZkBenchError::validation(
        "exploration.operator.minimized.replay",
        "failure entry has no retained reproducible local replay classification",
    ))
}

pub(super) fn validate_operator_root(root: &Path) -> Result<()> {
    if root.as_os_str().is_empty()
        || root
            .components()
            .any(|component| component == Component::ParentDir)
    {
        return Err(ZkBenchError::validation(
            "exploration.operator.root",
            "operator artifact root must be non-empty and free of parent traversal",
        ));
    }
    if root == Path::new("/") || root == Path::new(".") {
        return Err(ZkBenchError::validation(
            "exploration.operator.root",
            "operator artifact root is too broad",
        ));
    }
    Ok(())
}

pub(super) fn validate_relative_operator_path(relative_path: &str) -> Result<()> {
    let path = Path::new(relative_path);
    if relative_path.trim().is_empty()
        || path.is_absolute()
        || path.components().any(|component| {
            matches!(
                component,
                Component::ParentDir | Component::RootDir | Component::Prefix(_)
            )
        })
        || relative_path.contains('\\')
    {
        return Err(ZkBenchError::validation(
            "exploration.operator.relative_path",
            "operator artifact paths must be portable relative paths",
        ));
    }
    Ok(())
}

fn validate_entry_id(entry_id: &str) -> Result<()> {
    if entry_id.trim().is_empty()
        || entry_id.contains('/')
        || entry_id.contains('\\')
        || entry_id.contains("..")
    {
        return Err(ZkBenchError::validation(
            "exploration.operator.entry_id",
            "failure entry ids must be safe portable names",
        ));
    }
    Ok(())
}

impl ExplorationOperatorStore {
    fn ensure_minimized_directory(&self) -> Result<()> {
        let path = self.path(OPERATOR_MINIMIZED_DIR);
        if path.exists() {
            let metadata = fs::symlink_metadata(&path).map_err(|error| {
                operator_io_error("exploration.operator.minimized.metadata", error)
            })?;
            if !metadata.is_dir() || metadata.file_type().is_symlink() {
                return Err(ZkBenchError::validation(
                    "exploration.operator.minimized",
                    "minimized artifact directory must be a non-symlink directory",
                ));
            }
        } else {
            fs::create_dir_all(&path).map_err(|error| {
                operator_io_error("exploration.operator.minimized.create", error)
            })?;
        }
        Ok(())
    }
}

pub(super) fn reject_symlink(path: &Path, error_path: &str) -> Result<()> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(error) => return Err(operator_io_error(format!("{error_path}.metadata"), error)),
    };
    if metadata.file_type().is_symlink() {
        return Err(ZkBenchError::validation(
            error_path,
            "operator artifacts must not be symlinks",
        ));
    }
    Ok(())
}

pub(super) fn operator_io_error(path: impl Into<String>, error: std::io::Error) -> ZkBenchError {
    ZkBenchError::validation(
        path,
        format!("local operator filesystem operation failed: {error}"),
    )
}

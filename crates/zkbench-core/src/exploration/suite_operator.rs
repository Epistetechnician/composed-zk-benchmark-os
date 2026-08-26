//! Persistent operator workflow for independent assessment suites.
//!
//! This module is the named state slice
//! `antithesis-inspired-deterministic-exploration-v1-independent-assessment-suite-operator`.
//! It stores only local deterministic suite configuration, validation results,
//! explicitly finalized assessment results, and derived reports. Assessment
//! case identities are absent from the retained validation artifact until the
//! one-way finalization operation.

use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{compute_artifact_digest_bytes, ClaimBoundary};

use super::operator::{
    operator_io_error, reject_symlink, validate_operator_root, validate_relative_operator_path,
};
use super::{
    deserialize_independent_campaign_suite_json, serialize_independent_campaign_suite_json,
    BaselinePolicyKind, ExplorationPhase, IndependentCampaignComparisonReport,
    IndependentCampaignSuiteConfig, IndependentCampaignSuiteResult, IndependentCampaignSuiteRunner,
    IndependentPolicyAggregateRow, EXPLORATION_CLAIM_BOUNDARY,
};

/// Persistent suite operator state slice.
pub const SUITE_OPERATOR_STATE_SLICE: &str =
    "antithesis-inspired-deterministic-exploration-v1-independent-assessment-suite-operator";

/// Persistent suite operator schema version.
pub const SUITE_OPERATOR_SCHEMA_VERSION: &str =
    "antithesis-inspired-independent-assessment-suite-operator-v1";

/// Named derived scorecard state slice.
pub const SUITE_SCORECARD_STATE_SLICE: &str =
    "antithesis-inspired-deterministic-exploration-v1-independent-assessment-scorecard";

/// Version of the validation-to-assessment scorecard schema.
pub const SUITE_SCORECARD_SCHEMA_VERSION: &str =
    "antithesis-inspired-independent-assessment-scorecard-v1";

/// Retained suite configuration.
pub const SUITE_OPERATOR_CONFIG_PATH: &str = "suite-config.json";
/// Validation-only suite result.
pub const SUITE_OPERATOR_VALIDATION_PATH: &str = "suite-validation.json";
/// Finalized suite result.
pub const SUITE_OPERATOR_FINALIZED_PATH: &str = "suite-finalized.json";
/// Canonical suite report JSON.
pub const SUITE_OPERATOR_REPORT_JSON_PATH: &str = "suite-report.json";
/// Canonical suite report Markdown.
pub const SUITE_OPERATOR_REPORT_MARKDOWN_PATH: &str = "suite-report.md";
/// Suite artifact manifest.
pub const SUITE_OPERATOR_MANIFEST_PATH: &str = "suite-manifest.json";

/// Canonical report for the active suite phase.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IndependentSuiteOperatorReport {
    /// Schema version.
    pub schema_version: String,
    /// Suite identifier.
    pub suite_id: String,
    /// Active report phase.
    pub phase: ExplorationPhase,
    /// Whether assessment is finalized.
    pub finalized: bool,
    /// Frozen primary metric id.
    pub metric_id: String,
    /// Candidate policy.
    pub candidate_policy: BaselinePolicyKind,
    /// Number of independent campaigns.
    pub campaign_count: usize,
    /// Policy aggregate rows for the active phase only.
    pub rows: Vec<IndependentPolicyAggregateRow>,
    /// Validation policy rows retained in every report.
    pub validation_rows: Vec<IndependentPolicyAggregateRow>,
    /// Assessment policy rows, present only after finalization.
    #[serde(default)]
    pub assessment_rows: Option<Vec<IndependentPolicyAggregateRow>>,
    /// Validation-to-assessment deltas, present only after finalization.
    #[serde(default)]
    pub policy_deltas: Option<Vec<IndependentSuitePolicyDelta>>,
    /// Required strict assessment improvements, when finalized.
    #[serde(default)]
    pub required_assessment_improvements: Option<usize>,
    /// Observed strict assessment improvements, when finalized.
    #[serde(default)]
    pub observed_assessment_improvements: Option<usize>,
    /// Promotion result, when finalized.
    #[serde(default)]
    pub promoted: Option<bool>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaims.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Per-policy validation-to-assessment generalization delta.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IndependentSuitePolicyDelta {
    /// Policy kind.
    pub kind: BaselinePolicyKind,
    /// Policy digests in canonical campaign order.
    pub policy_digests: Vec<String>,
    /// Validation metric values by campaign.
    pub validation_metric_values: Vec<usize>,
    /// Sealed assessment metric values by campaign.
    pub assessment_metric_values: Vec<usize>,
    /// Assessment minus validation per campaign.
    pub assessment_minus_validation: Vec<i64>,
    /// Validation total metric value.
    pub validation_total_metric_value: usize,
    /// Assessment total metric value.
    pub assessment_total_metric_value: usize,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

impl IndependentSuiteOperatorReport {
    /// Build a report without exposing assessment rows before finalization.
    pub fn from_result(result: &IndependentCampaignSuiteResult) -> Result<Self> {
        let comparison = active_comparison(result)?;
        if result.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
            || comparison.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
        {
            return Err(ZkBenchError::validation(
                "exploration.suite_operator.report.claim_boundary",
                "suite operator reports must remain Level0DesignNote",
            ));
        }
        let gate = result.promotion_gate.as_ref();
        let (assessment_rows, policy_deltas) =
            if let Some(assessment) = &result.assessment_comparison {
                (
                    Some(assessment.rows.clone()),
                    Some(build_policy_deltas(
                        &result.validation_comparison.rows,
                        &assessment.rows,
                    )?),
                )
            } else {
                (None, None)
            };
        Ok(Self {
            schema_version: SUITE_SCORECARD_SCHEMA_VERSION.to_string(),
            suite_id: result.suite_id.clone(),
            phase: comparison.phase,
            finalized: result.finalized,
            metric_id: comparison.metric_id.clone(),
            candidate_policy: comparison.candidate_policy,
            campaign_count: comparison.campaign_count,
            rows: comparison.rows.clone(),
            validation_rows: result.validation_comparison.rows.clone(),
            assessment_rows,
            policy_deltas,
            required_assessment_improvements: gate
                .map(|gate| gate.required_assessment_improvements),
            observed_assessment_improvements: gate
                .map(|gate| gate.observed_assessment_improvements),
            promoted: gate.map(|gate| gate.promoted),
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "This report is local strategy-development metadata only.".to_string(),
                "Assessment rows exist only after explicit one-way finalization.".to_string(),
                "No evidence ledger, accepted benchmark evidence, or external runner is produced."
                    .to_string(),
            ],
        })
    }

    /// Render a deterministic Markdown report.
    pub fn render_markdown(&self) -> String {
        let mut output = String::new();
        output.push_str("# Deterministic independent assessment suite report\n\n");
        output.push_str(&format!("- suite: `{}`\n", self.suite_id));
        output.push_str(&format!("- phase: `{:?}`\n", self.phase));
        output.push_str(&format!("- finalized: `{}`\n", self.finalized));
        output.push_str(&format!("- metric: `{}`\n", self.metric_id));
        output.push_str(&format!("- candidate: `{:?}`\n", self.candidate_policy));
        output.push_str(&format!("- campaigns: `{}`\n", self.campaign_count));
        if let (Some(required), Some(observed), Some(promoted)) = (
            self.required_assessment_improvements,
            self.observed_assessment_improvements,
            self.promoted,
        ) {
            output.push_str(&format!(
                "- assessment gate: `{observed}/{required}` strict improvements; promoted `{promoted}`\n"
            ));
        }
        output.push_str(&format!(
            "- claim boundary: `{:?}`\n\n",
            self.claim_boundary
        ));
        output.push_str("| policy | metric total | metric values | strict improvements | work units/campaign |\n");
        output.push_str("| --- | ---: | --- | ---: | ---: |\n");
        for row in &self.rows {
            output.push_str(&format!(
                "| `{:?}` | {} | {:?} | {} | ({}, {}, {}, {}) |\n",
                row.kind,
                row.total_metric_value,
                row.metric_values,
                row.strict_improvement_count,
                row.work_units_per_campaign.case_count,
                row.work_units_per_campaign.shard_count,
                row.work_units_per_campaign.mutation_attempt_count,
                row.work_units_per_campaign.replay_attempt_count,
            ));
        }
        if let (Some(assessment_rows), Some(policy_deltas)) =
            (&self.assessment_rows, &self.policy_deltas)
        {
            output.push_str("\nValidation-to-assessment deltas:\n\n");
            output.push_str("| policy | validation | assessment | delta |\n");
            output.push_str("| --- | --- | --- | --- |\n");
            for (assessment, delta) in assessment_rows.iter().zip(policy_deltas) {
                output.push_str(&format!(
                    "| `{:?}` | {:?} | {:?} | {:?} |\n",
                    assessment.kind,
                    delta.validation_metric_values,
                    delta.assessment_metric_values,
                    delta.assessment_minus_validation,
                ));
            }
        }
        output.push_str("\nNonclaims:\n\n");
        for note in &self.notes {
            output.push_str(&format!("- {note}\n"));
        }
        output
    }
}

/// One retained suite artifact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IndependentSuiteOperatorArtifactRecord {
    /// Portable relative path.
    pub relative_path: String,
    /// Byte length.
    pub byte_len: usize,
    /// SHA-256 digest of exact retained bytes.
    pub sha256: String,
}

/// Retained suite artifact manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IndependentSuiteOperatorManifest {
    /// Schema version.
    pub schema_version: String,
    /// Suite identifier.
    pub suite_id: String,
    /// Suite configuration digest.
    pub config_digest: String,
    /// Whether assessment is finalized.
    pub finalized: bool,
    /// Exact retained artifacts, excluding this manifest.
    pub artifacts: Vec<IndependentSuiteOperatorArtifactRecord>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaims.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Persistent local operator store for an independent suite.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IndependentSuiteOperatorStore {
    root: PathBuf,
}

impl IndependentSuiteOperatorStore {
    /// Create or open a bounded local artifact root.
    pub fn new(root: impl Into<PathBuf>) -> Result<Self> {
        let root = root.into();
        validate_operator_root(&root)?;
        if root.exists() {
            let metadata = fs::symlink_metadata(&root).map_err(|error| {
                operator_io_error("exploration.suite_operator.root.metadata", error)
            })?;
            if !metadata.is_dir() || metadata.file_type().is_symlink() {
                return Err(ZkBenchError::validation(
                    "exploration.suite_operator.root",
                    "suite operator root must be a non-symlink directory",
                ));
            }
        } else {
            fs::create_dir_all(&root).map_err(|error| {
                operator_io_error("exploration.suite_operator.root.create", error)
            })?;
        }
        Ok(Self { root })
    }

    /// Return the artifact root.
    pub fn root(&self) -> &Path {
        &self.root
    }

    /// Read and validate the retained suite configuration.
    pub fn read_config(&self) -> Result<IndependentCampaignSuiteConfig> {
        let json = self.read(SUITE_OPERATOR_CONFIG_PATH)?;
        let config: IndependentCampaignSuiteConfig =
            serde_json::from_str(&json).map_err(|error| {
                ZkBenchError::deserialization(
                    "exploration.suite_operator.config.deserialize",
                    error.to_string(),
                )
            })?;
        IndependentCampaignSuiteRunner::new(config.clone())?;
        Ok(config)
    }

    /// Run and retain validation artifacts only.
    pub fn run_validation(
        &self,
        config: &IndependentCampaignSuiteConfig,
    ) -> Result<IndependentCampaignSuiteResult> {
        let runner = IndependentCampaignSuiteRunner::new(config.clone())?;
        if self.path(SUITE_OPERATOR_VALIDATION_PATH).exists()
            || self.path(SUITE_OPERATOR_FINALIZED_PATH).exists()
        {
            return Err(ZkBenchError::validation(
                "exploration.suite_operator.run",
                "suite artifacts already exist; use resume or finalize",
            ));
        }
        self.write_config(config)?;
        let result = runner.run_validation()?;
        self.write_immutable(
            SUITE_OPERATOR_VALIDATION_PATH,
            &serialize_independent_campaign_suite_json(&result)?,
        )?;
        self.refresh_derived_artifacts(&result)?;
        Ok(result)
    }

    /// Resume validation from the retained suite checkpoint.
    pub fn resume_validation(
        &self,
        config: &IndependentCampaignSuiteConfig,
    ) -> Result<IndependentCampaignSuiteResult> {
        let runner = IndependentCampaignSuiteRunner::new(config.clone())?;
        let retained = self.read_result(SUITE_OPERATOR_VALIDATION_PATH, config)?;
        if retained.finalized {
            return Err(ZkBenchError::validation(
                "exploration.suite_operator.resume",
                "finalized suites cannot resume validation",
            ));
        }
        let result = runner.resume_validation(retained.checkpoint.clone())?;
        self.write_immutable(
            SUITE_OPERATOR_VALIDATION_PATH,
            &serialize_independent_campaign_suite_json(&result)?,
        )?;
        self.refresh_derived_artifacts(&result)?;
        Ok(result)
    }

    /// Finalize the sealed assessment exactly once.
    pub fn finalize_assessment(
        &self,
        config: &IndependentCampaignSuiteConfig,
    ) -> Result<IndependentCampaignSuiteResult> {
        let runner = IndependentCampaignSuiteRunner::new(config.clone())?;
        if self.path(SUITE_OPERATOR_FINALIZED_PATH).exists() {
            return Err(ZkBenchError::validation(
                "exploration.suite_operator.finalize",
                "suite assessment has already been finalized",
            ));
        }
        let mut result = self.read_result(SUITE_OPERATOR_VALIDATION_PATH, config)?;
        runner.finalize_assessment(&mut result)?;
        self.write_immutable(
            SUITE_OPERATOR_FINALIZED_PATH,
            &serialize_independent_campaign_suite_json(&result)?,
        )?;
        self.refresh_derived_artifacts(&result)?;
        Ok(result)
    }

    /// Read the finalized result when present, otherwise validation.
    pub fn read_active_result(
        &self,
        config: &IndependentCampaignSuiteConfig,
    ) -> Result<IndependentCampaignSuiteResult> {
        if self.path(SUITE_OPERATOR_FINALIZED_PATH).exists() {
            self.read_result(SUITE_OPERATOR_FINALIZED_PATH, config)
        } else {
            self.read_result(SUITE_OPERATOR_VALIDATION_PATH, config)
        }
    }

    /// Read the retained suite report.
    pub fn read_report(&self) -> Result<IndependentSuiteOperatorReport> {
        let json = self.read(SUITE_OPERATOR_REPORT_JSON_PATH)?;
        let report: IndependentSuiteOperatorReport =
            serde_json::from_str(&json).map_err(|error| {
                ZkBenchError::deserialization(
                    "exploration.suite_operator.report.deserialize",
                    error.to_string(),
                )
            })?;
        validate_report(&report)?;
        Ok(report)
    }

    /// Read the retained suite manifest.
    pub fn read_manifest(&self) -> Result<IndependentSuiteOperatorManifest> {
        let json = self.read(SUITE_OPERATOR_MANIFEST_PATH)?;
        let manifest: IndependentSuiteOperatorManifest =
            serde_json::from_str(&json).map_err(|error| {
                ZkBenchError::deserialization(
                    "exploration.suite_operator.manifest.deserialize",
                    error.to_string(),
                )
            })?;
        self.validate_manifest(&manifest)?;
        Ok(manifest)
    }

    fn write_config(&self, config: &IndependentCampaignSuiteConfig) -> Result<()> {
        let json = serde_json::to_string_pretty(config).map_err(|error| {
            ZkBenchError::serialization(
                "exploration.suite_operator.config.serialize",
                error.to_string(),
            )
        })?;
        self.write_immutable(SUITE_OPERATOR_CONFIG_PATH, &json)
    }

    fn read_result(
        &self,
        relative_path: &str,
        config: &IndependentCampaignSuiteConfig,
    ) -> Result<IndependentCampaignSuiteResult> {
        let json = self.read(relative_path)?;
        deserialize_independent_campaign_suite_json(&json, config)
    }

    fn path(&self, relative_path: &str) -> PathBuf {
        self.root.join(relative_path)
    }

    fn read(&self, relative_path: &str) -> Result<String> {
        validate_relative_operator_path(relative_path)?;
        let path = self.path(relative_path);
        reject_symlink(&path, "exploration.suite_operator.read")?;
        fs::read_to_string(path).map_err(|error| {
            operator_io_error(
                format!("exploration.suite_operator.read.{relative_path}"),
                error,
            )
        })
    }

    fn write_immutable(&self, relative_path: &str, content: &str) -> Result<()> {
        let path = self.path(relative_path);
        if path.exists() {
            let existing = self.read(relative_path)?;
            if existing != content {
                return Err(ZkBenchError::validation(
                    format!("exploration.suite_operator.immutable.{relative_path}"),
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
        reject_symlink(&path, "exploration.suite_operator.write")?;
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|error| {
                operator_io_error("exploration.suite_operator.write.parent", error)
            })?;
        }
        fs::write(&path, content.as_bytes()).map_err(|error| {
            operator_io_error(
                format!("exploration.suite_operator.write.{relative_path}"),
                error,
            )
        })
    }

    fn refresh_derived_artifacts(&self, result: &IndependentCampaignSuiteResult) -> Result<()> {
        let report = IndependentSuiteOperatorReport::from_result(result)?;
        let report_json = serde_json::to_string_pretty(&report).map_err(|error| {
            ZkBenchError::serialization(
                "exploration.suite_operator.report.serialize",
                error.to_string(),
            )
        })?;
        self.write_replace(SUITE_OPERATOR_REPORT_JSON_PATH, &report_json)?;
        self.write_replace(
            SUITE_OPERATOR_REPORT_MARKDOWN_PATH,
            &report.render_markdown(),
        )?;
        self.refresh_manifest(result)
    }

    fn refresh_manifest(&self, result: &IndependentCampaignSuiteResult) -> Result<()> {
        let mut relative_paths = vec![
            SUITE_OPERATOR_CONFIG_PATH.to_string(),
            SUITE_OPERATOR_VALIDATION_PATH.to_string(),
            SUITE_OPERATOR_REPORT_JSON_PATH.to_string(),
            SUITE_OPERATOR_REPORT_MARKDOWN_PATH.to_string(),
        ];
        if result.finalized {
            relative_paths.push(SUITE_OPERATOR_FINALIZED_PATH.to_string());
        }
        relative_paths.sort();
        let mut artifacts = Vec::new();
        for relative_path in relative_paths {
            let bytes = fs::read(self.path(&relative_path)).map_err(|error| {
                operator_io_error(
                    format!("exploration.suite_operator.manifest.read.{relative_path}"),
                    error,
                )
            })?;
            let digest = compute_artifact_digest_bytes(&bytes, None, None);
            artifacts.push(IndependentSuiteOperatorArtifactRecord {
                relative_path,
                byte_len: bytes.len(),
                sha256: digest.hex_digest,
            });
        }
        let manifest = IndependentSuiteOperatorManifest {
            schema_version: SUITE_OPERATOR_SCHEMA_VERSION.to_string(),
            suite_id: result.suite_id.clone(),
            config_digest: result.config_digest.clone(),
            finalized: result.finalized,
            artifacts,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Manifest records local deterministic suite artifacts only.".to_string(),
                "The manifest itself is excluded from its artifact list.".to_string(),
            ],
        };
        let json = serde_json::to_string_pretty(&manifest).map_err(|error| {
            ZkBenchError::serialization(
                "exploration.suite_operator.manifest.serialize",
                error.to_string(),
            )
        })?;
        self.write_replace(SUITE_OPERATOR_MANIFEST_PATH, &json)
    }

    fn validate_manifest(&self, manifest: &IndependentSuiteOperatorManifest) -> Result<()> {
        if manifest.schema_version != SUITE_OPERATOR_SCHEMA_VERSION
            || manifest.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
        {
            return Err(ZkBenchError::validation(
                "exploration.suite_operator.manifest.identity",
                "suite operator manifest schema or claim boundary is invalid",
            ));
        }
        let mut expected_paths = vec![
            SUITE_OPERATOR_CONFIG_PATH.to_string(),
            SUITE_OPERATOR_VALIDATION_PATH.to_string(),
            SUITE_OPERATOR_REPORT_JSON_PATH.to_string(),
            SUITE_OPERATOR_REPORT_MARKDOWN_PATH.to_string(),
        ];
        if manifest.finalized {
            expected_paths.push(SUITE_OPERATOR_FINALIZED_PATH.to_string());
        }
        expected_paths.sort();
        let actual_paths = manifest
            .artifacts
            .iter()
            .map(|artifact| artifact.relative_path.clone())
            .collect::<Vec<_>>();
        if actual_paths != expected_paths {
            return Err(ZkBenchError::validation(
                "exploration.suite_operator.manifest.paths",
                "suite operator manifest paths are not canonical",
            ));
        }
        for artifact in &manifest.artifacts {
            validate_relative_operator_path(&artifact.relative_path)?;
            let path = self.path(&artifact.relative_path);
            reject_symlink(&path, "exploration.suite_operator.manifest")?;
            let bytes = fs::read(&path).map_err(|error| {
                operator_io_error(
                    format!(
                        "exploration.suite_operator.manifest.validate.{}",
                        artifact.relative_path
                    ),
                    error,
                )
            })?;
            let digest = compute_artifact_digest_bytes(&bytes, None, None);
            if artifact.byte_len != bytes.len() || artifact.sha256 != digest.hex_digest {
                return Err(ZkBenchError::validation(
                    "exploration.suite_operator.manifest.digest",
                    "suite operator manifest digest does not match retained bytes",
                ));
            }
        }
        Ok(())
    }
}

fn validate_report(report: &IndependentSuiteOperatorReport) -> Result<()> {
    if report.schema_version != SUITE_SCORECARD_SCHEMA_VERSION
        || report.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
        || report.campaign_count == 0
        || report.rows.is_empty()
        || report.validation_rows.is_empty()
    {
        return Err(ZkBenchError::validation(
            "exploration.suite_operator.report.identity",
            "suite operator report schema, boundary, or rows are invalid",
        ));
    }
    if report.finalized != (report.phase == ExplorationPhase::FinalizedAssessment)
        || report.finalized != report.required_assessment_improvements.is_some()
        || report.finalized != report.observed_assessment_improvements.is_some()
        || report.finalized != report.promoted.is_some()
    {
        return Err(ZkBenchError::validation(
            "exploration.suite_operator.report.phase",
            "suite operator report phase and finalization fields are inconsistent",
        ));
    }
    let expected_active_rows: &[IndependentPolicyAggregateRow] = if report.finalized {
        report.assessment_rows.as_deref().ok_or_else(|| {
            ZkBenchError::validation(
                "exploration.suite_operator.report.assessment_rows",
                "finalized report is missing assessment rows",
            )
        })?
    } else {
        &report.validation_rows
    };
    if report.rows.as_slice() != expected_active_rows {
        return Err(ZkBenchError::validation(
            "exploration.suite_operator.report.active_rows",
            "active report rows do not match the report phase",
        ));
    }
    validate_scorecard_rows(&report.validation_rows, report.campaign_count)?;
    if report.finalized {
        let assessment_rows = report.assessment_rows.as_deref().ok_or_else(|| {
            ZkBenchError::validation(
                "exploration.suite_operator.report.assessment_rows",
                "finalized report is missing assessment rows",
            )
        })?;
        validate_scorecard_rows(assessment_rows, report.campaign_count)?;
        let expected_deltas = build_policy_deltas(&report.validation_rows, assessment_rows)?;
        if report.policy_deltas.as_ref() != Some(&expected_deltas) {
            return Err(ZkBenchError::validation(
                "exploration.suite_operator.report.policy_deltas",
                "policy deltas do not match validation and assessment rows",
            ));
        }
    } else if report.assessment_rows.is_some() || report.policy_deltas.is_some() {
        return Err(ZkBenchError::validation(
            "exploration.suite_operator.report.assessment_sealing",
            "assessment scorecard rows are present before finalization",
        ));
    }
    Ok(())
}

fn validate_scorecard_rows(
    rows: &[IndependentPolicyAggregateRow],
    campaign_count: usize,
) -> Result<()> {
    if rows.is_empty() || rows.len() != 5 {
        return Err(ZkBenchError::validation(
            "exploration.suite_operator.report.rows",
            "scorecard must contain exactly five policy rows",
        ));
    }
    for row in rows {
        if row.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
            || row.policy_digests.len() != campaign_count
            || row.metric_values.len() != campaign_count
            || row.total_metric_value != row.metric_values.iter().sum::<usize>()
        {
            return Err(ZkBenchError::validation(
                "exploration.suite_operator.report.rows",
                "scorecard policy row is inconsistent with its campaign values",
            ));
        }
    }
    Ok(())
}

fn build_policy_deltas(
    validation_rows: &[IndependentPolicyAggregateRow],
    assessment_rows: &[IndependentPolicyAggregateRow],
) -> Result<Vec<IndependentSuitePolicyDelta>> {
    if validation_rows.len() != assessment_rows.len() {
        return Err(ZkBenchError::validation(
            "exploration.suite_operator.report.policy_deltas",
            "validation and assessment policy row counts differ",
        ));
    }
    let mut deltas = Vec::new();
    for (validation, assessment) in validation_rows.iter().zip(assessment_rows) {
        if validation.kind != assessment.kind
            || validation.policy_digests != assessment.policy_digests
            || validation.metric_values.len() != assessment.metric_values.len()
        {
            return Err(ZkBenchError::validation(
                "exploration.suite_operator.report.policy_deltas",
                "validation and assessment policy identities differ",
            ));
        }
        let assessment_minus_validation = assessment
            .metric_values
            .iter()
            .zip(&validation.metric_values)
            .map(|(assessment, validation)| *assessment as i64 - *validation as i64)
            .collect();
        deltas.push(IndependentSuitePolicyDelta {
            kind: validation.kind,
            policy_digests: validation.policy_digests.clone(),
            validation_metric_values: validation.metric_values.clone(),
            assessment_metric_values: assessment.metric_values.clone(),
            assessment_minus_validation,
            validation_total_metric_value: validation.total_metric_value,
            assessment_total_metric_value: assessment.total_metric_value,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        });
    }
    Ok(deltas)
}

fn active_comparison(
    result: &IndependentCampaignSuiteResult,
) -> Result<&IndependentCampaignComparisonReport> {
    if result.finalized {
        result.assessment_comparison.as_ref().ok_or_else(|| {
            ZkBenchError::validation(
                "exploration.suite_operator.report.assessment",
                "finalized suite is missing assessment comparison",
            )
        })
    } else {
        Ok(&result.validation_comparison)
    }
}

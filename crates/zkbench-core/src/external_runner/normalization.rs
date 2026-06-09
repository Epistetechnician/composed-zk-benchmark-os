//! Normalized synthetic result draft primitives.
//!
//! Normalization produces reviewable local drafts only. The drafts preserve
//! candidate metrics as pending-review metadata and never feed score reports.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary,
};

use super::importer::{ResultCandidateArtifactResolver, SyntheticImportValidation};
use super::provenance::ExternalRunProvenanceDraft;
use super::result_import::{ExternalMetricUnit, ExternalResultCandidate, ExternalResultStatus};

/// Normalized external result draft id.
pub type NormalizedExternalResultDraftId = String;

/// Review status for a normalized synthetic draft.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum NormalizedExternalResultDraftStatus {
    /// Draft is pending human/policy review.
    PendingReview,
    /// Draft is synthetic-only and cannot be accepted as evidence.
    SyntheticOnly,
    /// Draft was quarantined and should not be proposed.
    Quarantined,
}

/// Normalized artifact reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalizedArtifactRef {
    /// Relative artifact reference.
    pub artifact_ref: String,
    /// Candidate or recomputed digest.
    pub digest: ArtifactDigest,
    /// True when the importer verified this digest against available local bytes.
    pub verified_by_importer: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Normalized metric draft. Values remain candidate-only metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalizedMetricDraft {
    /// Metric kind label.
    pub metric_kind: String,
    /// Metric unit.
    pub unit: ExternalMetricUnit,
    /// Optional candidate value.
    #[serde(default)]
    pub value: Option<String>,
    /// Optional source artifact reference.
    #[serde(default)]
    pub source_artifact_ref: Option<String>,
    /// True because Phase I metrics are imported candidate metadata only.
    pub candidate_only: bool,
    /// True because a future review must decide whether anything can be appended.
    pub pending_review: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Normalized provenance draft summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalizedProvenanceDraft {
    /// Source provenance draft id.
    #[serde(default)]
    pub source_provenance_id: Option<String>,
    /// Operator or agent label.
    #[serde(default)]
    pub operator_or_agent: Option<String>,
    /// External tool name.
    #[serde(default)]
    pub external_tool_name: Option<String>,
    /// External tool version.
    #[serde(default)]
    pub external_tool_version: Option<String>,
    /// Declared network policy.
    #[serde(default)]
    pub network_policy: Option<String>,
    /// Source command plan id.
    #[serde(default)]
    pub command_plan_id: Option<String>,
    /// Source benchmark pack id.
    #[serde(default)]
    pub benchmark_pack_id: Option<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl From<&ExternalRunProvenanceDraft> for NormalizedProvenanceDraft {
    fn from(value: &ExternalRunProvenanceDraft) -> Self {
        Self {
            source_provenance_id: value.id.clone(),
            operator_or_agent: value.operator.operator_or_agent.clone(),
            external_tool_name: value.external_tool.external_tool_name.clone(),
            external_tool_version: value.external_tool.external_tool_version.clone(),
            network_policy: value.environment.network_policy.clone(),
            command_plan_id: value.source.command_plan_id.clone(),
            benchmark_pack_id: value.source.benchmark_pack_id.clone(),
            notes: value.notes.clone(),
        }
    }
}

/// Non-blocking normalization warning.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalizationWarning {
    /// Warning path.
    pub path: String,
    /// Warning message.
    pub message: String,
}

/// Normalization report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalizationReport {
    /// Number of metrics copied into the draft.
    pub metric_count: usize,
    /// Number of artifact references copied into the draft.
    pub artifact_ref_count: usize,
    /// Warnings.
    #[serde(default)]
    pub warnings: Vec<NormalizationWarning>,
    /// Claim boundary for the report.
    pub claim_boundary: ClaimBoundary,
}

/// Normalized external result draft.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct NormalizedExternalResultDraft {
    /// Draft id.
    pub normalized_result_draft_id: NormalizedExternalResultDraftId,
    /// Source candidate id.
    pub source_result_candidate_id: String,
    /// Source benchmark pack id.
    pub source_benchmark_pack_id: String,
    /// Source dry-run plan id.
    pub dry_run_plan_id: String,
    /// Source result status.
    pub source_result_status: ExternalResultStatus,
    /// Draft status.
    pub status: NormalizedExternalResultDraftStatus,
    /// Claim boundary for this draft artifact.
    pub claim_boundary: ClaimBoundary,
    /// Candidate metrics copied as pending-review metadata.
    pub metrics: Vec<NormalizedMetricDraft>,
    /// Artifact references associated with this draft.
    pub artifact_refs: Vec<NormalizedArtifactRef>,
    /// Normalized provenance summary.
    pub provenance_draft: NormalizedProvenanceDraft,
    /// Digest of the validation report.
    #[serde(default)]
    pub validation_report_digest: Option<ArtifactDigest>,
    /// Normalization report.
    pub normalization_report: NormalizationReport,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Normalize a validated synthetic result candidate into a pending-review draft.
pub fn normalize_synthetic_result_candidate(
    candidate: &ExternalResultCandidate,
    validation: &SyntheticImportValidation,
    resolver: &ResultCandidateArtifactResolver,
) -> Result<NormalizedExternalResultDraft> {
    if !validation.valid {
        return Err(ZkBenchError::synthetic_import(
            "normalize_synthetic_result_candidate.validation",
            "cannot normalize an invalid synthetic result candidate",
        ));
    }

    let validation_report_digest = Some(compute_artifact_digest(
        validation,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Digest),
    )?);
    let metrics = candidate
        .normalized_metrics
        .iter()
        .map(|metric| NormalizedMetricDraft {
            metric_kind: metric.metric_kind.clone(),
            unit: metric.unit,
            value: metric.value.clone(),
            source_artifact_ref: metric.source_artifact_ref.clone(),
            candidate_only: true,
            pending_review: true,
            notes: metric.notes.clone(),
        })
        .collect::<Vec<_>>();
    let artifact_refs = candidate
        .raw_output_artifact_refs
        .iter()
        .filter_map(|artifact_ref| {
            resolver
                .lookup(artifact_ref)
                .map(|lookup| NormalizedArtifactRef {
                    artifact_ref: artifact_ref.clone(),
                    digest: lookup.expected_digest.clone(),
                    verified_by_importer: lookup.bytes.is_some(),
                    notes: vec!["synthetic candidate artifact reference only".to_string()],
                })
        })
        .collect::<Vec<_>>();
    let provenance_draft = candidate
        .provenance_draft
        .as_ref()
        .map(NormalizedProvenanceDraft::from)
        .ok_or_else(|| {
            ZkBenchError::synthetic_import(
                "normalize_synthetic_result_candidate.provenance_draft",
                "validated candidates must have provenance drafts",
            )
        })?;

    Ok(NormalizedExternalResultDraft {
        normalized_result_draft_id: format!("normalized_{}", candidate.result_candidate_id),
        source_result_candidate_id: candidate.result_candidate_id.clone(),
        source_benchmark_pack_id: candidate.source_benchmark_pack_id.clone(),
        dry_run_plan_id: candidate.dry_run_plan_id.clone(),
        source_result_status: candidate.result_status,
        status: NormalizedExternalResultDraftStatus::PendingReview,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        metrics,
        artifact_refs,
        provenance_draft,
        validation_report_digest,
        normalization_report: NormalizationReport {
            metric_count: candidate.normalized_metrics.len(),
            artifact_ref_count: candidate.raw_output_artifact_refs.len(),
            warnings: Vec::new(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
        },
        notes: vec![
            "Normalized synthetic result drafts are not accepted evidence.".to_string(),
            "Synthetic result candidates are not benchmark results.".to_string(),
        ],
    })
}

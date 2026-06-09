//! Synthetic result import bundle primitives.
//!
//! A Phase I import bundle records parsing, validation, normalization, and
//! quarantine metadata for a synthetic candidate. It is not accepted evidence
//! and must remain Level0DesignNote.

use serde::{Deserialize, Serialize};

use crate::evidence::ClaimBoundary;

use super::importer::{
    ResultCandidateSource, SyntheticImportValidation, SyntheticImportValidationIssueKind,
};
use super::normalization::NormalizedExternalResultDraft;
use super::quarantine::QuarantineManifest;
use super::result_import::ExternalResultCandidate;

/// Synthetic result import bundle id.
pub type SyntheticResultImportBundleId = String;

/// Synthetic import bundle schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntheticResultImportBundleVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for SyntheticResultImportBundleVersion {
    fn default() -> Self {
        Self {
            value: "phase-i-synthetic-result-import-bundle-v0".to_string(),
        }
    }
}

/// Count of validation issues by issue kind.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntheticValidationIssueCount {
    /// Issue kind label.
    pub kind: SyntheticImportValidationIssueKind,
    /// Count.
    pub count: usize,
}

/// Summary report for one synthetic import bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntheticResultImportReport {
    /// Number of candidates parsed into the bundle.
    pub candidates_imported: usize,
    /// Number of candidates normalized into review drafts.
    pub candidates_normalized: usize,
    /// Number of candidates quarantined.
    pub candidates_quarantined: usize,
    /// Number of evidence append proposals created by this bundle.
    pub proposals_created: usize,
    /// Total validation issues.
    pub validation_issue_count: usize,
    /// Validation issue counts by kind.
    pub validation_issues_by_type: Vec<SyntheticValidationIssueCount>,
    /// Claim boundary for the bundle artifact.
    pub claim_boundary: ClaimBoundary,
}

impl SyntheticResultImportReport {
    /// Build a deterministic single-candidate report from validation output.
    pub fn from_validation(
        validation: &SyntheticImportValidation,
        normalized: bool,
        quarantined: bool,
        proposals_created: usize,
    ) -> Self {
        let mut issue_counts = Vec::<SyntheticValidationIssueCount>::new();
        for issue in &validation.issues {
            match issue_counts
                .iter_mut()
                .find(|entry| entry.kind == issue.kind)
            {
                Some(entry) => entry.count += 1,
                None => issue_counts.push(SyntheticValidationIssueCount {
                    kind: issue.kind,
                    count: 1,
                }),
            }
        }
        issue_counts.sort_by_key(|entry| entry.kind);

        Self {
            candidates_imported: 1,
            candidates_normalized: usize::from(normalized),
            candidates_quarantined: usize::from(quarantined),
            proposals_created,
            validation_issue_count: validation.issues.len(),
            validation_issues_by_type: issue_counts,
            claim_boundary: ClaimBoundary::Level0DesignNote,
        }
    }
}

/// Full Phase I synthetic import bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SyntheticResultImportBundle {
    /// Bundle id.
    pub id: SyntheticResultImportBundleId,
    /// Bundle schema version.
    pub version: SyntheticResultImportBundleVersion,
    /// Candidate source metadata.
    pub source: ResultCandidateSource,
    /// Parsed candidate.
    pub candidate: ExternalResultCandidate,
    /// Validation report.
    pub validation: SyntheticImportValidation,
    /// Normalized draft, present only when validation passes.
    #[serde(default)]
    pub normalized_draft: Option<NormalizedExternalResultDraft>,
    /// Quarantine manifest, present when validation fails.
    #[serde(default)]
    pub quarantine_manifest: Option<QuarantineManifest>,
    /// Bundle summary report.
    pub report: SyntheticResultImportReport,
    /// Claim boundary for the bundle artifact.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl SyntheticResultImportBundle {
    /// Create a new bundle for one candidate.
    pub fn new(
        source: ResultCandidateSource,
        candidate: ExternalResultCandidate,
        validation: SyntheticImportValidation,
        normalized_draft: Option<NormalizedExternalResultDraft>,
        quarantine_manifest: Option<QuarantineManifest>,
    ) -> Self {
        let normalized = normalized_draft.is_some();
        let quarantined = quarantine_manifest.is_some();
        let report =
            SyntheticResultImportReport::from_validation(&validation, normalized, quarantined, 0);
        Self {
            id: format!("synthetic_import_bundle_{}", candidate.result_candidate_id),
            version: SyntheticResultImportBundleVersion::default(),
            source,
            candidate,
            validation,
            normalized_draft,
            quarantine_manifest,
            report,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec![
                "Synthetic result candidates are not benchmark results.".to_string(),
                "Evidence append proposals are not accepted evidence.".to_string(),
            ],
        }
    }
}

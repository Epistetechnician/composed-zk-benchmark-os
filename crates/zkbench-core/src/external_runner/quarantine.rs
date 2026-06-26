//! Quarantine schema for external result candidates.

use serde::{Deserialize, Serialize};

use crate::evidence::ClaimBoundary;

use super::result_import::{
    validate_external_result_candidate, ExternalResultCandidate, ExternalResultValidationIssue,
};
use super::validation::{
    contains_rejected_path, phase_h_actual_claim_allowed, ExternalValidationIssueSeverity,
};

/// Quarantine status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum QuarantineStatus {
    /// Candidate is pending review.
    PendingReview,
    /// Candidate is quarantined.
    Quarantined,
    /// Candidate was rejected.
    Rejected,
}

/// Reason for quarantine.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum QuarantineReason {
    /// Pending review.
    PendingReview,
    /// Missing provenance.
    MissingProvenance,
    /// Invalid digest.
    InvalidDigest,
    /// Claim boundary too high.
    ClaimBoundaryTooHigh,
    /// Unsupported metric.
    UnsupportedMetric,
    /// Absolute path rejected.
    AbsolutePathRejected,
    /// Official claim rejected.
    OfficialClaimRejected,
    /// Formal claim rejected.
    FormalClaimRejected,
    /// Unknown source.
    UnknownSource,
    /// Metric validation failed.
    MetricValidationFailed,
    /// Provenance validation failed.
    ProvenanceValidationFailed,
    /// Artifact digest mismatch.
    ArtifactDigestMismatch,
    /// Official claim detected.
    OfficialClaimDetected,
    /// Formal claim detected.
    FormalClaimDetected,
    /// Soundness claim detected.
    SoundnessClaimDetected,
    /// Proposal is blocked.
    ProposalBlocked,
}

/// Quarantine entry for one external result candidate.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuarantineEntry {
    /// Candidate result id.
    pub candidate_result_id: String,
    /// Quarantine reason.
    pub reason: QuarantineReason,
    /// Source artifact refs.
    #[serde(default)]
    pub source_artifact_refs: Vec<String>,
    /// Validation issues.
    #[serde(default)]
    pub validation_issues: Vec<ExternalResultValidationIssue>,
    /// Claim boundary associated with the candidate.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Quarantine validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuarantineValidation {
    /// True when no validation errors were found.
    pub valid: bool,
    /// Status summary.
    pub status: QuarantineStatus,
    /// Issues.
    pub issues: Vec<QuarantineValidationIssue>,
}

/// Quarantine validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuarantineValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: ExternalValidationIssueSeverity,
}

impl QuarantineValidationIssue {
    fn error(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Error,
        }
    }
}

/// Manifest of quarantined external result candidates.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QuarantineManifest {
    /// Quarantine id.
    pub quarantine_id: String,
    /// Schema version.
    pub schema_version: String,
    /// Quarantine entries.
    pub entries: Vec<QuarantineEntry>,
    /// Validation status.
    pub validation_status: QuarantineStatus,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Convert an external result candidate into a quarantine manifest.
pub fn quarantine_external_result_candidate(
    candidate: &ExternalResultCandidate,
) -> QuarantineManifest {
    let validation = validate_external_result_candidate(candidate);
    let reason = choose_reason(candidate, &validation.issues);
    QuarantineManifest {
        quarantine_id: format!("quarantine_{}", candidate.result_candidate_id),
        schema_version: "phase-h-quarantine-manifest-v0".to_string(),
        entries: vec![QuarantineEntry {
            candidate_result_id: candidate.result_candidate_id.clone(),
            reason,
            source_artifact_refs: candidate.raw_output_artifact_refs.clone(),
            validation_issues: validation.issues,
            claim_boundary: candidate.claim_boundary_requested,
            notes: vec![
                "This is a local quarantine entry, not benchmark acceptance evidence.".to_string(),
            ],
        }],
        validation_status: QuarantineStatus::Quarantined,
        notes: vec![
            "Result import candidates are quarantined or pending review until validated."
                .to_string(),
            "Quarantine acceptance is not evidence acceptance.".to_string(),
        ],
    }
}

/// Validate a quarantine manifest.
pub fn validate_quarantine_manifest(manifest: &QuarantineManifest) -> QuarantineValidation {
    let mut issues = Vec::new();
    if manifest.quarantine_id.trim().is_empty() {
        issues.push(QuarantineValidationIssue::error(
            "manifest.quarantine_id",
            "quarantine id is empty",
        ));
    }
    for (index, entry) in manifest.entries.iter().enumerate() {
        if entry.candidate_result_id.trim().is_empty() {
            issues.push(QuarantineValidationIssue::error(
                format!("manifest.entries[{index}].candidate_result_id"),
                "candidate result id is empty",
            ));
        }
        if !phase_h_actual_claim_allowed(entry.claim_boundary) {
            issues.push(QuarantineValidationIssue::error(
                format!("manifest.entries[{index}].claim_boundary"),
                "quarantine entry claim boundary exceeds Phase H local limits",
            ));
        }
        for (ref_index, reference) in entry.source_artifact_refs.iter().enumerate() {
            if contains_rejected_path(reference) {
                issues.push(QuarantineValidationIssue::error(
                    format!("manifest.entries[{index}].source_artifact_refs[{ref_index}]"),
                    "source artifact ref is absolute or contains traversal",
                ));
            }
        }
    }
    QuarantineValidation {
        valid: issues.is_empty(),
        status: if issues.is_empty() {
            manifest.validation_status
        } else {
            QuarantineStatus::Rejected
        },
        issues,
    }
}

fn choose_reason(
    candidate: &ExternalResultCandidate,
    issues: &[ExternalResultValidationIssue],
) -> QuarantineReason {
    if candidate.claim_boundary_requested >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact {
        return QuarantineReason::ClaimBoundaryTooHigh;
    }
    if candidate.claims_official_benchmark_evidence {
        return QuarantineReason::OfficialClaimRejected;
    }
    if candidate.claims_formal_evidence || candidate.claims_proof_system_soundness {
        return QuarantineReason::FormalClaimRejected;
    }
    if candidate.provenance_draft.is_none() {
        return QuarantineReason::MissingProvenance;
    }
    if issues
        .iter()
        .any(|issue| issue.message.contains("absolute"))
    {
        return QuarantineReason::AbsolutePathRejected;
    }
    if issues
        .iter()
        .any(|issue| issue.path.contains("artifact_ref") || issue.path.contains("unit"))
    {
        return QuarantineReason::UnsupportedMetric;
    }
    if candidate.source_benchmark_pack_id.trim().is_empty()
        || candidate.dry_run_plan_id.trim().is_empty()
    {
        return QuarantineReason::UnknownSource;
    }
    QuarantineReason::PendingReview
}

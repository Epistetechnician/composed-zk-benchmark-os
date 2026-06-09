//! Phase I synthetic import helpers.

use crate::evidence::ClaimBoundary;

use super::importer::{SyntheticImportValidation, SyntheticImportValidationIssueKind};
use super::quarantine::{QuarantineEntry, QuarantineManifest, QuarantineReason, QuarantineStatus};
use super::result_import::ExternalResultCandidate;

/// Claim boundary for Phase I synthetic import artifacts.
pub const PHASE_I_SYNTHETIC_CLAIM_BOUNDARY: ClaimBoundary = ClaimBoundary::Level0DesignNote;

/// Convert a synthetic validation result into a quarantine manifest.
pub fn quarantine_synthetic_result_candidate(
    candidate: &ExternalResultCandidate,
    validation: &SyntheticImportValidation,
) -> QuarantineManifest {
    let reason = choose_synthetic_quarantine_reason(validation);
    QuarantineManifest {
        quarantine_id: format!("synthetic_quarantine_{}", candidate.result_candidate_id),
        schema_version: "phase-i-synthetic-quarantine-manifest-v0".to_string(),
        entries: vec![QuarantineEntry {
            candidate_result_id: candidate.result_candidate_id.clone(),
            reason,
            source_artifact_refs: candidate.raw_output_artifact_refs.clone(),
            validation_issues: validation
                .issues
                .iter()
                .map(|issue| issue.as_external_result_issue())
                .collect(),
            claim_boundary: PHASE_I_SYNTHETIC_CLAIM_BOUNDARY,
            notes: vec![
                "Synthetic result candidates are not benchmark results.".to_string(),
                "Quarantine entries are not accepted evidence.".to_string(),
            ],
        }],
        validation_status: QuarantineStatus::Quarantined,
        notes: vec![
            "Synthetic result candidate was blocked before normalization.".to_string(),
            "Evidence append proposals are not accepted evidence.".to_string(),
        ],
    }
}

fn choose_synthetic_quarantine_reason(validation: &SyntheticImportValidation) -> QuarantineReason {
    if validation
        .issues
        .iter()
        .any(|issue| issue.kind == SyntheticImportValidationIssueKind::ClaimBoundaryTooHigh)
    {
        return QuarantineReason::ClaimBoundaryTooHigh;
    }
    if validation
        .issues
        .iter()
        .any(|issue| issue.kind == SyntheticImportValidationIssueKind::OfficialClaimDetected)
    {
        return QuarantineReason::OfficialClaimDetected;
    }
    if validation
        .issues
        .iter()
        .any(|issue| issue.kind == SyntheticImportValidationIssueKind::FormalClaimDetected)
    {
        return QuarantineReason::FormalClaimDetected;
    }
    if validation
        .issues
        .iter()
        .any(|issue| issue.kind == SyntheticImportValidationIssueKind::SoundnessClaimDetected)
    {
        return QuarantineReason::SoundnessClaimDetected;
    }
    if validation
        .issues
        .iter()
        .any(|issue| issue.kind == SyntheticImportValidationIssueKind::ArtifactDigestMismatch)
    {
        return QuarantineReason::ArtifactDigestMismatch;
    }
    if validation.issues.iter().any(|issue| {
        matches!(
            issue.kind,
            SyntheticImportValidationIssueKind::ArtifactDigestMissing
                | SyntheticImportValidationIssueKind::ArtifactDigestUnsupported
                | SyntheticImportValidationIssueKind::ArtifactLookupMissing
        )
    }) {
        return QuarantineReason::InvalidDigest;
    }
    if validation
        .issues
        .iter()
        .any(|issue| issue.kind == SyntheticImportValidationIssueKind::ProvenanceValidationFailed)
    {
        return QuarantineReason::ProvenanceValidationFailed;
    }
    if validation
        .issues
        .iter()
        .any(|issue| issue.kind == SyntheticImportValidationIssueKind::MetricValidationFailed)
    {
        return QuarantineReason::MetricValidationFailed;
    }
    QuarantineReason::PendingReview
}

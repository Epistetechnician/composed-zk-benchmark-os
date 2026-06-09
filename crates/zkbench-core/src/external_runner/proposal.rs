//! Evidence append proposal primitives for synthetic imports.
//!
//! Proposals are review artifacts, not accepted evidence records. They do not
//! mutate the EvidenceLedger.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{ArtifactDigest, ClaimBoundary, EvidenceClass};

use super::importer::{SyntheticImportValidationIssue, SyntheticImportValidationIssueKind};
use super::normalization::{NormalizedArtifactRef, NormalizedExternalResultDraft};
use super::review::EvidenceReviewChecklist;
use super::validation::{
    contains_forbidden_claim_text, phase_h_design_artifact_claim_allowed,
    ExternalValidationIssueSeverity,
};

/// Evidence append proposal id.
pub type EvidenceAppendProposalId = String;

/// Evidence append proposal version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposalVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for EvidenceAppendProposalVersion {
    fn default() -> Self {
        Self {
            value: "phase-i-evidence-append-proposal-v0".to_string(),
        }
    }
}

/// Proposal kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceAppendProposalKind {
    /// Proposal created from a synthetic result import.
    SyntheticResultImport,
}

/// Proposal status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceAppendProposalStatus {
    /// Draft.
    Draft,
    /// Pending review.
    PendingReview,
    /// Rejected.
    Rejected,
    /// Future append-only approval marker, not accepted evidence.
    ApprovedForFutureAppendOnly,
    /// Superseded by a later proposal.
    Superseded,
}

/// Proposal review state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceAppendProposalReviewState {
    /// Not reviewed.
    NotReviewed,
    /// Pending review.
    PendingReview,
    /// Changes requested.
    ChangesRequested,
    /// Rejected.
    Rejected,
    /// Future approval is required before any append.
    FutureApprovalRequired,
}

/// Proposal validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposalValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue severity.
    pub severity: ExternalValidationIssueSeverity,
}

impl EvidenceAppendProposalValidationIssue {
    fn error(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            message: message.into(),
            severity: ExternalValidationIssueSeverity::Error,
        }
    }
}

/// Proposal validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposalValidation {
    /// True when no validation errors were found.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<EvidenceAppendProposalValidationIssue>,
}

/// Evidence append proposal. This is not an EvidenceRecord.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposal {
    /// Proposal id.
    pub id: EvidenceAppendProposalId,
    /// Proposal version.
    pub version: EvidenceAppendProposalVersion,
    /// Source normalized draft id.
    pub source_normalized_draft_id: String,
    /// Proposal kind.
    pub kind: EvidenceAppendProposalKind,
    /// Proposal status.
    pub status: EvidenceAppendProposalStatus,
    /// Review state.
    pub review_state: EvidenceAppendProposalReviewState,
    /// Proposed evidence class. Phase I accepts DesignNote only.
    pub proposed_evidence_class: EvidenceClass,
    /// Proposed claim boundary. Phase I proposal artifacts stay Level0DesignNote.
    pub proposed_claim_boundary: ClaimBoundary,
    /// Provenance summary copied from the normalized draft.
    pub proposed_provenance_summary: Vec<String>,
    /// Proposed artifact references.
    #[serde(default)]
    pub proposed_artifact_refs: Vec<NormalizedArtifactRef>,
    /// Digest of the validation report that led to this proposal.
    #[serde(default)]
    pub validation_report_digest: Option<ArtifactDigest>,
    /// Blocking import issues.
    #[serde(default)]
    pub blocking_issues: Vec<SyntheticImportValidationIssue>,
    /// Review checklist.
    pub reviewer_checklist: EvidenceReviewChecklist,
    /// Must remain false in Phase I.
    pub claims_accepted_evidence: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl EvidenceAppendProposal {
    /// Return false for every Phase I proposal.
    pub fn is_accepted_evidence(&self) -> bool {
        false
    }
}

/// Create a pending-review proposal from a normalized synthetic result draft.
pub fn create_evidence_append_proposal(
    draft: &NormalizedExternalResultDraft,
) -> Result<EvidenceAppendProposal> {
    if !phase_h_design_artifact_claim_allowed(draft.claim_boundary) {
        return Err(ZkBenchError::evidence_append_proposal(
            "create_evidence_append_proposal.draft.claim_boundary",
            "synthetic normalized drafts must remain Level0DesignNote",
        ));
    }

    Ok(EvidenceAppendProposal {
        id: format!("proposal_{}", draft.normalized_result_draft_id),
        version: EvidenceAppendProposalVersion::default(),
        source_normalized_draft_id: draft.normalized_result_draft_id.clone(),
        kind: EvidenceAppendProposalKind::SyntheticResultImport,
        status: EvidenceAppendProposalStatus::PendingReview,
        review_state: EvidenceAppendProposalReviewState::PendingReview,
        proposed_evidence_class: EvidenceClass::DesignNote,
        proposed_claim_boundary: ClaimBoundary::Level0DesignNote,
        proposed_provenance_summary: vec![
            format!("source_candidate={}", draft.source_result_candidate_id),
            format!("source_pack={}", draft.source_benchmark_pack_id),
            format!("dry_run_plan={}", draft.dry_run_plan_id),
        ],
        proposed_artifact_refs: draft.artifact_refs.clone(),
        validation_report_digest: draft.validation_report_digest.clone(),
        blocking_issues: Vec::new(),
        reviewer_checklist: EvidenceReviewChecklist::default(),
        claims_accepted_evidence: false,
        notes: vec![
            "Evidence append proposals are not accepted evidence.".to_string(),
            "Synthetic result candidates are not benchmark results.".to_string(),
        ],
    })
}

/// Validate an evidence append proposal.
pub fn validate_evidence_append_proposal(
    proposal: &EvidenceAppendProposal,
) -> EvidenceAppendProposalValidation {
    let mut issues = Vec::new();
    if proposal.id.trim().is_empty() {
        issues.push(EvidenceAppendProposalValidationIssue::error(
            "proposal.id",
            "evidence append proposal id is empty",
        ));
    }
    if proposal.source_normalized_draft_id.trim().is_empty() {
        issues.push(EvidenceAppendProposalValidationIssue::error(
            "proposal.source_normalized_draft_id",
            "source normalized draft id is empty",
        ));
    }
    if proposal.proposed_evidence_class != EvidenceClass::DesignNote {
        issues.push(EvidenceAppendProposalValidationIssue::error(
            "proposal.proposed_evidence_class",
            "Phase I proposals may propose DesignNote evidence class only",
        ));
    }
    if proposal.proposed_claim_boundary != ClaimBoundary::Level0DesignNote {
        issues.push(EvidenceAppendProposalValidationIssue::error(
            "proposal.proposed_claim_boundary",
            "Phase I proposal artifacts must remain Level0DesignNote",
        ));
    }
    if proposal.claims_accepted_evidence {
        issues.push(EvidenceAppendProposalValidationIssue::error(
            "proposal.claims_accepted_evidence",
            "evidence append proposals are not accepted evidence",
        ));
    }
    for (index, artifact_ref) in proposal.proposed_artifact_refs.iter().enumerate() {
        if artifact_ref.artifact_ref.trim().is_empty() {
            issues.push(EvidenceAppendProposalValidationIssue::error(
                format!("proposal.proposed_artifact_refs[{index}].artifact_ref"),
                "proposed artifact ref is empty",
            ));
        }
    }
    for (index, issue) in proposal.blocking_issues.iter().enumerate() {
        if issue.severity == ExternalValidationIssueSeverity::Error {
            issues.push(EvidenceAppendProposalValidationIssue::error(
                format!("proposal.blocking_issues[{index}]"),
                "proposal has unresolved blocking import issues",
            ));
        }
        if matches!(
            issue.kind,
            SyntheticImportValidationIssueKind::OfficialClaimDetected
                | SyntheticImportValidationIssueKind::FormalClaimDetected
                | SyntheticImportValidationIssueKind::SoundnessClaimDetected
                | SyntheticImportValidationIssueKind::ClaimBoundaryTooHigh
        ) {
            issues.push(EvidenceAppendProposalValidationIssue::error(
                format!("proposal.blocking_issues[{index}].kind"),
                "proposal contains a blocked claim-boundary import issue",
            ));
        }
    }
    for (index, note) in proposal.notes.iter().enumerate() {
        if contains_forbidden_claim_text(note) {
            issues.push(EvidenceAppendProposalValidationIssue::error(
                format!("proposal.notes[{index}]"),
                "proposal notes contain a forbidden claim",
            ));
        }
    }
    for (index, summary) in proposal.proposed_provenance_summary.iter().enumerate() {
        if contains_forbidden_claim_text(summary) {
            issues.push(EvidenceAppendProposalValidationIssue::error(
                format!("proposal.proposed_provenance_summary[{index}]"),
                "proposal provenance summary contains a forbidden claim",
            ));
        }
    }
    for (index, requirement) in proposal.reviewer_checklist.requirements.iter().enumerate() {
        for (note_index, note) in requirement.notes.iter().enumerate() {
            if contains_forbidden_claim_text(note) {
                issues.push(EvidenceAppendProposalValidationIssue::error(
                    format!(
                        "proposal.reviewer_checklist.requirements[{index}].notes[{note_index}]"
                    ),
                    "review requirement notes contain a forbidden claim",
                ));
            }
        }
    }
    for (index, finding) in proposal.reviewer_checklist.findings.iter().enumerate() {
        if contains_forbidden_claim_text(&finding.message) {
            issues.push(EvidenceAppendProposalValidationIssue::error(
                format!("proposal.reviewer_checklist.findings[{index}].message"),
                "review finding contains a forbidden claim",
            ));
        }
    }

    EvidenceAppendProposalValidation {
        valid: issues.is_empty(),
        issues,
    }
}

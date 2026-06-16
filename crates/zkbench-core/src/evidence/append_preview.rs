//! Evidence ledger append preview primitives.
//!
//! Append previews simulate a future ledger transaction. They do not mutate an
//! `EvidenceLedger` and they do not turn candidates into accepted evidence.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::candidate::{
    validate_evidence_record_candidate, EvidenceRecordCandidate, EvidenceRecordCandidateId,
};
use super::digest::compute_artifact_digest;
use super::{
    ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary, EvidenceClass, EvidenceLedger,
    EvidenceLedgerSummary, EvidenceLedgerSummaryCount,
};

/// Append preview id.
pub type EvidenceAppendPreviewId = String;

/// Append preview version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendPreviewVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for EvidenceAppendPreviewVersion {
    fn default() -> Self {
        Self {
            value: "phase-j-evidence-append-preview-v0".to_string(),
        }
    }
}

/// Append preview status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceAppendPreviewStatus {
    /// Preview is valid metadata only.
    PreviewOnly,
    /// Preview is blocked by validation.
    Blocked,
    /// Preview is superseded.
    Superseded,
}

/// Append preview validation issue kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EvidenceAppendPreviewIssueKind {
    /// Required id was empty.
    EmptyId,
    /// Source candidate was invalid.
    InvalidCandidate,
    /// Claim boundary exceeded Phase J caps.
    ClaimBoundaryTooHigh,
    /// Preview tried to imply ledger mutation.
    MutatesLedger,
    /// Forbidden claim language was detected.
    ForbiddenClaimLanguage,
}

/// Append preview validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendPreviewValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
    /// Issue kind.
    pub kind: EvidenceAppendPreviewIssueKind,
}

/// Append preview validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendPreviewValidation {
    /// True when no validation issues were found.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<EvidenceAppendPreviewValidationIssue>,
}

/// One projected ledger append entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceLedgerAppendPreviewEntry {
    /// Candidate id.
    pub candidate_id: EvidenceRecordCandidateId,
    /// Proposed evidence class.
    pub proposed_evidence_class: EvidenceClass,
    /// Proposed claim boundary.
    pub proposed_claim_boundary: ClaimBoundary,
    /// Digest of the proposed candidate record.
    pub proposed_record_digest: ArtifactDigest,
    /// Digest of the projected ledger entry.
    pub projected_entry_digest: ArtifactDigest,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Projected ledger append transaction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceLedgerAppendTransactionPreview {
    /// Optional target ledger id.
    #[serde(default)]
    pub target_ledger_id: Option<String>,
    /// Current chain digest before the simulated append.
    #[serde(default)]
    pub current_ledger_digest: Option<ArtifactDigest>,
    /// Candidate entries projected by this preview.
    pub candidate_entries: Vec<EvidenceLedgerAppendPreviewEntry>,
    /// Projected summary after the simulated append.
    pub projected_ledger_summary: EvidenceLedgerSummary,
    /// Validation issues recorded inside the transaction preview.
    #[serde(default)]
    pub validation_issues: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Evidence append preview.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendPreview {
    /// Preview id.
    pub id: EvidenceAppendPreviewId,
    /// Preview version.
    pub version: EvidenceAppendPreviewVersion,
    /// Source candidate id.
    pub source_candidate_id: EvidenceRecordCandidateId,
    /// Optional target evidence ledger id.
    #[serde(default)]
    pub target_evidence_ledger_id: Option<String>,
    /// Proposed append entries.
    pub proposed_append_entries: Vec<EvidenceLedgerAppendPreviewEntry>,
    /// Validation result.
    pub validation: EvidenceAppendPreviewValidation,
    /// Claim boundary of this preview artifact.
    pub claim_boundary: ClaimBoundary,
    /// Preview status.
    pub status: EvidenceAppendPreviewStatus,
    /// Transaction preview.
    pub transaction_preview: EvidenceLedgerAppendTransactionPreview,
    /// True would be invalid; previews never mutate ledgers.
    pub mutates_evidence_ledger: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl EvidenceAppendPreview {
    /// Append previews never mutate evidence ledgers.
    pub fn mutates_ledger(&self) -> bool {
        false
    }
}

/// Create an append preview from a candidate without mutating a ledger.
pub fn create_evidence_append_preview(
    candidate: &EvidenceRecordCandidate,
    ledger: Option<&EvidenceLedger>,
) -> Result<EvidenceAppendPreview> {
    let candidate_validation = validate_evidence_record_candidate(candidate);
    if !candidate_validation.valid {
        return Err(ZkBenchError::evidence_append_preview(
            "append_preview.candidate",
            format!("candidate is invalid: {:?}", candidate_validation.issues),
        ));
    }
    let previous_digest = ledger
        .and_then(|ledger| ledger.entries.last())
        .map(|entry| entry.entry_digest.clone());
    let proposed_record_digest = compute_artifact_digest(
        candidate,
        Some(ArtifactKind::EvidenceLedger),
        Some(ArtifactRole::Evidence),
    )?;
    let projected_entry_digest = compute_artifact_digest(
        &ProjectedEntryDigestInput {
            candidate_id: &candidate.id,
            proposed_record_digest: &proposed_record_digest,
            previous_digest: previous_digest.as_ref(),
        },
        Some(ArtifactKind::EvidenceLedger),
        Some(ArtifactRole::Digest),
    )?;
    let entry = EvidenceLedgerAppendPreviewEntry {
        candidate_id: candidate.id.clone(),
        proposed_evidence_class: candidate.proposed_evidence_class.clone(),
        proposed_claim_boundary: candidate.proposed_claim_boundary,
        proposed_record_digest,
        projected_entry_digest,
        notes: vec!["projected entry only".to_string()],
    };
    let projected_summary = projected_summary(ledger, candidate);
    let transaction_preview = EvidenceLedgerAppendTransactionPreview {
        target_ledger_id: None,
        current_ledger_digest: previous_digest,
        candidate_entries: vec![entry.clone()],
        projected_ledger_summary: projected_summary,
        validation_issues: Vec::new(),
        notes: vec!["transaction preview only".to_string()],
    };
    let mut preview = EvidenceAppendPreview {
        id: format!("append_preview_{}", candidate.id),
        version: EvidenceAppendPreviewVersion::default(),
        source_candidate_id: candidate.id.clone(),
        target_evidence_ledger_id: None,
        proposed_append_entries: vec![entry],
        validation: EvidenceAppendPreviewValidation {
            valid: true,
            issues: Vec::new(),
        },
        claim_boundary: ClaimBoundary::Level0DesignNote,
        status: EvidenceAppendPreviewStatus::PreviewOnly,
        transaction_preview,
        mutates_evidence_ledger: false,
        notes: vec![
            "Append previews are transaction metadata only.".to_string(),
            "Future manual append is required before any EvidenceLedger mutation.".to_string(),
        ],
    };
    preview.validation = validate_evidence_append_preview(&preview);
    if preview.validation.valid {
        Ok(preview)
    } else {
        Err(ZkBenchError::evidence_append_preview(
            "append_preview",
            format!(
                "created preview failed validation: {:?}",
                preview.validation.issues
            ),
        ))
    }
}

/// Validate an append preview.
pub fn validate_evidence_append_preview(
    preview: &EvidenceAppendPreview,
) -> EvidenceAppendPreviewValidation {
    let mut issues = Vec::new();
    if preview.id.trim().is_empty() {
        issues.push(issue(
            "preview.id",
            "append preview id is empty",
            EvidenceAppendPreviewIssueKind::EmptyId,
        ));
    }
    if preview.source_candidate_id.trim().is_empty() {
        issues.push(issue(
            "preview.source_candidate_id",
            "source candidate id is empty",
            EvidenceAppendPreviewIssueKind::EmptyId,
        ));
    }
    if preview.claim_boundary > ClaimBoundary::Level0DesignNote {
        issues.push(issue(
            "preview.claim_boundary",
            "append preview artifacts must remain Level0DesignNote",
            EvidenceAppendPreviewIssueKind::ClaimBoundaryTooHigh,
        ));
    }
    if preview.mutates_evidence_ledger {
        issues.push(issue(
            "preview.mutates_evidence_ledger",
            "append preview must not mutate EvidenceLedger",
            EvidenceAppendPreviewIssueKind::MutatesLedger,
        ));
    }
    for (index, entry) in preview.proposed_append_entries.iter().enumerate() {
        if entry.proposed_claim_boundary >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact {
            issues.push(issue(
                format!("preview.proposed_append_entries[{index}].proposed_claim_boundary"),
                "append preview cannot propose Level2+ actual evidence",
                EvidenceAppendPreviewIssueKind::ClaimBoundaryTooHigh,
            ));
        }
    }
    scan_preview_text(preview, &mut issues);
    EvidenceAppendPreviewValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Serialize an append preview to pretty JSON.
pub fn serialize_evidence_append_preview_json(preview: &EvidenceAppendPreview) -> Result<String> {
    serde_json::to_string_pretty(preview).map_err(|error| {
        ZkBenchError::serialization("serialize_evidence_append_preview_json", error.to_string())
    })
}

/// Deserialize an append preview from JSON.
pub fn deserialize_evidence_append_preview_json(json: &str) -> Result<EvidenceAppendPreview> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_evidence_append_preview_json",
            error.to_string(),
        )
    })
}

fn projected_summary(
    ledger: Option<&EvidenceLedger>,
    candidate: &EvidenceRecordCandidate,
) -> EvidenceLedgerSummary {
    let existing_entries = ledger.map(|ledger| ledger.entries.len()).unwrap_or(0);
    let mut class_counts = BTreeMap::<String, usize>::new();
    let mut boundary_counts = BTreeMap::<String, usize>::new();
    if let Some(ledger) = ledger {
        for count in &ledger.summary.evidence_class_counts {
            class_counts.insert(count.name.clone(), count.count);
        }
        for count in &ledger.summary.claim_boundary_counts {
            boundary_counts.insert(count.name.clone(), count.count);
        }
    }
    *class_counts
        .entry(format!("{:?}", candidate.proposed_evidence_class))
        .or_insert(0) += 1;
    *boundary_counts
        .entry(candidate.proposed_claim_boundary.to_string())
        .or_insert(0) += 1;
    EvidenceLedgerSummary {
        entry_count: existing_entries + 1,
        evidence_class_counts: class_counts
            .into_iter()
            .map(|(name, count)| EvidenceLedgerSummaryCount { name, count })
            .collect(),
        claim_boundary_counts: boundary_counts
            .into_iter()
            .map(|(name, count)| EvidenceLedgerSummaryCount { name, count })
            .collect(),
    }
}

fn scan_preview_text(
    preview: &EvidenceAppendPreview,
    issues: &mut Vec<EvidenceAppendPreviewValidationIssue>,
) {
    for (index, note) in preview.notes.iter().enumerate() {
        push_claim_issue(format!("preview.notes[{index}]"), note, issues);
    }
    for (index, note) in preview.transaction_preview.notes.iter().enumerate() {
        push_claim_issue(
            format!("preview.transaction_preview.notes[{index}]"),
            note,
            issues,
        );
    }
}

fn push_claim_issue(
    path: String,
    text: &str,
    issues: &mut Vec<EvidenceAppendPreviewValidationIssue>,
) {
    if crate::external_runner::contains_forbidden_claim_text(text) {
        issues.push(issue(
            path,
            "append preview text contains forbidden claim language",
            EvidenceAppendPreviewIssueKind::ForbiddenClaimLanguage,
        ));
    }
}

fn issue(
    path: impl Into<String>,
    message: impl Into<String>,
    kind: EvidenceAppendPreviewIssueKind,
) -> EvidenceAppendPreviewValidationIssue {
    EvidenceAppendPreviewValidationIssue {
        path: path.into(),
        message: message.into(),
        kind,
    }
}

#[derive(Debug, Serialize)]
struct ProjectedEntryDigestInput<'a> {
    candidate_id: &'a str,
    proposed_record_digest: &'a ArtifactDigest,
    previous_digest: Option<&'a ArtifactDigest>,
}

//! Evidence review ledger primitives.
//!
//! This ledger records review decisions and append previews. It is separate
//! from `EvidenceLedger` and does not record accepted benchmark evidence.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::append_preview::{validate_evidence_append_preview, EvidenceAppendPreview};
use super::digest::compute_artifact_digest;
use super::review::{validate_evidence_review_decision, EvidenceReviewDecision};
use super::{ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary};

/// Review ledger digest alias.
pub type EvidenceReviewLedgerDigest = ArtifactDigest;

/// Review ledger version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewLedgerVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for EvidenceReviewLedgerVersion {
    fn default() -> Self {
        Self {
            value: "phase-j-evidence-review-ledger-v0".to_string(),
        }
    }
}

/// Review ledger entry version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewLedgerEntryVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for EvidenceReviewLedgerEntryVersion {
    fn default() -> Self {
        Self {
            value: "phase-j-evidence-review-ledger-entry-v0".to_string(),
        }
    }
}

/// Subject of a review ledger entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvidenceReviewLedgerEntrySubject {
    /// Manual review decision.
    ReviewDecision(EvidenceReviewDecision),
    /// Append preview.
    AppendPreview(EvidenceAppendPreview),
}

/// Review ledger entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewLedgerEntry {
    /// Entry version.
    pub version: EvidenceReviewLedgerEntryVersion,
    /// Sequence number.
    pub sequence_number: u64,
    /// Entry subject.
    pub subject: EvidenceReviewLedgerEntrySubject,
    /// Previous entry digest.
    #[serde(default)]
    pub previous_digest: Option<EvidenceReviewLedgerDigest>,
    /// Entry digest.
    pub entry_digest: EvidenceReviewLedgerDigest,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Review ledger summary count.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewLedgerSummaryCount {
    /// Count name.
    pub name: String,
    /// Count.
    pub count: usize,
}

/// Review ledger summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct EvidenceReviewLedgerSummary {
    /// Entry count.
    pub entry_count: usize,
    /// Subject kind counts.
    pub subject_kind_counts: Vec<EvidenceReviewLedgerSummaryCount>,
    /// Decision kind counts.
    pub decision_kind_counts: Vec<EvidenceReviewLedgerSummaryCount>,
    /// Decision status counts.
    pub decision_status_counts: Vec<EvidenceReviewLedgerSummaryCount>,
    /// Preview status counts.
    pub preview_status_counts: Vec<EvidenceReviewLedgerSummaryCount>,
}

impl EvidenceReviewLedgerSummary {
    /// Build a summary from entries.
    pub fn from_entries(entries: &[EvidenceReviewLedgerEntry]) -> Self {
        let mut subject_kind_counts = BTreeMap::<String, usize>::new();
        let mut decision_kind_counts = BTreeMap::<String, usize>::new();
        let mut decision_status_counts = BTreeMap::<String, usize>::new();
        let mut preview_status_counts = BTreeMap::<String, usize>::new();
        for entry in entries {
            match &entry.subject {
                EvidenceReviewLedgerEntrySubject::ReviewDecision(decision) => {
                    *subject_kind_counts
                        .entry("ReviewDecision".to_string())
                        .or_insert(0) += 1;
                    *decision_kind_counts
                        .entry(format!("{:?}", decision.decision_kind))
                        .or_insert(0) += 1;
                    *decision_status_counts
                        .entry(format!("{:?}", decision.decision_status))
                        .or_insert(0) += 1;
                }
                EvidenceReviewLedgerEntrySubject::AppendPreview(preview) => {
                    *subject_kind_counts
                        .entry("AppendPreview".to_string())
                        .or_insert(0) += 1;
                    *preview_status_counts
                        .entry(format!("{:?}", preview.status))
                        .or_insert(0) += 1;
                }
            }
        }
        Self {
            entry_count: entries.len(),
            subject_kind_counts: counts(subject_kind_counts),
            decision_kind_counts: counts(decision_kind_counts),
            decision_status_counts: counts(decision_status_counts),
            preview_status_counts: counts(preview_status_counts),
        }
    }
}

/// Review ledger validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewLedgerValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
}

/// Review ledger validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewLedgerValidation {
    /// True when validation found no issues.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<EvidenceReviewLedgerValidationIssue>,
    /// Recomputed summary.
    pub summary: EvidenceReviewLedgerSummary,
}

/// Local review ledger.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceReviewLedger {
    /// Ledger id.
    pub id: String,
    /// Ledger version.
    pub version: EvidenceReviewLedgerVersion,
    /// Review ledger entries.
    pub entries: Vec<EvidenceReviewLedgerEntry>,
    /// Cached summary.
    pub summary: EvidenceReviewLedgerSummary,
    /// Claim boundary of this ledger artifact.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for EvidenceReviewLedger {
    fn default() -> Self {
        Self::new("phase_j_review_ledger")
    }
}

impl EvidenceReviewLedger {
    /// Create an empty review ledger.
    pub fn new(id: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            version: EvidenceReviewLedgerVersion::default(),
            entries: Vec::new(),
            summary: EvidenceReviewLedgerSummary::default(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec![
                "Review ledgers record policy metadata only.".to_string(),
                "Review ledgers do not mutate EvidenceLedger.".to_string(),
            ],
        }
    }

    /// Append a review decision to the review ledger.
    pub fn append_review_decision(&mut self, decision: EvidenceReviewDecision) -> Result<()> {
        self.append_subject(EvidenceReviewLedgerEntrySubject::ReviewDecision(decision))
    }

    /// Append an append preview to the review ledger.
    pub fn append_append_preview(&mut self, preview: EvidenceAppendPreview) -> Result<()> {
        self.append_subject(EvidenceReviewLedgerEntrySubject::AppendPreview(preview))
    }

    /// Validate this review ledger.
    pub fn validate(&self) -> EvidenceReviewLedgerValidation {
        let mut issues = Vec::new();
        if self.id.trim().is_empty() {
            issues.push(issue("ledger.id", "review ledger id is empty"));
        }
        if self.claim_boundary > ClaimBoundary::Level0DesignNote {
            issues.push(issue(
                "ledger.claim_boundary",
                "review ledger artifacts must remain Level0DesignNote",
            ));
        }
        for (index, note) in self.notes.iter().enumerate() {
            if crate::external_runner::contains_forbidden_claim_text(note) {
                issues.push(issue(
                    format!("ledger.notes[{index}]"),
                    "review ledger notes contain forbidden claim language",
                ));
            }
        }
        let mut previous_digest = None;
        for (index, entry) in self.entries.iter().enumerate() {
            for (note_index, note) in entry.notes.iter().enumerate() {
                if crate::external_runner::contains_forbidden_claim_text(note) {
                    issues.push(issue(
                        format!("ledger.entries[{index}].notes[{note_index}]"),
                        "review ledger entry notes contain forbidden claim language",
                    ));
                }
            }
            if entry.sequence_number != index as u64 {
                issues.push(issue(
                    format!("ledger.entries[{index}].sequence_number"),
                    "sequence number does not match entry index",
                ));
            }
            if entry.previous_digest != previous_digest {
                issues.push(issue(
                    format!("ledger.entries[{index}].previous_digest"),
                    "previous digest does not match prior entry",
                ));
            }
            match digest_entry(
                entry.sequence_number,
                entry.previous_digest.as_ref(),
                &entry.subject,
            ) {
                Ok(expected) if expected == entry.entry_digest => {}
                Ok(_) => issues.push(issue(
                    format!("ledger.entries[{index}].entry_digest"),
                    "entry digest mismatch",
                )),
                Err(error) => issues.push(issue(
                    format!("ledger.entries[{index}].entry_digest"),
                    error.to_string(),
                )),
            }
            match &entry.subject {
                EvidenceReviewLedgerEntrySubject::ReviewDecision(decision) => {
                    let report = validate_evidence_review_decision(decision);
                    if !report.valid {
                        issues.push(issue(
                            format!("ledger.entries[{index}].subject.review_decision"),
                            format!("review decision invalid: {:?}", report.blocking_issues),
                        ));
                    }
                }
                EvidenceReviewLedgerEntrySubject::AppendPreview(preview) => {
                    let validation = validate_evidence_append_preview(preview);
                    if !validation.valid {
                        issues.push(issue(
                            format!("ledger.entries[{index}].subject.append_preview"),
                            format!("append preview invalid: {:?}", validation.issues),
                        ));
                    }
                }
            }
            previous_digest = Some(entry.entry_digest.clone());
        }
        let summary = EvidenceReviewLedgerSummary::from_entries(&self.entries);
        if summary != self.summary {
            issues.push(issue(
                "ledger.summary",
                "cached summary does not match entries",
            ));
        }
        EvidenceReviewLedgerValidation {
            valid: issues.is_empty(),
            issues,
            summary,
        }
    }

    fn append_subject(&mut self, subject: EvidenceReviewLedgerEntrySubject) -> Result<()> {
        validate_subject(&subject)?;
        let sequence_number = self.entries.len() as u64;
        let previous_digest = self.entries.last().map(|entry| entry.entry_digest.clone());
        let entry_digest = digest_entry(sequence_number, previous_digest.as_ref(), &subject)?;
        let entry = EvidenceReviewLedgerEntry {
            version: EvidenceReviewLedgerEntryVersion::default(),
            sequence_number,
            subject,
            previous_digest,
            entry_digest,
            notes: Vec::new(),
        };
        self.entries.push(entry);
        self.summary = EvidenceReviewLedgerSummary::from_entries(&self.entries);
        Ok(())
    }
}

/// Serialize a review ledger to pretty JSON.
pub fn serialize_evidence_review_ledger_json(ledger: &EvidenceReviewLedger) -> Result<String> {
    serde_json::to_string_pretty(ledger).map_err(|error| {
        ZkBenchError::serialization("serialize_evidence_review_ledger_json", error.to_string())
    })
}

/// Deserialize a review ledger from JSON.
pub fn deserialize_evidence_review_ledger_json(json: &str) -> Result<EvidenceReviewLedger> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_evidence_review_ledger_json", error.to_string())
    })
}

fn validate_subject(subject: &EvidenceReviewLedgerEntrySubject) -> Result<()> {
    match subject {
        EvidenceReviewLedgerEntrySubject::ReviewDecision(decision) => {
            let report = validate_evidence_review_decision(decision);
            if report.valid {
                Ok(())
            } else {
                Err(ZkBenchError::evidence_review_ledger(
                    "review_ledger.review_decision",
                    format!("review decision invalid: {:?}", report.blocking_issues),
                ))
            }
        }
        EvidenceReviewLedgerEntrySubject::AppendPreview(preview) => {
            let validation = validate_evidence_append_preview(preview);
            if validation.valid {
                Ok(())
            } else {
                Err(ZkBenchError::evidence_review_ledger(
                    "review_ledger.append_preview",
                    format!("append preview invalid: {:?}", validation.issues),
                ))
            }
        }
    }
}

#[derive(Debug, Serialize)]
struct ReviewLedgerEntryDigestInput<'a> {
    sequence_number: u64,
    previous_digest: Option<&'a EvidenceReviewLedgerDigest>,
    subject: &'a EvidenceReviewLedgerEntrySubject,
}

fn digest_entry(
    sequence_number: u64,
    previous_digest: Option<&EvidenceReviewLedgerDigest>,
    subject: &EvidenceReviewLedgerEntrySubject,
) -> Result<EvidenceReviewLedgerDigest> {
    compute_artifact_digest(
        &ReviewLedgerEntryDigestInput {
            sequence_number,
            previous_digest,
            subject,
        },
        Some(ArtifactKind::EvidenceLedger),
        Some(ArtifactRole::Digest),
    )
}

fn issue(
    path: impl Into<String>,
    message: impl Into<String>,
) -> EvidenceReviewLedgerValidationIssue {
    EvidenceReviewLedgerValidationIssue {
        path: path.into(),
        message: message.into(),
    }
}

fn counts(map: BTreeMap<String, usize>) -> Vec<EvidenceReviewLedgerSummaryCount> {
    map.into_iter()
        .map(|(name, count)| EvidenceReviewLedgerSummaryCount { name, count })
        .collect()
}

//! Persistent local Evidence Ledger.
//!
//! The digest chain is a local integrity check only. It is not tamper-proof,
//! not a Merkle proof, and not independent reproduction.

use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::artifact::{ArtifactDigest, ArtifactKind, ArtifactRole};
use super::digest::compute_artifact_digest;
use super::{ClaimBoundary, EvidenceClass, EvidenceRecord};

/// Evidence ledger schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceLedgerVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for EvidenceLedgerVersion {
    fn default() -> Self {
        Self {
            value: "phase-f-local-ledger-v0".to_string(),
        }
    }
}

/// Evidence append policy.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum EvidenceAppendPolicy {
    /// Reject actual evidence above Level1LocalReplay.
    #[default]
    RejectAboveLevel1Actual,
    /// Allow future metadata. This phase does not use it for actual evidence.
    AllowFutureMetadata,
}

/// Alias for the current ledger digest.
pub type EvidenceChainDigest = ArtifactDigest;

/// Persistent evidence ledger.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceLedger {
    /// Ledger schema version.
    pub version: EvidenceLedgerVersion,
    /// Ledger entries.
    pub entries: Vec<EvidenceLedgerEntry>,
    /// Cached summary.
    pub summary: EvidenceLedgerSummary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for EvidenceLedger {
    fn default() -> Self {
        Self::new()
    }
}

impl EvidenceLedger {
    /// Create a new empty ledger.
    pub fn new() -> Self {
        Self {
            version: EvidenceLedgerVersion::default(),
            entries: Vec::new(),
            summary: EvidenceLedgerSummary::default(),
            notes: vec![
                "Evidence ledger digest validation is a local integrity check, not independent reproduction.".to_string(),
            ],
        }
    }

    /// Append one evidence record under the default append policy.
    pub fn append(&mut self, record: EvidenceRecord) -> Result<()> {
        self.append_with_policy(record, EvidenceAppendPolicy::default())
    }

    /// Append one evidence record.
    pub fn append_with_policy(
        &mut self,
        record: EvidenceRecord,
        policy: EvidenceAppendPolicy,
    ) -> Result<()> {
        if policy == EvidenceAppendPolicy::RejectAboveLevel1Actual
            && record.claim_boundary > ClaimBoundary::Level1LocalReplay
        {
            return Err(ZkBenchError::evidence_ledger(
                "ledger.append.claim_boundary",
                format!(
                    "actual evidence claim boundary {:?} exceeds Level1LocalReplay",
                    record.claim_boundary
                ),
            ));
        }

        let sequence_number = self.entries.len() as u64;
        let previous_digest = self.entries.last().map(|entry| entry.entry_digest.clone());
        let entry_digest = digest_entry(sequence_number, previous_digest.as_ref(), &record)?;
        let entry = EvidenceLedgerEntry {
            sequence_number,
            evidence_record: record,
            previous_digest,
            entry_digest,
            notes: Vec::new(),
        };
        self.entries.push(entry);
        self.summary = EvidenceLedgerSummary::from_entries(&self.entries);
        Ok(())
    }

    /// Append evidence records from a replay result.
    pub fn append_replay_result(&mut self, result: &crate::replay::ReplayResult) -> Result<()> {
        for record in &result.evidence_records {
            self.append(record.clone())?;
        }
        Ok(())
    }

    /// Save ledger as pretty JSON.
    pub fn save_json(&self, path: impl AsRef<Path>) -> Result<()> {
        let json = serde_json::to_string_pretty(self).map_err(|error| {
            ZkBenchError::serialization("evidence_ledger.save_json", error.to_string())
        })?;
        fs::write(path.as_ref(), json).map_err(|error| {
            ZkBenchError::evidence_ledger(path.as_ref().display().to_string(), error.to_string())
        })
    }

    /// Load ledger from JSON.
    pub fn load_json(path: impl AsRef<Path>) -> Result<Self> {
        let json = fs::read_to_string(path.as_ref()).map_err(|error| {
            ZkBenchError::evidence_ledger(path.as_ref().display().to_string(), error.to_string())
        })?;
        serde_json::from_str(&json).map_err(|error| {
            ZkBenchError::deserialization("evidence_ledger.load_json", error.to_string())
        })
    }

    /// Validate the local digest chain.
    pub fn validate(&self) -> EvidenceLedgerValidation {
        let mut errors = Vec::new();
        for (index, note) in self.notes.iter().enumerate() {
            push_forbidden_claim_text_error(
                self.entries.len() as u64,
                format!("ledger.notes[{index}]"),
                note,
                &mut errors,
            );
        }
        let mut previous_digest = None;
        for (index, entry) in self.entries.iter().enumerate() {
            for (note_index, note) in entry.notes.iter().enumerate() {
                push_forbidden_claim_text_error(
                    entry.sequence_number,
                    format!("ledger.entries[{index}].notes[{note_index}]"),
                    note,
                    &mut errors,
                );
            }
            for (note_index, note) in entry.evidence_record.notes.iter().enumerate() {
                push_forbidden_claim_text_error(
                    entry.sequence_number,
                    format!("ledger.entries[{index}].evidence_record.notes[{note_index}]"),
                    note,
                    &mut errors,
                );
            }
            for (note_index, note) in entry.evidence_record.provenance.notes.iter().enumerate() {
                push_forbidden_claim_text_error(
                    entry.sequence_number,
                    format!(
                        "ledger.entries[{index}].evidence_record.provenance.notes[{note_index}]"
                    ),
                    note,
                    &mut errors,
                );
            }
            if entry.sequence_number != index as u64 {
                errors.push(EvidenceLedgerValidationError {
                    sequence_number: entry.sequence_number,
                    message: format!(
                        "sequence number {} does not match index {}",
                        entry.sequence_number, index
                    ),
                });
            }
            if entry.previous_digest != previous_digest {
                errors.push(EvidenceLedgerValidationError {
                    sequence_number: entry.sequence_number,
                    message: "previous digest does not match prior entry".to_string(),
                });
            }
            match digest_entry(
                entry.sequence_number,
                entry.previous_digest.as_ref(),
                &entry.evidence_record,
            ) {
                Ok(expected) if expected == entry.entry_digest => {}
                Ok(_) => errors.push(EvidenceLedgerValidationError {
                    sequence_number: entry.sequence_number,
                    message: "entry digest mismatch".to_string(),
                }),
                Err(error) => errors.push(EvidenceLedgerValidationError {
                    sequence_number: entry.sequence_number,
                    message: error.to_string(),
                }),
            }
            if entry.evidence_record.claim_boundary > ClaimBoundary::Level1LocalReplay {
                errors.push(EvidenceLedgerValidationError {
                    sequence_number: entry.sequence_number,
                    message: "actual evidence exceeds Level1LocalReplay".to_string(),
                });
            }
            previous_digest = Some(entry.entry_digest.clone());
        }
        let summary = EvidenceLedgerSummary::from_entries(&self.entries);
        if summary != self.summary {
            errors.push(EvidenceLedgerValidationError {
                sequence_number: self.entries.len() as u64,
                message: "cached summary does not match entries".to_string(),
            });
        }
        EvidenceLedgerValidation {
            valid: errors.is_empty(),
            errors,
            summary,
        }
    }
}

/// Evidence ledger entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceLedgerEntry {
    /// Sequence number.
    pub sequence_number: u64,
    /// Evidence record.
    pub evidence_record: EvidenceRecord,
    /// Previous digest.
    #[serde(default)]
    pub previous_digest: Option<ArtifactDigest>,
    /// Entry digest.
    pub entry_digest: ArtifactDigest,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Evidence ledger summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct EvidenceLedgerSummary {
    /// Entry count.
    pub entry_count: usize,
    /// Evidence class counts.
    pub evidence_class_counts: Vec<EvidenceLedgerSummaryCount>,
    /// Claim boundary counts.
    pub claim_boundary_counts: Vec<EvidenceLedgerSummaryCount>,
}

impl EvidenceLedgerSummary {
    /// Build summary from entries.
    pub fn from_entries(entries: &[EvidenceLedgerEntry]) -> Self {
        let mut class_counts = BTreeMap::new();
        let mut boundary_counts = BTreeMap::new();
        for entry in entries {
            *class_counts
                .entry(format!("{:?}", entry.evidence_record.evidence_class))
                .or_insert(0usize) += 1;
            *boundary_counts
                .entry(entry.evidence_record.claim_boundary.to_string())
                .or_insert(0usize) += 1;
        }
        Self {
            entry_count: entries.len(),
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
}

/// Named count used in summaries.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceLedgerSummaryCount {
    /// Count name.
    pub name: String,
    /// Count.
    pub count: usize,
}

/// Evidence ledger validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceLedgerValidation {
    /// True when validation found no errors.
    pub valid: bool,
    /// Validation errors.
    pub errors: Vec<EvidenceLedgerValidationError>,
    /// Recomputed summary.
    pub summary: EvidenceLedgerSummary,
}

/// Evidence ledger validation error.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceLedgerValidationError {
    /// Sequence number associated with the error.
    pub sequence_number: u64,
    /// Error message.
    pub message: String,
}

#[derive(Debug, Serialize)]
struct EntryDigestInput<'a> {
    sequence_number: u64,
    previous_digest: Option<&'a ArtifactDigest>,
    evidence_record: &'a EvidenceRecord,
}

fn digest_entry(
    sequence_number: u64,
    previous_digest: Option<&ArtifactDigest>,
    evidence_record: &EvidenceRecord,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        &EntryDigestInput {
            sequence_number,
            previous_digest,
            evidence_record,
        },
        Some(ArtifactKind::EvidenceLedger),
        Some(ArtifactRole::Digest),
    )
}

fn push_forbidden_claim_text_error(
    sequence_number: u64,
    path: String,
    text: &str,
    errors: &mut Vec<EvidenceLedgerValidationError>,
) {
    if contains_forbidden_evidence_ledger_claim_text(text) {
        errors.push(EvidenceLedgerValidationError {
            sequence_number,
            message: format!("{path} contains forbidden claim language"),
        });
    }
}

fn contains_forbidden_evidence_ledger_claim_text(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    if lowered.contains("not official benchmark evidence")
        || lowered.contains("not official benchmark result")
        || lowered.contains("no official benchmark evidence")
        || lowered.contains("no official benchmark result")
        || lowered.contains("does not create official benchmark evidence")
        || lowered.contains("does not create official benchmark result")
    {
        return false;
    }
    crate::external_runner::contains_forbidden_claim_text(text)
}

#[allow(dead_code)]
fn _class_is_used_for_docs(_: EvidenceClass) {}

//! Local proposal ledger for evidence append proposals.
//!
//! This ledger is deliberately separate from EvidenceLedger. It records review
//! candidates and local digest-chain integrity only.

use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary,
};

use super::proposal::{
    validate_evidence_append_proposal, EvidenceAppendProposal, EvidenceAppendProposalReviewState,
    EvidenceAppendProposalStatus,
};
use super::validation::contains_forbidden_claim_text;

/// Alias for proposal ledger entry digests.
pub type EvidenceAppendProposalDigest = ArtifactDigest;

/// Proposal ledger version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposalLedgerVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for EvidenceAppendProposalLedgerVersion {
    fn default() -> Self {
        Self {
            value: "phase-i-evidence-append-proposal-ledger-v0".to_string(),
        }
    }
}

/// Proposal ledger entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposalLedgerEntry {
    /// Sequence number.
    pub sequence_number: u64,
    /// Stored proposal.
    pub proposal: EvidenceAppendProposal,
    /// Previous entry digest.
    #[serde(default)]
    pub previous_digest: Option<EvidenceAppendProposalDigest>,
    /// Entry digest.
    pub entry_digest: EvidenceAppendProposalDigest,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Named count used in proposal ledger summaries.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposalLedgerSummaryCount {
    /// Count name.
    pub name: String,
    /// Count.
    pub count: usize,
}

/// Proposal ledger summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct EvidenceAppendProposalLedgerSummary {
    /// Entry count.
    pub entry_count: usize,
    /// Status counts.
    pub status_counts: Vec<EvidenceAppendProposalLedgerSummaryCount>,
    /// Review state counts.
    pub review_state_counts: Vec<EvidenceAppendProposalLedgerSummaryCount>,
    /// Claim boundary counts.
    pub claim_boundary_counts: Vec<EvidenceAppendProposalLedgerSummaryCount>,
}

impl EvidenceAppendProposalLedgerSummary {
    /// Build a deterministic summary from ledger entries.
    pub fn from_entries(entries: &[EvidenceAppendProposalLedgerEntry]) -> Self {
        let mut status_counts = BTreeMap::new();
        let mut review_state_counts = BTreeMap::new();
        let mut claim_boundary_counts = BTreeMap::new();
        for entry in entries {
            *status_counts
                .entry(format!("{:?}", entry.proposal.status))
                .or_insert(0usize) += 1;
            *review_state_counts
                .entry(format!("{:?}", entry.proposal.review_state))
                .or_insert(0usize) += 1;
            *claim_boundary_counts
                .entry(entry.proposal.proposed_claim_boundary.to_string())
                .or_insert(0usize) += 1;
        }
        Self {
            entry_count: entries.len(),
            status_counts: map_counts(status_counts),
            review_state_counts: map_counts(review_state_counts),
            claim_boundary_counts: map_counts(claim_boundary_counts),
        }
    }
}

/// Proposal ledger validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposalLedgerValidationIssue {
    /// Sequence number associated with the issue.
    pub sequence_number: u64,
    /// Issue message.
    pub message: String,
}

/// Proposal ledger validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposalLedgerValidation {
    /// True when no validation errors were found.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<EvidenceAppendProposalLedgerValidationIssue>,
    /// Recomputed summary.
    pub summary: EvidenceAppendProposalLedgerSummary,
}

/// Persistent local proposal ledger.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceAppendProposalLedger {
    /// Ledger version.
    pub version: EvidenceAppendProposalLedgerVersion,
    /// Ledger entries.
    pub entries: Vec<EvidenceAppendProposalLedgerEntry>,
    /// Cached summary.
    pub summary: EvidenceAppendProposalLedgerSummary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for EvidenceAppendProposalLedger {
    fn default() -> Self {
        Self::new()
    }
}

impl EvidenceAppendProposalLedger {
    /// Create an empty proposal ledger.
    pub fn new() -> Self {
        Self {
            version: EvidenceAppendProposalLedgerVersion::default(),
            entries: Vec::new(),
            summary: EvidenceAppendProposalLedgerSummary::default(),
            notes: vec![
                "Proposal ledger entries are not accepted evidence.".to_string(),
                "Evidence append proposals are not accepted evidence.".to_string(),
            ],
        }
    }

    /// Append one proposal after validation.
    pub fn append(&mut self, proposal: EvidenceAppendProposal) -> Result<()> {
        let validation = validate_evidence_append_proposal(&proposal);
        if !validation.valid {
            return Err(ZkBenchError::evidence_append_proposal(
                "proposal_ledger.append.validation",
                format!("proposal validation failed: {:?}", validation.issues),
            ));
        }
        if proposal.is_accepted_evidence() {
            return Err(ZkBenchError::evidence_append_proposal(
                "proposal_ledger.append.accepted_evidence",
                "proposal ledger cannot append accepted evidence records",
            ));
        }
        if proposal.proposed_claim_boundary != ClaimBoundary::Level0DesignNote {
            return Err(ZkBenchError::evidence_append_proposal(
                "proposal_ledger.append.claim_boundary",
                "Phase I proposal ledger entries must remain Level0DesignNote",
            ));
        }

        let sequence_number = self.entries.len() as u64;
        let previous_digest = self.entries.last().map(|entry| entry.entry_digest.clone());
        let entry_digest = digest_entry(sequence_number, previous_digest.as_ref(), &proposal)?;
        self.entries.push(EvidenceAppendProposalLedgerEntry {
            sequence_number,
            proposal,
            previous_digest,
            entry_digest,
            notes: Vec::new(),
        });
        self.summary = EvidenceAppendProposalLedgerSummary::from_entries(&self.entries);
        Ok(())
    }

    /// Validate the local digest chain and proposal boundaries.
    pub fn validate(&self) -> EvidenceAppendProposalLedgerValidation {
        let mut issues = Vec::new();
        for (index, note) in self.notes.iter().enumerate() {
            if contains_forbidden_claim_text(note) {
                issues.push(EvidenceAppendProposalLedgerValidationIssue {
                    sequence_number: self.entries.len() as u64,
                    message: format!(
                        "proposal ledger notes[{index}] contain forbidden claim language"
                    ),
                });
            }
        }
        let mut previous_digest = None;
        for (index, entry) in self.entries.iter().enumerate() {
            for (note_index, note) in entry.notes.iter().enumerate() {
                if contains_forbidden_claim_text(note) {
                    issues.push(EvidenceAppendProposalLedgerValidationIssue {
                        sequence_number: entry.sequence_number,
                        message: format!(
                            "proposal ledger entries[{index}].notes[{note_index}] contain forbidden claim language"
                        ),
                    });
                }
            }
            if entry.sequence_number != index as u64 {
                issues.push(EvidenceAppendProposalLedgerValidationIssue {
                    sequence_number: entry.sequence_number,
                    message: format!(
                        "sequence number {} does not match index {}",
                        entry.sequence_number, index
                    ),
                });
            }
            if entry.previous_digest != previous_digest {
                issues.push(EvidenceAppendProposalLedgerValidationIssue {
                    sequence_number: entry.sequence_number,
                    message: "previous digest does not match prior entry".to_string(),
                });
            }
            let proposal_validation = validate_evidence_append_proposal(&entry.proposal);
            if !proposal_validation.valid {
                issues.push(EvidenceAppendProposalLedgerValidationIssue {
                    sequence_number: entry.sequence_number,
                    message: format!(
                        "proposal validation failed: {:?}",
                        proposal_validation.issues
                    ),
                });
            }
            if entry.proposal.is_accepted_evidence()
                || (entry.proposal.status
                    == EvidenceAppendProposalStatus::ApprovedForFutureAppendOnly
                    && entry.proposal.review_state
                        != EvidenceAppendProposalReviewState::FutureApprovalRequired)
            {
                issues.push(EvidenceAppendProposalLedgerValidationIssue {
                    sequence_number: entry.sequence_number,
                    message: "proposal state does not authorize accepted evidence".to_string(),
                });
            }
            match digest_entry(
                entry.sequence_number,
                entry.previous_digest.as_ref(),
                &entry.proposal,
            ) {
                Ok(expected) if expected == entry.entry_digest => {}
                Ok(_) => issues.push(EvidenceAppendProposalLedgerValidationIssue {
                    sequence_number: entry.sequence_number,
                    message: "entry digest mismatch".to_string(),
                }),
                Err(error) => issues.push(EvidenceAppendProposalLedgerValidationIssue {
                    sequence_number: entry.sequence_number,
                    message: error.to_string(),
                }),
            }
            previous_digest = Some(entry.entry_digest.clone());
        }
        let summary = EvidenceAppendProposalLedgerSummary::from_entries(&self.entries);
        if summary != self.summary {
            issues.push(EvidenceAppendProposalLedgerValidationIssue {
                sequence_number: self.entries.len() as u64,
                message: "cached summary does not match entries".to_string(),
            });
        }
        EvidenceAppendProposalLedgerValidation {
            valid: issues.is_empty(),
            issues,
            summary,
        }
    }

    /// Save ledger as pretty JSON.
    pub fn save_json(&self, path: impl AsRef<Path>) -> Result<()> {
        let json = serde_json::to_string_pretty(self).map_err(|error| {
            ZkBenchError::serialization("proposal_ledger.save_json", error.to_string())
        })?;
        fs::write(path.as_ref(), json).map_err(|error| {
            ZkBenchError::evidence_append_proposal(
                path.as_ref().display().to_string(),
                error.to_string(),
            )
        })
    }

    /// Load ledger from JSON.
    pub fn load_json(path: impl AsRef<Path>) -> Result<Self> {
        let json = fs::read_to_string(path.as_ref()).map_err(|error| {
            ZkBenchError::evidence_append_proposal(
                path.as_ref().display().to_string(),
                error.to_string(),
            )
        })?;
        serde_json::from_str(&json).map_err(|error| {
            ZkBenchError::deserialization("proposal_ledger.load_json", error.to_string())
        })
    }
}

#[derive(Debug, Serialize)]
struct EntryDigestInput<'a> {
    sequence_number: u64,
    previous_digest: Option<&'a ArtifactDigest>,
    proposal: &'a EvidenceAppendProposal,
}

fn digest_entry(
    sequence_number: u64,
    previous_digest: Option<&ArtifactDigest>,
    proposal: &EvidenceAppendProposal,
) -> Result<ArtifactDigest> {
    compute_artifact_digest(
        &EntryDigestInput {
            sequence_number,
            previous_digest,
            proposal,
        },
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Digest),
    )
}

fn map_counts(values: BTreeMap<String, usize>) -> Vec<EvidenceAppendProposalLedgerSummaryCount> {
    values
        .into_iter()
        .map(|(name, count)| EvidenceAppendProposalLedgerSummaryCount { name, count })
        .collect()
}

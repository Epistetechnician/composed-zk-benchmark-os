use crate::{hash_parts, Digest};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum JournalState {
    Authorized,
    Completed,
    RolledBack,
    Frozen,
    Shutdown,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ReplayJournalEntry {
    sequence_number: u64,
    previous_entry_digest: Option<Digest>,
    proposal_digest: Digest,
    receipt_digest: Digest,
    permit_digest: Digest,
    nonce: u64,
    state: JournalState,
    entry_digest: Digest,
}

impl ReplayJournalEntry {
    fn new(
        sequence_number: u64,
        previous_entry_digest: Option<Digest>,
        proposal_digest: Digest,
        receipt_digest: Digest,
        permit_digest: Digest,
        nonce: u64,
        state: JournalState,
    ) -> Self {
        let entry_digest = Self::compute_digest(
            sequence_number,
            &previous_entry_digest,
            &proposal_digest,
            &receipt_digest,
            &permit_digest,
            nonce,
            state,
        );
        Self {
            sequence_number,
            previous_entry_digest,
            proposal_digest,
            receipt_digest,
            permit_digest,
            nonce,
            state,
            entry_digest,
        }
    }

    fn compute_digest(
        sequence_number: u64,
        previous_entry_digest: &Option<Digest>,
        proposal_digest: &Digest,
        receipt_digest: &Digest,
        permit_digest: &Digest,
        nonce: u64,
        state: JournalState,
    ) -> Digest {
        hash_parts(
            "hsai-control-plane:replay-journal-entry:v1",
            &[
                sequence_number.to_string(),
                previous_entry_digest
                    .as_ref()
                    .map(Digest::to_hex)
                    .unwrap_or_else(|| "absent".to_owned()),
                proposal_digest.to_hex(),
                receipt_digest.to_hex(),
                permit_digest.to_hex(),
                nonce.to_string(),
                format!("{state:?}"),
            ],
        )
    }

    pub fn sequence_number(&self) -> u64 {
        self.sequence_number
    }

    pub fn previous_entry_digest(&self) -> Option<Digest> {
        self.previous_entry_digest.clone()
    }

    pub fn proposal_digest(&self) -> Digest {
        self.proposal_digest.clone()
    }

    pub fn receipt_digest(&self) -> Digest {
        self.receipt_digest.clone()
    }

    pub fn permit_digest(&self) -> Digest {
        self.permit_digest.clone()
    }

    pub fn nonce(&self) -> u64 {
        self.nonce
    }

    pub fn state(&self) -> JournalState {
        self.state
    }

    pub fn digest(&self) -> Digest {
        self.entry_digest.clone()
    }

    pub fn is_digest_valid(&self) -> bool {
        Self::compute_digest(
            self.sequence_number,
            &self.previous_entry_digest,
            &self.proposal_digest,
            &self.receipt_digest,
            &self.permit_digest,
            self.nonce,
            self.state,
        ) == self.entry_digest
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ReplayJournal {
    first_nonce: u64,
    next_nonce: u64,
    entries: Vec<ReplayJournalEntry>,
}

impl ReplayJournal {
    pub const fn new(first_nonce: u64) -> Self {
        Self {
            first_nonce,
            next_nonce: first_nonce,
            entries: Vec::new(),
        }
    }

    pub fn first_nonce(&self) -> u64 {
        self.first_nonce
    }

    pub fn next_nonce(&self) -> u64 {
        self.next_nonce
    }

    pub fn entries(&self) -> &[ReplayJournalEntry] {
        &self.entries
    }

    pub fn tip_digest(&self) -> Option<Digest> {
        self.entries.last().map(ReplayJournalEntry::digest)
    }

    pub fn append(
        &self,
        proposal_digest: Digest,
        receipt_digest: Digest,
        permit_digest: Digest,
        nonce: u64,
        state: JournalState,
    ) -> Result<Self, JournalBlocker> {
        if !self.validate().is_empty() {
            return Err(JournalBlocker::InvalidJournal);
        }
        if proposal_digest.is_zero() {
            return Err(JournalBlocker::MissingProposalDigest);
        }
        if receipt_digest.is_zero() {
            return Err(JournalBlocker::MissingReceiptDigest);
        }
        if permit_digest.is_zero() {
            return Err(JournalBlocker::MissingPermitDigest);
        }
        if self.first_nonce == 0 || self.next_nonce == 0 {
            return Err(JournalBlocker::ZeroNonce);
        }
        if nonce != self.next_nonce {
            return Err(JournalBlocker::UnexpectedNonce {
                expected: self.next_nonce,
                received: nonce,
            });
        }
        let sequence_number = u64::try_from(self.entries.len())
            .ok()
            .and_then(|length| length.checked_add(1))
            .ok_or(JournalBlocker::SequenceExhausted)?;
        let next_nonce = nonce.checked_add(1).ok_or(JournalBlocker::NonceExhausted)?;
        let entry = ReplayJournalEntry::new(
            sequence_number,
            self.tip_digest(),
            proposal_digest,
            receipt_digest,
            permit_digest,
            nonce,
            state,
        );
        let mut entries = self.entries.clone();
        entries.push(entry);
        Ok(Self {
            first_nonce: self.first_nonce,
            next_nonce,
            entries,
        })
    }

    pub fn append_if_tip(
        &self,
        expected_tip: Option<Digest>,
        proposal_digest: Digest,
        receipt_digest: Digest,
        permit_digest: Digest,
        nonce: u64,
        state: JournalState,
    ) -> Result<Self, JournalBlocker> {
        if self.tip_digest() != expected_tip {
            return Err(JournalBlocker::TipMismatch);
        }
        self.append(proposal_digest, receipt_digest, permit_digest, nonce, state)
    }

    pub fn validate(&self) -> Vec<JournalValidationError> {
        let mut errors = Vec::new();
        if self.first_nonce == 0 {
            errors.push(JournalValidationError::ZeroFirstNonce);
        }
        let mut expected_nonce = self.first_nonce;
        let mut previous_digest = None;
        for (index, entry) in self.entries.iter().enumerate() {
            let expected_sequence = index as u64 + 1;
            if entry.sequence_number != expected_sequence {
                errors.push(JournalValidationError::SequenceMismatch);
            }
            if entry.previous_entry_digest != previous_digest {
                errors.push(JournalValidationError::PreviousDigestMismatch);
            }
            if entry.nonce != expected_nonce {
                errors.push(JournalValidationError::NonceMismatch);
            }
            if !entry.is_digest_valid() {
                errors.push(JournalValidationError::EntryDigestInvalid);
            }
            if entry.proposal_digest.is_zero() {
                errors.push(JournalValidationError::MissingProposalDigest);
            }
            if entry.receipt_digest.is_zero() {
                errors.push(JournalValidationError::MissingReceiptDigest);
            }
            if entry.permit_digest.is_zero() {
                errors.push(JournalValidationError::MissingPermitDigest);
            }
            previous_digest = Some(entry.digest());
            expected_nonce = match expected_nonce.checked_add(1) {
                Some(next) => next,
                None => {
                    errors.push(JournalValidationError::NonceOverflow);
                    expected_nonce
                }
            };
        }
        if self.next_nonce != expected_nonce {
            errors.push(JournalValidationError::NextNonceMismatch);
        }
        errors
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum JournalBlocker {
    InvalidJournal,
    TipMismatch,
    MissingProposalDigest,
    MissingReceiptDigest,
    MissingPermitDigest,
    ZeroNonce,
    UnexpectedNonce { expected: u64, received: u64 },
    NonceExhausted,
    SequenceExhausted,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum JournalValidationError {
    ZeroFirstNonce,
    SequenceMismatch,
    PreviousDigestMismatch,
    NonceMismatch,
    EntryDigestInvalid,
    MissingProposalDigest,
    MissingReceiptDigest,
    MissingPermitDigest,
    NonceOverflow,
    NextNonceMismatch,
}

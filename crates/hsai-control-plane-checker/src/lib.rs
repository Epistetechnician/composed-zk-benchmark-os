#![forbid(unsafe_code)]

//! Implementation-independent checks for `hsai-control-plane` records.
//!
//! State-slice mutation: `hsai-proof-carrying-capability-bounded-agent-platform-v1`.
//! This crate is a second pure-data Adapter. It recomputes public invariants
//! from returned records without issuing them, executing work, verifying a
//! signature, checking a proof, settling value, or granting authority.

use hsai_control_plane::{
    AdmissionDecision, AlignmentDecision, CapabilityReceipt, ComputeJobRequest, ComputeMatch,
    ComputeOffer, ExecutionPermit, KillSwitch, LearningDecision, MonitorDecision,
    MonitorObservation, MonitorSignal, ReplayJournal, SettlementRail,
};

pub const STATE_SLICE: &str = "hsai-proof-carrying-capability-bounded-agent-platform-v1";
pub const CLAIM_BOUNDARY: &str = "independent local pure-data invariant checks only; no signature verification, proof verification, execution, settlement, policy authority, or alignment claim";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckerViolation {
    EmptyBlockerList,
    ReceiptDigestInvalid,
    ReceiptDigestMissing,
    ReceiptCapabilitiesEmpty,
    ReceiptValidityWindowInvalid,
    ReceiptNonceZero,
    ReceiptGrantsAuthority,
    PermitDigestMissing,
    PermitReceiptDigestMissing,
    PermitProposalDigestMissing,
    PermitExpiryMissing,
    PermitGrantsAuthority,
    MonitorDispositionMismatch,
    MonitorReasonMismatch,
    MonitorGrantsAuthority,
    AlignmentCandidateDigestMissing,
    LearningPromotionAllowed,
    LearningShadowContractMissing,
    MarketJobDigestMismatch,
    MarketOfferDigestMismatch,
    MarketProviderMismatch,
    MarketPriceMismatch,
    MarketSettlementRailMismatch,
    MarketSettlementJobMismatch,
    MarketSettlementAmountMismatch,
    MarketSettlementExecuted,
    MarketProofVerified,
    MarketGrantsAuthority,
    JournalFirstNonceZero,
    JournalSequenceMismatch,
    JournalPreviousDigestMismatch,
    JournalNonceMismatch,
    JournalEntryDigestInvalid,
    JournalProposalDigestMissing,
    JournalReceiptDigestMissing,
    JournalPermitDigestMissing,
    JournalNextNonceMismatch,
}

pub fn check_admission_decision(decision: &AdmissionDecision) -> Vec<CheckerViolation> {
    match decision {
        AdmissionDecision::Accepted(receipt) => check_receipt(receipt),
        AdmissionDecision::Rejected(blockers) | AdmissionDecision::Quarantined(blockers) => {
            if blockers.is_empty() {
                vec![CheckerViolation::EmptyBlockerList]
            } else {
                Vec::new()
            }
        }
    }
}

pub fn check_receipt(receipt: &CapabilityReceipt) -> Vec<CheckerViolation> {
    let mut violations = Vec::new();
    if receipt.digest().is_zero() {
        violations.push(CheckerViolation::ReceiptDigestMissing);
    }
    if !receipt.is_digest_valid() {
        violations.push(CheckerViolation::ReceiptDigestInvalid);
    }
    if receipt.capabilities().is_empty() {
        violations.push(CheckerViolation::ReceiptCapabilitiesEmpty);
    }
    if receipt.expires_at() <= receipt.issued_at() {
        violations.push(CheckerViolation::ReceiptValidityWindowInvalid);
    }
    if receipt.nonce() == 0 {
        violations.push(CheckerViolation::ReceiptNonceZero);
    }
    if receipt.grants_authority() {
        violations.push(CheckerViolation::ReceiptGrantsAuthority);
    }
    violations
}

pub fn check_execution_permit(permit: &ExecutionPermit) -> Vec<CheckerViolation> {
    let mut violations = Vec::new();
    if permit.digest().is_zero() {
        violations.push(CheckerViolation::PermitDigestMissing);
    }
    if permit.receipt_digest().is_zero() {
        violations.push(CheckerViolation::PermitReceiptDigestMissing);
    }
    if permit.proposal_digest().is_zero() {
        violations.push(CheckerViolation::PermitProposalDigestMissing);
    }
    if permit.expires_at() == 0 {
        violations.push(CheckerViolation::PermitExpiryMissing);
    }
    if permit.grants_authority() {
        violations.push(CheckerViolation::PermitGrantsAuthority);
    }
    violations
}

pub fn check_monitor_decision(
    receipt: &CapabilityReceipt,
    observation: &MonitorObservation,
    kill_switch: &KillSwitch,
    decision: &MonitorDecision,
) -> Vec<CheckerViolation> {
    let expected_reason =
        if kill_switch.is_tripped() || observation.signal == MonitorSignal::KillSwitch {
            MonitorSignal::KillSwitch
        } else {
            observation.signal
        };
    let expected_disposition = if expected_reason == MonitorSignal::KillSwitch {
        hsai_control_plane::MonitorDisposition::Shutdown
    } else if observation.now >= receipt.expires_at()
        || matches!(
            observation.signal,
            MonitorSignal::Timeout
                | MonitorSignal::InvariantViolation
                | MonitorSignal::EvidenceInvalidated
                | MonitorSignal::ResourceExceeded
        )
    {
        hsai_control_plane::MonitorDisposition::RollbackAndFreeze
    } else {
        match observation.signal {
            MonitorSignal::Healthy => hsai_control_plane::MonitorDisposition::Continue,
            MonitorSignal::Completed => hsai_control_plane::MonitorDisposition::Completed,
            MonitorSignal::KillSwitch
            | MonitorSignal::Timeout
            | MonitorSignal::InvariantViolation
            | MonitorSignal::EvidenceInvalidated
            | MonitorSignal::ResourceExceeded => {
                hsai_control_plane::MonitorDisposition::RollbackAndFreeze
            }
        }
    };

    let mut violations = Vec::new();
    if decision.disposition != expected_disposition {
        violations.push(CheckerViolation::MonitorDispositionMismatch);
    }
    if decision.reason != expected_reason {
        violations.push(CheckerViolation::MonitorReasonMismatch);
    }
    if decision.authority_granted {
        violations.push(CheckerViolation::MonitorGrantsAuthority);
    }
    violations
}

pub fn check_alignment_decision(decision: &AlignmentDecision) -> Vec<CheckerViolation> {
    match decision {
        AlignmentDecision::Blocked(blockers) if blockers.is_empty() => {
            vec![CheckerViolation::EmptyBlockerList]
        }
        AlignmentDecision::Blocked(_) => Vec::new(),
        AlignmentDecision::LocalCandidate {
            plan_digest,
            evidence_digest,
        } => {
            let mut violations = Vec::new();
            if plan_digest.is_zero() || evidence_digest.is_zero() {
                violations.push(CheckerViolation::AlignmentCandidateDigestMissing);
            }
            violations
        }
    }
}

pub fn check_learning_decision(decision: &LearningDecision) -> Vec<CheckerViolation> {
    match decision {
        LearningDecision::Blocked(blockers) if blockers.is_empty() => {
            vec![CheckerViolation::EmptyBlockerList]
        }
        LearningDecision::Blocked(_) => Vec::new(),
        LearningDecision::ShadowOnly {
            promotion_allowed,
            update_digest,
        } => {
            let mut violations = Vec::new();
            if *promotion_allowed {
                violations.push(CheckerViolation::LearningPromotionAllowed);
            }
            if update_digest.is_zero() {
                violations.push(CheckerViolation::LearningShadowContractMissing);
            }
            violations
        }
    }
}

pub fn check_compute_match(
    job: &ComputeJobRequest,
    offer: &ComputeOffer,
    matched: &ComputeMatch,
) -> Vec<CheckerViolation> {
    let mut violations = Vec::new();
    if matched.job_digest != job.digest() {
        violations.push(CheckerViolation::MarketJobDigestMismatch);
    }
    if matched.offer_digest != offer.digest() {
        violations.push(CheckerViolation::MarketOfferDigestMismatch);
    }
    if matched.provider_id != offer.provider_id {
        violations.push(CheckerViolation::MarketProviderMismatch);
    }
    if matched.price_units != offer.price_units {
        violations.push(CheckerViolation::MarketPriceMismatch);
    }
    if matched.settlement.rail != SettlementRail::Hyperliquid {
        violations.push(CheckerViolation::MarketSettlementRailMismatch);
    }
    if matched.settlement.job_digest != matched.job_digest {
        violations.push(CheckerViolation::MarketSettlementJobMismatch);
    }
    if matched.settlement.amount_units != matched.price_units {
        violations.push(CheckerViolation::MarketSettlementAmountMismatch);
    }
    if matched.settlement.executed {
        violations.push(CheckerViolation::MarketSettlementExecuted);
    }
    if matched.proof_verified {
        violations.push(CheckerViolation::MarketProofVerified);
    }
    if matched.authority_granted {
        violations.push(CheckerViolation::MarketGrantsAuthority);
    }
    violations
}

pub fn check_replay_journal(journal: &ReplayJournal) -> Vec<CheckerViolation> {
    let mut violations = Vec::new();
    if journal.first_nonce() == 0 {
        violations.push(CheckerViolation::JournalFirstNonceZero);
    }
    let mut expected_nonce = journal.first_nonce();
    let mut previous_digest = None;
    for (index, entry) in journal.entries().iter().enumerate() {
        if entry.sequence_number() != index as u64 + 1 {
            violations.push(CheckerViolation::JournalSequenceMismatch);
        }
        if entry.previous_entry_digest() != previous_digest {
            violations.push(CheckerViolation::JournalPreviousDigestMismatch);
        }
        if entry.nonce() != expected_nonce {
            violations.push(CheckerViolation::JournalNonceMismatch);
        }
        if !entry.is_digest_valid() {
            violations.push(CheckerViolation::JournalEntryDigestInvalid);
        }
        if entry.proposal_digest().is_zero() {
            violations.push(CheckerViolation::JournalProposalDigestMissing);
        }
        if entry.receipt_digest().is_zero() {
            violations.push(CheckerViolation::JournalReceiptDigestMissing);
        }
        if entry.permit_digest().is_zero() {
            violations.push(CheckerViolation::JournalPermitDigestMissing);
        }
        previous_digest = Some(entry.digest());
        expected_nonce = expected_nonce.saturating_add(1);
    }
    if journal.next_nonce() != expected_nonce {
        violations.push(CheckerViolation::JournalNextNonceMismatch);
    }
    violations
}

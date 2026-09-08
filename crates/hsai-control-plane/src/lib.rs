#![forbid(unsafe_code)]

//! Pure-data contracts for the proof-carrying, capability-bounded agent plan.
//!
//! State-slice mutation: `hsai-proof-carrying-capability-bounded-agent-platform-v1`.
//! This crate deliberately does not spawn processes, call providers, verify
//! signatures, hold secrets, move value, or enforce OS/network policy. Its
//! outputs are typed local records that a future enforcement adapter may
//! consume only after an independently authorized integration phase.

use serde::{Deserialize, Serialize};
use sha2::{Digest as ShaDigest, Sha256};
use std::collections::BTreeSet;

mod alignment;
mod journal;
mod market;
mod storage;

pub use alignment::{
    evaluate_alignment, evaluate_learning_update, AlignmentBlocker, AlignmentDecision,
    AlignmentEvidence, AlignmentPlan, AlignmentTrack, LearningDecision, LearningUpdateProposal,
    UpdateBlocker, UpdateSurface,
};
pub use journal::{
    JournalBlocker, JournalState, JournalValidationError, ReplayJournal, ReplayJournalEntry,
};
pub use market::{
    match_compute_job, ComputeJobRequest, ComputeMatch, ComputeOffer, ComputeRoute,
    ConfidentialityTier, MarketBlocker, SettlementIntent, SettlementRail, VerifiabilityTier,
};
pub use storage::{JournalStorageError, ReplayJournalFileStore};

pub const STATE_SLICE: &str = "hsai-proof-carrying-capability-bounded-agent-platform-v1";
pub const SCHEMA_VERSION: &str = "hsai-control-plane:v1";
pub const CLAIM_BOUNDARY: &str = "local pure-data control-plane and caller-owned file-persistence contract evidence only; no signature verification, OS sandbox, network enforcement, secret custody, value movement, formal proof, semantic correctness, alignment guarantee, production readiness, cross-process linearizability, or authority to execute an action";

#[derive(Clone, Debug, Deserialize, Eq, Hash, PartialEq, Serialize)]
pub struct Digest([u8; 32]);

impl Digest {
    pub const ZERO: Self = Self([0; 32]);

    pub fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    pub fn from_text(text: &str) -> Self {
        hash_parts("hsai-control-plane:text:v1", &[text.to_owned()])
    }

    pub fn is_zero(&self) -> bool {
        self == &Self::ZERO
    }

    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    pub fn to_hex(&self) -> String {
        self.0.iter().map(|byte| format!("{byte:02x}")).collect()
    }
}

pub(crate) fn hash_parts(tag: &str, parts: &[String]) -> Digest {
    let mut hasher = Sha256::new();
    hasher.update(tag.as_bytes());
    hasher.update([0]);
    for part in parts {
        hasher.update((part.len() as u64).to_le_bytes());
        hasher.update(part.as_bytes());
        hasher.update([0]);
    }
    let digest = hasher.finalize();
    let mut bytes = [0; 32];
    bytes.copy_from_slice(&digest);
    Digest(bytes)
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum Capability {
    Read,
    Write,
    Network,
    Secrets,
    Spend,
    Replication,
    CodeExecution,
    SelfModification,
}

impl Capability {
    fn label(self) -> &'static str {
        match self {
            Self::Read => "read",
            Self::Write => "write",
            Self::Network => "network",
            Self::Secrets => "secrets",
            Self::Spend => "spend",
            Self::Replication => "replication",
            Self::CodeExecution => "code_execution",
            Self::SelfModification => "self_modification",
        }
    }
}

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
pub struct CapabilitySet(BTreeSet<Capability>);

impl CapabilitySet {
    pub fn new(capabilities: impl IntoIterator<Item = Capability>) -> Self {
        Self(capabilities.into_iter().collect())
    }

    pub fn empty() -> Self {
        Self::default()
    }

    pub fn contains(&self, capability: Capability) -> bool {
        self.0.contains(&capability)
    }

    pub fn is_empty(&self) -> bool {
        self.0.is_empty()
    }

    pub fn is_subset_of(&self, allowed: &Self) -> bool {
        self.0.is_subset(&allowed.0)
    }

    pub fn iter(&self) -> impl Iterator<Item = &Capability> {
        self.0.iter()
    }

    pub fn canonical(&self) -> String {
        self.0
            .iter()
            .map(|capability| capability.label())
            .collect::<Vec<_>>()
            .join(",")
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum RiskLabel {
    PromptInjection,
    DataExfiltration,
    PrivilegeEscalation,
    DeceptiveCompliance,
    RewardHacking,
    ProvenanceTampering,
    SybilReplication,
    UnsafeSelfModification,
    EconomicManipulation,
    DistributionShift,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum ClaimLevel {
    Local,
    Attested,
    Proven,
    External,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct EvidenceBinding {
    pub artifact_digest: Digest,
    pub validator_id: String,
    pub nonclaims_digest: Digest,
    pub valid_until: u64,
    pub claim_level: ClaimLevel,
    pub independently_validated: bool,
    pub contradictory: bool,
}

impl EvidenceBinding {
    pub fn validated(
        artifact_digest: Digest,
        validator_id: impl Into<String>,
        nonclaims_digest: Digest,
        valid_until: u64,
        claim_level: ClaimLevel,
    ) -> Self {
        Self {
            artifact_digest,
            validator_id: validator_id.into(),
            nonclaims_digest,
            valid_until,
            claim_level,
            independently_validated: true,
            contradictory: false,
        }
    }

    pub fn is_fresh_and_independent(&self, now: u64) -> bool {
        !self.artifact_digest.is_zero()
            && !self.nonclaims_digest.is_zero()
            && !self.validator_id.is_empty()
            && self.valid_until >= now
            && self.independently_validated
            && !self.contradictory
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentProposal {
    pub proposal_id: String,
    pub actor_id: String,
    pub intent_digest: Digest,
    pub policy_digest: Digest,
    pub requested_capabilities: CapabilitySet,
    pub max_spend_units: u64,
    pub proposed_at: u64,
    pub expires_at: u64,
    pub nonce: u64,
    pub reversible: bool,
    pub model_generated: bool,
    pub model_requested_authority: bool,
    pub evidence: Option<EvidenceBinding>,
    pub risk_labels: BTreeSet<RiskLabel>,
}

impl AgentProposal {
    pub fn digest(&self) -> Digest {
        hash_parts(
            "hsai-control-plane:agent-proposal:v1",
            &[
                self.proposal_id.clone(),
                self.actor_id.clone(),
                self.intent_digest.to_hex(),
                self.policy_digest.to_hex(),
                self.requested_capabilities.canonical(),
                self.max_spend_units.to_string(),
                self.proposed_at.to_string(),
                self.expires_at.to_string(),
                self.nonce.to_string(),
                self.reversible.to_string(),
                self.model_generated.to_string(),
                self.model_requested_authority.to_string(),
                self.risk_labels
                    .iter()
                    .map(|label| format!("{label:?}"))
                    .collect::<Vec<_>>()
                    .join(","),
            ],
        )
    }

    fn validate(&self) -> Vec<ProposalError> {
        let mut errors = Vec::new();
        if self.proposal_id.is_empty() {
            errors.push(ProposalError::EmptyProposalId);
        }
        if self.actor_id.is_empty() {
            errors.push(ProposalError::EmptyActorId);
        }
        if self.intent_digest.is_zero() {
            errors.push(ProposalError::MissingIntentDigest);
        }
        if self.policy_digest.is_zero() {
            errors.push(ProposalError::MissingPolicyDigest);
        }
        if self.requested_capabilities.is_empty() {
            errors.push(ProposalError::EmptyCapabilitySet);
        }
        if self.expires_at <= self.proposed_at {
            errors.push(ProposalError::InvalidValidityWindow);
        }
        if self.nonce == 0 {
            errors.push(ProposalError::ZeroNonce);
        }
        errors
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ProposalError {
    EmptyProposalId,
    EmptyActorId,
    MissingIntentDigest,
    MissingPolicyDigest,
    EmptyCapabilitySet,
    InvalidValidityWindow,
    ZeroNonce,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AdmissionPolicy {
    pub policy_id: String,
    pub allowed_capabilities: CapabilitySet,
    pub max_capability_ttl: u64,
    pub max_spend_units: u64,
    pub require_independent_evidence: bool,
    pub require_reversible: bool,
    pub forbidden_risks: BTreeSet<RiskLabel>,
}

impl AdmissionPolicy {
    pub fn digest(&self) -> Digest {
        hash_parts(
            "hsai-control-plane:admission-policy:v1",
            &[
                self.policy_id.clone(),
                self.allowed_capabilities.canonical(),
                self.max_capability_ttl.to_string(),
                self.max_spend_units.to_string(),
                self.require_independent_evidence.to_string(),
                self.require_reversible.to_string(),
                self.forbidden_risks
                    .iter()
                    .map(|risk| format!("{risk:?}"))
                    .collect::<Vec<_>>()
                    .join(","),
            ],
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum KillSwitch {
    Armed,
    Tripped { reason_digest: Digest },
}

impl KillSwitch {
    pub fn is_tripped(&self) -> bool {
        matches!(self, Self::Tripped { .. })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AdmissionBlocker {
    InvalidProposal(ProposalError),
    PolicyDigestMismatch,
    KillSwitchActive,
    CapabilityNotAllowed(Capability),
    SpendLimitExceeded,
    CapabilityLifetimeExceeded,
    IrreversibleProposal,
    ModelRequestedAuthority,
    ForbiddenRisk(RiskLabel),
    MissingEvidence,
    EvidenceNotIndependent,
    EvidenceContradictory,
    EvidenceStale,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AdmissionDecision {
    Accepted(CapabilityReceipt),
    Rejected(Vec<AdmissionBlocker>),
    Quarantined(Vec<AdmissionBlocker>),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct CapabilityReceipt {
    receipt_digest: Digest,
    proposal_digest: Digest,
    policy_digest: Digest,
    capabilities: CapabilitySet,
    issued_at: u64,
    expires_at: u64,
    nonce: u64,
    spend_limit_units: u64,
}

impl CapabilityReceipt {
    fn new(
        proposal_digest: Digest,
        policy_digest: Digest,
        capabilities: CapabilitySet,
        issued_at: u64,
        expires_at: u64,
        nonce: u64,
        spend_limit_units: u64,
    ) -> Self {
        let receipt_digest = hash_parts(
            "hsai-control-plane:capability-receipt:v1",
            &[
                proposal_digest.to_hex(),
                policy_digest.to_hex(),
                capabilities.canonical(),
                issued_at.to_string(),
                expires_at.to_string(),
                nonce.to_string(),
                spend_limit_units.to_string(),
            ],
        );
        Self {
            receipt_digest,
            proposal_digest,
            policy_digest,
            capabilities,
            issued_at,
            expires_at,
            nonce,
            spend_limit_units,
        }
    }

    pub fn digest(&self) -> Digest {
        self.receipt_digest.clone()
    }

    pub fn proposal_digest(&self) -> Digest {
        self.proposal_digest.clone()
    }

    pub fn policy_digest(&self) -> Digest {
        self.policy_digest.clone()
    }

    pub fn capabilities(&self) -> &CapabilitySet {
        &self.capabilities
    }

    pub fn issued_at(&self) -> u64 {
        self.issued_at
    }

    pub fn expires_at(&self) -> u64 {
        self.expires_at
    }

    pub fn spend_limit_units(&self) -> u64 {
        self.spend_limit_units
    }

    pub fn nonce(&self) -> u64 {
        self.nonce
    }

    pub fn grants_authority(&self) -> bool {
        false
    }

    pub fn is_digest_valid(&self) -> bool {
        Self::new(
            self.proposal_digest.clone(),
            self.policy_digest.clone(),
            self.capabilities.clone(),
            self.issued_at,
            self.expires_at,
            self.nonce,
            self.spend_limit_units,
        )
        .receipt_digest
            == self.receipt_digest
    }
}

pub fn evaluate_admission(
    proposal: &AgentProposal,
    policy: &AdmissionPolicy,
    now: u64,
    kill_switch: &KillSwitch,
) -> AdmissionDecision {
    let validation_errors = proposal.validate();
    if !validation_errors.is_empty() {
        return AdmissionDecision::Rejected(
            validation_errors
                .into_iter()
                .map(AdmissionBlocker::InvalidProposal)
                .collect(),
        );
    }

    let mut rejected = Vec::new();
    if proposal.policy_digest != policy.digest() {
        rejected.push(AdmissionBlocker::PolicyDigestMismatch);
    }
    if kill_switch.is_tripped() {
        rejected.push(AdmissionBlocker::KillSwitchActive);
    }
    if proposal.model_requested_authority {
        rejected.push(AdmissionBlocker::ModelRequestedAuthority);
    }
    if proposal.max_spend_units > policy.max_spend_units {
        rejected.push(AdmissionBlocker::SpendLimitExceeded);
    }
    if proposal.expires_at.saturating_sub(now) > policy.max_capability_ttl {
        rejected.push(AdmissionBlocker::CapabilityLifetimeExceeded);
    }
    if policy.require_reversible && !proposal.reversible {
        rejected.push(AdmissionBlocker::IrreversibleProposal);
    }
    for capability in proposal.requested_capabilities.iter() {
        if !policy.allowed_capabilities.contains(*capability) {
            rejected.push(AdmissionBlocker::CapabilityNotAllowed(*capability));
        }
    }
    for risk in &proposal.risk_labels {
        if policy.forbidden_risks.contains(risk) {
            rejected.push(AdmissionBlocker::ForbiddenRisk(risk.clone()));
        }
    }
    if now < proposal.proposed_at || now >= proposal.expires_at {
        rejected.push(AdmissionBlocker::CapabilityLifetimeExceeded);
    }
    if !rejected.is_empty() {
        return AdmissionDecision::Rejected(rejected);
    }

    let evidence = match &proposal.evidence {
        Some(evidence) => evidence,
        None if policy.require_independent_evidence => {
            return AdmissionDecision::Quarantined(vec![AdmissionBlocker::MissingEvidence]);
        }
        None => {
            let receipt = CapabilityReceipt::new(
                proposal.digest(),
                policy.digest(),
                proposal.requested_capabilities.clone(),
                now,
                proposal.expires_at,
                proposal.nonce,
                proposal.max_spend_units,
            );
            return AdmissionDecision::Accepted(receipt);
        }
    };
    if !evidence.independently_validated {
        return AdmissionDecision::Quarantined(vec![AdmissionBlocker::EvidenceNotIndependent]);
    }
    if evidence.contradictory {
        return AdmissionDecision::Quarantined(vec![AdmissionBlocker::EvidenceContradictory]);
    }
    if evidence.valid_until < now {
        return AdmissionDecision::Quarantined(vec![AdmissionBlocker::EvidenceStale]);
    }
    if policy.require_independent_evidence && !evidence.is_fresh_and_independent(now) {
        return AdmissionDecision::Quarantined(vec![AdmissionBlocker::EvidenceNotIndependent]);
    }

    let expires_at = proposal.expires_at.min(evidence.valid_until);
    if expires_at <= now {
        return AdmissionDecision::Quarantined(vec![AdmissionBlocker::EvidenceStale]);
    }
    AdmissionDecision::Accepted(CapabilityReceipt::new(
        proposal.digest(),
        policy.digest(),
        proposal.requested_capabilities.clone(),
        now,
        expires_at,
        proposal.nonce,
        proposal.max_spend_units,
    ))
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ExecutionRequest {
    pub proposal_digest: Digest,
    pub requested_capabilities: CapabilitySet,
    pub spend_units: u64,
    pub reversible: bool,
    pub nonce: u64,
    pub now: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ExecutionBlocker {
    MalformedReceipt,
    ProposalMismatch,
    NonceMismatch,
    NotYetValid,
    Expired,
    KillSwitchActive,
    CapabilityEscalation(Capability),
    SpendLimitExceeded,
    IrreversibleExecution,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ExecutionPermit {
    permit_digest: Digest,
    receipt_digest: Digest,
    proposal_digest: Digest,
    expires_at: u64,
}

impl ExecutionPermit {
    pub fn digest(&self) -> Digest {
        self.permit_digest.clone()
    }

    pub fn receipt_digest(&self) -> Digest {
        self.receipt_digest.clone()
    }

    pub fn proposal_digest(&self) -> Digest {
        self.proposal_digest.clone()
    }

    pub fn expires_at(&self) -> u64 {
        self.expires_at
    }

    pub fn grants_authority(&self) -> bool {
        false
    }
}

pub fn authorize_execution(
    receipt: &CapabilityReceipt,
    request: &ExecutionRequest,
    kill_switch: &KillSwitch,
) -> Result<ExecutionPermit, Vec<ExecutionBlocker>> {
    let mut blockers = Vec::new();
    if !receipt.is_digest_valid() {
        blockers.push(ExecutionBlocker::MalformedReceipt);
    }
    if receipt.proposal_digest != request.proposal_digest {
        blockers.push(ExecutionBlocker::ProposalMismatch);
    }
    if receipt.nonce != request.nonce {
        blockers.push(ExecutionBlocker::NonceMismatch);
    }
    if request.now < receipt.issued_at {
        blockers.push(ExecutionBlocker::NotYetValid);
    }
    if request.now >= receipt.expires_at {
        blockers.push(ExecutionBlocker::Expired);
    }
    if kill_switch.is_tripped() {
        blockers.push(ExecutionBlocker::KillSwitchActive);
    }
    for capability in request.requested_capabilities.iter() {
        if !receipt.capabilities.contains(*capability) {
            blockers.push(ExecutionBlocker::CapabilityEscalation(*capability));
        }
    }
    if request.spend_units > receipt.spend_limit_units {
        blockers.push(ExecutionBlocker::SpendLimitExceeded);
    }
    if !request.reversible {
        blockers.push(ExecutionBlocker::IrreversibleExecution);
    }
    if !blockers.is_empty() {
        return Err(blockers);
    }
    let permit_digest = hash_parts(
        "hsai-control-plane:execution-permit:v1",
        &[
            receipt.receipt_digest.to_hex(),
            request.proposal_digest.to_hex(),
            request.requested_capabilities.canonical(),
            request.spend_units.to_string(),
            request.nonce.to_string(),
            request.now.to_string(),
        ],
    );
    Ok(ExecutionPermit {
        permit_digest,
        receipt_digest: receipt.receipt_digest.clone(),
        proposal_digest: receipt.proposal_digest.clone(),
        expires_at: receipt.expires_at,
    })
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum MonitorSignal {
    Healthy,
    Completed,
    Timeout,
    InvariantViolation,
    EvidenceInvalidated,
    ResourceExceeded,
    KillSwitch,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct MonitorObservation {
    pub now: u64,
    pub signal: MonitorSignal,
    pub resource_units_used: u64,
    pub spend_units_used: u64,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum MonitorDisposition {
    Continue,
    Completed,
    RollbackAndFreeze,
    Shutdown,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct MonitorDecision {
    pub disposition: MonitorDisposition,
    pub reason: MonitorSignal,
    pub authority_granted: bool,
}

pub fn monitor_execution(
    receipt: &CapabilityReceipt,
    observation: &MonitorObservation,
    kill_switch: &KillSwitch,
) -> MonitorDecision {
    if kill_switch.is_tripped() || observation.signal == MonitorSignal::KillSwitch {
        return MonitorDecision {
            disposition: MonitorDisposition::Shutdown,
            reason: MonitorSignal::KillSwitch,
            authority_granted: false,
        };
    }
    let disposition = if observation.now >= receipt.expires_at
        || observation.signal == MonitorSignal::Timeout
        || observation.signal == MonitorSignal::InvariantViolation
        || observation.signal == MonitorSignal::EvidenceInvalidated
        || observation.signal == MonitorSignal::ResourceExceeded
    {
        MonitorDisposition::RollbackAndFreeze
    } else {
        match observation.signal {
            MonitorSignal::Completed => MonitorDisposition::Completed,
            MonitorSignal::Healthy => MonitorDisposition::Continue,
            MonitorSignal::KillSwitch
            | MonitorSignal::Timeout
            | MonitorSignal::InvariantViolation
            | MonitorSignal::EvidenceInvalidated
            | MonitorSignal::ResourceExceeded => MonitorDisposition::RollbackAndFreeze,
        }
    };
    MonitorDecision {
        disposition,
        reason: observation.signal,
        authority_granted: false,
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum ControlState {
    Proposal,
    Quarantined,
    Rejected,
    Admitted,
    Executing,
    Completed,
    RolledBack,
    Frozen,
    Shutdown,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum StateTransition {
    Admit,
    Quarantine,
    Reject,
    BeginExecution,
    Complete,
    Rollback,
    Freeze,
    Shutdown,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct InvalidTransition;

pub fn transition_state(
    state: ControlState,
    transition: StateTransition,
) -> Result<ControlState, InvalidTransition> {
    let next = match (state, transition) {
        (ControlState::Proposal, StateTransition::Admit) => ControlState::Admitted,
        (ControlState::Proposal, StateTransition::Quarantine) => ControlState::Quarantined,
        (ControlState::Proposal, StateTransition::Reject) => ControlState::Rejected,
        (ControlState::Admitted, StateTransition::BeginExecution) => ControlState::Executing,
        (ControlState::Executing, StateTransition::Complete) => ControlState::Completed,
        (ControlState::Executing, StateTransition::Rollback) => ControlState::RolledBack,
        (ControlState::Executing, StateTransition::Freeze) => ControlState::Frozen,
        (ControlState::Executing, StateTransition::Shutdown) => ControlState::Shutdown,
        (ControlState::Frozen, StateTransition::Shutdown) => ControlState::Shutdown,
        (ControlState::RolledBack, StateTransition::Freeze) => ControlState::Frozen,
        _ => return Err(InvalidTransition),
    };
    Ok(next)
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReplayGuard {
    next_nonce: u64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReplayBlocker {
    UnexpectedNonce { expected: u64, received: u64 },
    NonceExhausted,
}

impl ReplayGuard {
    pub const fn new(first_nonce: u64) -> Self {
        Self {
            next_nonce: first_nonce,
        }
    }

    pub const fn next_nonce(&self) -> u64 {
        self.next_nonce
    }

    pub fn consume(&self, nonce: u64) -> Result<Self, ReplayBlocker> {
        if nonce != self.next_nonce {
            return Err(ReplayBlocker::UnexpectedNonce {
                expected: self.next_nonce,
                received: nonce,
            });
        }
        let next_nonce = nonce.checked_add(1).ok_or(ReplayBlocker::NonceExhausted)?;
        Ok(Self { next_nonce })
    }
}

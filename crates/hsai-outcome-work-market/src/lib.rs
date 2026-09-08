#![forbid(unsafe_code)]

//! Pure-data contracts for the evidence-bound outcome-priced work-market slice.
//!
//! State-slice mutation: `hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-contracts-v1`.

use hsai_control_plane::{CapabilitySet, Digest};
use serde::{Deserialize, Serialize};
use sha2::{Digest as ShaDigest, Sha256};
use std::collections::BTreeSet;

pub const STATE_SLICE: &str =
    "hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-contracts-v1";
pub const SCHEMA_VERSION: &str = "hsai-outcome-work-market:v1";
pub const CLAIM_BOUNDARY: &str = "local pure-data work-market contract evidence only; no live market, testnet, payment, provider, verifier, signature, settlement, or authority";
pub const PRICE_SCALE_MICROS: u64 = 1_000_000;

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum PaymentRail {
    Stripe,
    Tempo,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum OutcomeMode {
    BinarySuccess,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum MarketSource {
    Offchain,
    HyperliquidTestnet,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum MarketStatus {
    Frozen,
    Open,
    Resolved,
    Cancelled,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum EvidenceStatus {
    Accepted,
    Rejected,
    Unknown,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum WorkOutcome {
    Yes,
    No,
    Unknown,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum PayoutStatus {
    PendingAuthorization,
    Authorized,
    Submitted,
    Confirmed,
    Refunded,
    Failed,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct WorkJob {
    pub job_id: String,
    pub buyer_id: String,
    pub objective_digest: Digest,
    pub program_digest: Digest,
    pub input_commitment: Digest,
    pub output_schema_digest: Digest,
    pub acceptance_policy_digest: Digest,
    pub assessment_set_commitment: Digest,
    pub resource_budget_units: u64,
    pub deadline: u64,
    pub grace_period: u64,
    pub required_capabilities: CapabilitySet,
    pub max_price_units: u64,
    pub base_bounty_units: u64,
    pub payment_rails: BTreeSet<PaymentRail>,
    pub claim_ceiling: String,
}

impl WorkJob {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:job:v1", self)
    }

    pub fn validate(&self) -> Result<(), Vec<ContractBlocker>> {
        let mut blockers = Vec::new();
        if self.job_id.is_empty() {
            blockers.push(ContractBlocker::EmptyJobId);
        }
        if self.buyer_id.is_empty() {
            blockers.push(ContractBlocker::EmptyBuyerId);
        }
        if self.objective_digest.is_zero()
            || self.program_digest.is_zero()
            || self.input_commitment.is_zero()
            || self.output_schema_digest.is_zero()
            || self.acceptance_policy_digest.is_zero()
            || self.assessment_set_commitment.is_zero()
        {
            blockers.push(ContractBlocker::MissingJobDigest);
        }
        if self.resource_budget_units == 0 {
            blockers.push(ContractBlocker::ZeroResourceBudget);
        }
        if self.deadline == 0 {
            blockers.push(ContractBlocker::ZeroDeadline);
        }
        if self.required_capabilities.is_empty() {
            blockers.push(ContractBlocker::EmptyCapabilitySet);
        }
        if self.base_bounty_units == 0 || self.base_bounty_units > self.max_price_units {
            blockers.push(ContractBlocker::InvalidPriceBounds);
        }
        if self.payment_rails.is_empty() {
            blockers.push(ContractBlocker::EmptyPaymentRails);
        }
        if self.claim_ceiling.is_empty() {
            blockers.push(ContractBlocker::EmptyClaimCeiling);
        }
        if blockers.is_empty() {
            Ok(())
        } else {
            Err(blockers)
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OutcomeMarket {
    pub market_id: String,
    pub job_digest: Digest,
    pub mode: OutcomeMode,
    pub source: MarketSource,
    pub status: MarketStatus,
    pub opened_at: u64,
    pub closes_at: u64,
}

impl OutcomeMarket {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:market:v1", self)
    }
}

pub fn create_outcome_market(
    job: &WorkJob,
    market_id: impl Into<String>,
    source: MarketSource,
    opened_at: u64,
    closes_at: u64,
) -> Result<OutcomeMarket, Vec<ContractBlocker>> {
    let mut blockers = job.validate().err().unwrap_or_default();
    let market_id = market_id.into();
    if market_id.is_empty() {
        blockers.push(ContractBlocker::EmptyMarketId);
    }
    if opened_at == 0 || closes_at <= opened_at || closes_at > job.deadline {
        blockers.push(ContractBlocker::InvalidMarketWindow);
    }
    if !blockers.is_empty() {
        return Err(blockers);
    }
    Ok(OutcomeMarket {
        market_id,
        job_digest: job.digest(),
        mode: OutcomeMode::BinarySuccess,
        source,
        status: MarketStatus::Frozen,
        opened_at,
        closes_at,
    })
}

pub fn open_outcome_market(
    market: &OutcomeMarket,
    now: u64,
) -> Result<OutcomeMarket, Vec<ContractBlocker>> {
    let mut blockers = Vec::new();
    if market.status != MarketStatus::Frozen {
        blockers.push(ContractBlocker::InvalidMarketTransition);
    }
    if now < market.opened_at || now >= market.closes_at {
        blockers.push(ContractBlocker::MarketOutsideOpenWindow);
    }
    if blockers.is_empty() {
        let mut opened = market.clone();
        opened.status = MarketStatus::Open;
        Ok(opened)
    } else {
        Err(blockers)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct MarketObservation {
    pub market_id: String,
    pub job_digest: Digest,
    pub source: MarketSource,
    pub sequence: u64,
    pub observed_at: u64,
    pub yes_price_micros: u64,
    pub liquidity_units: u64,
}

impl MarketObservation {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:observation:v1", self)
    }

    pub fn validate(&self) -> Result<(), Vec<ContractBlocker>> {
        let mut blockers = Vec::new();
        if self.market_id.is_empty() {
            blockers.push(ContractBlocker::EmptyMarketId);
        }
        if self.job_digest.is_zero() {
            blockers.push(ContractBlocker::MissingJobDigest);
        }
        if self.sequence == 0 {
            blockers.push(ContractBlocker::ZeroObservationSequence);
        }
        if self.observed_at == 0 {
            blockers.push(ContractBlocker::ZeroObservationTime);
        }
        if self.yes_price_micros > PRICE_SCALE_MICROS {
            blockers.push(ContractBlocker::PriceOutOfRange);
        }
        if self.liquidity_units == 0 {
            blockers.push(ContractBlocker::ZeroLiquidity);
        }
        if blockers.is_empty() {
            Ok(())
        } else {
            Err(blockers)
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct MarketState {
    pub market_digest: Digest,
    pub observations: Vec<MarketObservation>,
}

impl MarketState {
    pub fn new(market: &OutcomeMarket) -> Self {
        Self {
            market_digest: market.digest(),
            observations: Vec::new(),
        }
    }

    pub fn record(
        &self,
        market: &OutcomeMarket,
        observation: MarketObservation,
    ) -> Result<Self, Vec<ContractBlocker>> {
        let mut blockers = Vec::new();
        if self.market_digest != market.digest() {
            blockers.push(ContractBlocker::InvalidMarketState);
        }
        let previous_sequence = self.observations.last().map(|item| item.sequence);
        if let Err(mut observation_blockers) =
            validate_market_observation(market, &observation, previous_sequence)
        {
            blockers.append(&mut observation_blockers);
        }
        if blockers.is_empty() {
            let mut next = self.clone();
            next.observations.push(observation);
            Ok(next)
        } else {
            Err(blockers)
        }
    }

    pub fn close_signal(
        &self,
        market: &OutcomeMarket,
        now: u64,
    ) -> Result<MarketSignal, Vec<ContractBlocker>> {
        let mut blockers = Vec::new();
        if self.market_digest != market.digest() {
            blockers.push(ContractBlocker::InvalidMarketState);
        }
        if market.status != MarketStatus::Open {
            blockers.push(ContractBlocker::InvalidMarketTransition);
        }
        if now < market.closes_at {
            blockers.push(ContractBlocker::MarketNotClosed);
        }
        if self.observations.is_empty() {
            blockers.push(ContractBlocker::NoObservations);
        }
        if !blockers.is_empty() {
            return Err(blockers);
        }
        let mut weighted_sum = 0_u128;
        let mut duration_sum = 0_u128;
        for (index, observation) in self.observations.iter().enumerate() {
            let end = self
                .observations
                .get(index + 1)
                .map(|next| next.observed_at)
                .unwrap_or(market.closes_at);
            let duration = end.saturating_sub(observation.observed_at) as u128;
            let weighted = (observation.yes_price_micros as u128)
                .checked_mul(duration)
                .ok_or_else(|| vec![ContractBlocker::TwapOverflow])?;
            weighted_sum = weighted_sum
                .checked_add(weighted)
                .ok_or_else(|| vec![ContractBlocker::TwapOverflow])?;
            duration_sum = duration_sum
                .checked_add(duration)
                .ok_or_else(|| vec![ContractBlocker::TwapOverflow])?;
        }
        if duration_sum == 0 {
            return Err(vec![ContractBlocker::TwapOverflow]);
        }
        Ok(MarketSignal {
            market_digest: self.market_digest.clone(),
            yes_price_micros: (weighted_sum / duration_sum) as u64,
            observation_count: self.observations.len() as u64,
            observed_from: self.observations[0].observed_at,
            observed_until: market.closes_at,
            advisory_only: true,
        })
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct MarketSignal {
    pub market_digest: Digest,
    pub yes_price_micros: u64,
    pub observation_count: u64,
    pub observed_from: u64,
    pub observed_until: u64,
    pub advisory_only: bool,
}

impl MarketSignal {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:signal:v1", self)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct WorkEvidencePacket {
    pub evidence_id: String,
    pub job_digest: Digest,
    pub provider_id: String,
    pub artifact_digest: Digest,
    pub evaluator_id: String,
    pub evaluator_digest: Digest,
    pub assessment_set_commitment: Digest,
    pub status: EvidenceStatus,
    pub submitted_at: u64,
    pub accepted_at: Option<u64>,
    pub independently_validated: bool,
    pub contradictory: bool,
}

impl WorkEvidencePacket {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:evidence:v1", self)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ResolutionDecision {
    pub job_digest: Digest,
    pub evidence_digest: Digest,
    pub outcome: WorkOutcome,
    pub resolved_at: u64,
    pub resolver_id: String,
    pub payout_eligible: bool,
    pub authority_granted: bool,
}

impl ResolutionDecision {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:resolution:v1", self)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PayoutIntent {
    pub payout_id: String,
    pub job_digest: Digest,
    pub evidence_digest: Digest,
    pub resolution_digest: Digest,
    pub provider_id: String,
    pub amount_units: u64,
    pub rail: PaymentRail,
    pub idempotency_key: String,
    pub status: PayoutStatus,
    pub authority_granted: bool,
}

impl PayoutIntent {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:payout:v1", self)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum ContractBlocker {
    EmptyJobId,
    EmptyBuyerId,
    MissingJobDigest,
    ZeroResourceBudget,
    ZeroDeadline,
    EmptyCapabilitySet,
    InvalidPriceBounds,
    EmptyPaymentRails,
    EmptyClaimCeiling,
    EmptyMarketId,
    InvalidMarketWindow,
    InvalidMarketTransition,
    MarketOutsideOpenWindow,
    ZeroObservationSequence,
    ZeroObservationTime,
    PriceOutOfRange,
    ObservationMarketMismatch,
    ObservationJobMismatch,
    ObservationSourceMismatch,
    ObservationSequenceReplay,
    ZeroLiquidity,
    InvalidMarketState,
    MarketNotClosed,
    NoObservations,
    TwapOverflow,
    EmptyEvidenceId,
    EmptyProviderId,
    MissingArtifactDigest,
    EmptyEvaluatorId,
    MissingEvaluatorDigest,
    EvidenceJobMismatch,
    AssessmentCommitmentMismatch,
    ZeroSubmissionTime,
    AcceptedEvidenceMissingTime,
    EvidenceAfterGracePeriod,
    EvidenceNotIndependent,
    ContradictoryEvidence,
    EmptyResolverId,
    ZeroResolutionTime,
    ResolutionJobMismatch,
    ResolutionEvidenceMismatch,
    ResolutionProviderMismatch,
    ResolutionNotPayoutEligible,
    ResolutionAuthorityGranted,
    EmptyPayoutId,
    EmptyIdempotencyKey,
    UnsupportedPaymentRail,
    InvalidPayoutStatus,
    PayoutAuthorityGranted,
}

pub fn validate_market_observation(
    market: &OutcomeMarket,
    observation: &MarketObservation,
    previous_sequence: Option<u64>,
) -> Result<(), Vec<ContractBlocker>> {
    let mut blockers = observation.validate().err().unwrap_or_default();
    if observation.market_id != market.market_id {
        blockers.push(ContractBlocker::ObservationMarketMismatch);
    }
    if observation.job_digest != market.job_digest {
        blockers.push(ContractBlocker::ObservationJobMismatch);
    }
    if observation.source != market.source {
        blockers.push(ContractBlocker::ObservationSourceMismatch);
    }
    if let Some(previous) = previous_sequence {
        if observation.sequence <= previous {
            blockers.push(ContractBlocker::ObservationSequenceReplay);
        }
    }
    if market.status != MarketStatus::Open
        || observation.observed_at < market.opened_at
        || observation.observed_at >= market.closes_at
    {
        blockers.push(ContractBlocker::MarketOutsideOpenWindow);
    }
    if blockers.is_empty() {
        Ok(())
    } else {
        Err(blockers)
    }
}

pub fn resolve_work(
    job: &WorkJob,
    evidence: &WorkEvidencePacket,
    resolved_at: u64,
) -> Result<ResolutionDecision, Vec<ContractBlocker>> {
    let mut blockers = job.validate().err().unwrap_or_default();
    if evidence.evidence_id.is_empty() {
        blockers.push(ContractBlocker::EmptyEvidenceId);
    }
    if evidence.provider_id.is_empty() {
        blockers.push(ContractBlocker::EmptyProviderId);
    }
    if evidence.artifact_digest.is_zero() {
        blockers.push(ContractBlocker::MissingArtifactDigest);
    }
    if evidence.evaluator_id.is_empty() {
        blockers.push(ContractBlocker::EmptyEvaluatorId);
    }
    if evidence.evaluator_digest.is_zero() {
        blockers.push(ContractBlocker::MissingEvaluatorDigest);
    }
    if evidence.job_digest != job.digest() {
        blockers.push(ContractBlocker::EvidenceJobMismatch);
    }
    if evidence.assessment_set_commitment != job.assessment_set_commitment {
        blockers.push(ContractBlocker::AssessmentCommitmentMismatch);
    }
    if evidence.submitted_at == 0 {
        blockers.push(ContractBlocker::ZeroSubmissionTime);
    }
    if evidence.submitted_at > job.deadline.saturating_add(job.grace_period) {
        blockers.push(ContractBlocker::EvidenceAfterGracePeriod);
    }
    if evidence.contradictory {
        blockers.push(ContractBlocker::ContradictoryEvidence);
    }
    if matches!(
        evidence.status,
        EvidenceStatus::Accepted | EvidenceStatus::Rejected
    ) && !evidence.independently_validated
    {
        blockers.push(ContractBlocker::EvidenceNotIndependent);
    }
    if evidence.status == EvidenceStatus::Accepted {
        match evidence.accepted_at {
            Some(accepted_at) if accepted_at <= job.deadline.saturating_add(job.grace_period) => {}
            Some(_) => blockers.push(ContractBlocker::EvidenceAfterGracePeriod),
            None => blockers.push(ContractBlocker::AcceptedEvidenceMissingTime),
        }
    }
    if resolved_at == 0 {
        blockers.push(ContractBlocker::ZeroResolutionTime);
    }
    if !blockers.is_empty() {
        return Err(blockers);
    }
    let outcome = match evidence.status {
        EvidenceStatus::Accepted => WorkOutcome::Yes,
        EvidenceStatus::Rejected => WorkOutcome::No,
        EvidenceStatus::Unknown => WorkOutcome::Unknown,
    };
    Ok(ResolutionDecision {
        job_digest: job.digest(),
        evidence_digest: evidence.digest(),
        outcome,
        resolved_at,
        resolver_id: evidence.evaluator_id.clone(),
        payout_eligible: outcome == WorkOutcome::Yes,
        authority_granted: false,
    })
}

pub fn build_payout_intent(
    job: &WorkJob,
    evidence: &WorkEvidencePacket,
    resolution: &ResolutionDecision,
    payout_id: impl Into<String>,
    rail: PaymentRail,
    idempotency_key: impl Into<String>,
) -> Result<PayoutIntent, Vec<ContractBlocker>> {
    let mut blockers = job.validate().err().unwrap_or_default();
    let payout_id = payout_id.into();
    let idempotency_key = idempotency_key.into();
    if payout_id.is_empty() {
        blockers.push(ContractBlocker::EmptyPayoutId);
    }
    if idempotency_key.is_empty() {
        blockers.push(ContractBlocker::EmptyIdempotencyKey);
    }
    if !job.payment_rails.contains(&rail) {
        blockers.push(ContractBlocker::UnsupportedPaymentRail);
    }
    if resolution.job_digest != job.digest() {
        blockers.push(ContractBlocker::ResolutionJobMismatch);
    }
    if resolution.evidence_digest != evidence.digest() {
        blockers.push(ContractBlocker::ResolutionEvidenceMismatch);
    }
    if resolution.outcome != WorkOutcome::Yes || !resolution.payout_eligible {
        blockers.push(ContractBlocker::ResolutionNotPayoutEligible);
    }
    if resolution.authority_granted {
        blockers.push(ContractBlocker::ResolutionAuthorityGranted);
    }
    if !blockers.is_empty() {
        return Err(blockers);
    }
    Ok(PayoutIntent {
        payout_id,
        job_digest: job.digest(),
        evidence_digest: evidence.digest(),
        resolution_digest: resolution.digest(),
        provider_id: evidence.provider_id.clone(),
        amount_units: job.base_bounty_units,
        rail,
        idempotency_key,
        status: PayoutStatus::PendingAuthorization,
        authority_granted: false,
    })
}

fn canonical_digest<T: Serialize>(tag: &str, value: &T) -> Digest {
    let bytes = serde_json::to_vec(value).expect("contract values serialize");
    let mut hasher = Sha256::new();
    hasher.update(tag.as_bytes());
    hasher.update([0]);
    hasher.update((bytes.len() as u64).to_le_bytes());
    hasher.update(bytes);
    let output = hasher.finalize();
    let mut digest = [0; 32];
    digest.copy_from_slice(&output);
    Digest::from_bytes(digest)
}

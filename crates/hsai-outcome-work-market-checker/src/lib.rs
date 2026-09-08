#![forbid(unsafe_code)]

//! Independent local checker for the outcome-priced work-market contracts.
//!
//! State-slice mutation: `hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-contracts-v1`.

use hsai_control_plane::Digest;
use hsai_outcome_work_market::{
    build_payout_intent, resolve_work, validate_market_observation, ContractBlocker,
    MarketObservation, MarketSignal, MarketState, OutcomeMarket, PayoutIntent, ResolutionDecision,
    WorkEvidencePacket, WorkJob,
};

pub const STATE_SLICE: &str =
    "hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-contracts-v1";
pub const CLAIM_BOUNDARY: &str = "independent local pure-data outcome-work-market invariant checks only; no signature verification, proof verification, execution, settlement, policy authority, or alignment claim";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckerViolation {
    InvalidJob,
    MarketJobDigestMismatch,
    InvalidMarketWindow,
    InvalidObservation,
    MarketStateDigestMismatch,
    MarketSignalInvalid,
    ResolutionInputInvalid,
    ResolutionDigestMismatch,
    ResolutionOutcomeMismatch,
    ResolutionPayoutMismatch,
    ResolutionAuthorityGranted,
    PayoutInputInvalid,
    PayoutDigestMismatch,
    PayoutAuthorityGranted,
    PayoutStatusInvalid,
}

pub fn check_work_job(job: &WorkJob) -> Vec<CheckerViolation> {
    if job.validate().is_err() {
        vec![CheckerViolation::InvalidJob]
    } else {
        Vec::new()
    }
}

pub fn check_outcome_market(job: &WorkJob, market: &OutcomeMarket) -> Vec<CheckerViolation> {
    let mut violations = Vec::new();
    if !check_work_job(job).is_empty() {
        violations.push(CheckerViolation::InvalidJob);
    }
    if market.job_digest != job.digest() {
        violations.push(CheckerViolation::MarketJobDigestMismatch);
    }
    if market.market_id.is_empty() || market.opened_at == 0 || market.closes_at <= market.opened_at
    {
        violations.push(CheckerViolation::InvalidMarketWindow);
    }
    violations
}

pub fn check_market_observation(
    market: &OutcomeMarket,
    observation: &MarketObservation,
    previous_sequence: Option<u64>,
) -> Vec<CheckerViolation> {
    if validate_market_observation(market, observation, previous_sequence).is_err() {
        vec![CheckerViolation::InvalidObservation]
    } else {
        Vec::new()
    }
}

pub fn check_market_state(market: &OutcomeMarket, state: &MarketState) -> Vec<CheckerViolation> {
    if state.market_digest != market.digest() {
        return vec![CheckerViolation::MarketStateDigestMismatch];
    }
    let mut previous_sequence = None;
    let mut violations = Vec::new();
    for observation in &state.observations {
        if !check_market_observation(market, observation, previous_sequence).is_empty() {
            violations.push(CheckerViolation::InvalidObservation);
        }
        previous_sequence = Some(observation.sequence);
    }
    violations
}

pub fn check_market_signal(
    market: &OutcomeMarket,
    state: &MarketState,
    signal: &MarketSignal,
    now: u64,
) -> Vec<CheckerViolation> {
    let Ok(expected) = state.close_signal(market, now) else {
        return vec![CheckerViolation::MarketSignalInvalid];
    };
    if signal != &expected {
        vec![CheckerViolation::MarketSignalInvalid]
    } else {
        Vec::new()
    }
}

pub fn check_resolution(
    job: &WorkJob,
    evidence: &WorkEvidencePacket,
    resolution: &ResolutionDecision,
) -> Vec<CheckerViolation> {
    let Ok(expected) = resolve_work(job, evidence, resolution.resolved_at) else {
        return vec![CheckerViolation::ResolutionInputInvalid];
    };
    let mut violations = Vec::new();
    if resolution.job_digest != job.digest() {
        violations.push(CheckerViolation::ResolutionDigestMismatch);
    }
    if resolution.evidence_digest != evidence.digest() {
        violations.push(CheckerViolation::ResolutionDigestMismatch);
    }
    if resolution.outcome != expected.outcome {
        violations.push(CheckerViolation::ResolutionOutcomeMismatch);
    }
    if resolution.payout_eligible != expected.payout_eligible {
        violations.push(CheckerViolation::ResolutionPayoutMismatch);
    }
    if resolution.authority_granted {
        violations.push(CheckerViolation::ResolutionAuthorityGranted);
    }
    violations
}

pub fn check_payout_intent(
    job: &WorkJob,
    evidence: &WorkEvidencePacket,
    resolution: &ResolutionDecision,
    payout: &PayoutIntent,
) -> Vec<CheckerViolation> {
    let Ok(expected) = build_payout_intent(
        job,
        evidence,
        resolution,
        payout.payout_id.clone(),
        payout.rail,
        payout.idempotency_key.clone(),
    ) else {
        return vec![CheckerViolation::PayoutInputInvalid];
    };
    let mut violations = Vec::new();
    if payout != &expected {
        violations.push(CheckerViolation::PayoutDigestMismatch);
    }
    if payout.authority_granted {
        violations.push(CheckerViolation::PayoutAuthorityGranted);
    }
    if payout.status != hsai_outcome_work_market::PayoutStatus::PendingAuthorization {
        violations.push(CheckerViolation::PayoutStatusInvalid);
    }
    violations
}

pub fn check_digest_present(digest: &Digest) -> bool {
    !digest.is_zero()
}

#[allow(dead_code)]
fn _contract_blocker_type_is_public(_: Option<ContractBlocker>) {}

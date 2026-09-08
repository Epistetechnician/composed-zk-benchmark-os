#![forbid(unsafe_code)]

//! Implementation-diverse validation for local outcome-work projections.
//!
//! State-slice mutation: `hsai-proof-carrying-capability-bounded-agent-platform-offchain-work-market-checker-v1`.
//! The checker does not execute providers, connect to external markets, move
//! value, or grant authority.

use hsai_outcome_work_market::MarketState;
use hsai_outcome_work_market_offchain::{
    MarketProjection, MatchRecord, OffchainEvent, OffchainMarketLog, WorkQuote,
};

pub const STATE_SLICE: &str =
    "hsai-proof-carrying-capability-bounded-agent-platform-offchain-work-market-checker-v1";
pub const CLAIM_BOUNDARY: &str =
    "independent local projection checking only; no proof, payment, settlement, or authority claim";

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CheckerViolation {
    ProjectionMismatch,
    EventAfterClose,
    DuplicateQuote,
    DuplicateFill,
    UnknownQuote,
    FillMismatch,
    CapacityExceeded,
    InvalidQuote,
    InvalidClose,
}

pub fn check_projection(
    log: &OffchainMarketLog,
    projection: &MarketProjection,
) -> Result<(), Vec<CheckerViolation>> {
    let mut violations = Vec::new();
    let mut state = MarketState::new(&log.market);
    let mut bids: Vec<WorkQuote> = Vec::new();
    let mut fills: Vec<MatchRecord> = Vec::new();
    let mut signal = None;
    let mut closed = false;
    let mut quote_count = 0_u64;

    for event in &log.events {
        match event {
            OffchainEvent::Quote(observation) => {
                if closed {
                    violations.push(CheckerViolation::EventAfterClose);
                } else {
                    match state.record(&log.market, observation.clone()) {
                        Ok(next) => {
                            state = next;
                            quote_count += 1;
                        }
                        Err(_) => violations.push(CheckerViolation::InvalidQuote),
                    }
                }
            }
            OffchainEvent::Bid(bid) => {
                if closed {
                    violations.push(CheckerViolation::EventAfterClose);
                } else if bids.iter().any(|item| item.quote_id == bid.quote_id) {
                    violations.push(CheckerViolation::DuplicateQuote);
                } else if !valid_bid(&log.market, bid) {
                    violations.push(CheckerViolation::InvalidQuote);
                } else {
                    bids.push(bid.clone());
                }
            }
            OffchainEvent::Fill(fill) => {
                if closed {
                    violations.push(CheckerViolation::EventAfterClose);
                } else if fills.iter().any(|item| item.quote_id == fill.quote_id) {
                    violations.push(CheckerViolation::DuplicateFill);
                } else {
                    let Some(bid) = bids.iter().find(|item| item.quote_id == fill.quote_id) else {
                        violations.push(CheckerViolation::UnknownQuote);
                        continue;
                    };
                    if !valid_fill(&log.market, bid, fill) {
                        violations.push(CheckerViolation::FillMismatch);
                    } else {
                        let allocated = fills
                            .iter()
                            .filter(|item| item.quote_id == fill.quote_id)
                            .map(|item| item.allocated_units)
                            .sum::<u64>();
                        if fill.allocated_units > bid.capacity_units.saturating_sub(allocated) {
                            violations.push(CheckerViolation::CapacityExceeded);
                        } else {
                            fills.push(fill.clone());
                        }
                    }
                }
            }
            OffchainEvent::Close { closed_at } => {
                if closed {
                    violations.push(CheckerViolation::InvalidClose);
                } else if let Ok(candidate) = state.close_signal(&log.market, *closed_at) {
                    signal = Some(candidate);
                    closed = true;
                } else {
                    violations.push(CheckerViolation::InvalidClose);
                }
            }
        }
    }

    let expected_last_sequence = state.observations.last().map_or(0, |item| item.sequence);
    if projection.market_digest != state.market_digest
        || projection.log_digest != log.digest()
        || projection.quote_count != quote_count
        || projection.last_sequence != expected_last_sequence
        || projection.bid_count != bids.len() as u64
        || projection.fill_count != fills.len() as u64
        || projection.fills != fills
        || projection.signal != signal
    {
        violations.push(CheckerViolation::ProjectionMismatch);
    }
    if violations.is_empty() {
        Ok(())
    } else {
        Err(violations)
    }
}

fn valid_bid(market: &hsai_outcome_work_market::OutcomeMarket, bid: &WorkQuote) -> bool {
    !bid.quote_id.is_empty()
        && !bid.provider_id.is_empty()
        && bid.market_digest == market.digest()
        && bid.job_digest == market.job_digest
        && bid.price_units > 0
        && bid.success_probability_micros <= hsai_outcome_work_market::PRICE_SCALE_MICROS
        && bid.capacity_units > 0
        && bid.posted_at >= market.opened_at
        && bid.posted_at < market.closes_at
        && bid.expires_at > bid.posted_at
}

fn valid_fill(
    market: &hsai_outcome_work_market::OutcomeMarket,
    bid: &WorkQuote,
    fill: &MatchRecord,
) -> bool {
    !fill.allocation_id.is_empty()
        && fill.market_digest == market.digest()
        && fill.job_digest == bid.job_digest
        && fill.quote_id == bid.quote_id
        && fill.provider_id == bid.provider_id
        && fill.price_units == bid.price_units
        && fill.allocated_units > 0
        && fill.allocated_units <= bid.capacity_units
        && fill.matched_at >= bid.posted_at
        && fill.matched_at < bid.expires_at
}

#![forbid(unsafe_code)]

//! Deterministic internal-credit simulation for the outcome-priced work market.
//!
//! State-slice mutation: `hsai-proof-carrying-capability-bounded-agent-platform-offchain-work-market-v1`.
//! This crate replays local events and produces advisory projections. It does
//! not connect to a market, move value, execute work, or grant authority.

use hsai_control_plane::Digest;
use hsai_outcome_work_market::{
    validate_market_observation, MarketObservation, MarketSignal, MarketState, MarketStatus,
    OutcomeMarket, WorkJob, PRICE_SCALE_MICROS,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest as ShaDigest, Sha256};

mod storage;

pub use storage::{EventLogStorageError, OffchainMarketLogFileStore};

pub const STATE_SLICE: &str =
    "hsai-proof-carrying-capability-bounded-agent-platform-offchain-work-market-v1";
pub const SCHEMA_VERSION: &str = "hsai-outcome-work-market:offchain-log:v1";
pub const CLAIM_BOUNDARY: &str =
    "local deterministic internal-credit market simulation only; advisory projections are not proof, payment authorization, or external settlement";

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum OffchainEvent {
    Quote(MarketObservation),
    Bid(WorkQuote),
    Fill(MatchRecord),
    Close { closed_at: u64 },
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct WorkQuote {
    pub quote_id: String,
    pub market_digest: Digest,
    pub job_digest: Digest,
    pub provider_id: String,
    pub price_units: u64,
    pub success_probability_micros: u64,
    pub capacity_units: u64,
    pub posted_at: u64,
    pub expires_at: u64,
}

impl WorkQuote {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:work-quote:v1", self)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct MatchRecord {
    pub allocation_id: String,
    pub quote_id: String,
    pub market_digest: Digest,
    pub job_digest: Digest,
    pub provider_id: String,
    pub price_units: u64,
    pub allocated_units: u64,
    pub matched_at: u64,
}

impl MatchRecord {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:match:v1", self)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OffchainMarketLog {
    pub market: OutcomeMarket,
    pub events: Vec<OffchainEvent>,
}

impl OffchainMarketLog {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:offchain-log:v1", self)
    }
}

pub fn encode_event_log(log: &OffchainMarketLog) -> Result<Vec<u8>, Vec<OffchainBlocker>> {
    serde_json::to_vec(log).map_err(|_| vec![OffchainBlocker::EventLogEncoding])
}

pub fn decode_event_log(bytes: &[u8]) -> Result<OffchainMarketLog, Vec<OffchainBlocker>> {
    serde_json::from_slice(bytes).map_err(|_| vec![OffchainBlocker::EventLogDecoding])
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct MarketProjection {
    pub market_digest: Digest,
    pub log_digest: Digest,
    pub quote_count: u64,
    pub last_sequence: u64,
    pub bid_count: u64,
    pub fill_count: u64,
    pub fills: Vec<MatchRecord>,
    pub signal: Option<MarketSignal>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum BaselineMechanism {
    FixedBounty,
    ProviderAuction,
    OutcomeMarket,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct BaselineQuote {
    pub mechanism: BaselineMechanism,
    pub price_units: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum OffchainBlocker {
    EmptyEventLog,
    MarketNotOpen,
    EventAfterClose,
    CloseAlreadyRecorded,
    InvalidCloseTime,
    InvalidObservation(Vec<String>),
    EmptyQuoteId,
    EmptyProviderId,
    InvalidBidBinding,
    BidPriceOutOfRange,
    InvalidBidWindow,
    DuplicateQuote,
    UnknownQuote,
    DuplicateFill,
    FillMismatch,
    CapacityExceeded,
    NoEligibleBid,
    EventLogEncoding,
    EventLogDecoding,
}

pub fn create_offchain_log(
    market: &OutcomeMarket,
) -> Result<OffchainMarketLog, Vec<OffchainBlocker>> {
    if market.status != MarketStatus::Open {
        return Err(vec![OffchainBlocker::MarketNotOpen]);
    }
    Ok(OffchainMarketLog {
        market: market.clone(),
        events: Vec::new(),
    })
}

pub fn append_quote(
    log: &OffchainMarketLog,
    observation: MarketObservation,
) -> Result<OffchainMarketLog, Vec<OffchainBlocker>> {
    let mut blockers = Vec::new();
    if log
        .events
        .iter()
        .any(|event| matches!(event, OffchainEvent::Close { .. }))
    {
        blockers.push(OffchainBlocker::EventAfterClose);
    }
    let previous_sequence = log.events.iter().rev().find_map(|event| match event {
        OffchainEvent::Quote(item) => Some(item.sequence),
        OffchainEvent::Close { .. } => None,
        OffchainEvent::Bid(_) | OffchainEvent::Fill(_) => None,
    });
    if let Err(items) = validate_market_observation(&log.market, &observation, previous_sequence) {
        blockers.push(OffchainBlocker::InvalidObservation(
            items.into_iter().map(|item| format!("{item:?}")).collect(),
        ));
    }
    if blockers.is_empty() {
        let mut next = log.clone();
        next.events.push(OffchainEvent::Quote(observation));
        Ok(next)
    } else {
        Err(blockers)
    }
}

pub fn append_provider_bid(
    log: &OffchainMarketLog,
    job: &WorkJob,
    bid: WorkQuote,
) -> Result<OffchainMarketLog, Vec<OffchainBlocker>> {
    let mut blockers = validate_bid(log, job, &bid);
    if log.events.iter().any(
        |event| matches!(event, OffchainEvent::Bid(existing) if existing.quote_id == bid.quote_id),
    ) {
        blockers.push(OffchainBlocker::DuplicateQuote);
    }
    if blockers.is_empty() {
        let mut next = log.clone();
        next.events.push(OffchainEvent::Bid(bid));
        Ok(next)
    } else {
        Err(blockers)
    }
}

pub fn match_best_bid(
    log: &OffchainMarketLog,
    job: &WorkJob,
    now: u64,
) -> Result<MatchRecord, Vec<OffchainBlocker>> {
    if log
        .events
        .iter()
        .any(|event| matches!(event, OffchainEvent::Close { .. }))
    {
        return Err(vec![OffchainBlocker::EventAfterClose]);
    }
    let bids = log.events.iter().filter_map(|event| match event {
        OffchainEvent::Bid(bid) if bid.posted_at <= now && now < bid.expires_at => Some(bid),
        _ => None,
    });
    let best = bids
        .filter(|bid| remaining_capacity(log, bid) > 0)
        .min_by(|left, right| {
            left.price_units
                .cmp(&right.price_units)
                .then_with(|| {
                    right
                        .success_probability_micros
                        .cmp(&left.success_probability_micros)
                })
                .then_with(|| left.quote_id.cmp(&right.quote_id))
        });
    let Some(best) = best else {
        return Err(vec![OffchainBlocker::NoEligibleBid]);
    };
    if best.job_digest != job.digest() || best.price_units > job.max_price_units {
        return Err(vec![OffchainBlocker::InvalidBidBinding]);
    }
    let allocation_number = log
        .events
        .iter()
        .filter_map(|event| match event {
            OffchainEvent::Fill(fill) if fill.quote_id == best.quote_id => Some(()),
            _ => None,
        })
        .count()
        + 1;
    Ok(MatchRecord {
        allocation_id: format!("allocation:{}:{}:{}", best.quote_id, now, allocation_number),
        quote_id: best.quote_id.clone(),
        market_digest: best.market_digest.clone(),
        job_digest: best.job_digest.clone(),
        provider_id: best.provider_id.clone(),
        price_units: best.price_units,
        allocated_units: 1,
        matched_at: now,
    })
}

pub fn append_fill(
    log: &OffchainMarketLog,
    fill: MatchRecord,
) -> Result<OffchainMarketLog, Vec<OffchainBlocker>> {
    let mut blockers = Vec::new();
    if log
        .events
        .iter()
        .any(|event| matches!(event, OffchainEvent::Close { .. }))
    {
        blockers.push(OffchainBlocker::EventAfterClose);
    }
    if log.events.iter().any(|event| {
        matches!(event, OffchainEvent::Fill(existing) if existing.allocation_id == fill.allocation_id)
    }) {
        blockers.push(OffchainBlocker::DuplicateFill);
    }
    let Some(bid) = log.events.iter().find_map(|event| match event {
        OffchainEvent::Bid(bid) if bid.quote_id == fill.quote_id => Some(bid),
        _ => None,
    }) else {
        blockers.push(OffchainBlocker::UnknownQuote);
        return Err(blockers);
    };
    if !fill_matches_bid(&log.market, bid, &fill) {
        blockers.push(OffchainBlocker::FillMismatch);
    }
    if fill.allocated_units > remaining_capacity(log, bid) {
        blockers.push(OffchainBlocker::CapacityExceeded);
    }
    if blockers.is_empty() {
        let mut next = log.clone();
        next.events.push(OffchainEvent::Fill(fill));
        Ok(next)
    } else {
        Err(blockers)
    }
}

pub fn close_market(
    log: &OffchainMarketLog,
    closed_at: u64,
) -> Result<OffchainMarketLog, Vec<OffchainBlocker>> {
    let mut blockers = Vec::new();
    if log
        .events
        .iter()
        .any(|event| matches!(event, OffchainEvent::Close { .. }))
    {
        blockers.push(OffchainBlocker::CloseAlreadyRecorded);
    }
    if closed_at < log.market.closes_at {
        blockers.push(OffchainBlocker::InvalidCloseTime);
    }
    if blockers.is_empty() {
        let mut next = log.clone();
        next.events.push(OffchainEvent::Close { closed_at });
        Ok(next)
    } else {
        Err(blockers)
    }
}

pub fn replay_projection(
    log: &OffchainMarketLog,
) -> Result<MarketProjection, Vec<OffchainBlocker>> {
    if log.events.is_empty() {
        return Err(vec![OffchainBlocker::EmptyEventLog]);
    }
    let mut state = MarketState::new(&log.market);
    let mut bids = Vec::new();
    let mut fills = Vec::new();
    let mut signal = None;
    for event in &log.events {
        match event {
            OffchainEvent::Quote(observation) => {
                if signal.is_some() {
                    return Err(vec![OffchainBlocker::EventAfterClose]);
                }
                state = state
                    .record(&log.market, observation.clone())
                    .map_err(|items| {
                        vec![OffchainBlocker::InvalidObservation(
                            items.into_iter().map(|item| format!("{item:?}")).collect(),
                        )]
                    })?;
            }
            OffchainEvent::Bid(bid) => {
                if signal.is_some() {
                    return Err(vec![OffchainBlocker::EventAfterClose]);
                }
                if bids
                    .iter()
                    .any(|existing: &WorkQuote| existing.quote_id == bid.quote_id)
                {
                    return Err(vec![OffchainBlocker::DuplicateQuote]);
                }
                if !validate_bid_basic(&log.market, bid) {
                    return Err(vec![OffchainBlocker::InvalidBidBinding]);
                }
                bids.push(bid.clone());
            }
            OffchainEvent::Fill(fill) => {
                if signal.is_some() {
                    return Err(vec![OffchainBlocker::EventAfterClose]);
                }
                if fills
                    .iter()
                    .any(|existing: &MatchRecord| existing.allocation_id == fill.allocation_id)
                {
                    return Err(vec![OffchainBlocker::DuplicateFill]);
                }
                let Some(bid) = bids.iter().find(|bid| bid.quote_id == fill.quote_id) else {
                    return Err(vec![OffchainBlocker::UnknownQuote]);
                };
                if !fill_matches_bid(&log.market, bid, fill) {
                    return Err(vec![OffchainBlocker::FillMismatch]);
                }
                let allocated = fills
                    .iter()
                    .filter(|existing| existing.quote_id == fill.quote_id)
                    .map(|existing| existing.allocated_units)
                    .sum::<u64>();
                if fill.allocated_units > bid.capacity_units.saturating_sub(allocated) {
                    return Err(vec![OffchainBlocker::CapacityExceeded]);
                }
                fills.push(fill.clone());
            }
            OffchainEvent::Close { closed_at } => {
                if signal.is_some() {
                    return Err(vec![OffchainBlocker::CloseAlreadyRecorded]);
                }
                signal = Some(
                    state
                        .close_signal(&log.market, *closed_at)
                        .map_err(|items| {
                            vec![OffchainBlocker::InvalidObservation(
                                items.into_iter().map(|item| format!("{item:?}")).collect(),
                            )]
                        })?,
                );
            }
        }
    }
    Ok(MarketProjection {
        market_digest: state.market_digest,
        log_digest: log.digest(),
        quote_count: state.observations.len() as u64,
        last_sequence: state.observations.last().map_or(0, |item| item.sequence),
        bid_count: bids.len() as u64,
        fill_count: fills.len() as u64,
        fills,
        signal,
    })
}

pub fn project_advisory_budget(job: &WorkJob, signal: &MarketSignal) -> u64 {
    let spread = job.max_price_units.saturating_sub(job.base_bounty_units) as u128;
    let premium = spread * signal.yes_price_micros as u128 / 1_000_000;
    job.base_bounty_units
        .saturating_add(u64::try_from(premium).unwrap_or(u64::MAX))
}

fn validate_bid(log: &OffchainMarketLog, job: &WorkJob, bid: &WorkQuote) -> Vec<OffchainBlocker> {
    let mut blockers = Vec::new();
    if log
        .events
        .iter()
        .any(|event| matches!(event, OffchainEvent::Close { .. }))
    {
        blockers.push(OffchainBlocker::EventAfterClose);
    }
    if bid.quote_id.is_empty() {
        blockers.push(OffchainBlocker::EmptyQuoteId);
    }
    if bid.provider_id.is_empty() {
        blockers.push(OffchainBlocker::EmptyProviderId);
    }
    if bid.market_digest != log.market.digest() || bid.job_digest != job.digest() {
        blockers.push(OffchainBlocker::InvalidBidBinding);
    }
    if bid.price_units == 0 || bid.price_units > job.max_price_units {
        blockers.push(OffchainBlocker::BidPriceOutOfRange);
    }
    if bid.success_probability_micros > PRICE_SCALE_MICROS || bid.capacity_units == 0 {
        blockers.push(OffchainBlocker::BidPriceOutOfRange);
    }
    if bid.posted_at < log.market.opened_at
        || bid.posted_at >= log.market.closes_at
        || bid.expires_at <= bid.posted_at
        || bid.expires_at > job.deadline
    {
        blockers.push(OffchainBlocker::InvalidBidWindow);
    }
    blockers
}

fn validate_bid_basic(market: &OutcomeMarket, bid: &WorkQuote) -> bool {
    !bid.quote_id.is_empty()
        && !bid.provider_id.is_empty()
        && bid.market_digest == market.digest()
        && bid.job_digest == market.job_digest
        && bid.price_units > 0
        && bid.success_probability_micros <= PRICE_SCALE_MICROS
        && bid.capacity_units > 0
        && bid.posted_at >= market.opened_at
        && bid.posted_at < market.closes_at
        && bid.expires_at > bid.posted_at
}

fn fill_matches_bid(market: &OutcomeMarket, bid: &WorkQuote, fill: &MatchRecord) -> bool {
    !fill.allocation_id.is_empty()
        && fill.market_digest == market.digest()
        && fill.job_digest == bid.job_digest
        && fill.quote_id == bid.quote_id
        && fill.provider_id == bid.provider_id
        && fill.price_units == bid.price_units
        && fill.allocated_units > 0
        && fill.matched_at >= bid.posted_at
        && fill.matched_at < bid.expires_at
}

fn remaining_capacity(log: &OffchainMarketLog, bid: &WorkQuote) -> u64 {
    let allocated = log
        .events
        .iter()
        .filter_map(|event| match event {
            OffchainEvent::Fill(fill) if fill.quote_id == bid.quote_id => {
                Some(fill.allocated_units)
            }
            _ => None,
        })
        .sum::<u64>();
    bid.capacity_units.saturating_sub(allocated)
}

fn canonical_digest<T: Serialize>(tag: &str, value: &T) -> Digest {
    let bytes = serde_json::to_vec(value).expect("offchain values serialize");
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

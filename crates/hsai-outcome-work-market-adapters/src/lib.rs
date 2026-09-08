#![forbid(unsafe_code)]

//! Dry-run records for external outcome-market and payout Adapters.
//!
//! State-slice mutation: `hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-adapters-v1`.
//! This crate does not perform network calls, sign transactions, move value,
//! or grant authority.

use hsai_control_plane::Digest;
use hsai_outcome_work_market::{PaymentRail, PayoutIntent};
use serde::{Deserialize, Serialize};
use sha2::{Digest as ShaDigest, Sha256};

pub const STATE_SLICE: &str =
    "hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-adapters-v1";
pub const CLAIM_BOUNDARY: &str = "local dry-run Adapter records only; no network call, transaction signing, value movement, proof verification, or authority";
pub const HYPERLIQUID_TESTNET_CHAIN_ID: u64 = 998;
pub const HYPERLIQUID_TESTNET_RPC_URL: &str = "https://rpc.hyperliquid-testnet.xyz/evm";
pub const HYPERLIQUID_TESTNET_API_URL: &str = "https://api.hyperliquid-testnet.xyz";

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct HyperliquidTestnetConfig {
    pub chain_id: u64,
    pub rpc_url: String,
    pub api_url: String,
    pub market_id: String,
    pub market_digest: Digest,
    pub job_digest: Digest,
}

impl HyperliquidTestnetConfig {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:hyperliquid-config:v1", self)
    }

    pub fn validate(&self) -> Result<(), Vec<AdapterBlocker>> {
        let mut blockers = Vec::new();
        if self.chain_id != HYPERLIQUID_TESTNET_CHAIN_ID {
            blockers.push(AdapterBlocker::ChainIdMismatch);
        }
        if self.rpc_url != HYPERLIQUID_TESTNET_RPC_URL {
            blockers.push(AdapterBlocker::RpcUrlMismatch);
        }
        if self.api_url != HYPERLIQUID_TESTNET_API_URL {
            blockers.push(AdapterBlocker::ApiUrlMismatch);
        }
        if self.market_id.is_empty() {
            blockers.push(AdapterBlocker::EmptyMarketId);
        }
        if self.market_digest.is_zero() || self.job_digest.is_zero() {
            blockers.push(AdapterBlocker::MissingBindingDigest);
        }
        if blockers.is_empty() {
            Ok(())
        } else {
            Err(blockers)
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum ChainObservationStatus {
    Pending,
    Confirmed,
    Rejected,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct HyperliquidObservation {
    pub observation_id: String,
    pub config_digest: Digest,
    pub tx_reference: String,
    pub block_number: Option<u64>,
    pub status: ChainObservationStatus,
    pub observed_at: u64,
    pub market_signal_digest: Digest,
}

impl HyperliquidObservation {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:hyperliquid-observation:v1", self)
    }
}

pub fn prepare_hyperliquid_observation(
    config: &HyperliquidTestnetConfig,
    observation_id: impl Into<String>,
    tx_reference: impl Into<String>,
    market_signal_digest: Digest,
    observed_at: u64,
) -> Result<HyperliquidObservation, Vec<AdapterBlocker>> {
    let mut blockers = config.validate().err().unwrap_or_default();
    let observation_id = observation_id.into();
    let tx_reference = tx_reference.into();
    if observation_id.is_empty() {
        blockers.push(AdapterBlocker::EmptyObservationId);
    }
    if tx_reference.is_empty() {
        blockers.push(AdapterBlocker::EmptyTransactionReference);
    }
    if market_signal_digest.is_zero() {
        blockers.push(AdapterBlocker::MissingSignalDigest);
    }
    if observed_at == 0 {
        blockers.push(AdapterBlocker::ZeroObservationTime);
    }
    if !blockers.is_empty() {
        return Err(blockers);
    }
    Ok(HyperliquidObservation {
        observation_id,
        config_digest: config.digest(),
        tx_reference,
        block_number: None,
        status: ChainObservationStatus::Pending,
        observed_at,
        market_signal_digest,
    })
}

pub fn confirm_hyperliquid_observation(
    config: &HyperliquidTestnetConfig,
    observation: &HyperliquidObservation,
    block_number: u64,
) -> Result<HyperliquidObservation, Vec<AdapterBlocker>> {
    let mut blockers = config.validate().err().unwrap_or_default();
    if observation.config_digest != config.digest() {
        blockers.push(AdapterBlocker::ConfigDigestMismatch);
    }
    if observation.status != ChainObservationStatus::Pending {
        blockers.push(AdapterBlocker::InvalidChainTransition);
    }
    if block_number == 0 {
        blockers.push(AdapterBlocker::ZeroBlockNumber);
    }
    if !blockers.is_empty() {
        return Err(blockers);
    }
    let mut confirmed = observation.clone();
    confirmed.block_number = Some(block_number);
    confirmed.status = ChainObservationStatus::Confirmed;
    Ok(confirmed)
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum PaymentPreparationStatus {
    Prepared,
    Submitted,
    Confirmed,
    Refunded,
    Failed,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PaymentPreparation {
    pub payout_digest: Digest,
    pub rail: PaymentRail,
    pub recipient_id: String,
    pub amount_units: u64,
    pub idempotency_key: String,
    pub status: PaymentPreparationStatus,
    pub external_reference: Option<String>,
    pub confirmed_at: Option<u64>,
}

impl PaymentPreparation {
    pub fn digest(&self) -> Digest {
        canonical_digest("hsai-outcome-work-market:payment-preparation:v1", self)
    }
}

pub fn prepare_payment(
    payout: &PayoutIntent,
    recipient_id: impl Into<String>,
) -> Result<PaymentPreparation, Vec<AdapterBlocker>> {
    let mut blockers = Vec::new();
    let recipient_id = recipient_id.into();
    if payout.authority_granted {
        blockers.push(AdapterBlocker::PayoutAlreadyGrantedAuthority);
    }
    if payout.status != hsai_outcome_work_market::PayoutStatus::PendingAuthorization {
        blockers.push(AdapterBlocker::PayoutNotPendingAuthorization);
    }
    if recipient_id.is_empty() {
        blockers.push(AdapterBlocker::EmptyRecipientId);
    }
    if payout.idempotency_key.is_empty() {
        blockers.push(AdapterBlocker::EmptyIdempotencyKey);
    }
    if payout.amount_units == 0 || payout.job_digest.is_zero() || payout.evidence_digest.is_zero() {
        blockers.push(AdapterBlocker::InvalidPayoutBinding);
    }
    if !blockers.is_empty() {
        return Err(blockers);
    }
    Ok(PaymentPreparation {
        payout_digest: payout.digest(),
        rail: payout.rail,
        recipient_id,
        amount_units: payout.amount_units,
        idempotency_key: payout.idempotency_key.clone(),
        status: PaymentPreparationStatus::Prepared,
        external_reference: None,
        confirmed_at: None,
    })
}

pub fn reconcile_payment(
    payment: &PaymentPreparation,
    external_reference: impl Into<String>,
    status: PaymentPreparationStatus,
    confirmed_at: Option<u64>,
) -> Result<PaymentPreparation, Vec<AdapterBlocker>> {
    let mut blockers = Vec::new();
    let external_reference = external_reference.into();
    if payment.status != PaymentPreparationStatus::Prepared
        && payment.status != PaymentPreparationStatus::Submitted
    {
        blockers.push(AdapterBlocker::InvalidPaymentTransition);
    }
    if external_reference.is_empty() {
        blockers.push(AdapterBlocker::EmptyExternalReference);
    }
    if status == PaymentPreparationStatus::Prepared {
        blockers.push(AdapterBlocker::InvalidPaymentTransition);
    }
    if status == PaymentPreparationStatus::Confirmed
        && confirmed_at.map_or(true, |timestamp| timestamp == 0)
    {
        blockers.push(AdapterBlocker::MissingConfirmationTime);
    }
    if !blockers.is_empty() {
        return Err(blockers);
    }
    let mut reconciled = payment.clone();
    reconciled.external_reference = Some(external_reference);
    reconciled.status = status;
    reconciled.confirmed_at = confirmed_at;
    Ok(reconciled)
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AdapterBlocker {
    ChainIdMismatch,
    RpcUrlMismatch,
    ApiUrlMismatch,
    EmptyMarketId,
    MissingBindingDigest,
    EmptyObservationId,
    EmptyTransactionReference,
    MissingSignalDigest,
    ZeroObservationTime,
    ConfigDigestMismatch,
    InvalidChainTransition,
    ZeroBlockNumber,
    PayoutAlreadyGrantedAuthority,
    PayoutNotPendingAuthorization,
    EmptyRecipientId,
    EmptyIdempotencyKey,
    InvalidPayoutBinding,
    InvalidPaymentTransition,
    EmptyExternalReference,
    MissingConfirmationTime,
}

fn canonical_digest<T: Serialize>(tag: &str, value: &T) -> Digest {
    let bytes = serde_json::to_vec(value).expect("adapter values serialize");
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

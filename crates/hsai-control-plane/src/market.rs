use crate::{hash_parts, CapabilitySet, Digest};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum ComputeRoute {
    Local,
    GeneralMesh,
    ProofMarket,
    ConfidentialMesh,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum ConfidentialityTier {
    Plain,
    TransportEncrypted,
    Mpc,
    Fhe,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum VerifiabilityTier {
    None,
    Receipt,
    ZkProof,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ComputeJobRequest {
    pub job_id: String,
    pub program_digest: Digest,
    pub input_commitment: Digest,
    pub route: ComputeRoute,
    pub required_capabilities: CapabilitySet,
    pub minimum_confidentiality: ConfidentialityTier,
    pub minimum_verifiability: VerifiabilityTier,
    pub max_price_units: u64,
    pub deadline: u64,
}

impl ComputeJobRequest {
    pub fn digest(&self) -> Digest {
        hash_parts(
            "hsai-control-plane:compute-job-request:v1",
            &[
                self.job_id.clone(),
                self.program_digest.to_hex(),
                self.input_commitment.to_hex(),
                format!("{:?}", self.route),
                self.required_capabilities.canonical(),
                format!("{:?}", self.minimum_confidentiality),
                format!("{:?}", self.minimum_verifiability),
                self.max_price_units.to_string(),
                self.deadline.to_string(),
            ],
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ComputeOffer {
    pub offer_id: String,
    pub job_id: String,
    pub provider_id: String,
    pub offered_capabilities: CapabilitySet,
    pub confidentiality: ConfidentialityTier,
    pub verifiability: VerifiabilityTier,
    pub price_units: u64,
    pub completion_deadline: u64,
    pub result_digest: Option<Digest>,
    pub proof_digest: Option<Digest>,
}

impl ComputeOffer {
    pub fn digest(&self) -> Digest {
        hash_parts(
            "hsai-control-plane:compute-offer:v1",
            &[
                self.offer_id.clone(),
                self.job_id.clone(),
                self.provider_id.clone(),
                self.offered_capabilities.canonical(),
                format!("{:?}", self.confidentiality),
                format!("{:?}", self.verifiability),
                self.price_units.to_string(),
                self.completion_deadline.to_string(),
                optional_digest(&self.result_digest),
                optional_digest(&self.proof_digest),
            ],
        )
    }
}

fn optional_digest(digest: &Option<Digest>) -> String {
    digest
        .as_ref()
        .map(Digest::to_hex)
        .unwrap_or_else(|| "absent".to_owned())
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum MarketBlocker {
    EmptyJobId,
    EmptyOfferId,
    EmptyProviderId,
    MissingProgramDigest,
    MissingInputCommitment,
    EmptyCapabilitySet,
    JobOfferMismatch,
    PriceLimitExceeded,
    DeadlineExceeded,
    CapabilityNotOffered,
    ConfidentialityInsufficient,
    VerifiabilityInsufficient,
    MissingResultDigest,
    MissingProofDigest,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum SettlementRail {
    Hyperliquid,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct SettlementIntent {
    pub rail: SettlementRail,
    pub job_digest: Digest,
    pub amount_units: u64,
    pub executed: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ComputeMatch {
    pub job_digest: Digest,
    pub offer_digest: Digest,
    pub provider_id: String,
    pub price_units: u64,
    pub settlement: SettlementIntent,
    pub proof_verified: bool,
    pub authority_granted: bool,
}

pub fn match_compute_job(
    job: &ComputeJobRequest,
    offer: &ComputeOffer,
) -> Result<ComputeMatch, Vec<MarketBlocker>> {
    let mut blockers = Vec::new();
    if job.job_id.is_empty() {
        blockers.push(MarketBlocker::EmptyJobId);
    }
    if offer.offer_id.is_empty() {
        blockers.push(MarketBlocker::EmptyOfferId);
    }
    if offer.provider_id.is_empty() {
        blockers.push(MarketBlocker::EmptyProviderId);
    }
    if job.program_digest.is_zero() {
        blockers.push(MarketBlocker::MissingProgramDigest);
    }
    if job.input_commitment.is_zero() {
        blockers.push(MarketBlocker::MissingInputCommitment);
    }
    if job.required_capabilities.is_empty() {
        blockers.push(MarketBlocker::EmptyCapabilitySet);
    }
    if job.job_id != offer.job_id {
        blockers.push(MarketBlocker::JobOfferMismatch);
    }
    if offer.price_units > job.max_price_units {
        blockers.push(MarketBlocker::PriceLimitExceeded);
    }
    if offer.completion_deadline > job.deadline {
        blockers.push(MarketBlocker::DeadlineExceeded);
    }
    for capability in job.required_capabilities.iter() {
        if !offer.offered_capabilities.contains(*capability) {
            blockers.push(MarketBlocker::CapabilityNotOffered);
        }
    }
    if offer.confidentiality < job.minimum_confidentiality {
        blockers.push(MarketBlocker::ConfidentialityInsufficient);
    }
    if offer.verifiability < job.minimum_verifiability {
        blockers.push(MarketBlocker::VerifiabilityInsufficient);
    }
    if job.minimum_verifiability >= VerifiabilityTier::Receipt
        && offer.result_digest.as_ref().map_or(true, Digest::is_zero)
    {
        blockers.push(MarketBlocker::MissingResultDigest);
    }
    if job.minimum_verifiability == VerifiabilityTier::ZkProof
        && offer.proof_digest.as_ref().map_or(true, Digest::is_zero)
    {
        blockers.push(MarketBlocker::MissingProofDigest);
    }
    if !blockers.is_empty() {
        return Err(blockers);
    }
    let job_digest = job.digest();
    Ok(ComputeMatch {
        job_digest: job_digest.clone(),
        offer_digest: offer.digest(),
        provider_id: offer.provider_id.clone(),
        price_units: offer.price_units,
        settlement: SettlementIntent {
            rail: SettlementRail::Hyperliquid,
            job_digest,
            amount_units: offer.price_units,
            executed: false,
        },
        proof_verified: false,
        authority_granted: false,
    })
}

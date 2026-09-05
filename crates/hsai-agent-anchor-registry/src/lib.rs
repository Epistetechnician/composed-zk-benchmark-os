//! Phase 4 Proof of Agent anchor registry.
//!
//! State slice: `agent-identity-end-to-end-verification-hardening-v1`.
//!
//! The registry authorizes only this claim after signed evidence and anchor
//! receipts verify: one active HSAI identity per accepted, non-reused
//! registered anchor set.
//! It does not prove global software-agent uniqueness, competence, safety, or
//! semantic correctness. Output maturity is inherited from admitted inputs and
//! is never elevated by registry bookkeeping.

use hsai_claim_envelope::{
    admits, AcceptancePolicy, ClaimEnvelope, Hash, LaneId, Maturity, Predicate, PropertyKind,
    Rejection, StakeRef, SubjectId, TrustRoot, VkId,
};
use hsai_distinct_agent::Anchor;
use p256::ecdsa::{signature::Verifier, Signature, VerifyingKey};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub const PHASE_4_CLAIM_BOUNDARY: &str =
    "one active HSAI identity per accepted, non-reused registered anchor set; not global software-agent uniqueness";
pub const REGISTRY_EVIDENCE_SIGNATURE_DOMAIN: &str = "hsai-agent-anchor-registry:evidence:v1";
pub const REGISTRY_RECEIPT_SIGNATURE_DOMAIN: &str = "hsai-agent-anchor-registry:receipt:v1";
const REGISTRY_SPONSOR_ANCHOR_DOMAIN: &str = "hsai-agent-anchor-registry:sponsor-anchor:v1";
const REGISTRY_BOND_ANCHOR_DOMAIN: &str = "hsai-agent-anchor-registry:bond-anchor:v1";
const REGISTRY_REPUTATION_ANCHOR_DOMAIN: &str = "hsai-agent-anchor-registry:reputation-anchor:v1";

/// The kind of non-runtime anchor authenticated by an [`AnchorReceipt`].
#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum AnchorReceiptKind {
    Sponsor,
    Bond,
    Reputation,
}

/// A signed receipt for one sponsor, bond, or reputation anchor.
#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct AnchorReceipt {
    pub kind: AnchorReceiptKind,
    pub anchor_id: String,
    pub anchor_digest: Hash,
    pub lane: LaneId,
    pub issued_at: u64,
    pub expires_at: u64,
    pub signer_key_id: String,
    pub signature: Vec<u8>,
}

impl AnchorReceipt {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        kind: AnchorReceiptKind,
        anchor_id: impl Into<String>,
        anchor_digest: Hash,
        lane: LaneId,
        issued_at: u64,
        expires_at: u64,
        signer_key_id: impl Into<String>,
        signature: Vec<u8>,
    ) -> Self {
        Self {
            kind,
            anchor_id: anchor_id.into(),
            anchor_digest,
            lane,
            issued_at,
            expires_at,
            signer_key_id: signer_key_id.into(),
            signature,
        }
    }
}

/// An evidence envelope signed by a trusted registry lane.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct SignedClaimEnvelope {
    pub anchor_set_id: Hash,
    pub envelope: ClaimEnvelope,
    pub signer_key_id: String,
    pub signature: Vec<u8>,
}

impl SignedClaimEnvelope {
    pub fn new(
        anchor_set_id: Hash,
        envelope: ClaimEnvelope,
        signer_key_id: impl Into<String>,
        signature: Vec<u8>,
    ) -> Self {
        Self {
            anchor_set_id,
            envelope,
            signer_key_id: signer_key_id.into(),
            signature,
        }
    }
}

/// A public key trusted for one or more registry evidence lanes.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RegistryTrustedKey {
    pub key_id: String,
    pub x: Vec<u8>,
    pub y: Vec<u8>,
    pub trusted_lanes: BTreeSet<LaneId>,
    trust_root: TrustRoot,
}

impl RegistryTrustedKey {
    pub fn new(key_id: impl Into<String>, x: Vec<u8>, y: Vec<u8>, trusted_lane: LaneId) -> Self {
        let key_id = key_id.into();
        Self {
            trust_root: TrustRoot::VerifyingKey(VkId(format!("agent-anchor-registry:{key_id}"))),
            key_id,
            x,
            y,
            trusted_lanes: BTreeSet::from([trusted_lane]),
        }
    }
}

/// A verified envelope that cannot be constructed from caller data alone.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VerifiedClaimEnvelope {
    envelope: ClaimEnvelope,
}

/// Offline verifier for signed registry evidence and anchor receipts.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RegistryEvidenceVerifier {
    keys_by_id: BTreeMap<String, RegistryTrustedKey>,
}

impl RegistryEvidenceVerifier {
    /// Build a verifier from deployment-provided trusted key configuration.
    ///
    /// This constructor does not authenticate the configuration itself. The
    /// deployment must load these keys and lane assignments from an
    /// immutable/operator-authenticated trust store; caller-controlled key
    /// configuration cannot establish a trusted registry identity.
    pub fn new(keys: Vec<RegistryTrustedKey>) -> Self {
        Self {
            keys_by_id: keys
                .into_iter()
                .map(|key| (key.key_id.clone(), key))
                .collect(),
        }
    }

    pub fn verify(
        &self,
        anchor_set: &AgentAnchorSet,
        signed: &SignedClaimEnvelope,
        now: u64,
    ) -> Result<VerifiedClaimEnvelope, RegistryVerificationError> {
        if signed.anchor_set_id != anchor_set.anchor_set_id() {
            return Err(RegistryVerificationError::AnchorSetMismatch);
        }
        let key = self
            .keys_by_id
            .get(&signed.signer_key_id)
            .ok_or(RegistryVerificationError::UnknownKey)?;
        if !key.trusted_lanes.contains(&signed.envelope.lane) {
            return Err(RegistryVerificationError::UntrustedLane);
        }
        verify_key_signature(
            key,
            &claim_envelope_signature_preimage(signed.anchor_set_id, &signed.envelope),
            &signed.signature,
        )?;
        if !signed.envelope.valid.contains(now) {
            return Err(RegistryVerificationError::EvidenceExpired);
        }

        let mut envelope = signed.envelope.clone();
        envelope.trust_roots.insert(key.trust_root.clone());
        Ok(VerifiedClaimEnvelope { envelope })
    }

    fn verify_receipts(
        &self,
        anchor_set: &AgentAnchorSet,
        now: u64,
    ) -> Result<BTreeSet<TrustRoot>, RegistryVerificationError> {
        let expected = expected_receipts(anchor_set);
        if expected.is_empty() && !anchor_set.anchor_receipts.is_empty() {
            return Err(RegistryVerificationError::UnexpectedAnchorReceipt);
        }
        let mut seen = BTreeSet::new();
        let mut trust_roots = BTreeSet::new();
        for receipt in &anchor_set.anchor_receipts {
            let key = self
                .keys_by_id
                .get(&receipt.signer_key_id)
                .ok_or(RegistryVerificationError::UnknownKey)?;
            if !key.trusted_lanes.contains(&receipt.lane) {
                return Err(RegistryVerificationError::UntrustedLane);
            }
            if receipt.issued_at > receipt.expires_at || !receipt_valid_at(receipt, now) {
                return Err(RegistryVerificationError::ReceiptExpired);
            }
            verify_key_signature(
                key,
                &anchor_receipt_signature_preimage(&anchor_set.subject, receipt),
                &receipt.signature,
            )?;
            let identity = (receipt.kind.clone(), receipt.anchor_id.clone());
            let Some(expected_digest) = expected.get(&identity) else {
                return Err(RegistryVerificationError::UnexpectedAnchorReceipt);
            };
            if receipt.anchor_digest != *expected_digest {
                return Err(RegistryVerificationError::AnchorDigestMismatch(
                    receipt.anchor_id.clone(),
                ));
            }
            if !seen.insert(identity) {
                return Err(RegistryVerificationError::UnexpectedAnchorReceipt);
            }
            trust_roots.insert(key.trust_root.clone());
        }
        for (identity, _) in expected {
            if !seen.contains(&identity) {
                return Err(RegistryVerificationError::MissingAnchorReceipt(identity.1));
            }
        }
        Ok(trust_roots)
    }
}

/// Failure modes at the cryptographic registry boundary.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum RegistryVerificationError {
    AnchorSetMismatch,
    UnknownKey,
    UntrustedLane,
    InvalidKey,
    InvalidSignature,
    HighSSignature,
    EvidenceExpired,
    MissingAnchorReceipt(String),
    UnexpectedAnchorReceipt,
    AnchorDigestMismatch(String),
    ReceiptExpired,
}

pub fn claim_envelope_signature_preimage(anchor_set_id: Hash, envelope: &ClaimEnvelope) -> Vec<u8> {
    let body = (anchor_set_id, envelope);
    domain_preimage(REGISTRY_EVIDENCE_SIGNATURE_DOMAIN, &body)
}

pub fn anchor_receipt_signature_preimage(subject: &SubjectId, receipt: &AnchorReceipt) -> Vec<u8> {
    let body = (
        subject,
        &receipt.kind,
        &receipt.anchor_id,
        receipt.anchor_digest,
        &receipt.lane,
        receipt.issued_at,
        receipt.expires_at,
        &receipt.signer_key_id,
    );
    domain_preimage(REGISTRY_RECEIPT_SIGNATURE_DOMAIN, &body)
}

fn domain_preimage<T: Serialize>(domain: &str, value: &T) -> Vec<u8> {
    let bytes = serde_json::to_vec(value).expect("registry signing body must serialize");
    let mut preimage = Vec::with_capacity(domain.len() + 8 + bytes.len());
    preimage.extend_from_slice(domain.as_bytes());
    preimage.extend_from_slice(&(bytes.len() as u64).to_be_bytes());
    preimage.extend_from_slice(&bytes);
    preimage
}

pub fn sponsor_anchor_digest(anchor: &SponsorAnchor) -> Hash {
    anchor_digest(REGISTRY_SPONSOR_ANCHOR_DOMAIN, anchor)
}

pub fn bond_anchor_digest(anchor: &BondAnchor) -> Hash {
    anchor_digest(REGISTRY_BOND_ANCHOR_DOMAIN, anchor)
}

pub fn reputation_anchor_digest(anchor: &ReputationAnchor) -> Hash {
    anchor_digest(REGISTRY_REPUTATION_ANCHOR_DOMAIN, anchor)
}

fn anchor_digest<T: Serialize>(domain: &str, anchor: &T) -> Hash {
    let digest = Sha256::digest(domain_preimage(domain, anchor));
    let mut out = [0_u8; 32];
    out.copy_from_slice(&digest);
    Hash(out)
}

fn verify_key_signature(
    key: &RegistryTrustedKey,
    preimage: &[u8],
    signature_bytes: &[u8],
) -> Result<(), RegistryVerificationError> {
    if key.x.len() != 32 || key.y.len() != 32 {
        return Err(RegistryVerificationError::InvalidKey);
    }
    let mut sec1 = Vec::with_capacity(65);
    sec1.push(0x04);
    sec1.extend_from_slice(&key.x);
    sec1.extend_from_slice(&key.y);
    let verifying_key =
        VerifyingKey::from_sec1_bytes(&sec1).map_err(|_| RegistryVerificationError::InvalidKey)?;
    let signature = Signature::from_slice(signature_bytes)
        .map_err(|_| RegistryVerificationError::InvalidSignature)?;
    if signature.normalize_s().is_some() {
        return Err(RegistryVerificationError::HighSSignature);
    }
    verifying_key
        .verify(preimage, &signature)
        .map_err(|_| RegistryVerificationError::InvalidSignature)
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum AnchorTier {
    ClaimedAgent,
    HardwareAnchoredAgent,
    HumanitySponsoredAgent,
    BondedAgent,
    CompositeDistinctAgent,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum SponsorshipPolicy {
    OneAgentPerSponsor,
    LimitedAgentsPerSponsor { max: u64 },
    UnlimitedLowTrust,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum SponsorAnchor {
    ProofOfHumanity {
        humanity_id: String,
        policy: SponsorshipPolicy,
    },
    LegalEntity {
        registry: String,
        entity_id: String,
        policy: SponsorshipPolicy,
    },
    WebCredential {
        issuer: String,
        credential_id: String,
        policy: SponsorshipPolicy,
    },
}

impl SponsorAnchor {
    pub fn sponsor_id(&self) -> String {
        match self {
            Self::ProofOfHumanity { humanity_id, .. } => {
                format!("poh:{humanity_id}")
            }
            Self::LegalEntity {
                registry,
                entity_id,
                ..
            } => format!("legal:{registry}:{entity_id}"),
            Self::WebCredential {
                issuer,
                credential_id,
                ..
            } => format!("web:{issuer}:{credential_id}"),
        }
    }

    pub fn policy(&self) -> &SponsorshipPolicy {
        match self {
            Self::ProofOfHumanity { policy, .. }
            | Self::LegalEntity { policy, .. }
            | Self::WebCredential { policy, .. } => policy,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct BondAnchor {
    pub bond_id: String,
    pub amount: u64,
    pub slash_policy_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct ReputationAnchor {
    pub agent_id: String,
    pub since: u64,
    pub min_observations: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentAnchorSet {
    pub subject: SubjectId,
    pub runtime_anchors: BTreeSet<Anchor>,
    pub sponsor_anchors: BTreeSet<SponsorAnchor>,
    pub bond_anchors: BTreeSet<BondAnchor>,
    pub reputation_anchor: Option<ReputationAnchor>,
    pub anchor_receipts: BTreeSet<AnchorReceipt>,
}

impl Default for AgentAnchorSet {
    fn default() -> Self {
        Self {
            subject: SubjectId(String::new()),
            runtime_anchors: BTreeSet::new(),
            sponsor_anchors: BTreeSet::new(),
            bond_anchors: BTreeSet::new(),
            reputation_anchor: None,
            anchor_receipts: BTreeSet::new(),
        }
    }
}

impl AgentAnchorSet {
    pub fn anchor_set_id(&self) -> Hash {
        let bytes = serde_json::to_vec(self).expect("agent anchor set must serialize");
        let digest = Sha256::digest(bytes);
        let mut out = [0u8; 32];
        out.copy_from_slice(&digest);
        Hash(out)
    }

    pub fn is_empty(&self) -> bool {
        self.runtime_anchors.is_empty()
            && self.sponsor_anchors.is_empty()
            && self.bond_anchors.is_empty()
            && self.reputation_anchor.is_none()
    }

    pub fn tier(&self) -> AnchorTier {
        let has_runtime = !self.runtime_anchors.is_empty();
        let has_sponsor = !self.sponsor_anchors.is_empty();
        let has_bond = !self.bond_anchors.is_empty();
        let has_reputation = self.reputation_anchor.is_some();

        match (has_runtime, has_sponsor, has_bond, has_reputation) {
            (true, true, _, _) | (true, _, true, true) | (_, true, true, true) => {
                AnchorTier::CompositeDistinctAgent
            }
            (true, _, _, _) => AnchorTier::HardwareAnchoredAgent,
            (_, true, true, _) => AnchorTier::CompositeDistinctAgent,
            (_, true, _, _) => AnchorTier::HumanitySponsoredAgent,
            (_, _, true, _) => AnchorTier::BondedAgent,
            _ => AnchorTier::ClaimedAgent,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RegisteredAgentAnchor {
    pub subject: SubjectId,
    pub anchor_set: AgentAnchorSet,
    pub anchor_set_id: Hash,
    pub tier: AnchorTier,
    pub opened_at: u64,
    pub revoked_at: Option<u64>,
    pub envelope: ClaimEnvelope,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AgentAnchorError {
    NotAdmitted(Vec<Rejection>),
    OpenAssumption(Predicate),
    AnchorReuse(String),
    SponsorReuse(String),
    BondReuse(String),
    RevokedAnchor(String),
    EmptyAnchorSet,
    InsufficientTier,
    AlreadyRegistered(SubjectId),
    SubjectMismatch {
        expected: SubjectId,
        actual: SubjectId,
    },
    MissingRuntimeValidity(String),
    UnverifiedEvidence,
    EvidenceVerification(RegistryVerificationError),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum RegistryStateError {
    ActiveRuntimeIndexMismatch {
        indexed: BTreeSet<String>,
        derived: BTreeSet<String>,
    },
    ActiveBondIndexMismatch {
        indexed: BTreeSet<String>,
        derived: BTreeSet<String>,
    },
    SponsorUseCountMismatch {
        indexed: BTreeMap<String, u64>,
        derived: BTreeMap<String, u64>,
    },
    RevokedRuntimeStillActive(String),
    RegisteredTierMismatch {
        subject: SubjectId,
        actual: AnchorTier,
        expected: AnchorTier,
    },
    RevokedRegistrationStillHasActiveTier(SubjectId),
}

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentAnchorRegistry {
    active: BTreeMap<SubjectId, RegisteredAgentAnchor>,
    used_runtime_anchors: BTreeSet<String>,
    used_bond_anchors: BTreeSet<String>,
    sponsor_use_counts: BTreeMap<String, u64>,
    revoked_runtime_anchors: BTreeSet<String>,
}

impl AgentAnchorRegistry {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register(
        &mut self,
        _anchor_set: AgentAnchorSet,
        _evidence: ClaimEnvelope,
        _policy: AcceptancePolicy,
    ) -> Result<&RegisteredAgentAnchor, AgentAnchorError> {
        // State slice: agent-identity-end-to-end-verification-hardening-v1.
        // A plain ClaimEnvelope is caller-constructible data, not registry
        // authorization. Callers must use register_signed with a trusted lane.
        Err(AgentAnchorError::UnverifiedEvidence)
    }

    /// Verify signed evidence and authenticated non-runtime anchor receipts,
    /// then register the exact bound anchor set.
    pub fn register_signed(
        &mut self,
        anchor_set: AgentAnchorSet,
        signed_evidence: SignedClaimEnvelope,
        verifier: &RegistryEvidenceVerifier,
        policy: AcceptancePolicy,
    ) -> Result<&RegisteredAgentAnchor, AgentAnchorError> {
        let mut verified = verifier
            .verify(&anchor_set, &signed_evidence, policy.at)
            .map_err(AgentAnchorError::EvidenceVerification)?;
        let receipt_roots = verifier
            .verify_receipts(&anchor_set, policy.at)
            .map_err(AgentAnchorError::EvidenceVerification)?;
        verified.envelope.trust_roots.extend(receipt_roots);
        self.register_verified(anchor_set, verified, policy)
    }

    fn register_verified(
        &mut self,
        anchor_set: AgentAnchorSet,
        verified: VerifiedClaimEnvelope,
        policy: AcceptancePolicy,
    ) -> Result<&RegisteredAgentAnchor, AgentAnchorError> {
        let evidence = verified.envelope;
        if anchor_set.is_empty() {
            return Err(AgentAnchorError::EmptyAnchorSet);
        }
        if anchor_set.subject != policy_subject(&policy)? {
            return Err(AgentAnchorError::SubjectMismatch {
                expected: policy_subject(&policy)?,
                actual: anchor_set.subject,
            });
        }
        if self.active.contains_key(&anchor_set.subject) {
            return Err(AgentAnchorError::AlreadyRegistered(anchor_set.subject));
        }

        admits(policy.clone(), evidence.clone()).map_err(AgentAnchorError::NotAdmitted)?;
        if let Some(open) = evidence.assumptions.iter().next() {
            return Err(AgentAnchorError::OpenAssumption(open.clone()));
        }

        for anchor in &anchor_set.runtime_anchors {
            let anchor_id = anchor.anchor_id();
            if self.revoked_runtime_anchors.contains(&anchor_id) {
                return Err(AgentAnchorError::RevokedAnchor(anchor_id));
            }
            if self.used_runtime_anchors.contains(&anchor_id) {
                return Err(AgentAnchorError::AnchorReuse(anchor_id));
            }
            if !evidence
                .guarantees
                .contains(&anchor.validity_assumption(&anchor_set.subject))
            {
                return Err(AgentAnchorError::MissingRuntimeValidity(anchor_id));
            }
        }

        for bond in &anchor_set.bond_anchors {
            if self.used_bond_anchors.contains(&bond.bond_id) {
                return Err(AgentAnchorError::BondReuse(bond.bond_id.clone()));
            }
        }

        for sponsor in &anchor_set.sponsor_anchors {
            let sponsor_id = sponsor.sponsor_id();
            let current = *self.sponsor_use_counts.get(&sponsor_id).unwrap_or(&0);
            if !sponsor_allows_count(sponsor.policy(), current.saturating_add(1)) {
                return Err(AgentAnchorError::SponsorReuse(sponsor_id));
            }
        }

        let tier = anchor_set.tier();
        if tier == AnchorTier::ClaimedAgent {
            return Err(AgentAnchorError::InsufficientTier);
        }

        let output = anchor_claim_envelope(&anchor_set, &evidence, tier.clone());
        let registered = RegisteredAgentAnchor {
            subject: anchor_set.subject.clone(),
            anchor_set: anchor_set.clone(),
            anchor_set_id: anchor_set.anchor_set_id(),
            tier,
            opened_at: policy.at,
            revoked_at: None,
            envelope: output,
        };

        self.used_runtime_anchors
            .extend(anchor_set.runtime_anchors.iter().map(Anchor::anchor_id));
        self.used_bond_anchors.extend(
            anchor_set
                .bond_anchors
                .iter()
                .map(|bond| bond.bond_id.clone()),
        );
        for sponsor in &anchor_set.sponsor_anchors {
            let sponsor_id = sponsor.sponsor_id();
            *self.sponsor_use_counts.entry(sponsor_id).or_insert(0) += 1;
        }

        let subject = anchor_set.subject.clone();
        self.active.insert(subject.clone(), registered);
        Ok(self
            .active
            .get(&subject)
            .expect("registered anchor must be present"))
    }

    pub fn revoke_runtime_anchor(
        &mut self,
        subject: &SubjectId,
        anchor: &Anchor,
        revoked_at: u64,
    ) -> Result<&RegisteredAgentAnchor, AgentAnchorError> {
        let registration = self
            .active
            .get_mut(subject)
            .ok_or_else(|| AgentAnchorError::RevokedAnchor(anchor.anchor_id()))?;
        let anchor_id = anchor.anchor_id();
        if !registration.anchor_set.runtime_anchors.remove(anchor) {
            return Err(AgentAnchorError::RevokedAnchor(anchor_id));
        }
        self.revoked_runtime_anchors.insert(anchor_id.clone());
        self.used_runtime_anchors.remove(&anchor_id);

        let updated_tier = registration.anchor_set.tier();
        if updated_tier == AnchorTier::ClaimedAgent {
            registration.tier = AnchorTier::ClaimedAgent;
            registration.envelope.guarantees =
                BTreeSet::from([anchor_tier_predicate(subject, &registration.tier)]);
            registration.revoked_at = Some(revoked_at);
        } else {
            registration.tier = updated_tier;
            registration.envelope.guarantees =
                BTreeSet::from([anchor_tier_predicate(subject, &registration.tier)]);
        }

        Ok(registration)
    }

    pub fn registration(&self, subject: &SubjectId) -> Option<&RegisteredAgentAnchor> {
        self.active.get(subject)
    }

    pub fn active_count(&self) -> usize {
        self.active
            .values()
            .filter(|registration| registration.revoked_at.is_none())
            .count()
    }

    pub fn registered_count(&self) -> usize {
        self.active.len()
    }

    pub fn used_runtime_anchor_ids(&self) -> BTreeSet<String> {
        self.used_runtime_anchors.clone()
    }

    pub fn used_bond_anchor_ids(&self) -> BTreeSet<String> {
        self.used_bond_anchors.clone()
    }

    pub fn sponsor_use_count(&self, sponsor: &SponsorAnchor) -> u64 {
        *self
            .sponsor_use_counts
            .get(&sponsor.sponsor_id())
            .unwrap_or(&0)
    }

    pub fn revoked_runtime_anchor_ids(&self) -> BTreeSet<String> {
        self.revoked_runtime_anchors.clone()
    }

    pub fn validate_internal_state(&self) -> Result<(), RegistryStateError> {
        let mut derived_runtime = BTreeSet::new();
        let mut derived_bonds = BTreeSet::new();
        let mut derived_sponsors = BTreeMap::<String, u64>::new();

        for registration in self.active.values() {
            let expected_tier = registration.anchor_set.tier();
            if registration.revoked_at.is_none() {
                if expected_tier != registration.tier {
                    return Err(RegistryStateError::RegisteredTierMismatch {
                        subject: registration.subject.clone(),
                        actual: registration.tier.clone(),
                        expected: expected_tier,
                    });
                }
                for anchor in &registration.anchor_set.runtime_anchors {
                    let anchor_id = anchor.anchor_id();
                    if self.revoked_runtime_anchors.contains(&anchor_id) {
                        return Err(RegistryStateError::RevokedRuntimeStillActive(anchor_id));
                    }
                    derived_runtime.insert(anchor_id);
                }
                derived_bonds.extend(
                    registration
                        .anchor_set
                        .bond_anchors
                        .iter()
                        .map(|bond| bond.bond_id.clone()),
                );
            } else if registration.tier != AnchorTier::ClaimedAgent
                && registration.anchor_set.tier() == AnchorTier::ClaimedAgent
            {
                return Err(RegistryStateError::RevokedRegistrationStillHasActiveTier(
                    registration.subject.clone(),
                ));
            }

            for sponsor in &registration.anchor_set.sponsor_anchors {
                *derived_sponsors.entry(sponsor.sponsor_id()).or_insert(0) += 1;
            }
        }

        if self.used_runtime_anchors != derived_runtime {
            return Err(RegistryStateError::ActiveRuntimeIndexMismatch {
                indexed: self.used_runtime_anchors.clone(),
                derived: derived_runtime,
            });
        }
        if self.used_bond_anchors != derived_bonds {
            return Err(RegistryStateError::ActiveBondIndexMismatch {
                indexed: self.used_bond_anchors.clone(),
                derived: derived_bonds,
            });
        }
        if self.sponsor_use_counts != derived_sponsors {
            return Err(RegistryStateError::SponsorUseCountMismatch {
                indexed: self.sponsor_use_counts.clone(),
                derived: derived_sponsors,
            });
        }

        Ok(())
    }
}

fn sponsor_allows_count(policy: &SponsorshipPolicy, count: u64) -> bool {
    match policy {
        SponsorshipPolicy::OneAgentPerSponsor => count <= 1,
        SponsorshipPolicy::LimitedAgentsPerSponsor { max } => count <= *max,
        SponsorshipPolicy::UnlimitedLowTrust => true,
    }
}

fn expected_receipts(anchor_set: &AgentAnchorSet) -> BTreeMap<(AnchorReceiptKind, String), Hash> {
    let mut expected = BTreeMap::new();
    expected.extend(anchor_set.sponsor_anchors.iter().map(|anchor| {
        (
            (AnchorReceiptKind::Sponsor, anchor.sponsor_id()),
            sponsor_anchor_digest(anchor),
        )
    }));
    expected.extend(anchor_set.bond_anchors.iter().map(|anchor| {
        (
            (AnchorReceiptKind::Bond, anchor.bond_id.clone()),
            bond_anchor_digest(anchor),
        )
    }));
    if let Some(anchor) = &anchor_set.reputation_anchor {
        expected.insert(
            (AnchorReceiptKind::Reputation, anchor.agent_id.clone()),
            reputation_anchor_digest(anchor),
        );
    }
    expected
}

fn receipt_valid_at(receipt: &AnchorReceipt, now: u64) -> bool {
    receipt.issued_at <= now && now <= receipt.expires_at
}

fn policy_subject(policy: &AcceptancePolicy) -> Result<SubjectId, AgentAnchorError> {
    policy
        .require
        .iter()
        .next()
        .map(|predicate| predicate.subject.clone())
        .ok_or(AgentAnchorError::InsufficientTier)
}

pub fn anchor_tier_predicate(subject: &SubjectId, tier: &AnchorTier) -> Predicate {
    Predicate {
        subject: subject.clone(),
        property: PropertyKind::Custom(format!("agent-anchor-tier:{tier:?}")),
    }
}

pub fn tier_strength(tier: &AnchorTier) -> u8 {
    match tier {
        AnchorTier::ClaimedAgent => 0,
        AnchorTier::HumanitySponsoredAgent => 1,
        AnchorTier::BondedAgent => 2,
        AnchorTier::HardwareAnchoredAgent => 3,
        AnchorTier::CompositeDistinctAgent => 4,
    }
}

fn nonclaim(subject: &SubjectId, label: &str) -> Predicate {
    Predicate {
        subject: subject.clone(),
        property: PropertyKind::Custom(format!("does-not-prove:{label}")),
    }
}

pub fn anchor_claim_envelope(
    anchor_set: &AgentAnchorSet,
    input: &ClaimEnvelope,
    tier: AnchorTier,
) -> ClaimEnvelope {
    let mut excludes = input.excludes.clone();
    excludes.extend([
        nonclaim(&anchor_set.subject, "global-software-agent-uniqueness"),
        nonclaim(&anchor_set.subject, "competence"),
        nonclaim(&anchor_set.subject, "safety"),
        nonclaim(&anchor_set.subject, "semantic-correctness"),
        nonclaim(&anchor_set.subject, "sponsor-controls-every-agent-action"),
    ]);
    if anchor_set.runtime_anchors.is_empty() {
        excludes.insert(nonclaim(&anchor_set.subject, "runtime-scarcity"));
    }

    let mut trust_roots = input.trust_roots.clone();
    trust_roots.extend(
        anchor_set
            .bond_anchors
            .iter()
            .map(|bond| TrustRoot::EconomicStake(StakeRef(bond.bond_id.clone()))),
    );

    ClaimEnvelope::new(
        BTreeSet::from([anchor_tier_predicate(&anchor_set.subject, &tier)]),
        BTreeSet::new(),
        excludes,
        input.maturity.clone(),
        trust_roots,
        input.valid.clone(),
        LaneId::Named("agent-anchor-registry".to_owned()),
    )
}

pub fn anchor_acceptance_policy(
    subject: &SubjectId,
    at: u64,
    min_maturity: Maturity,
) -> AcceptancePolicy {
    AcceptancePolicy {
        require: BTreeSet::from([Predicate {
            subject: subject.clone(),
            property: PropertyKind::Distinctness,
        }]),
        min_maturity,
        forbid_roots: BTreeSet::new(),
        require_closed: true,
        at,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_claim_envelope::{TimeWindow, TrustRootClass, VendorId};
    use hsai_distinct_agent::distinctness;
    use p256::ecdsa::{signature::Signer, Signature, SigningKey, VerifyingKey};
    use proptest::prelude::*;
    use std::sync::OnceLock;

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn runtime_anchor(id: &str) -> Anchor {
        Anchor::HardwareAttested {
            vendor: "phala-dstack".to_owned(),
            device: id.to_owned(),
        }
    }

    fn sponsor(id: &str, policy: SponsorshipPolicy) -> SponsorAnchor {
        SponsorAnchor::ProofOfHumanity {
            humanity_id: id.to_owned(),
            policy,
        }
    }

    fn bond(id: &str) -> BondAnchor {
        BondAnchor {
            bond_id: id.to_owned(),
            amount: 100,
            slash_policy_id: "slash:v1".to_owned(),
        }
    }

    fn closed_runtime_evidence(subject: &SubjectId, anchor: &Anchor, at: u64) -> ClaimEnvelope {
        ClaimEnvelope::new(
            BTreeSet::from([distinctness(subject), anchor.validity_assumption(subject)]),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Attested,
            BTreeSet::from([
                anchor.trust_root(),
                TrustRoot::HardwareVendor(VendorId("managed:phala-trust-center".to_owned())),
            ]),
            TimeWindow {
                start: at - 1,
                end: at + 1,
            },
            LaneId::Named("test-runtime".to_owned()),
        )
    }

    fn closed_sponsor_evidence(subject: &SubjectId, at: u64) -> ClaimEnvelope {
        ClaimEnvelope::new(
            BTreeSet::from([distinctness(subject)]),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Local,
            BTreeSet::new(),
            TimeWindow {
                start: at - 1,
                end: at + 1,
            },
            LaneId::Named("test-sponsor".to_owned()),
        )
    }

    #[test]
    fn caller_constructed_evidence_is_not_registry_authorization() {
        let subject = subject("caller-built");
        let anchor = runtime_anchor("caller-built-cvm");
        let mut registry = AgentAnchorRegistry::new();

        let result = registry.register(
            AgentAnchorSet {
                subject: subject.clone(),
                runtime_anchors: BTreeSet::from([anchor.clone()]),
                ..AgentAnchorSet::default()
            },
            closed_runtime_evidence(&subject, &anchor, 10),
            policy(&subject, 10, Maturity::Attested),
        );

        assert_eq!(result, Err(AgentAnchorError::UnverifiedEvidence));
    }

    #[test]
    fn bookkeeping_only_sponsor_anchor_requires_an_authenticated_receipt() {
        let subject = subject("unreceipted-sponsor");
        let mut registry = AgentAnchorRegistry::new();

        let result = registry.register(
            AgentAnchorSet {
                subject: subject.clone(),
                sponsor_anchors: BTreeSet::from([sponsor(
                    "unreceipted-human",
                    SponsorshipPolicy::OneAgentPerSponsor,
                )]),
                ..AgentAnchorSet::default()
            },
            closed_sponsor_evidence(&subject, 10),
            policy(&subject, 10, Maturity::Local),
        );

        assert_eq!(result, Err(AgentAnchorError::UnverifiedEvidence));
    }

    fn policy(subject: &SubjectId, at: u64, min_maturity: Maturity) -> AcceptancePolicy {
        AcceptancePolicy {
            require: BTreeSet::from([distinctness(subject)]),
            min_maturity,
            forbid_roots: BTreeSet::<TrustRootClass>::new(),
            require_closed: true,
            at,
        }
    }

    fn test_signing_key() -> &'static SigningKey {
        static KEY: OnceLock<SigningKey> = OnceLock::new();
        KEY.get_or_init(|| {
            SigningKey::from_bytes((&[7_u8; 32]).into()).expect("test signing key is valid")
        })
    }

    fn test_verifier() -> &'static RegistryEvidenceVerifier {
        static VERIFIER: OnceLock<RegistryEvidenceVerifier> = OnceLock::new();
        VERIFIER.get_or_init(|| {
            let signing_key = test_signing_key();
            let point = VerifyingKey::from(signing_key).to_encoded_point(false);
            let mut key = RegistryTrustedKey::new(
                "test-registry-key",
                point.x().expect("P-256 point has x").to_vec(),
                point.y().expect("P-256 point has y").to_vec(),
                LaneId::Named("test-runtime".to_owned()),
            );
            key.trusted_lanes
                .insert(LaneId::Named("test-sponsor".to_owned()));
            key.trusted_lanes
                .insert(LaneId::Named("proof-theater".to_owned()));
            key.trusted_lanes
                .insert(LaneId::Named("test-receipt".to_owned()));
            RegistryEvidenceVerifier::new(vec![key])
        })
    }

    fn signed_receipt(
        subject: &SubjectId,
        kind: AnchorReceiptKind,
        anchor_id: String,
        anchor_digest: Hash,
    ) -> AnchorReceipt {
        let mut receipt = AnchorReceipt::new(
            kind,
            anchor_id,
            anchor_digest,
            LaneId::Named("test-receipt".to_owned()),
            0,
            100,
            "test-registry-key",
            Vec::new(),
        );
        let signature: Signature =
            test_signing_key().sign(&anchor_receipt_signature_preimage(subject, &receipt));
        let signature = signature.normalize_s().unwrap_or(signature);
        receipt.signature = signature.to_bytes().to_vec();
        receipt
    }

    fn authenticate_anchor_set(mut anchor_set: AgentAnchorSet) -> AgentAnchorSet {
        let subject = anchor_set.subject.clone();
        for sponsor in &anchor_set.sponsor_anchors {
            anchor_set.anchor_receipts.insert(signed_receipt(
                &subject,
                AnchorReceiptKind::Sponsor,
                sponsor.sponsor_id(),
                sponsor_anchor_digest(sponsor),
            ));
        }
        for bond in &anchor_set.bond_anchors {
            anchor_set.anchor_receipts.insert(signed_receipt(
                &subject,
                AnchorReceiptKind::Bond,
                bond.bond_id.clone(),
                bond_anchor_digest(bond),
            ));
        }
        if let Some(reputation) = &anchor_set.reputation_anchor {
            anchor_set.anchor_receipts.insert(signed_receipt(
                &subject,
                AnchorReceiptKind::Reputation,
                reputation.agent_id.clone(),
                reputation_anchor_digest(reputation),
            ));
        }
        anchor_set
    }

    fn register_test(
        registry: &mut AgentAnchorRegistry,
        anchor_set: AgentAnchorSet,
        evidence: ClaimEnvelope,
        policy: AcceptancePolicy,
    ) -> Result<&RegisteredAgentAnchor, AgentAnchorError> {
        let anchor_set = authenticate_anchor_set(anchor_set);
        let signer = test_signing_key();
        let signed = signed_test_evidence(&anchor_set, evidence, signer);
        let verifier = test_verifier();
        registry.register_signed(anchor_set, signed, verifier, policy)
    }

    fn signed_test_evidence(
        anchor_set: &AgentAnchorSet,
        evidence: ClaimEnvelope,
        signer: &SigningKey,
    ) -> SignedClaimEnvelope {
        let anchor_set_id = anchor_set.anchor_set_id();
        let signature: Signature =
            signer.sign(&claim_envelope_signature_preimage(anchor_set_id, &evidence));
        let signature = signature.normalize_s().unwrap_or(signature);
        SignedClaimEnvelope::new(
            anchor_set_id,
            evidence,
            "test-registry-key",
            signature.to_bytes().to_vec(),
        )
    }

    #[test]
    fn authenticated_evidence_without_sponsor_receipt_is_rejected() {
        let subject = subject("missing-receipt");
        let anchor_set = AgentAnchorSet {
            subject: subject.clone(),
            sponsor_anchors: BTreeSet::from([sponsor(
                "missing-receipt-human",
                SponsorshipPolicy::OneAgentPerSponsor,
            )]),
            ..AgentAnchorSet::default()
        };
        let evidence = closed_sponsor_evidence(&subject, 10);
        let signer = test_signing_key();
        let signed = signed_test_evidence(&anchor_set, evidence, signer);
        let verifier = test_verifier();
        let mut registry = AgentAnchorRegistry::new();

        assert_eq!(
            registry.register_signed(
                anchor_set,
                signed,
                verifier,
                policy(&subject, 10, Maturity::Local),
            ),
            Err(AgentAnchorError::EvidenceVerification(
                RegistryVerificationError::MissingAnchorReceipt(
                    "poh:missing-receipt-human".to_owned()
                )
            ))
        );
    }

    #[test]
    fn authenticated_evidence_signature_and_anchor_set_are_bound() {
        let bound_subject = subject("signed-binding");
        let anchor = runtime_anchor("signed-cvm");
        let anchor_set = AgentAnchorSet {
            subject: bound_subject.clone(),
            runtime_anchors: BTreeSet::from([anchor.clone()]),
            ..AgentAnchorSet::default()
        };
        let evidence = closed_runtime_evidence(&bound_subject, &anchor, 10);
        let signer = test_signing_key();
        let mut signed = signed_test_evidence(&anchor_set, evidence, signer);
        let verifier = test_verifier();
        let mut registry = AgentAnchorRegistry::new();

        signed.signature[0] ^= 1;
        assert_eq!(
            registry.register_signed(
                anchor_set.clone(),
                signed,
                verifier,
                policy(&bound_subject, 10, Maturity::Attested),
            ),
            Err(AgentAnchorError::EvidenceVerification(
                RegistryVerificationError::InvalidSignature
            ))
        );

        let signed = signed_test_evidence(
            &anchor_set,
            closed_runtime_evidence(&bound_subject, &anchor, 10),
            signer,
        );
        let changed_set = AgentAnchorSet {
            subject: bound_subject.clone(),
            runtime_anchors: BTreeSet::from([runtime_anchor("other-cvm")]),
            ..AgentAnchorSet::default()
        };
        assert_eq!(
            registry.register_signed(
                changed_set,
                signed,
                verifier,
                policy(&bound_subject, 10, Maturity::Attested),
            ),
            Err(AgentAnchorError::EvidenceVerification(
                RegistryVerificationError::AnchorSetMismatch
            ))
        );
    }

    #[test]
    fn anchor_receipt_is_bound_to_complete_anchor_contents() {
        let subject = subject("receipt-binding");
        let anchor = sponsor("receipt-human", SponsorshipPolicy::OneAgentPerSponsor);
        let mut anchor_set = AgentAnchorSet {
            subject: subject.clone(),
            sponsor_anchors: BTreeSet::from([anchor.clone()]),
            ..AgentAnchorSet::default()
        };
        let receipt = signed_receipt(
            &subject,
            AnchorReceiptKind::Sponsor,
            anchor.sponsor_id(),
            sponsor_anchor_digest(&sponsor(
                "receipt-human",
                SponsorshipPolicy::UnlimitedLowTrust,
            )),
        );
        anchor_set.anchor_receipts.insert(receipt);
        let signer = test_signing_key();
        let signed =
            signed_test_evidence(&anchor_set, closed_sponsor_evidence(&subject, 10), signer);
        let verifier = test_verifier();

        assert_eq!(
            AgentAnchorRegistry::new().register_signed(
                anchor_set,
                signed,
                verifier,
                policy(&subject, 10, Maturity::Local),
            ),
            Err(AgentAnchorError::EvidenceVerification(
                RegistryVerificationError::AnchorDigestMismatch("poh:receipt-human".to_owned())
            ))
        );
    }

    #[derive(Clone, Debug)]
    enum RegistryStrategyStep {
        RegisterRuntime {
            subject_id: u8,
            anchor_id: u8,
        },
        RegisterSponsor {
            subject_id: u8,
            sponsor_id: u8,
            max_uses: u8,
        },
        RegisterComposite {
            subject_id: u8,
            anchor_id: u8,
            sponsor_id: u8,
        },
        RevokeRuntime {
            subject_id: u8,
            anchor_id: u8,
        },
        Nested(Vec<RegistryStrategyStep>),
    }

    #[derive(Default)]
    struct StrategyOracle {
        registered_subjects: BTreeSet<u8>,
        active_subjects: BTreeSet<u8>,
        runtime_subjects: BTreeMap<u8, u8>,
        subject_sponsors: BTreeMap<u8, BTreeSet<u8>>,
        sponsor_uses: BTreeMap<u8, u64>,
        revoked_runtime_anchors: BTreeSet<u8>,
    }

    fn small_subject(id: u8) -> SubjectId {
        subject(&format!("agent{id}"))
    }

    fn small_runtime_anchor(id: u8) -> Anchor {
        runtime_anchor(&format!("cvm-{id}"))
    }

    fn small_sponsor(id: u8, policy: SponsorshipPolicy) -> SponsorAnchor {
        sponsor(&format!("human-{id}"), policy)
    }

    fn strategy_tree() -> impl Strategy<Value = Vec<RegistryStrategyStep>> {
        let leaf = prop_oneof![
            (0u8..8, 0u8..8).prop_map(|(subject_id, anchor_id)| {
                RegistryStrategyStep::RegisterRuntime {
                    subject_id,
                    anchor_id,
                }
            }),
            (0u8..8, 0u8..8, 1u8..4).prop_map(|(subject_id, sponsor_id, max_uses)| {
                RegistryStrategyStep::RegisterSponsor {
                    subject_id,
                    sponsor_id,
                    max_uses,
                }
            }),
            (0u8..8, 0u8..8, 0u8..8).prop_map(|(subject_id, anchor_id, sponsor_id)| {
                RegistryStrategyStep::RegisterComposite {
                    subject_id,
                    anchor_id,
                    sponsor_id,
                }
            }),
            (0u8..8, 0u8..8).prop_map(|(subject_id, anchor_id)| {
                RegistryStrategyStep::RevokeRuntime {
                    subject_id,
                    anchor_id,
                }
            }),
        ];

        leaf.prop_recursive(3, 32, 4, |inner| {
            proptest::collection::vec(inner, 1..5).prop_map(RegistryStrategyStep::Nested)
        })
        .prop_flat_map(|step| proptest::collection::vec(Just(step), 1..16))
    }

    fn run_strategy_step(
        registry: &mut AgentAnchorRegistry,
        oracle: &mut StrategyOracle,
        step: &RegistryStrategyStep,
    ) {
        match step {
            RegistryStrategyStep::RegisterRuntime {
                subject_id,
                anchor_id,
            } => {
                let subject = small_subject(*subject_id);
                let anchor = small_runtime_anchor(*anchor_id);
                let result = register_test(
                    registry,
                    AgentAnchorSet {
                        subject: subject.clone(),
                        runtime_anchors: BTreeSet::from([anchor.clone()]),
                        ..AgentAnchorSet::default()
                    },
                    closed_runtime_evidence(&subject, &anchor, 10),
                    policy(&subject, 10, Maturity::Attested),
                );
                let expected_ok = !oracle.registered_subjects.contains(subject_id)
                    && !oracle.runtime_subjects.contains_key(anchor_id)
                    && !oracle.revoked_runtime_anchors.contains(anchor_id);
                assert_eq!(result.is_ok(), expected_ok);
                if result.is_ok() {
                    oracle.registered_subjects.insert(*subject_id);
                    oracle.active_subjects.insert(*subject_id);
                    oracle.runtime_subjects.insert(*anchor_id, *subject_id);
                }
            }
            RegistryStrategyStep::RegisterSponsor {
                subject_id,
                sponsor_id,
                max_uses,
            } => {
                let subject = small_subject(*subject_id);
                let sponsor_anchor = small_sponsor(
                    *sponsor_id,
                    SponsorshipPolicy::LimitedAgentsPerSponsor {
                        max: u64::from(*max_uses),
                    },
                );
                let result = register_test(
                    registry,
                    AgentAnchorSet {
                        subject: subject.clone(),
                        sponsor_anchors: BTreeSet::from([sponsor_anchor]),
                        ..AgentAnchorSet::default()
                    },
                    closed_sponsor_evidence(&subject, 10),
                    policy(&subject, 10, Maturity::Local),
                );
                let current_uses = *oracle.sponsor_uses.get(sponsor_id).unwrap_or(&0);
                let expected_ok = !oracle.registered_subjects.contains(subject_id)
                    && current_uses < u64::from(*max_uses);
                assert_eq!(result.is_ok(), expected_ok);
                if result.is_ok() {
                    oracle.registered_subjects.insert(*subject_id);
                    oracle.active_subjects.insert(*subject_id);
                    oracle
                        .subject_sponsors
                        .entry(*subject_id)
                        .or_default()
                        .insert(*sponsor_id);
                    *oracle.sponsor_uses.entry(*sponsor_id).or_insert(0) += 1;
                }
            }
            RegistryStrategyStep::RegisterComposite {
                subject_id,
                anchor_id,
                sponsor_id,
            } => {
                let subject = small_subject(*subject_id);
                let anchor = small_runtime_anchor(*anchor_id);
                let sponsor_anchor =
                    small_sponsor(*sponsor_id, SponsorshipPolicy::OneAgentPerSponsor);
                let result = register_test(
                    registry,
                    AgentAnchorSet {
                        subject: subject.clone(),
                        runtime_anchors: BTreeSet::from([anchor.clone()]),
                        sponsor_anchors: BTreeSet::from([sponsor_anchor]),
                        ..AgentAnchorSet::default()
                    },
                    closed_runtime_evidence(&subject, &anchor, 10),
                    policy(&subject, 10, Maturity::Attested),
                );
                let current_uses = *oracle.sponsor_uses.get(sponsor_id).unwrap_or(&0);
                let expected_ok = !oracle.registered_subjects.contains(subject_id)
                    && !oracle.runtime_subjects.contains_key(anchor_id)
                    && !oracle.revoked_runtime_anchors.contains(anchor_id)
                    && current_uses == 0;
                assert_eq!(result.is_ok(), expected_ok);
                if result.is_ok() {
                    oracle.registered_subjects.insert(*subject_id);
                    oracle.active_subjects.insert(*subject_id);
                    oracle.runtime_subjects.insert(*anchor_id, *subject_id);
                    oracle
                        .subject_sponsors
                        .entry(*subject_id)
                        .or_default()
                        .insert(*sponsor_id);
                    *oracle.sponsor_uses.entry(*sponsor_id).or_insert(0) += 1;
                }
            }
            RegistryStrategyStep::RevokeRuntime {
                subject_id,
                anchor_id,
            } => {
                let subject = small_subject(*subject_id);
                let anchor = small_runtime_anchor(*anchor_id);
                let result = registry.revoke_runtime_anchor(&subject, &anchor, 20);
                let expected_ok = oracle.runtime_subjects.get(anchor_id) == Some(subject_id);
                assert_eq!(result.is_ok(), expected_ok);
                if result.is_ok() {
                    oracle.runtime_subjects.remove(anchor_id);
                    oracle.revoked_runtime_anchors.insert(*anchor_id);
                    if oracle
                        .subject_sponsors
                        .get(subject_id)
                        .map(BTreeSet::is_empty)
                        .unwrap_or(true)
                    {
                        oracle.active_subjects.remove(subject_id);
                    }
                }
            }
            RegistryStrategyStep::Nested(steps) => {
                for nested_step in steps {
                    run_strategy_step(registry, oracle, nested_step);
                }
            }
        }
        registry
            .validate_internal_state()
            .expect("registry indexes must match after every strategy step");
    }

    #[test]
    fn pa_1_hardware_anchor_set_registers() {
        let subject = subject("agentA");
        let anchor = runtime_anchor("cvm-1");
        let set = AgentAnchorSet {
            subject: subject.clone(),
            runtime_anchors: BTreeSet::from([anchor.clone()]),
            ..AgentAnchorSet::default()
        };
        let mut registry = AgentAnchorRegistry::new();
        let registered = register_test(
            &mut registry,
            set,
            closed_runtime_evidence(&subject, &anchor, 10),
            policy(&subject, 10, Maturity::Attested),
        )
        .expect("hardware anchor should register");

        assert_eq!(registered.tier, AnchorTier::HardwareAnchoredAgent);
        assert!(registered.revoked_at.is_none());
    }

    #[test]
    fn pa_2_runtime_anchor_reuse_rejected() {
        let subject_a = subject("agentA");
        let subject_b = subject("agentB");
        let anchor = runtime_anchor("cvm-1");
        let mut registry = AgentAnchorRegistry::new();

        register_test(
            &mut registry,
            AgentAnchorSet {
                subject: subject_a.clone(),
                runtime_anchors: BTreeSet::from([anchor.clone()]),
                ..AgentAnchorSet::default()
            },
            closed_runtime_evidence(&subject_a, &anchor, 10),
            policy(&subject_a, 10, Maturity::Attested),
        )
        .expect("first registration should work");

        let error = register_test(
            &mut registry,
            AgentAnchorSet {
                subject: subject_b.clone(),
                runtime_anchors: BTreeSet::from([anchor.clone()]),
                ..AgentAnchorSet::default()
            },
            closed_runtime_evidence(&subject_b, &anchor, 10),
            policy(&subject_b, 10, Maturity::Attested),
        )
        .expect_err("second active runtime anchor registration must fail");

        assert_eq!(error, AgentAnchorError::AnchorReuse(anchor.anchor_id()));
    }

    #[test]
    fn pa_3_human_sponsor_one_agent_policy_rejected_on_reuse() {
        let mut registry = AgentAnchorRegistry::new();
        let sponsor = sponsor("human-1", SponsorshipPolicy::OneAgentPerSponsor);
        for id in ["agentA", "agentB"] {
            let subject = subject(id);
            let result = register_test(
                &mut registry,
                AgentAnchorSet {
                    subject: subject.clone(),
                    sponsor_anchors: BTreeSet::from([sponsor.clone()]),
                    ..AgentAnchorSet::default()
                },
                closed_sponsor_evidence(&subject, 10),
                policy(&subject, 10, Maturity::Local),
            );
            if id == "agentA" {
                assert!(result.is_ok());
            } else {
                assert_eq!(
                    result.expect_err("second sponsor use must fail"),
                    AgentAnchorError::SponsorReuse("poh:human-1".to_owned())
                );
            }
        }
    }

    #[test]
    fn pa_4_limited_sponsor_policy_allows_n_and_rejects_n_plus_one() {
        let mut registry = AgentAnchorRegistry::new();
        let sponsor = sponsor(
            "human-1",
            SponsorshipPolicy::LimitedAgentsPerSponsor { max: 2 },
        );
        for (idx, id) in ["agentA", "agentB", "agentC"].into_iter().enumerate() {
            let subject = subject(id);
            let result = register_test(
                &mut registry,
                AgentAnchorSet {
                    subject: subject.clone(),
                    sponsor_anchors: BTreeSet::from([sponsor.clone()]),
                    ..AgentAnchorSet::default()
                },
                closed_sponsor_evidence(&subject, 10),
                policy(&subject, 10, Maturity::Local),
            );
            assert_eq!(result.is_ok(), idx < 2);
        }
    }

    #[test]
    fn pa_5_hardware_plus_sponsor_elevates_to_composite() {
        let subject = subject("agentA");
        let anchor = runtime_anchor("cvm-1");
        let mut registry = AgentAnchorRegistry::new();
        let registered = register_test(
            &mut registry,
            AgentAnchorSet {
                subject: subject.clone(),
                runtime_anchors: BTreeSet::from([anchor.clone()]),
                sponsor_anchors: BTreeSet::from([sponsor(
                    "human-1",
                    SponsorshipPolicy::OneAgentPerSponsor,
                )]),
                ..AgentAnchorSet::default()
            },
            closed_runtime_evidence(&subject, &anchor, 10),
            policy(&subject, 10, Maturity::Attested),
        )
        .expect("composite anchor should register");

        assert_eq!(registered.tier, AnchorTier::CompositeDistinctAgent);
    }

    #[test]
    fn pa_6_sponsor_alone_is_accountability_not_runtime_scarcity() {
        let subject = subject("agentA");
        let mut registry = AgentAnchorRegistry::new();
        let registered = register_test(
            &mut registry,
            AgentAnchorSet {
                subject: subject.clone(),
                sponsor_anchors: BTreeSet::from([sponsor(
                    "human-1",
                    SponsorshipPolicy::OneAgentPerSponsor,
                )]),
                ..AgentAnchorSet::default()
            },
            closed_sponsor_evidence(&subject, 10),
            policy(&subject, 10, Maturity::Local),
        )
        .expect("sponsor-only accountability anchor should register");

        assert_eq!(registered.tier, AnchorTier::HumanitySponsoredAgent);
        assert!(registered
            .envelope
            .excludes
            .contains(&nonclaim(&subject, "global-software-agent-uniqueness")));
        assert!(registered
            .envelope
            .excludes
            .contains(&nonclaim(&subject, "runtime-scarcity")));
    }

    #[test]
    fn pa_7_revoked_anchor_downgrades_or_revokes() {
        let subject = subject("agentA");
        let anchor = runtime_anchor("cvm-1");
        let mut registry = AgentAnchorRegistry::new();
        register_test(
            &mut registry,
            AgentAnchorSet {
                subject: subject.clone(),
                runtime_anchors: BTreeSet::from([anchor.clone()]),
                sponsor_anchors: BTreeSet::from([sponsor(
                    "human-1",
                    SponsorshipPolicy::OneAgentPerSponsor,
                )]),
                ..AgentAnchorSet::default()
            },
            closed_runtime_evidence(&subject, &anchor, 10),
            policy(&subject, 10, Maturity::Attested),
        )
        .expect("composite anchor should register");

        let updated = registry
            .revoke_runtime_anchor(&subject, &anchor, 20)
            .expect("revocation should update registration");
        assert_eq!(updated.tier, AnchorTier::HumanitySponsoredAgent);
        assert!(updated.revoked_at.is_none());
    }

    #[test]
    fn pa_8_canonical_anchor_set_hash_is_order_independent() {
        let subject = subject("agentA");
        let a = runtime_anchor("cvm-1");
        let b = runtime_anchor("cvm-2");
        let set_one = AgentAnchorSet {
            subject: subject.clone(),
            runtime_anchors: BTreeSet::from([a.clone(), b.clone()]),
            ..AgentAnchorSet::default()
        };
        let set_two = AgentAnchorSet {
            subject,
            runtime_anchors: BTreeSet::from([b, a]),
            ..AgentAnchorSet::default()
        };

        assert_eq!(set_one.anchor_set_id(), set_two.anchor_set_id());
    }

    #[test]
    fn state_1_internal_indexes_match_active_registrations() {
        let subject = subject("agentA");
        let anchor = runtime_anchor("cvm-1");
        let sponsor = sponsor("human-1", SponsorshipPolicy::OneAgentPerSponsor);
        let bond = bond("bond-1");
        let mut registry = AgentAnchorRegistry::new();

        register_test(
            &mut registry,
            AgentAnchorSet {
                subject: subject.clone(),
                runtime_anchors: BTreeSet::from([anchor.clone()]),
                sponsor_anchors: BTreeSet::from([sponsor.clone()]),
                bond_anchors: BTreeSet::from([bond.clone()]),
                reputation_anchor: Some(ReputationAnchor {
                    agent_id: subject.0.clone(),
                    since: 1,
                    min_observations: 1,
                }),
                ..AgentAnchorSet::default()
            },
            closed_runtime_evidence(&subject, &anchor, 10),
            policy(&subject, 10, Maturity::Attested),
        )
        .expect("registration must work");

        assert_eq!(registry.active_count(), 1);
        assert_eq!(registry.registered_count(), 1);
        assert!(registry
            .used_runtime_anchor_ids()
            .contains(&anchor.anchor_id()));
        assert!(registry.used_bond_anchor_ids().contains(&bond.bond_id));
        assert_eq!(registry.sponsor_use_count(&sponsor), 1);
        assert!(registry.validate_internal_state().is_ok());
    }

    #[test]
    fn state_2_revoked_runtime_leaves_consistent_sponsor_state() {
        let subject = subject("agentA");
        let anchor = runtime_anchor("cvm-1");
        let sponsor = sponsor("human-1", SponsorshipPolicy::OneAgentPerSponsor);
        let mut registry = AgentAnchorRegistry::new();

        register_test(
            &mut registry,
            AgentAnchorSet {
                subject: subject.clone(),
                runtime_anchors: BTreeSet::from([anchor.clone()]),
                sponsor_anchors: BTreeSet::from([sponsor.clone()]),
                ..AgentAnchorSet::default()
            },
            closed_runtime_evidence(&subject, &anchor, 10),
            policy(&subject, 10, Maturity::Attested),
        )
        .expect("registration must work");
        registry
            .revoke_runtime_anchor(&subject, &anchor, 20)
            .expect("revocation should downgrade");

        assert_eq!(registry.active_count(), 1);
        assert_eq!(registry.sponsor_use_count(&sponsor), 1);
        assert!(!registry
            .used_runtime_anchor_ids()
            .contains(&anchor.anchor_id()));
        assert!(registry
            .revoked_runtime_anchor_ids()
            .contains(&anchor.anchor_id()));
        assert!(registry.validate_internal_state().is_ok());
    }

    #[test]
    fn state_3_deep_nested_rejections_do_not_drift_registry_state() {
        let mut registry = AgentAnchorRegistry::new();
        let mut oracle = StrategyOracle::default();
        let steps = vec![RegistryStrategyStep::Nested(vec![
            RegistryStrategyStep::Nested(vec![
                RegistryStrategyStep::RegisterRuntime {
                    subject_id: 0,
                    anchor_id: 0,
                },
                RegistryStrategyStep::Nested(vec![
                    RegistryStrategyStep::RegisterRuntime {
                        subject_id: 1,
                        anchor_id: 0,
                    },
                    RegistryStrategyStep::RevokeRuntime {
                        subject_id: 1,
                        anchor_id: 0,
                    },
                ]),
            ]),
            RegistryStrategyStep::Nested(vec![
                RegistryStrategyStep::RevokeRuntime {
                    subject_id: 0,
                    anchor_id: 0,
                },
                RegistryStrategyStep::RegisterComposite {
                    subject_id: 2,
                    anchor_id: 0,
                    sponsor_id: 0,
                },
                RegistryStrategyStep::RegisterSponsor {
                    subject_id: 2,
                    sponsor_id: 0,
                    max_uses: 1,
                },
            ]),
        ])];

        for step in &steps {
            run_strategy_step(&mut registry, &mut oracle, step);
        }

        assert_eq!(registry.active_count(), oracle.active_subjects.len());
        assert_eq!(
            registry.used_runtime_anchor_ids().len(),
            oracle.runtime_subjects.len()
        );
        assert_eq!(
            registry.revoked_runtime_anchor_ids().len(),
            oracle.revoked_runtime_anchors.len()
        );
        assert_eq!(
            registry.registered_count(),
            oracle.registered_subjects.len()
        );
        assert!(registry.validate_internal_state().is_ok());
    }

    proptest! {
        #[test]
        fn pap_1_no_active_anchor_reuse(ids in proptest::collection::vec("[a-z]{1,8}", 1..12)) {
            let mut registry = AgentAnchorRegistry::new();
            let mut expected_used = BTreeSet::new();
            for (idx, id) in ids.iter().enumerate() {
                let subject = subject(&format!("agent{idx}"));
                let anchor = runtime_anchor(id);
                let result = register_test(
                    &mut registry,
                    AgentAnchorSet {
                        subject: subject.clone(),
                        runtime_anchors: BTreeSet::from([anchor.clone()]),
                        ..AgentAnchorSet::default()
                    },
                    closed_runtime_evidence(&subject, &anchor, 10),
                    policy(&subject, 10, Maturity::Attested),
                );
                prop_assert_eq!(result.is_ok(), expected_used.insert(anchor.anchor_id()));
            }
        }

        #[test]
        fn pap_2_sponsor_policy_is_enforced(max in 1u64..5, attempts in 1usize..8) {
            let mut registry = AgentAnchorRegistry::new();
            let sponsor = sponsor("human-1", SponsorshipPolicy::LimitedAgentsPerSponsor { max });
            let mut accepted = 0u64;
            for idx in 0..attempts {
                let subject = subject(&format!("agent{idx}"));
                let result = register_test(
                    &mut registry,
                    AgentAnchorSet {
                        subject: subject.clone(),
                        sponsor_anchors: BTreeSet::from([sponsor.clone()]),
                        ..AgentAnchorSet::default()
                    },
                    closed_sponsor_evidence(&subject, 10),
                    policy(&subject, 10, Maturity::Local),
                );
                if result.is_ok() {
                    accepted += 1;
                }
            }
            prop_assert!(accepted <= max);
        }

        #[test]
        fn pap_3_tier_is_monotone_under_added_valid_anchors(has_runtime in any::<bool>(), has_sponsor in any::<bool>(), has_bond in any::<bool>()) {
            let subject = subject("agentA");
            let mut base = AgentAnchorSet { subject: subject.clone(), ..AgentAnchorSet::default() };
            if has_runtime {
                base.runtime_anchors.insert(runtime_anchor("cvm-1"));
            }
            if has_sponsor {
                base.sponsor_anchors.insert(sponsor("human-1", SponsorshipPolicy::UnlimitedLowTrust));
            }
            if has_bond {
                base.bond_anchors.insert(bond("bond-1"));
            }
            let before = base.tier();
            base.sponsor_anchors.insert(sponsor("human-2", SponsorshipPolicy::UnlimitedLowTrust));
            let after = base.tier();
            prop_assert!(tier_strength(&after) >= tier_strength(&before));
        }

        #[test]
        fn pap_4_revocation_cannot_strengthen(add_sponsor in any::<bool>()) {
            let subject = subject("agentA");
            let anchor = runtime_anchor("cvm-1");
            let mut set = AgentAnchorSet {
                subject: subject.clone(),
                runtime_anchors: BTreeSet::from([anchor.clone()]),
                ..AgentAnchorSet::default()
            };
            if add_sponsor {
                set.sponsor_anchors.insert(sponsor("human-1", SponsorshipPolicy::OneAgentPerSponsor));
            }
            let before = set.tier();
            let mut registry = AgentAnchorRegistry::new();
            register_test(
                &mut registry,
                set,
                closed_runtime_evidence(&subject, &anchor, 10),
                policy(&subject, 10, Maturity::Attested),
            ).expect("registration must work");
            let after = registry.revoke_runtime_anchor(&subject, &anchor, 20).expect("revoke").tier.clone();
            prop_assert!(tier_strength(&after) <= tier_strength(&before));
        }

        #[test]
        fn pap_5_canonical_hash_determinism(a in "[a-z]{1,8}", b in "[a-z]{1,8}") {
            let subject = subject("agentA");
            let set_one = AgentAnchorSet {
                subject: subject.clone(),
                runtime_anchors: BTreeSet::from([runtime_anchor(&a), runtime_anchor(&b)]),
                ..AgentAnchorSet::default()
            };
            let set_two = AgentAnchorSet {
                subject,
                runtime_anchors: BTreeSet::from([runtime_anchor(&b), runtime_anchor(&a)]),
                ..AgentAnchorSet::default()
            };
            prop_assert_eq!(set_one.anchor_set_id(), set_two.anchor_set_id());
        }

        #[test]
        fn pap_6_recursive_strategy_tree_preserves_registry_state(steps in strategy_tree()) {
            let mut registry = AgentAnchorRegistry::new();
            let mut oracle = StrategyOracle::default();

            for step in &steps {
                run_strategy_step(&mut registry, &mut oracle, step);
            }

            prop_assert_eq!(registry.active_count(), oracle.active_subjects.len());
            prop_assert_eq!(
                registry.used_runtime_anchor_ids().len(),
                oracle.runtime_subjects.len()
            );
            prop_assert_eq!(
                registry.revoked_runtime_anchor_ids().len(),
                oracle.revoked_runtime_anchors.len()
            );
            prop_assert!(registry.validate_internal_state().is_ok());
        }
    }
}

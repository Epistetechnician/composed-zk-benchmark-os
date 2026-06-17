//! Phase 4 Proof of Agent anchor registry.
//!
//! The registry authorizes only this claim:
//! one active HSAI identity per accepted, non-reused registered anchor set.
//! It does not prove global software-agent uniqueness, competence, safety, or
//! semantic correctness. Output maturity is inherited from admitted inputs and
//! is never elevated by registry bookkeeping.

use hsai_claim_envelope::{
    admits, AcceptancePolicy, ClaimEnvelope, Hash, LaneId, Maturity, Predicate, PropertyKind,
    Rejection, StakeRef, SubjectId, TrustRoot,
};
use hsai_distinct_agent::Anchor;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub const PHASE_4_CLAIM_BOUNDARY: &str =
    "one active HSAI identity per accepted, non-reused registered anchor set; not global software-agent uniqueness";

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
}

impl Default for AgentAnchorSet {
    fn default() -> Self {
        Self {
            subject: SubjectId(String::new()),
            runtime_anchors: BTreeSet::new(),
            sponsor_anchors: BTreeSet::new(),
            bond_anchors: BTreeSet::new(),
            reputation_anchor: None,
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
        anchor_set: AgentAnchorSet,
        evidence: ClaimEnvelope,
        policy: AcceptancePolicy,
    ) -> Result<&RegisteredAgentAnchor, AgentAnchorError> {
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
}

fn sponsor_allows_count(policy: &SponsorshipPolicy, count: u64) -> bool {
    match policy {
        SponsorshipPolicy::OneAgentPerSponsor => count <= 1,
        SponsorshipPolicy::LimitedAgentsPerSponsor { max } => count <= *max,
        SponsorshipPolicy::UnlimitedLowTrust => true,
    }
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
    use proptest::prelude::*;

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

    fn policy(subject: &SubjectId, at: u64, min_maturity: Maturity) -> AcceptancePolicy {
        AcceptancePolicy {
            require: BTreeSet::from([distinctness(subject)]),
            min_maturity,
            forbid_roots: BTreeSet::<TrustRootClass>::new(),
            require_closed: true,
            at,
        }
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
        let registered = registry
            .register(
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

        registry
            .register(
                AgentAnchorSet {
                    subject: subject_a.clone(),
                    runtime_anchors: BTreeSet::from([anchor.clone()]),
                    ..AgentAnchorSet::default()
                },
                closed_runtime_evidence(&subject_a, &anchor, 10),
                policy(&subject_a, 10, Maturity::Attested),
            )
            .expect("first registration should work");

        let error = registry
            .register(
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
            let result = registry.register(
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
            let result = registry.register(
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
        let registered = registry
            .register(
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
        let registered = registry
            .register(
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
        registry
            .register(
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

    proptest! {
        #[test]
        fn pap_1_no_active_anchor_reuse(ids in proptest::collection::vec("[a-z]{1,8}", 1..12)) {
            let mut registry = AgentAnchorRegistry::new();
            let mut expected_used = BTreeSet::new();
            for (idx, id) in ids.iter().enumerate() {
                let subject = subject(&format!("agent{idx}"));
                let anchor = runtime_anchor(id);
                let result = registry.register(
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
                let result = registry.register(
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
            registry.register(
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
    }
}

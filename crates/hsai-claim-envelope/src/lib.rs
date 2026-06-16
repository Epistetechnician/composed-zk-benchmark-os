use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum Maturity {
    Stub,
    Local,
    Attested,
    Proven,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct VendorId(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct VkId(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct StakeRef(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct AgentId(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct SubjectId(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum TrustRoot {
    HardwareVendor(VendorId),
    VerifyingKey(VkId),
    EconomicStake(StakeRef),
    SocialReputation(AgentId),
}

impl TrustRoot {
    pub fn class(&self) -> TrustRootClass {
        match self {
            Self::HardwareVendor(_) => TrustRootClass::HardwareVendor,
            Self::VerifyingKey(_) => TrustRootClass::VerifyingKey,
            Self::EconomicStake(_) => TrustRootClass::EconomicStake,
            Self::SocialReputation(_) => TrustRootClass::SocialReputation,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum TrustRootClass {
    HardwareVendor,
    VerifyingKey,
    EconomicStake,
    SocialReputation,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum PropertyKind {
    Distinctness,
    MemoryIntegrity,
    PolicyCompliance,
    IsModel,
    SemanticCorrectness,
    Custom(String),
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct Predicate {
    pub subject: SubjectId,
    pub property: PropertyKind,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct TimeWindow {
    pub start: u64,
    pub end: u64,
}

impl TimeWindow {
    pub fn all() -> Self {
        Self {
            start: 0,
            end: u64::MAX,
        }
    }

    pub fn intersect(&self, other: &Self) -> Self {
        Self {
            start: self.start.max(other.start),
            end: self.end.min(other.end),
        }
    }

    pub fn contains(&self, at: u64) -> bool {
        self.start <= self.end && self.start <= at && at <= self.end
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum LaneId {
    Top,
    Composite,
    Named(String),
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct Hash(pub [u8; 32]);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct ClaimEnvelope {
    pub guarantees: BTreeSet<Predicate>,
    pub assumptions: BTreeSet<Predicate>,
    pub excludes: BTreeSet<Predicate>,
    pub maturity: Maturity,
    pub trust_roots: BTreeSet<TrustRoot>,
    pub valid: TimeWindow,
    pub lane: LaneId,
    pub provenance: Hash,
}

impl ClaimEnvelope {
    pub fn new(
        guarantees: BTreeSet<Predicate>,
        assumptions: BTreeSet<Predicate>,
        excludes: BTreeSet<Predicate>,
        maturity: Maturity,
        trust_roots: BTreeSet<TrustRoot>,
        valid: TimeWindow,
        lane: LaneId,
    ) -> Self {
        let mut envelope = Self {
            guarantees,
            assumptions,
            excludes,
            maturity,
            trust_roots,
            valid,
            lane,
            provenance: Hash([0; 32]),
        };
        envelope.provenance = hash_envelope_content("leaf", &envelope);
        envelope
    }

    fn is_top(&self) -> bool {
        self == &top()
    }
}

#[derive(Serialize)]
struct ProvenanceContent<'a> {
    tag: &'a str,
    guarantees: &'a BTreeSet<Predicate>,
    assumptions: &'a BTreeSet<Predicate>,
    excludes: &'a BTreeSet<Predicate>,
    maturity: &'a Maturity,
    trust_roots: &'a BTreeSet<TrustRoot>,
    valid: &'a TimeWindow,
    lane: &'a LaneId,
}

fn hash_bytes(bytes: &[u8]) -> Hash {
    let digest = Sha256::digest(bytes);
    let mut out = [0; 32];
    out.copy_from_slice(&digest);
    Hash(out)
}

fn hash_envelope_content(tag: &str, envelope: &ClaimEnvelope) -> Hash {
    let content = ProvenanceContent {
        tag,
        guarantees: &envelope.guarantees,
        assumptions: &envelope.assumptions,
        excludes: &envelope.excludes,
        maturity: &envelope.maturity,
        trust_roots: &envelope.trust_roots,
        valid: &envelope.valid,
        lane: &envelope.lane,
    };
    let bytes =
        serde_json::to_vec(&content).expect("canonical claim-envelope content must serialize");
    hash_bytes(&bytes)
}

fn hash_top() -> Hash {
    hash_bytes(b"hsai-claim-envelope:top:v1")
}

fn hash_composite(envelope: &ClaimEnvelope) -> Hash {
    hash_envelope_content("conjoin", envelope)
}

pub fn top() -> ClaimEnvelope {
    ClaimEnvelope {
        guarantees: BTreeSet::new(),
        assumptions: BTreeSet::new(),
        excludes: BTreeSet::new(),
        maturity: Maturity::Proven,
        trust_roots: BTreeSet::new(),
        valid: TimeWindow::all(),
        lane: LaneId::Top,
        provenance: hash_top(),
    }
}

pub fn conjoin(a: ClaimEnvelope, b: ClaimEnvelope) -> ClaimEnvelope {
    if a.is_top() {
        return b;
    }
    if b.is_top() {
        return a;
    }

    let guarantees = a
        .guarantees
        .union(&b.guarantees)
        .cloned()
        .collect::<BTreeSet<_>>();
    let assumptions = a
        .assumptions
        .union(&b.assumptions)
        .filter(|assumption| !guarantees.contains(*assumption))
        .cloned()
        .collect::<BTreeSet<_>>();

    let mut envelope = ClaimEnvelope {
        guarantees,
        assumptions,
        excludes: a.excludes.union(&b.excludes).cloned().collect(),
        maturity: a.maturity.min(b.maturity),
        trust_roots: a.trust_roots.union(&b.trust_roots).cloned().collect(),
        valid: a.valid.intersect(&b.valid),
        lane: LaneId::Composite,
        provenance: Hash([0; 32]),
    };
    envelope.provenance = hash_composite(&envelope);
    envelope
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AcceptancePolicy {
    pub require: BTreeSet<Predicate>,
    pub min_maturity: Maturity,
    pub forbid_roots: BTreeSet<TrustRootClass>,
    pub require_closed: bool,
    pub at: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum Rejection {
    MissingGuarantee(Predicate),
    InsufficientMaturity {
        actual: Maturity,
        required: Maturity,
    },
    OpenAssumption(Predicate),
    ForbiddenTrustRoot(TrustRoot),
    NotValidAt {
        at: u64,
        valid: TimeWindow,
    },
}

pub fn admits(policy: AcceptancePolicy, envelope: ClaimEnvelope) -> Result<(), Vec<Rejection>> {
    let mut rejections = Vec::new();

    for required in &policy.require {
        if !envelope.guarantees.contains(required) {
            rejections.push(Rejection::MissingGuarantee(required.clone()));
        }
    }

    if envelope.maturity < policy.min_maturity {
        rejections.push(Rejection::InsufficientMaturity {
            actual: envelope.maturity.clone(),
            required: policy.min_maturity,
        });
    }

    if policy.require_closed {
        rejections.extend(
            envelope
                .assumptions
                .iter()
                .cloned()
                .map(Rejection::OpenAssumption),
        );
    }

    for root in &envelope.trust_roots {
        if policy.forbid_roots.contains(&root.class()) {
            rejections.push(Rejection::ForbiddenTrustRoot(root.clone()));
        }
    }

    if !envelope.valid.contains(policy.at) {
        rejections.push(Rejection::NotValidAt {
            at: policy.at,
            valid: envelope.valid,
        });
    }

    if rejections.is_empty() {
        Ok(())
    } else {
        Err(rejections)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::collection::btree_set;
    use proptest::prelude::*;

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn vendor(id: &str) -> VendorId {
        VendorId(id.to_owned())
    }

    fn vk(id: &str) -> VkId {
        VkId(id.to_owned())
    }

    fn predicate(subject_id: &str, property: PropertyKind) -> Predicate {
        Predicate {
            subject: subject(subject_id),
            property,
        }
    }

    fn policy_compliance_action1() -> Predicate {
        predicate("action1", PropertyKind::PolicyCompliance)
    }

    fn is_model_agent_a() -> Predicate {
        predicate("agentA", PropertyKind::IsModel)
    }

    fn semantic_correctness_action1() -> Predicate {
        predicate("action1", PropertyKind::SemanticCorrectness)
    }

    fn e_policy() -> ClaimEnvelope {
        ClaimEnvelope::new(
            BTreeSet::from([policy_compliance_action1()]),
            BTreeSet::from([is_model_agent_a()]),
            BTreeSet::from([semantic_correctness_action1()]),
            Maturity::Proven,
            BTreeSet::from([TrustRoot::VerifyingKey(vk("policy_vk"))]),
            TimeWindow {
                start: 100,
                end: 200,
            },
            LaneId::Named("policy".to_owned()),
        )
    }

    fn e_prov() -> ClaimEnvelope {
        ClaimEnvelope::new(
            BTreeSet::from([is_model_agent_a()]),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Attested,
            BTreeSet::from([TrustRoot::HardwareVendor(vendor("nvidia"))]),
            TimeWindow {
                start: 150,
                end: 300,
            },
            LaneId::Named("provenance".to_owned()),
        )
    }

    #[test]
    fn v1_tee_caps_zk_and_discharges_assumption() {
        let actual = conjoin(e_policy(), e_prov());

        assert_eq!(
            actual.guarantees,
            BTreeSet::from([policy_compliance_action1(), is_model_agent_a()])
        );
        assert!(actual.assumptions.is_empty());
        assert_eq!(
            actual.excludes,
            BTreeSet::from([semantic_correctness_action1()])
        );
        assert_eq!(actual.maturity, Maturity::Attested);
        assert_eq!(
            actual.trust_roots,
            BTreeSet::from([
                TrustRoot::VerifyingKey(vk("policy_vk")),
                TrustRoot::HardwareVendor(vendor("nvidia")),
            ])
        );
        assert_eq!(
            actual.valid,
            TimeWindow {
                start: 150,
                end: 200
            }
        );

        let admitting_policy = AcceptancePolicy {
            require: BTreeSet::from([policy_compliance_action1()]),
            min_maturity: Maturity::Attested,
            forbid_roots: BTreeSet::new(),
            require_closed: true,
            at: 175,
        };
        assert_eq!(admits(admitting_policy, actual.clone()), Ok(()));

        let hardware_forbidden = AcceptancePolicy {
            require: BTreeSet::from([policy_compliance_action1()]),
            min_maturity: Maturity::Attested,
            forbid_roots: BTreeSet::from([TrustRootClass::HardwareVendor]),
            require_closed: true,
            at: 175,
        };
        assert_eq!(
            admits(hardware_forbidden, actual),
            Err(vec![Rejection::ForbiddenTrustRoot(
                TrustRoot::HardwareVendor(vendor("nvidia"))
            )])
        );
    }

    #[test]
    fn v2_open_assumption_is_inadmissible_when_closed_required() {
        let policy = AcceptancePolicy {
            require: BTreeSet::from([policy_compliance_action1()]),
            min_maturity: Maturity::Local,
            forbid_roots: BTreeSet::new(),
            require_closed: true,
            at: 120,
        };

        assert_eq!(
            admits(policy, e_policy()),
            Err(vec![Rejection::OpenAssumption(is_model_agent_a())])
        );
    }

    #[test]
    fn v3_top_is_identity() {
        assert_eq!(conjoin(e_prov(), top()), e_prov());
        assert_eq!(conjoin(top(), e_prov()), e_prov());
    }

    #[test]
    fn v4_disjoint_validity_yields_empty_window_and_fails_admission_time() {
        let left = ClaimEnvelope::new(
            BTreeSet::new(),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Local,
            BTreeSet::new(),
            TimeWindow { start: 0, end: 50 },
            LaneId::Named("left".to_owned()),
        );
        let right = ClaimEnvelope::new(
            BTreeSet::new(),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Local,
            BTreeSet::new(),
            TimeWindow {
                start: 60,
                end: 100,
            },
            LaneId::Named("right".to_owned()),
        );

        let actual = conjoin(left, right);
        assert_eq!(actual.valid, TimeWindow { start: 60, end: 50 });

        let policy = AcceptancePolicy {
            require: BTreeSet::new(),
            min_maturity: Maturity::Stub,
            forbid_roots: BTreeSet::new(),
            require_closed: false,
            at: 55,
        };
        assert_eq!(
            admits(policy, actual.clone()),
            Err(vec![Rejection::NotValidAt {
                at: 55,
                valid: actual.valid
            }])
        );
    }

    fn maturity_strategy() -> impl Strategy<Value = Maturity> {
        prop_oneof![
            Just(Maturity::Stub),
            Just(Maturity::Local),
            Just(Maturity::Attested),
            Just(Maturity::Proven),
        ]
    }

    fn property_strategy() -> impl Strategy<Value = PropertyKind> {
        prop_oneof![
            Just(PropertyKind::Distinctness),
            Just(PropertyKind::MemoryIntegrity),
            Just(PropertyKind::PolicyCompliance),
            Just(PropertyKind::IsModel),
            Just(PropertyKind::SemanticCorrectness),
            (0_u8..8).prop_map(|n| PropertyKind::Custom(format!("custom-{n}"))),
        ]
    }

    fn predicate_strategy() -> impl Strategy<Value = Predicate> {
        ((0_u8..8), property_strategy()).prop_map(|(subject_id, property)| Predicate {
            subject: SubjectId(format!("subject-{subject_id}")),
            property,
        })
    }

    fn trust_root_strategy() -> impl Strategy<Value = TrustRoot> {
        prop_oneof![
            (0_u8..8).prop_map(|n| TrustRoot::HardwareVendor(VendorId(format!("vendor-{n}")))),
            (0_u8..8).prop_map(|n| TrustRoot::VerifyingKey(VkId(format!("vk-{n}")))),
            (0_u8..8).prop_map(|n| TrustRoot::EconomicStake(StakeRef(format!("stake-{n}")))),
            (0_u8..8).prop_map(|n| TrustRoot::SocialReputation(AgentId(format!("agent-{n}")))),
        ]
    }

    fn window_strategy() -> impl Strategy<Value = TimeWindow> {
        (0_u64..1000, 0_u64..1000).prop_map(|(start, end)| TimeWindow { start, end })
    }

    fn lane_strategy() -> impl Strategy<Value = LaneId> {
        (0_u8..8).prop_map(|n| LaneId::Named(format!("lane-{n}")))
    }

    fn envelope_strategy() -> impl Strategy<Value = ClaimEnvelope> {
        (
            btree_set(predicate_strategy(), 0..6),
            btree_set(predicate_strategy(), 0..6),
            btree_set(predicate_strategy(), 0..6),
            maturity_strategy(),
            btree_set(trust_root_strategy(), 0..6),
            window_strategy(),
            lane_strategy(),
        )
            .prop_map(
                |(guarantees, assumptions, excludes, maturity, trust_roots, valid, lane)| {
                    ClaimEnvelope::new(
                        guarantees,
                        assumptions,
                        excludes,
                        maturity,
                        trust_roots,
                        valid,
                        lane,
                    )
                },
            )
    }

    fn is_subset_window(subset: &TimeWindow, superset: &TimeWindow) -> bool {
        subset.start > subset.end
            || (superset.start <= superset.end
                && superset.start <= subset.start
                && subset.end <= superset.end)
    }

    proptest! {
        #[test]
        fn inv_1_maturity_descends(a in envelope_strategy(), b in envelope_strategy()) {
            let expected = a.maturity.clone().min(b.maturity.clone());
            let c = conjoin(a, b);
            prop_assert!(c.maturity <= expected);
        }

        #[test]
        fn inv_2_excludes_accumulate(a in envelope_strategy(), b in envelope_strategy()) {
            let expected = a.excludes.union(&b.excludes).cloned().collect::<BTreeSet<_>>();
            let c = conjoin(a, b);
            prop_assert!(expected.is_subset(&c.excludes));
        }

        #[test]
        fn inv_3_trust_roots_accumulate(a in envelope_strategy(), b in envelope_strategy()) {
            let expected = a.trust_roots.union(&b.trust_roots).cloned().collect::<BTreeSet<_>>();
            let c = conjoin(a, b);
            prop_assert!(expected.is_subset(&c.trust_roots));
        }

        #[test]
        fn inv_4_validity_intersects(a in envelope_strategy(), b in envelope_strategy()) {
            let expected_intersection = a.valid.intersect(&b.valid);
            let c = conjoin(a, b);
            prop_assert!(is_subset_window(&c.valid, &expected_intersection));
        }

        #[test]
        fn law_1_conjoin_is_commutative(a in envelope_strategy(), b in envelope_strategy()) {
            prop_assert_eq!(conjoin(a.clone(), b.clone()), conjoin(b, a));
        }

        #[test]
        fn law_2_conjoin_is_associative(
            a in envelope_strategy(),
            b in envelope_strategy(),
            c in envelope_strategy()
        ) {
            let left = conjoin(conjoin(a.clone(), b.clone()), c.clone());
            let right = conjoin(a, conjoin(b, c));
            prop_assert_eq!(left, right);
        }

        #[test]
        fn law_3_top_is_identity(a in envelope_strategy()) {
            prop_assert_eq!(conjoin(a.clone(), top()), a.clone());
            prop_assert_eq!(conjoin(top(), a.clone()), a);
        }
    }
}

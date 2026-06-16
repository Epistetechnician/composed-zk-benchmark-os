use hsai_agent_case::{AgentCase, EvidenceLane};
use hsai_claim_envelope::{
    admits, AcceptancePolicy, ClaimEnvelope, LaneId, Maturity, Predicate, PropertyKind, Rejection,
    StakeRef, SubjectId, TimeWindow, TrustRoot, VendorId,
};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub enum Anchor {
    HardwareAttested { vendor: String, device: String },
    Staked { stake: String, amount: u64 },
    HumanCredentialed { issuer: String, credential: String },
}

impl PartialEq for Anchor {
    fn eq(&self, other: &Self) -> bool {
        self.anchor_id() == other.anchor_id()
    }
}

impl Eq for Anchor {}

impl PartialOrd for Anchor {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Anchor {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.anchor_id().cmp(&other.anchor_id())
    }
}

impl Anchor {
    pub fn anchor_id(&self) -> String {
        match self {
            Self::HardwareAttested { vendor, device } => format!("hw:{vendor}:{device}"),
            Self::Staked { stake, .. } => format!("stake:{stake}"),
            Self::HumanCredentialed { issuer, credential } => {
                format!("human:{issuer}:{credential}")
            }
        }
    }

    pub fn trust_root(&self) -> TrustRoot {
        match self {
            Self::HardwareAttested { .. } => TrustRoot::HardwareVendor(VendorId(self.anchor_id())),
            Self::Staked { .. } => TrustRoot::EconomicStake(StakeRef(self.anchor_id())),
            Self::HumanCredentialed { .. } => {
                TrustRoot::SocialReputation(hsai_claim_envelope::AgentId(self.anchor_id()))
            }
        }
    }

    pub fn validity_assumption(&self, subject: &SubjectId) -> Predicate {
        Predicate {
            subject: subject.clone(),
            property: PropertyKind::Custom(format!("anchor-valid:{}", self.anchor_id())),
        }
    }

    pub fn ceiling(&self) -> Maturity {
        Maturity::Attested
    }
}

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
pub struct AnchorBundle(pub BTreeSet<Anchor>);

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
pub struct DistinctAgentLane {
    pub anchors: AnchorBundle,
}

impl DistinctAgentLane {
    pub fn new(anchors: AnchorBundle) -> Self {
        Self { anchors }
    }
}

impl EvidenceLane for DistinctAgentLane {
    fn id(&self) -> LaneId {
        LaneId::Named("distinct-agent".to_owned())
    }

    fn ceiling(&self) -> Maturity {
        Maturity::Attested
    }

    fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope {
        if self.anchors.0.is_empty() {
            return ClaimEnvelope::new(
                BTreeSet::new(),
                BTreeSet::from([distinctness(&case.subject)]),
                case.oracle.excluded.clone(),
                Maturity::Stub,
                BTreeSet::new(),
                TimeWindow::all(),
                self.id(),
            );
        }

        let maturity = self
            .anchors
            .0
            .iter()
            .map(Anchor::ceiling)
            .min()
            .unwrap_or(Maturity::Stub);

        ClaimEnvelope::new(
            BTreeSet::from([distinctness(&case.subject)]),
            self.anchors
                .0
                .iter()
                .map(|anchor| anchor.validity_assumption(&case.subject))
                .collect(),
            case.oracle.excluded.clone(),
            maturity,
            self.anchors.0.iter().map(Anchor::trust_root).collect(),
            TimeWindow::all(),
            self.id(),
        )
    }
}

pub fn distinctness(subject: &SubjectId) -> Predicate {
    Predicate {
        subject: subject.clone(),
        property: PropertyKind::Distinctness,
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct Identity {
    pub subject: SubjectId,
    pub anchors: BTreeSet<TrustRoot>,
    pub reputation: u64,
}

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
pub struct IdentityRegistry {
    identities: BTreeMap<SubjectId, Identity>,
    used_anchors: BTreeSet<TrustRoot>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum RegisterError {
    NotAdmitted(Vec<Rejection>),
    DistinctnessNotGuaranteed,
    SybilAnchorReuse(TrustRoot),
    AlreadyRegistered(SubjectId),
}

impl From<Vec<Rejection>> for RegisterError {
    fn from(rejections: Vec<Rejection>) -> Self {
        Self::NotAdmitted(rejections)
    }
}

impl IdentityRegistry {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register(
        &mut self,
        subject: SubjectId,
        env: ClaimEnvelope,
        policy: AcceptancePolicy,
    ) -> Result<&Identity, RegisterError> {
        admits(policy, env.clone()).map_err(RegisterError::NotAdmitted)?;

        if !env.guarantees.contains(&distinctness(&subject)) {
            return Err(RegisterError::DistinctnessNotGuaranteed);
        }

        if self.identities.contains_key(&subject) {
            return Err(RegisterError::AlreadyRegistered(subject));
        }

        for root in &env.trust_roots {
            if self.used_anchors.contains(root) {
                return Err(RegisterError::SybilAnchorReuse(root.clone()));
            }
        }

        let identity = Identity {
            subject: subject.clone(),
            anchors: env.trust_roots.clone(),
            reputation: 0,
        };
        self.used_anchors.extend(env.trust_roots);
        self.identities.insert(subject.clone(), identity);
        Ok(self
            .identities
            .get(&subject)
            .expect("registered identity must be present"))
    }

    pub fn reward(&mut self, subject: &SubjectId, amount: u64) {
        if let Some(identity) = self.identities.get_mut(subject) {
            identity.reputation = identity.reputation.saturating_add(amount);
        }
    }

    pub fn slash(&mut self, subject: &SubjectId, amount: u64) {
        if let Some(identity) = self.identities.get_mut(subject) {
            identity.reputation = identity.reputation.saturating_sub(amount);
        }
    }

    pub fn identity(&self, subject: &SubjectId) -> Option<&Identity> {
        self.identities.get(subject)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_agent_case::{
        memory_integrity, ActionId, LocalMemoryLane, MemoryRoot, ModelId, OracleContract, Verdict,
    };
    use hsai_claim_envelope::{conjoin, AcceptancePolicy, Rejection, TrustRootClass};
    use proptest::collection::btree_set;
    use proptest::prelude::*;

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn predicate(subject_id: &str, property: PropertyKind) -> Predicate {
        Predicate {
            subject: subject(subject_id),
            property,
        }
    }

    fn distinctness_agent_a() -> Predicate {
        distinctness(&subject("agentA"))
    }

    fn memory_integrity_agent_a() -> Predicate {
        memory_integrity(&subject("agentA"))
    }

    fn semantic_correctness_action1() -> Predicate {
        predicate("action1", PropertyKind::SemanticCorrectness)
    }

    fn hw_anchor() -> Anchor {
        Anchor::HardwareAttested {
            vendor: "nvidia".to_owned(),
            device: "devX".to_owned(),
        }
    }

    fn hw_root() -> TrustRoot {
        TrustRoot::HardwareVendor(VendorId("hw:nvidia:devX".to_owned()))
    }

    fn hw_validity(subject: &SubjectId) -> Predicate {
        hw_anchor().validity_assumption(subject)
    }

    fn fixture_case(subject_id: &str) -> AgentCase {
        AgentCase {
            action: ActionId("action1".to_owned()),
            subject: subject(subject_id),
            claimed_model: ModelId("modelA".to_owned()),
            memory_root: MemoryRoot([7; 32]),
            observed_at: 120,
            oracle: OracleContract {
                expected: Verdict::Accept,
                target_guarantees: BTreeSet::from([
                    distinctness(&subject(subject_id)),
                    memory_integrity(&subject(subject_id)),
                ]),
                excluded: BTreeSet::from([semantic_correctness_action1()]),
            },
        }
    }

    fn hw_lane() -> DistinctAgentLane {
        DistinctAgentLane::new(AnchorBundle(BTreeSet::from([hw_anchor()])))
    }

    fn closed_policy(subject: &SubjectId) -> AcceptancePolicy {
        AcceptancePolicy {
            require: BTreeSet::from([distinctness(subject)]),
            min_maturity: Maturity::Attested,
            forbid_roots: BTreeSet::<TrustRootClass>::new(),
            require_closed: true,
            at: 120,
        }
    }

    fn attestation_verified(subject: &SubjectId, anchors: &AnchorBundle) -> ClaimEnvelope {
        ClaimEnvelope::new(
            anchors
                .0
                .iter()
                .map(|anchor| anchor.validity_assumption(subject))
                .collect(),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Attested,
            BTreeSet::new(),
            TimeWindow::all(),
            LaneId::Named("test-attestation-verified".to_owned()),
        )
    }

    fn verified_distinct_env(case: &AgentCase, lane: &DistinctAgentLane) -> ClaimEnvelope {
        conjoin(
            lane.evaluate(case),
            attestation_verified(&case.subject, &lane.anchors),
        )
    }

    #[test]
    fn d1_hardware_anchor_yields_conditional_distinctness() {
        let case = fixture_case("agentA");
        let envelope = hw_lane().evaluate(&case);

        assert_eq!(
            envelope.guarantees,
            BTreeSet::from([distinctness_agent_a()])
        );
        assert_eq!(
            envelope.assumptions,
            BTreeSet::from([hw_validity(&case.subject)])
        );
        assert_eq!(
            envelope.excludes,
            BTreeSet::from([semantic_correctness_action1()])
        );
        assert_eq!(envelope.maturity, Maturity::Attested);
        assert_eq!(envelope.trust_roots, BTreeSet::from([hw_root()]));
        assert_eq!(envelope.valid, TimeWindow::all());

        let policy = closed_policy(&case.subject);
        assert_eq!(
            hsai_claim_envelope::admits(policy, envelope),
            Err(vec![Rejection::OpenAssumption(hw_validity(&case.subject))])
        );
    }

    #[test]
    fn d2_distinctness_closes_agent_case_hole_except_anchor_validity() {
        let case = fixture_case("agentA");
        let combined = conjoin(LocalMemoryLane.evaluate(&case), hw_lane().evaluate(&case));

        assert_eq!(
            combined.guarantees,
            BTreeSet::from([memory_integrity_agent_a(), distinctness_agent_a()])
        );
        assert_eq!(
            combined.assumptions,
            BTreeSet::from([hw_validity(&case.subject)])
        );
        assert_eq!(
            combined.excludes,
            BTreeSet::from([semantic_correctness_action1()])
        );
        assert_eq!(combined.maturity, Maturity::Local);
        assert_eq!(combined.trust_roots, BTreeSet::from([hw_root()]));
        assert_eq!(
            combined.valid,
            TimeWindow {
                start: case.observed_at,
                end: u64::MAX,
            }
        );
    }

    #[test]
    fn d3_registry_rejects_reused_anchor() {
        let lane = hw_lane();
        let mut registry = IdentityRegistry::new();
        let case_a = fixture_case("agentA");
        let case_b = fixture_case("agentB");

        let first = registry.register(
            case_a.subject.clone(),
            verified_distinct_env(&case_a, &lane),
            closed_policy(&case_a.subject),
        );
        assert!(first.is_ok());

        let second = registry.register(
            case_b.subject.clone(),
            verified_distinct_env(&case_b, &lane),
            closed_policy(&case_b.subject),
        );
        assert_eq!(second, Err(RegisterError::SybilAnchorReuse(hw_root())));
    }

    #[test]
    fn d4_unverified_distinctness_cannot_register() {
        let case = fixture_case("agentA");
        let lane = hw_lane();
        let mut registry = IdentityRegistry::new();

        assert_eq!(
            registry.register(
                case.subject.clone(),
                lane.evaluate(&case),
                closed_policy(&case.subject),
            ),
            Err(RegisterError::NotAdmitted(vec![Rejection::OpenAssumption(
                hw_validity(&case.subject)
            )]))
        );
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

    fn case_strategy() -> impl Strategy<Value = AgentCase> {
        (
            0_u8..8,
            0_u8..8,
            any::<[u8; 32]>(),
            0_u64..10_000,
            btree_set(predicate_strategy(), 0..6),
            btree_set(predicate_strategy(), 0..6),
        )
            .prop_map(
                |(subject_id, model_id, memory_root, observed_at, target_guarantees, excluded)| {
                    AgentCase {
                        action: ActionId(format!("action-{subject_id}")),
                        subject: SubjectId(format!("subject-{subject_id}")),
                        claimed_model: ModelId(format!("model-{model_id}")),
                        memory_root: MemoryRoot(memory_root),
                        observed_at,
                        oracle: OracleContract {
                            expected: Verdict::Accept,
                            target_guarantees,
                            excluded,
                        },
                    }
                },
            )
    }

    fn anchor_strategy() -> impl Strategy<Value = Anchor> {
        prop_oneof![
            (0_u8..8, 0_u8..8).prop_map(|(vendor, device)| Anchor::HardwareAttested {
                vendor: format!("vendor-{vendor}"),
                device: format!("device-{device}"),
            }),
            (0_u8..8, 0_u64..10_000).prop_map(|(stake, amount)| Anchor::Staked {
                stake: format!("stake-{stake}"),
                amount,
            }),
            (0_u8..8, 0_u8..8).prop_map(|(issuer, credential)| Anchor::HumanCredentialed {
                issuer: format!("issuer-{issuer}"),
                credential: format!("credential-{credential}"),
            }),
        ]
    }

    fn bundle_strategy() -> impl Strategy<Value = AnchorBundle> {
        btree_set(anchor_strategy(), 0..6).prop_map(AnchorBundle)
    }

    fn nonempty_bundle_strategy() -> impl Strategy<Value = AnchorBundle> {
        btree_set(anchor_strategy(), 1..6).prop_map(AnchorBundle)
    }

    fn lane_strategy() -> impl Strategy<Value = DistinctAgentLane> {
        bundle_strategy().prop_map(DistinctAgentLane::new)
    }

    fn closed_distinct_env(case: &AgentCase, lane: &DistinctAgentLane) -> ClaimEnvelope {
        verified_distinct_env(case, lane)
    }

    proptest! {
        #[test]
        fn da_1_lane_maturity_never_exceeds_attested(lane in lane_strategy(), case in case_strategy()) {
            prop_assert!(lane.evaluate(&case).maturity <= Maturity::Attested);
        }

        #[test]
        fn da_2_nonempty_bundle_is_conditional(
            bundle in nonempty_bundle_strategy(),
            case in case_strategy()
        ) {
            let lane = DistinctAgentLane::new(bundle.clone());
            let envelope = lane.evaluate(&case);
            let expected_assumptions = bundle
                .0
                .iter()
                .map(|anchor| anchor.validity_assumption(&case.subject))
                .collect::<BTreeSet<_>>();

            prop_assert!(envelope.guarantees.contains(&distinctness(&case.subject)));
            prop_assert_eq!(&envelope.assumptions, &expected_assumptions);
            prop_assert_eq!(envelope.assumptions.len(), bundle.0.len());
        }

        #[test]
        fn da_3_roots_are_exactly_one_per_anchor(bundle in bundle_strategy(), case in case_strategy()) {
            let lane = DistinctAgentLane::new(bundle.clone());
            let expected_roots = bundle.0.iter().map(Anchor::trust_root).collect::<BTreeSet<_>>();

            prop_assert_eq!(lane.evaluate(&case).trust_roots, expected_roots);
        }

        #[test]
        fn da_4_empty_bundle_claims_nothing(case in case_strategy()) {
            let envelope = DistinctAgentLane::default().evaluate(&case);

            prop_assert!(envelope.guarantees.is_empty());
            prop_assert!(envelope.assumptions.contains(&distinctness(&case.subject)));
            prop_assert_eq!(envelope.maturity, Maturity::Stub);
            prop_assert!(envelope.trust_roots.is_empty());
        }

        #[test]
        fn da_5_shared_anchor_second_registration_is_sybil_reuse(
            anchor in anchor_strategy(),
            subject_a_id in 0_u8..8,
            subject_b_id in 8_u8..16
        ) {
            let bundle = AnchorBundle(BTreeSet::from([anchor.clone()]));
            let lane = DistinctAgentLane::new(bundle);
            let mut registry = IdentityRegistry::new();
            let mut case_a = fixture_case(&format!("agent-{subject_a_id}"));
            let mut case_b = fixture_case(&format!("agent-{subject_b_id}"));
            case_a.oracle.excluded = BTreeSet::new();
            case_b.oracle.excluded = BTreeSet::new();

            let first = registry.register(
                case_a.subject.clone(),
                closed_distinct_env(&case_a, &lane),
                closed_policy(&case_a.subject),
            );
            prop_assert!(first.is_ok());

            let second = registry.register(
                case_b.subject.clone(),
                closed_distinct_env(&case_b, &lane),
                closed_policy(&case_b.subject),
            );
            prop_assert_eq!(second, Err(RegisterError::SybilAnchorReuse(anchor.trust_root())));
        }

        #[test]
        fn da_6_missing_distinctness_guarantee_is_rejected(case in case_strategy()) {
            let mut registry = IdentityRegistry::new();
            let env = ClaimEnvelope::new(
                BTreeSet::new(),
                BTreeSet::new(),
                BTreeSet::new(),
                Maturity::Attested,
                BTreeSet::new(),
                TimeWindow::all(),
                LaneId::Named("missing-distinctness".to_owned()),
            );
            let policy = AcceptancePolicy {
                require: BTreeSet::new(),
                min_maturity: Maturity::Stub,
                forbid_roots: BTreeSet::new(),
                require_closed: true,
                at: 0,
            };

            prop_assert_eq!(
                registry.register(case.subject.clone(), env, policy),
                Err(RegisterError::DistinctnessNotGuaranteed)
            );
        }

        #[test]
        fn da_7_reregistering_subject_is_already_registered(
            bundle in nonempty_bundle_strategy(),
            case in case_strategy()
        ) {
            let lane = DistinctAgentLane::new(bundle);
            let mut registry = IdentityRegistry::new();

            let first = registry.register(
                case.subject.clone(),
                closed_distinct_env(&case, &lane),
                closed_policy(&case.subject),
            );
            prop_assert!(first.is_ok());

            let second = registry.register(
                case.subject.clone(),
                closed_distinct_env(&case, &lane),
                closed_policy(&case.subject),
            );
            prop_assert_eq!(
                second,
                Err(RegisterError::AlreadyRegistered(case.subject.clone()))
            );
        }

        #[test]
        fn da_8_open_assumption_is_not_admitted(
            bundle in nonempty_bundle_strategy(),
            case in case_strategy()
        ) {
            let lane = DistinctAgentLane::new(bundle);
            let env = lane.evaluate(&case);
            let expected_rejections = env
                .assumptions
                .iter()
                .cloned()
                .map(Rejection::OpenAssumption)
                .collect::<Vec<_>>();
            let mut registry = IdentityRegistry::new();

            prop_assert_eq!(
                registry.register(case.subject.clone(), env, closed_policy(&case.subject)),
                Err(RegisterError::NotAdmitted(expected_rejections))
            );
        }
    }
}

use hsai_claim_envelope::{
    ClaimEnvelope, LaneId, Maturity, Predicate, PropertyKind, SubjectId, TimeWindow,
};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct ActionId(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct ModelId(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct MemoryRoot(pub [u8; 32]);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum Verdict {
    Accept,
    Reject,
    Inconclusive,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct OracleContract {
    pub expected: Verdict,
    pub target_guarantees: BTreeSet<Predicate>,
    pub excluded: BTreeSet<Predicate>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentCase {
    pub action: ActionId,
    pub subject: SubjectId,
    pub claimed_model: ModelId,
    pub memory_root: MemoryRoot,
    pub observed_at: u64,
    pub oracle: OracleContract,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RawAction {
    pub action: ActionId,
    pub subject: SubjectId,
    pub claimed_model: ModelId,
    pub memory_root: MemoryRoot,
    pub observed_at: u64,
    pub oracle: OracleContract,
}

impl From<RawAction> for AgentCase {
    fn from(raw: RawAction) -> Self {
        Self {
            action: raw.action,
            subject: raw.subject,
            claimed_model: raw.claimed_model,
            memory_root: raw.memory_root,
            observed_at: raw.observed_at,
            oracle: raw.oracle,
        }
    }
}

pub trait CaseSource {
    fn lower(&self, action: RawAction) -> AgentCase;
}

pub trait EvidenceLane {
    fn id(&self) -> LaneId;
    fn ceiling(&self) -> Maturity;
    fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope;
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct DeclaredLane;

impl EvidenceLane for DeclaredLane {
    fn id(&self) -> LaneId {
        LaneId::Named("declared".to_owned())
    }

    fn ceiling(&self) -> Maturity {
        Maturity::Stub
    }

    fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope {
        ClaimEnvelope::new(
            BTreeSet::new(),
            case.oracle.target_guarantees.clone(),
            case.oracle.excluded.clone(),
            Maturity::Stub,
            BTreeSet::new(),
            TimeWindow::all(),
            self.id(),
        )
    }
}

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct LocalMemoryLane;

impl EvidenceLane for LocalMemoryLane {
    fn id(&self) -> LaneId {
        LaneId::Named("local-memory".to_owned())
    }

    fn ceiling(&self) -> Maturity {
        Maturity::Local
    }

    fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope {
        ClaimEnvelope::new(
            BTreeSet::from([memory_integrity(&case.subject)]),
            BTreeSet::new(),
            case.oracle.excluded.clone(),
            Maturity::Local,
            BTreeSet::new(),
            TimeWindow {
                start: case.observed_at,
                end: u64::MAX,
            },
            self.id(),
        )
    }
}

pub fn memory_integrity(subject: &SubjectId) -> Predicate {
    Predicate {
        subject: subject.clone(),
        property: PropertyKind::MemoryIntegrity,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_claim_envelope::{admits, conjoin, AcceptancePolicy, Rejection, TrustRootClass};
    use proptest::collection::btree_set;
    use proptest::prelude::*;

    #[derive(Clone, Copy, Debug, Default)]
    struct DeterministicCaseSource;

    impl CaseSource for DeterministicCaseSource {
        fn lower(&self, action: RawAction) -> AgentCase {
            action.into()
        }
    }

    #[derive(Clone, Debug)]
    enum ReferenceLane {
        Declared(DeclaredLane),
        LocalMemory(LocalMemoryLane),
    }

    impl EvidenceLane for ReferenceLane {
        fn id(&self) -> LaneId {
            match self {
                Self::Declared(lane) => lane.id(),
                Self::LocalMemory(lane) => lane.id(),
            }
        }

        fn ceiling(&self) -> Maturity {
            match self {
                Self::Declared(lane) => lane.ceiling(),
                Self::LocalMemory(lane) => lane.ceiling(),
            }
        }

        fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope {
            match self {
                Self::Declared(lane) => lane.evaluate(case),
                Self::LocalMemory(lane) => lane.evaluate(case),
            }
        }
    }

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn action(id: &str) -> ActionId {
        ActionId(id.to_owned())
    }

    fn model(id: &str) -> ModelId {
        ModelId(id.to_owned())
    }

    fn memory(byte: u8) -> MemoryRoot {
        MemoryRoot([byte; 32])
    }

    fn predicate(subject_id: &str, property: PropertyKind) -> Predicate {
        Predicate {
            subject: subject(subject_id),
            property,
        }
    }

    fn distinctness_agent_a() -> Predicate {
        predicate("agentA", PropertyKind::Distinctness)
    }

    fn memory_integrity_agent_a() -> Predicate {
        predicate("agentA", PropertyKind::MemoryIntegrity)
    }

    fn semantic_correctness_action1() -> Predicate {
        predicate("action1", PropertyKind::SemanticCorrectness)
    }

    fn fixture_case() -> AgentCase {
        AgentCase {
            action: action("action1"),
            subject: subject("agentA"),
            claimed_model: model("modelA"),
            memory_root: memory(7),
            observed_at: 120,
            oracle: OracleContract {
                expected: Verdict::Accept,
                target_guarantees: BTreeSet::from([
                    distinctness_agent_a(),
                    memory_integrity_agent_a(),
                ]),
                excluded: BTreeSet::from([semantic_correctness_action1()]),
            },
        }
    }

    #[test]
    fn w1_declaration_proves_nothing() {
        let case = fixture_case();
        let envelope = DeclaredLane.evaluate(&case);

        assert!(envelope.guarantees.is_empty());
        assert_eq!(
            envelope.assumptions,
            BTreeSet::from([distinctness_agent_a(), memory_integrity_agent_a()])
        );
        assert_eq!(
            envelope.excludes,
            BTreeSet::from([semantic_correctness_action1()])
        );
        assert_eq!(envelope.maturity, Maturity::Stub);
        assert!(envelope.trust_roots.is_empty());
        assert_eq!(envelope.valid, TimeWindow::all());

        let policy = AcceptancePolicy {
            require: BTreeSet::new(),
            min_maturity: Maturity::Stub,
            forbid_roots: BTreeSet::<TrustRootClass>::new(),
            require_closed: true,
            at: case.observed_at,
        };

        assert_eq!(
            admits(policy, envelope),
            Err(vec![
                Rejection::OpenAssumption(distinctness_agent_a()),
                Rejection::OpenAssumption(memory_integrity_agent_a()),
            ])
        );
    }

    #[test]
    fn w2_local_memory_discharges_memory_not_distinctness() {
        let case = fixture_case();
        let declaration = DeclaredLane.evaluate(&case);
        let memory = LocalMemoryLane.evaluate(&case);

        assert_eq!(
            memory.guarantees,
            BTreeSet::from([memory_integrity_agent_a()])
        );
        assert!(memory.assumptions.is_empty());
        assert_eq!(
            memory.excludes,
            BTreeSet::from([semantic_correctness_action1()])
        );
        assert_eq!(memory.maturity, Maturity::Local);
        assert!(memory.trust_roots.is_empty());
        assert_eq!(
            memory.valid,
            TimeWindow {
                start: case.observed_at,
                end: u64::MAX,
            }
        );

        let combined = conjoin(declaration, memory);
        assert_eq!(
            combined.guarantees,
            BTreeSet::from([memory_integrity_agent_a()])
        );
        assert_eq!(
            combined.assumptions,
            BTreeSet::from([distinctness_agent_a()])
        );
        assert_eq!(
            combined.excludes,
            BTreeSet::from([semantic_correctness_action1()])
        );
        assert_eq!(combined.maturity, Maturity::Stub);
        assert!(combined.trust_roots.is_empty());
        assert_eq!(
            combined.valid,
            TimeWindow {
                start: case.observed_at,
                end: u64::MAX,
            }
        );
    }

    #[test]
    fn w3_lowering_is_deterministic() {
        let source = DeterministicCaseSource;
        let raw = raw_action_fixture();

        assert_eq!(source.lower(raw.clone()), source.lower(raw));
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

    fn verdict_strategy() -> impl Strategy<Value = Verdict> {
        prop_oneof![
            Just(Verdict::Accept),
            Just(Verdict::Reject),
            Just(Verdict::Inconclusive),
        ]
    }

    fn agent_case_strategy() -> impl Strategy<Value = AgentCase> {
        (
            0_u8..8,
            0_u8..8,
            0_u8..8,
            any::<[u8; 32]>(),
            0_u64..10_000,
            verdict_strategy(),
            btree_set(predicate_strategy(), 0..6),
            btree_set(predicate_strategy(), 0..6),
        )
            .prop_map(
                |(
                    action_id,
                    subject_id,
                    model_id,
                    memory_root,
                    observed_at,
                    expected,
                    target_guarantees,
                    excluded,
                )| AgentCase {
                    action: ActionId(format!("action-{action_id}")),
                    subject: SubjectId(format!("subject-{subject_id}")),
                    claimed_model: ModelId(format!("model-{model_id}")),
                    memory_root: MemoryRoot(memory_root),
                    observed_at,
                    oracle: OracleContract {
                        expected,
                        target_guarantees,
                        excluded,
                    },
                },
            )
    }

    fn raw_action_strategy() -> impl Strategy<Value = RawAction> {
        agent_case_strategy().prop_map(|case| RawAction {
            action: case.action,
            subject: case.subject,
            claimed_model: case.claimed_model,
            memory_root: case.memory_root,
            observed_at: case.observed_at,
            oracle: case.oracle,
        })
    }

    fn lane_strategy() -> impl Strategy<Value = ReferenceLane> {
        prop_oneof![
            Just(ReferenceLane::Declared(DeclaredLane)),
            Just(ReferenceLane::LocalMemory(LocalMemoryLane)),
        ]
    }

    fn raw_action_fixture() -> RawAction {
        let case = fixture_case();
        RawAction {
            action: case.action,
            subject: case.subject,
            claimed_model: case.claimed_model,
            memory_root: case.memory_root,
            observed_at: case.observed_at,
            oracle: case.oracle,
        }
    }

    proptest! {
        #[test]
        fn lane_1_maturity_never_exceeds_ceiling(lane in lane_strategy(), case in agent_case_strategy()) {
            let envelope = lane.evaluate(&case);
            prop_assert!(envelope.maturity <= lane.ceiling());
        }

        #[test]
        fn lane_2_case_excluded_boundary_propagates(lane in lane_strategy(), case in agent_case_strategy()) {
            let envelope = lane.evaluate(&case);
            prop_assert!(case.oracle.excluded.is_subset(&envelope.excludes));
        }

        #[test]
        fn lane_3_reference_lanes_add_no_trust_roots(lane in lane_strategy(), case in agent_case_strategy()) {
            let envelope = lane.evaluate(&case);
            prop_assert!(envelope.trust_roots.is_empty());
        }

        #[test]
        fn lane_4_lane_evaluation_is_deterministic(lane in lane_strategy(), case in agent_case_strategy()) {
            prop_assert_eq!(lane.evaluate(&case), lane.evaluate(&case));
        }

        #[test]
        fn case_1_lowering_is_deterministic(raw in raw_action_strategy()) {
            let source = DeterministicCaseSource;
            prop_assert_eq!(source.lower(raw.clone()), source.lower(raw));
        }
    }
}

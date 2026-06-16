use hsai_claim_envelope::SubjectId;
use hsai_distinct_agent::IdentityRegistry;
use hsai_economy::{Credits, Economy, EconomyError, PoolPolicy};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct ExternalAmount(pub u128);

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum AutonomyLevel {
    Supervised,
    Bounded,
    Autonomous,
}

impl AutonomyLevel {
    pub fn out_factor(&self) -> u128 {
        match self {
            Self::Supervised => 4,
            Self::Bounded => 2,
            Self::Autonomous => 1,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct Membrane {
    pub base_cap: u128,
    pub out_in_window: u128,
    pub in_in_window: u128,
    pub window: u64,
}

impl Membrane {
    pub fn new(base_cap: u128) -> Self {
        Self {
            base_cap,
            out_in_window: 0,
            in_in_window: 0,
            window: 0,
        }
    }

    pub fn cap_for(&self, level: AutonomyLevel) -> u128 {
        self.base_cap
            .saturating_mul(level.out_factor())
            .min(i128::MAX as u128)
    }

    pub fn convert_out<P: PoolPolicy>(
        &mut self,
        economy: &mut Economy<P>,
        reg: &IdentityRegistry,
        subject: SubjectId,
        amount: Credits,
        level: AutonomyLevel,
    ) -> Result<ExternalAmount, MembraneError> {
        if amount.is_negative() {
            return Err(MembraneError::NegativeAmount);
        }
        let requested = amount.0 as u128;
        let remaining = self.cap_for(level).saturating_sub(self.out_in_window);
        if requested > remaining {
            return Err(MembraneError::OverCap {
                requested,
                remaining,
            });
        }

        economy
            .debit_external(reg, subject, amount)
            .map_err(MembraneError::Economy)?;
        self.out_in_window = self.out_in_window.saturating_add(requested);
        Ok(ExternalAmount(requested))
    }

    pub fn convert_in<P: PoolPolicy>(
        &mut self,
        economy: &mut Economy<P>,
        reg: &IdentityRegistry,
        subject: SubjectId,
        external: ExternalAmount,
        level: AutonomyLevel,
    ) -> Result<Credits, MembraneError> {
        let requested = external.0;
        let remaining = self.cap_for(level).saturating_sub(self.in_in_window);
        if requested > remaining {
            return Err(MembraneError::OverCap {
                requested,
                remaining,
            });
        }

        let amount = Credits(
            i128::try_from(requested).map_err(|_| MembraneError::OverCap {
                requested,
                remaining,
            })?,
        );
        economy
            .credit_external(reg, subject, amount)
            .map_err(MembraneError::Economy)?;
        self.in_in_window = self.in_in_window.saturating_add(requested);
        Ok(amount)
    }

    pub fn advance_window(&mut self) {
        self.window = self.window.saturating_add(1);
        self.out_in_window = 0;
        self.in_in_window = 0;
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum MembraneError {
    Economy(EconomyError),
    OverCap { requested: u128, remaining: u128 },
    NegativeAmount,
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_agent_case::{ActionId, AgentCase, MemoryRoot, ModelId, OracleContract, Verdict};
    use hsai_claim_envelope::{
        AcceptancePolicy, ClaimEnvelope, LaneId, Maturity, TimeWindow, TrustRootClass,
    };
    use hsai_distinct_agent::{
        distinctness, Anchor, AnchorBundle, DistinctAgentLane, IdentityRegistry,
    };
    use hsai_economy::{DemurragePolicy, FloorPlusDemandPeg};
    use proptest::prelude::*;
    use std::collections::BTreeSet;

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn case_for(subject_id: &str) -> AgentCase {
        let subject = subject(subject_id);
        AgentCase {
            action: ActionId(format!("action-{subject_id}")),
            subject: subject.clone(),
            claimed_model: ModelId("model".to_owned()),
            memory_root: MemoryRoot([1; 32]),
            observed_at: 0,
            oracle: OracleContract {
                expected: Verdict::Accept,
                target_guarantees: BTreeSet::from([distinctness(&subject)]),
                excluded: BTreeSet::new(),
            },
        }
    }

    fn anchor_for(id: &str) -> Anchor {
        Anchor::HardwareAttested {
            vendor: "test".to_owned(),
            device: id.to_owned(),
        }
    }

    fn closed_distinct_env(case: &AgentCase, lane: &DistinctAgentLane) -> ClaimEnvelope {
        let distinct = hsai_agent_case::EvidenceLane::evaluate(lane, case);
        let verified = ClaimEnvelope::new(
            lane.anchors
                .0
                .iter()
                .map(|anchor| anchor.validity_assumption(&case.subject))
                .collect(),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Attested,
            BTreeSet::new(),
            TimeWindow::all(),
            LaneId::Named("test-verified-anchor".to_owned()),
        );
        hsai_claim_envelope::conjoin(distinct, verified)
    }

    fn distinct_policy(subject: &SubjectId) -> AcceptancePolicy {
        AcceptancePolicy {
            require: BTreeSet::from([distinctness(subject)]),
            min_maturity: Maturity::Attested,
            forbid_roots: BTreeSet::<TrustRootClass>::new(),
            require_closed: true,
            at: 0,
        }
    }

    fn registry_with(subjects: &[&str]) -> IdentityRegistry {
        let mut registry = IdentityRegistry::new();
        for subject_id in subjects {
            let case = case_for(subject_id);
            let lane =
                DistinctAgentLane::new(AnchorBundle(BTreeSet::from([anchor_for(subject_id)])));
            registry
                .register(
                    case.subject.clone(),
                    closed_distinct_env(&case, &lane),
                    distinct_policy(&case.subject),
                )
                .expect("fixture identity must register");
        }
        registry
    }

    fn policy_with_floor(floor: u64) -> DemurragePolicy {
        DemurragePolicy {
            peg: FloorPlusDemandPeg {
                floor,
                demand_multiplier: 0,
            },
            rate: 0,
        }
    }

    fn economy_with_balance(
        registry: &IdentityRegistry,
        subject: &SubjectId,
        balance: i128,
    ) -> Economy<DemurragePolicy> {
        let mut economy = Economy::new(policy_with_floor(0));
        economy
            .credit_external(registry, subject.clone(), Credits(balance))
            .expect("fixture credit succeeds");
        economy
    }

    fn fixture_state() -> (
        IdentityRegistry,
        SubjectId,
        Economy<DemurragePolicy>,
        Membrane,
    ) {
        let registry = registry_with(&["agentA"]);
        let agent = subject("agentA");
        let economy = economy_with_balance(&registry, &agent, 100);
        (registry, agent, economy, Membrane::new(10))
    }

    #[test]
    fn mb1_convert_out_within_cap_debits_and_emits_external_amount() {
        let (registry, agent, mut economy, mut membrane) = fixture_state();
        let before_total = economy.total_credits();

        assert_eq!(
            membrane.convert_out(
                &mut economy,
                &registry,
                agent.clone(),
                Credits(8),
                AutonomyLevel::Autonomous,
            ),
            Ok(ExternalAmount(8))
        );
        assert_eq!(economy.balance(&agent), Credits(92));
        assert_eq!(economy.total_credits(), Credits(before_total.0 - 8));
        assert_eq!(membrane.out_in_window, 8);
    }

    #[test]
    fn mb2_over_cap_rejects_without_state_change() {
        let (registry, agent, mut economy, mut membrane) = fixture_state();
        membrane
            .convert_out(
                &mut economy,
                &registry,
                agent.clone(),
                Credits(8),
                AutonomyLevel::Autonomous,
            )
            .unwrap();
        let economy_before = economy.clone();
        let membrane_before = membrane.clone();

        assert_eq!(
            membrane.convert_out(
                &mut economy,
                &registry,
                agent,
                Credits(5),
                AutonomyLevel::Autonomous,
            ),
            Err(MembraneError::OverCap {
                requested: 5,
                remaining: 2,
            })
        );
        assert_eq!(economy, economy_before);
        assert_eq!(membrane, membrane_before);
    }

    #[test]
    fn mb3_frozen_account_cannot_externalize() {
        let (registry, agent, mut economy, mut membrane) = fixture_state();
        economy.freeze(agent.clone());
        let economy_before = economy.clone();
        let membrane_before = membrane.clone();

        assert_eq!(
            membrane.convert_out(
                &mut economy,
                &registry,
                agent.clone(),
                Credits(1),
                AutonomyLevel::Autonomous,
            ),
            Err(MembraneError::Economy(EconomyError::Frozen(agent)))
        );
        assert_eq!(economy, economy_before);
        assert_eq!(membrane, membrane_before);
    }

    #[test]
    fn mb4_advance_window_refreshes_cap() {
        let (registry, agent, mut economy, mut membrane) = fixture_state();
        membrane
            .convert_out(
                &mut economy,
                &registry,
                agent.clone(),
                Credits(8),
                AutonomyLevel::Autonomous,
            )
            .unwrap();
        membrane.advance_window();
        assert_eq!(membrane.out_in_window, 0);

        assert_eq!(
            membrane.convert_out(
                &mut economy,
                &registry,
                agent,
                Credits(8),
                AutonomyLevel::Autonomous,
            ),
            Ok(ExternalAmount(8))
        );
    }

    #[test]
    fn mb5_autonomy_tightens_the_cap() {
        let registry = registry_with(&["agentA"]);
        let agent = subject("agentA");
        let mut supervised_economy = economy_with_balance(&registry, &agent, 100);
        let mut supervised = Membrane::new(10);
        assert_eq!(
            supervised.convert_out(
                &mut supervised_economy,
                &registry,
                agent.clone(),
                Credits(30),
                AutonomyLevel::Supervised,
            ),
            Ok(ExternalAmount(30))
        );

        let mut autonomous_economy = economy_with_balance(&registry, &agent, 100);
        let mut autonomous = Membrane::new(10);
        assert_eq!(
            autonomous.convert_out(
                &mut autonomous_economy,
                &registry,
                agent,
                Credits(30),
                AutonomyLevel::Autonomous,
            ),
            Err(MembraneError::OverCap {
                requested: 30,
                remaining: 10,
            })
        );
    }

    fn level_strategy() -> impl Strategy<Value = AutonomyLevel> {
        prop_oneof![
            Just(AutonomyLevel::Supervised),
            Just(AutonomyLevel::Bounded),
            Just(AutonomyLevel::Autonomous),
        ]
    }

    proptest! {
        #[test]
        fn m_1_frozen_subject_cannot_convert_and_state_is_unchanged(
            amount in 0_i128..10,
            level in level_strategy()
        ) {
            let (registry, agent, mut economy, mut membrane) = fixture_state();
            economy.freeze(agent.clone());
            let economy_before = economy.clone();
            let membrane_before = membrane.clone();

            let out = membrane.convert_out(&mut economy, &registry, agent.clone(), Credits(amount), level);
            prop_assert_eq!(out, Err(MembraneError::Economy(EconomyError::Frozen(agent.clone()))));
            prop_assert_eq!(&economy, &economy_before);
            prop_assert_eq!(&membrane, &membrane_before);

            let input = membrane.convert_in(&mut economy, &registry, agent.clone(), ExternalAmount(amount as u128), level);
            prop_assert_eq!(input, Err(MembraneError::Economy(EconomyError::Frozen(agent))));
            prop_assert_eq!(&economy, &economy_before);
            prop_assert_eq!(&membrane, &membrane_before);
        }

        #[test]
        fn m_2_cumulative_out_never_exceeds_cap_and_overcap_is_unchanged(
            base_cap in 0_u128..50,
            first in 0_i128..50,
            second in 0_i128..50,
            level in level_strategy()
        ) {
            let registry = registry_with(&["agentA"]);
            let agent = subject("agentA");
            let mut economy = economy_with_balance(&registry, &agent, 500);
            let mut membrane = Membrane::new(base_cap);
            let cap = membrane.cap_for(level);

            let _ = membrane.convert_out(&mut economy, &registry, agent.clone(), Credits(first), level);
            prop_assert!(membrane.out_in_window <= cap);
            let before_economy = economy.clone();
            let before_membrane = membrane.clone();
            let remaining = cap.saturating_sub(membrane.out_in_window);
            let result = membrane.convert_out(&mut economy, &registry, agent.clone(), Credits(second), level);
            if second as u128 > remaining {
                prop_assert_eq!(
                    result,
                    Err(MembraneError::OverCap {
                        requested: second as u128,
                        remaining,
                    })
                );
                prop_assert_eq!(economy, before_economy);
                prop_assert_eq!(membrane, before_membrane);
            } else {
                prop_assert!(result.is_ok());
                prop_assert!(membrane.out_in_window <= cap);
            }
        }

        #[test]
        fn m_3_unregistered_subject_is_rejected_without_state_change(amount in 0_i128..10, level in level_strategy()) {
            let registry = IdentityRegistry::new();
            let agent = subject("agentA");
            let mut economy = Economy::new(policy_with_floor(0));
            let mut membrane = Membrane::new(10);
            let economy_before = economy.clone();
            let membrane_before = membrane.clone();

            prop_assert_eq!(
                membrane.convert_out(&mut economy, &registry, agent.clone(), Credits(amount), level),
                Err(MembraneError::Economy(EconomyError::NotRegistered(agent)))
            );
            prop_assert_eq!(economy, economy_before);
            prop_assert_eq!(membrane, membrane_before);
        }

        #[test]
        fn m_4_successful_convert_out_burns_exact_amount(amount in 0_i128..40, level in level_strategy()) {
            let registry = registry_with(&["agentA"]);
            let agent = subject("agentA");
            let mut economy = economy_with_balance(&registry, &agent, 500);
            let mut membrane = Membrane::new(40);
            let before = economy.total_credits();
            let result = membrane.convert_out(&mut economy, &registry, agent.clone(), Credits(amount), level);

            if result.is_ok() {
                prop_assert_eq!(result, Ok(ExternalAmount(amount as u128)));
                prop_assert_eq!(economy.total_credits(), Credits(before.0 - amount));
                prop_assert_eq!(membrane.out_in_window, amount as u128);
            }
        }

        #[test]
        fn m_5_convert_out_respects_policy_min_balance(amount in 0_i128..40) {
            let registry = registry_with(&["agentA"]);
            let agent = subject("agentA");
            let mut economy = economy_with_balance(&registry, &agent, 10);
            let mut membrane = Membrane::new(100);
            let before_economy = economy.clone();
            let before_membrane = membrane.clone();
            let result = membrane.convert_out(
                &mut economy,
                &registry,
                agent,
                Credits(amount),
                AutonomyLevel::Supervised,
            );

            if amount > 10 {
                prop_assert_eq!(result, Err(MembraneError::Economy(EconomyError::InsufficientBalance)));
                prop_assert_eq!(economy, before_economy);
                prop_assert_eq!(membrane, before_membrane);
            } else {
                prop_assert!(result.is_ok());
            }
        }

        #[test]
        fn m_6_window_reset_restores_full_cap(amount in 0_i128..20, level in level_strategy()) {
            let registry = registry_with(&["agentA"]);
            let agent = subject("agentA");
            let mut economy = economy_with_balance(&registry, &agent, 500);
            let mut membrane = Membrane::new(20);

            let _ = membrane.convert_out(&mut economy, &registry, agent.clone(), Credits(amount), level);
            membrane.convert_in(&mut economy, &registry, agent.clone(), ExternalAmount(amount as u128), level).ok();
            membrane.advance_window();

            prop_assert_eq!(membrane.out_in_window, 0);
            prop_assert_eq!(membrane.in_in_window, 0);
            prop_assert_eq!(membrane.window, 1);
            prop_assert_eq!(membrane.cap_for(level), Membrane::new(20).cap_for(level));
        }

        #[test]
        fn m_7_autonomy_caps_are_monotone(base_cap in 0_u128..1_000) {
            let membrane = Membrane::new(base_cap);

            prop_assert!(membrane.cap_for(AutonomyLevel::Autonomous) <= membrane.cap_for(AutonomyLevel::Bounded));
            prop_assert!(membrane.cap_for(AutonomyLevel::Bounded) <= membrane.cap_for(AutonomyLevel::Supervised));
        }

        #[test]
        fn m_8_identical_operation_sequences_are_deterministic(
            amount_out in 0_i128..20,
            amount_in in 0_u128..20,
            level in level_strategy()
        ) {
            let registry = registry_with(&["agentA"]);
            let agent = subject("agentA");
            let mut left_economy = economy_with_balance(&registry, &agent, 500);
            let mut right_economy = economy_with_balance(&registry, &agent, 500);
            let mut left = Membrane::new(20);
            let mut right = Membrane::new(20);

            let _ = left.convert_out(&mut left_economy, &registry, agent.clone(), Credits(amount_out), level);
            let _ = right.convert_out(&mut right_economy, &registry, agent.clone(), Credits(amount_out), level);
            let _ = left.convert_in(&mut left_economy, &registry, agent.clone(), ExternalAmount(amount_in), level);
            let _ = right.convert_in(&mut right_economy, &registry, agent, ExternalAmount(amount_in), level);
            left.advance_window();
            right.advance_window();

            prop_assert_eq!(left, right);
            prop_assert_eq!(left_economy, right_economy);
        }
    }
}

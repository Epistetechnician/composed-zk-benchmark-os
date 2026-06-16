use hsai_claim_envelope::{admits, AcceptancePolicy, ClaimEnvelope, Rejection, SubjectId};
use hsai_distinct_agent::IdentityRegistry;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct Credits(pub i128);

impl Credits {
    pub fn checked_add(self, other: Self) -> Option<Self> {
        self.0.checked_add(other.0).map(Self)
    }

    pub fn checked_sub(self, other: Self) -> Option<Self> {
        self.0.checked_sub(other.0).map(Self)
    }

    pub fn saturating_add(self, other: Self) -> Self {
        Self(self.0.saturating_add(other.0))
    }

    pub fn saturating_sub(self, other: Self) -> Self {
        Self(self.0.saturating_sub(other.0))
    }

    pub fn is_negative(self) -> bool {
        self.0 < 0
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct WorkRecord {
    pub worker: SubjectId,
    pub admitted: bool,
    pub demand: u64,
}

pub trait PegPolicy {
    fn reward(&self, work: &WorkRecord) -> Credits;
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct FloorPlusDemandPeg {
    pub floor: u64,
    pub demand_multiplier: u64,
}

impl PegPolicy for FloorPlusDemandPeg {
    fn reward(&self, work: &WorkRecord) -> Credits {
        if !work.admitted {
            return Credits(0);
        }

        let demand_reward = self.demand_multiplier.saturating_mul(work.demand);
        let reward = self.floor.saturating_add(demand_reward);
        Credits(i128::from(reward))
    }
}

pub trait PoolPolicy {
    fn issue(&self, work: &WorkRecord) -> Credits;
    fn decay(&self, balance: Credits, ticks: u64) -> Credits;
    fn min_balance(&self) -> i128;
    fn name(&self) -> &'static str;
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct DemurragePolicy {
    pub peg: FloorPlusDemandPeg,
    pub rate: u64,
}

impl PoolPolicy for DemurragePolicy {
    fn issue(&self, work: &WorkRecord) -> Credits {
        self.peg.reward(work)
    }

    fn decay(&self, balance: Credits, ticks: u64) -> Credits {
        let decay = i128::from(self.rate.saturating_mul(ticks));
        Credits(balance.0.saturating_sub(decay).max(0))
    }

    fn min_balance(&self) -> i128 {
        0
    }

    fn name(&self) -> &'static str {
        "demurrage"
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct MutualCreditPolicy {
    pub peg: FloorPlusDemandPeg,
    pub credit_limit: u64,
}

impl PoolPolicy for MutualCreditPolicy {
    fn issue(&self, work: &WorkRecord) -> Credits {
        self.peg.reward(work)
    }

    fn decay(&self, balance: Credits, _ticks: u64) -> Credits {
        balance
    }

    fn min_balance(&self) -> i128 {
        -i128::from(self.credit_limit)
    }

    fn name(&self) -> &'static str {
        "mutual-credit"
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct Economy<P: PoolPolicy> {
    pub policy: P,
    accounts: BTreeMap<SubjectId, Credits>,
    pool: Credits,
    frozen: BTreeSet<SubjectId>,
    tick: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EconomyError {
    NotRegistered(SubjectId),
    Frozen(SubjectId),
    WorkNotAdmitted(Vec<Rejection>),
    InsufficientBalance,
    PoolInsufficient,
}

impl<P: PoolPolicy> Economy<P> {
    pub fn new(policy: P) -> Self {
        Self {
            policy,
            accounts: BTreeMap::new(),
            pool: Credits(0),
            frozen: BTreeSet::new(),
            tick: 0,
        }
    }

    pub fn earn(
        &mut self,
        reg: &IdentityRegistry,
        worker: SubjectId,
        work_env: ClaimEnvelope,
        policy: AcceptancePolicy,
        demand: u64,
    ) -> Result<Credits, EconomyError> {
        self.ensure_registered(reg, &worker)?;
        self.ensure_unfrozen(&worker)?;
        admits(policy, work_env).map_err(EconomyError::WorkNotAdmitted)?;

        let work = WorkRecord {
            worker: worker.clone(),
            admitted: true,
            demand,
        };
        let credits = self.policy.issue(&work);
        let current = self.balance(&worker);
        let next = current
            .checked_add(credits)
            .ok_or(EconomyError::InsufficientBalance)?;
        self.accounts.insert(worker, next);
        Ok(credits)
    }

    pub fn gift(
        &mut self,
        reg: &IdentityRegistry,
        from: SubjectId,
        amount: Credits,
    ) -> Result<(), EconomyError> {
        self.ensure_registered(reg, &from)?;
        self.ensure_unfrozen(&from)?;
        if amount.is_negative() {
            return Err(EconomyError::InsufficientBalance);
        }

        let current = self.balance(&from);
        let next = current
            .checked_sub(amount)
            .ok_or(EconomyError::InsufficientBalance)?;
        if next.0 < self.policy.min_balance() {
            return Err(EconomyError::InsufficientBalance);
        }
        let next_pool = self
            .pool
            .checked_add(amount)
            .ok_or(EconomyError::PoolInsufficient)?;

        self.accounts.insert(from, next);
        self.pool = next_pool;
        Ok(())
    }

    pub fn fund(
        &mut self,
        reg: &IdentityRegistry,
        to: SubjectId,
        amount: Credits,
    ) -> Result<(), EconomyError> {
        self.ensure_registered(reg, &to)?;
        self.ensure_unfrozen(&to)?;
        if amount.is_negative() {
            return Err(EconomyError::PoolInsufficient);
        }

        let next_pool = self
            .pool
            .checked_sub(amount)
            .ok_or(EconomyError::PoolInsufficient)?;
        if next_pool.0 < 0 {
            return Err(EconomyError::PoolInsufficient);
        }
        let next_balance = self
            .balance(&to)
            .checked_add(amount)
            .ok_or(EconomyError::PoolInsufficient)?;

        self.pool = next_pool;
        self.accounts.insert(to, next_balance);
        Ok(())
    }

    pub fn debit_external(
        &mut self,
        reg: &IdentityRegistry,
        subject: SubjectId,
        amount: Credits,
    ) -> Result<(), EconomyError> {
        self.ensure_registered(reg, &subject)?;
        self.ensure_unfrozen(&subject)?;
        if amount.is_negative() {
            return Err(EconomyError::InsufficientBalance);
        }

        let next = self
            .balance(&subject)
            .checked_sub(amount)
            .ok_or(EconomyError::InsufficientBalance)?;
        if next.0 < self.policy.min_balance() {
            return Err(EconomyError::InsufficientBalance);
        }

        self.accounts.insert(subject, next);
        Ok(())
    }

    pub fn credit_external(
        &mut self,
        reg: &IdentityRegistry,
        subject: SubjectId,
        amount: Credits,
    ) -> Result<(), EconomyError> {
        self.ensure_registered(reg, &subject)?;
        self.ensure_unfrozen(&subject)?;
        if amount.is_negative() {
            return Err(EconomyError::InsufficientBalance);
        }

        let next = self
            .balance(&subject)
            .checked_add(amount)
            .ok_or(EconomyError::InsufficientBalance)?;
        self.accounts.insert(subject, next);
        Ok(())
    }

    pub fn tick(&mut self) {
        self.tick = self.tick.saturating_add(1);
        for balance in self.accounts.values_mut() {
            *balance = self.policy.decay(*balance, 1);
        }
    }

    pub fn freeze(&mut self, subject: SubjectId) {
        self.frozen.insert(subject);
    }

    pub fn unfreeze(&mut self, subject: &SubjectId) {
        self.frozen.remove(subject);
    }

    pub fn balance(&self, subject: &SubjectId) -> Credits {
        self.accounts.get(subject).copied().unwrap_or_default()
    }

    pub fn pool(&self) -> Credits {
        self.pool
    }

    pub fn tick_count(&self) -> u64 {
        self.tick
    }

    pub fn total_credits(&self) -> Credits {
        self.accounts
            .values()
            .copied()
            .fold(self.pool, Credits::saturating_add)
    }

    fn ensure_registered(
        &self,
        reg: &IdentityRegistry,
        subject: &SubjectId,
    ) -> Result<(), EconomyError> {
        if reg.identity(subject).is_some() {
            Ok(())
        } else {
            Err(EconomyError::NotRegistered(subject.clone()))
        }
    }

    fn ensure_unfrozen(&self, subject: &SubjectId) -> Result<(), EconomyError> {
        if self.frozen.contains(subject) {
            Err(EconomyError::Frozen(subject.clone()))
        } else {
            Ok(())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_agent_case::{ActionId, AgentCase, MemoryRoot, ModelId, OracleContract, Verdict};
    use hsai_claim_envelope::{
        AcceptancePolicy, ClaimEnvelope, LaneId, Maturity, Predicate, PropertyKind, TimeWindow,
        TrustRootClass,
    };
    use hsai_distinct_agent::{
        distinctness, Anchor, AnchorBundle, DistinctAgentLane, IdentityRegistry,
    };
    use proptest::prelude::*;
    use std::collections::BTreeSet;

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn work_predicate(worker: &SubjectId) -> Predicate {
        Predicate {
            subject: worker.clone(),
            property: PropertyKind::PolicyCompliance,
        }
    }

    fn admitted_work_env(worker: &SubjectId) -> ClaimEnvelope {
        ClaimEnvelope::new(
            BTreeSet::from([work_predicate(worker)]),
            BTreeSet::new(),
            BTreeSet::new(),
            Maturity::Local,
            BTreeSet::new(),
            TimeWindow::all(),
            LaneId::Named("test-work".to_owned()),
        )
    }

    fn work_policy(worker: &SubjectId) -> AcceptancePolicy {
        AcceptancePolicy {
            require: BTreeSet::from([work_predicate(worker)]),
            min_maturity: Maturity::Local,
            forbid_roots: BTreeSet::<TrustRootClass>::new(),
            require_closed: true,
            at: 0,
        }
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

    fn demurrage_policy() -> DemurragePolicy {
        DemurragePolicy {
            peg: FloorPlusDemandPeg {
                floor: 10,
                demand_multiplier: 2,
            },
            rate: 5,
        }
    }

    fn mutual_policy() -> MutualCreditPolicy {
        MutualCreditPolicy {
            peg: FloorPlusDemandPeg {
                floor: 10,
                demand_multiplier: 2,
            },
            credit_limit: 100,
        }
    }

    #[test]
    fn e1_unregistered_subject_cannot_earn() {
        let registry = IdentityRegistry::new();
        let worker = subject("agentA");
        let mut economy = Economy::new(demurrage_policy());

        assert_eq!(
            economy.earn(
                &registry,
                worker.clone(),
                admitted_work_env(&worker),
                work_policy(&worker),
                0,
            ),
            Err(EconomyError::NotRegistered(worker))
        );
    }

    #[test]
    fn e2_flywheel_and_transfer_conservation() {
        let registry = registry_with(&["agentA", "agentB"]);
        let agent_a = subject("agentA");
        let agent_b = subject("agentB");
        let mut economy = Economy::new(demurrage_policy());

        let earned = economy
            .earn(
                &registry,
                agent_a.clone(),
                admitted_work_env(&agent_a),
                work_policy(&agent_a),
                3,
            )
            .expect("registered admitted work earns");
        assert_eq!(earned, Credits(16));

        let before_transfers = economy.total_credits();
        economy
            .gift(&registry, agent_a.clone(), Credits(8))
            .expect("gift succeeds");
        economy
            .fund(&registry, agent_b.clone(), Credits(8))
            .expect("fund succeeds");

        assert_eq!(economy.balance(&agent_a), Credits(8));
        assert_eq!(economy.balance(&agent_b), Credits(8));
        assert_eq!(economy.pool(), Credits(0));
        assert_eq!(economy.total_credits(), before_transfers);
        assert_eq!(economy.total_credits(), Credits(16));
    }

    #[test]
    fn e3_decay_differs_by_policy() {
        let registry = registry_with(&["agentA"]);
        let agent_a = subject("agentA");
        let mut demurrage = Economy::new(demurrage_policy());
        demurrage
            .earn(
                &registry,
                agent_a.clone(),
                admitted_work_env(&agent_a),
                work_policy(&agent_a),
                3,
            )
            .unwrap();
        demurrage
            .gift(&registry, agent_a.clone(), Credits(8))
            .unwrap();
        assert_eq!(demurrage.balance(&agent_a), Credits(8));
        demurrage.tick();
        assert_eq!(demurrage.balance(&agent_a), Credits(3));
        demurrage.tick();
        assert_eq!(demurrage.balance(&agent_a), Credits(0));

        let mut mutual = Economy::new(mutual_policy());
        mutual
            .earn(
                &registry,
                agent_a.clone(),
                admitted_work_env(&agent_a),
                work_policy(&agent_a),
                3,
            )
            .unwrap();
        mutual.gift(&registry, agent_a.clone(), Credits(8)).unwrap();
        assert_eq!(mutual.balance(&agent_a), Credits(8));
        mutual.tick();
        assert_eq!(mutual.balance(&agent_a), Credits(8));
        mutual.tick();
        assert_eq!(mutual.balance(&agent_a), Credits(8));
    }

    #[test]
    fn e4_freeze_blocks_movement_until_unfrozen() {
        let registry = registry_with(&["agentA"]);
        let agent_a = subject("agentA");
        let mut economy = Economy::new(demurrage_policy());
        economy
            .earn(
                &registry,
                agent_a.clone(),
                admitted_work_env(&agent_a),
                work_policy(&agent_a),
                0,
            )
            .unwrap();
        let before = economy.balance(&agent_a);

        economy.freeze(agent_a.clone());
        assert_eq!(
            economy.gift(&registry, agent_a.clone(), Credits(1)),
            Err(EconomyError::Frozen(agent_a.clone()))
        );
        assert_eq!(economy.balance(&agent_a), before);

        economy.unfreeze(&agent_a);
        assert_eq!(economy.gift(&registry, agent_a.clone(), Credits(1)), Ok(()));
    }

    #[test]
    fn e5_mutual_credit_may_go_negative_demurrage_may_not() {
        let registry = registry_with(&["agentA"]);
        let agent_a = subject("agentA");

        let mut mutual = Economy::new(mutual_policy());
        assert_eq!(mutual.gift(&registry, agent_a.clone(), Credits(8)), Ok(()));
        assert_eq!(mutual.balance(&agent_a), Credits(-8));

        let mut demurrage = Economy::new(demurrage_policy());
        assert_eq!(
            demurrage.gift(&registry, agent_a.clone(), Credits(8)),
            Err(EconomyError::InsufficientBalance)
        );
        assert_eq!(demurrage.balance(&agent_a), Credits(0));
    }

    #[test]
    fn debit_external_burns_credits_and_respects_gates() {
        let registry = registry_with(&["agentA"]);
        let agent_a = subject("agentA");
        let mut economy = Economy::new(demurrage_policy());
        economy
            .earn(
                &registry,
                agent_a.clone(),
                admitted_work_env(&agent_a),
                work_policy(&agent_a),
                0,
            )
            .unwrap();

        let total_before = economy.total_credits();
        assert_eq!(
            economy.debit_external(&registry, agent_a.clone(), Credits(4)),
            Ok(())
        );
        assert_eq!(economy.balance(&agent_a), Credits(6));
        assert_eq!(economy.pool(), Credits(0));
        assert_eq!(economy.total_credits(), Credits(total_before.0 - 4));

        assert_eq!(
            economy.debit_external(&registry, agent_a.clone(), Credits(7)),
            Err(EconomyError::InsufficientBalance)
        );
        economy.freeze(agent_a.clone());
        assert_eq!(
            economy.debit_external(&registry, agent_a.clone(), Credits(1)),
            Err(EconomyError::Frozen(agent_a.clone()))
        );
        assert_eq!(
            economy.debit_external(&IdentityRegistry::new(), agent_a.clone(), Credits(1)),
            Err(EconomyError::NotRegistered(agent_a))
        );
    }

    #[test]
    fn credit_external_mints_credits_and_respects_gates() {
        let registry = registry_with(&["agentA"]);
        let agent_a = subject("agentA");
        let mut economy = Economy::new(demurrage_policy());

        assert_eq!(
            economy.credit_external(&registry, agent_a.clone(), Credits(9)),
            Ok(())
        );
        assert_eq!(economy.balance(&agent_a), Credits(9));
        assert_eq!(economy.total_credits(), Credits(9));

        assert_eq!(
            economy.credit_external(&registry, agent_a.clone(), Credits(-1)),
            Err(EconomyError::InsufficientBalance)
        );
        economy.freeze(agent_a.clone());
        assert_eq!(
            economy.credit_external(&registry, agent_a.clone(), Credits(1)),
            Err(EconomyError::Frozen(agent_a.clone()))
        );
        assert_eq!(
            economy.credit_external(&IdentityRegistry::new(), agent_a.clone(), Credits(1)),
            Err(EconomyError::NotRegistered(agent_a))
        );
    }

    fn subject_strategy() -> impl Strategy<Value = SubjectId> {
        (0_u8..32).prop_map(|id| SubjectId(format!("agent-{id}")))
    }

    fn registered_fixture() -> (IdentityRegistry, SubjectId, SubjectId) {
        (
            registry_with(&["agentA", "agentB"]),
            subject("agentA"),
            subject("agentB"),
        )
    }

    proptest! {
        #[test]
        fn ec_1_unregistered_subjects_cannot_touch_accounts(
            demand in 0_u64..20,
            amount in 0_i128..100
        ) {
            let registry = IdentityRegistry::new();
            let subject = subject("unregistered");
            let mut economy = Economy::new(demurrage_policy());

            prop_assert_eq!(
                economy.earn(
                    &registry,
                    subject.clone(),
                    admitted_work_env(&subject),
                    work_policy(&subject),
                    demand,
                ),
                Err(EconomyError::NotRegistered(subject.clone()))
            );
            prop_assert_eq!(
                economy.gift(&registry, subject.clone(), Credits(amount)),
                Err(EconomyError::NotRegistered(subject.clone()))
            );
            prop_assert_eq!(
                economy.fund(&registry, subject.clone(), Credits(amount)),
                Err(EconomyError::NotRegistered(subject))
            );
        }

        #[test]
        fn ec_2_gift_and_fund_preserve_total(amount in 0_i128..30) {
            let (registry, agent_a, agent_b) = registered_fixture();
            let mut economy = Economy::new(DemurragePolicy {
                peg: FloorPlusDemandPeg { floor: 100, demand_multiplier: 0 },
                rate: 1,
            });
            economy
                .earn(
                    &registry,
                    agent_a.clone(),
                    admitted_work_env(&agent_a),
                    work_policy(&agent_a),
                    0,
                )
                .unwrap();

            let before_gift = economy.total_credits();
            economy.gift(&registry, agent_a.clone(), Credits(amount)).unwrap();
            prop_assert_eq!(economy.total_credits(), before_gift);

            let before_fund = economy.total_credits();
            economy.fund(&registry, agent_b.clone(), Credits(amount)).unwrap();
            prop_assert_eq!(economy.total_credits(), before_fund);
        }

        #[test]
        fn ec_3_demurrage_decay_is_monotone_and_floored(
            balance in 0_i128..1_000,
            rate in 0_u64..100,
            ticks_a in 0_u64..50,
            ticks_b in 0_u64..50
        ) {
            let policy = DemurragePolicy {
                peg: FloorPlusDemandPeg { floor: 0, demand_multiplier: 0 },
                rate,
            };
            let low_ticks = ticks_a.min(ticks_b);
            let high_ticks = ticks_a.max(ticks_b);
            let low = policy.decay(Credits(balance), low_ticks);
            let high = policy.decay(Credits(balance), high_ticks);

            prop_assert!(high <= low);
            prop_assert!(high.0 >= 0);
        }

        #[test]
        fn ec_4_mutual_credit_decay_is_identity(balance in -1_000_i128..1_000, ticks in 0_u64..100) {
            let policy = MutualCreditPolicy {
                peg: FloorPlusDemandPeg { floor: 0, demand_multiplier: 0 },
                credit_limit: 1_000,
            };

            prop_assert_eq!(policy.decay(Credits(balance), ticks), Credits(balance));
        }

        #[test]
        fn ec_5_peg_matches_formula_and_is_monotone(
            floor in 0_u64..1_000,
            multiplier in 0_u64..100,
            demand_a in 0_u64..100,
            demand_b in 0_u64..100,
            worker in subject_strategy()
        ) {
            let peg = FloorPlusDemandPeg { floor, demand_multiplier: multiplier };
            let low_demand = demand_a.min(demand_b);
            let high_demand = demand_a.max(demand_b);
            let low = WorkRecord { worker: worker.clone(), admitted: true, demand: low_demand };
            let high = WorkRecord { worker: worker.clone(), admitted: true, demand: high_demand };
            let denied = WorkRecord { worker, admitted: false, demand: high_demand };
            let expected = i128::from(floor.saturating_add(multiplier.saturating_mul(low_demand)));

            prop_assert_eq!(peg.reward(&low), Credits(expected));
            prop_assert!(peg.reward(&high) >= peg.reward(&low));
            prop_assert_eq!(peg.reward(&denied), Credits(0));
        }

        #[test]
        fn ec_6_frozen_subject_cannot_gift_or_receive_fund(amount in 1_i128..20) {
            let (registry, agent_a, agent_b) = registered_fixture();
            let mut economy = Economy::new(DemurragePolicy {
                peg: FloorPlusDemandPeg { floor: 50, demand_multiplier: 0 },
                rate: 1,
            });
            economy
                .earn(
                    &registry,
                    agent_a.clone(),
                    admitted_work_env(&agent_a),
                    work_policy(&agent_a),
                    0,
                )
                .unwrap();
            economy.gift(&registry, agent_a.clone(), Credits(amount)).unwrap();

            let balance_before = economy.balance(&agent_a);
            let pool_before = economy.pool();
            economy.freeze(agent_a.clone());
            prop_assert_eq!(
                economy.gift(&registry, agent_a.clone(), Credits(1)),
                Err(EconomyError::Frozen(agent_a.clone()))
            );
            prop_assert_eq!(economy.balance(&agent_a), balance_before);

            economy.freeze(agent_b.clone());
            prop_assert_eq!(
                economy.fund(&registry, agent_b.clone(), Credits(1)),
                Err(EconomyError::Frozen(agent_b))
            );
            prop_assert_eq!(economy.pool(), pool_before);
        }

        #[test]
        fn ec_7_gift_respects_policy_min_balance(
            starting in 0_i128..100,
            amount in 0_i128..150,
            credit_limit in 0_u64..100
        ) {
            let (registry, agent_a, _) = registered_fixture();
            let policy = MutualCreditPolicy {
                peg: FloorPlusDemandPeg { floor: starting as u64, demand_multiplier: 0 },
                credit_limit,
            };
            let mut economy = Economy::new(policy);
            economy
                .earn(
                    &registry,
                    agent_a.clone(),
                    admitted_work_env(&agent_a),
                    work_policy(&agent_a),
                    0,
                )
                .unwrap();

            let result = economy.gift(&registry, agent_a.clone(), Credits(amount));
            if starting - amount < -i128::from(credit_limit) {
                prop_assert_eq!(result, Err(EconomyError::InsufficientBalance));
                prop_assert!(economy.balance(&agent_a).0 >= -i128::from(credit_limit));
            } else {
                prop_assert_eq!(result, Ok(()));
                prop_assert!(economy.balance(&agent_a).0 >= -i128::from(credit_limit));
            }
        }

        #[test]
        fn ec_8_identical_operation_sequences_are_deterministic(
            demand in 0_u64..20,
            gift_amount in 0_i128..20,
            fund_amount in 0_i128..20,
            ticks in 0_u8..5
        ) {
            let (registry, agent_a, agent_b) = registered_fixture();
            let policy = DemurragePolicy {
                peg: FloorPlusDemandPeg { floor: 100, demand_multiplier: 3 },
                rate: 2,
            };
            let mut left = Economy::new(policy.clone());
            let mut right = Economy::new(policy);

            for economy in [&mut left, &mut right] {
                economy
                    .earn(
                        &registry,
                        agent_a.clone(),
                        admitted_work_env(&agent_a),
                        work_policy(&agent_a),
                        demand,
                    )
                    .unwrap();
                economy.gift(&registry, agent_a.clone(), Credits(gift_amount)).unwrap();
                economy.fund(&registry, agent_b.clone(), Credits(fund_amount.min(gift_amount))).unwrap();
                for _ in 0..ticks {
                    economy.tick();
                }
            }

            prop_assert_eq!(left, right);
        }
    }
}

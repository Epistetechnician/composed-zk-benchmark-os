//! Deterministic flywheel simulation over the shipped HSAI economy.
//!
//! Claim boundary: a simulation outcome is model behavior, not empirical evidence.
//! "Regenerative" is an operational threshold the experimenter sets (see doc 38);
//! this harness only reports numbers. No floats; metrics are integers scaled
//! per-mille. This crate modifies no existing crate; the pool-demurrage question
//! is studied by observing the `pool` series.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};

use hsai_agent_case::{
    ActionId, AgentCase, EvidenceLane, MemoryRoot, ModelId, OracleContract, Verdict,
};
use hsai_claim_envelope::{
    conjoin, AcceptancePolicy, ClaimEnvelope, LaneId, Maturity, Predicate, PropertyKind, SubjectId,
    TimeWindow, TrustRootClass,
};
use hsai_distinct_agent::{
    distinctness, Anchor, AnchorBundle, DistinctAgentLane, IdentityRegistry,
};
use hsai_economy::{
    Credits, DemurragePolicy, Economy, FloorPlusDemandPeg, MutualCreditPolicy, PoolPolicy,
};

// ---- deterministic PRNG (splitmix64) ----

pub fn next_u64(state: &mut u64) -> u64 {
    *state = state.wrapping_add(0x9E37_79B9_7F4A_7C15);
    let mut z = *state;
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// Decision with probability `p` in `0..=100`.
fn chance(state: &mut u64, p: u8) -> bool {
    (next_u64(state) % 100) < u64::from(p)
}

// ---- fixed-point metrics (per-mille, x1000) ----

/// Gini over balances, generalized to allow negatives by shifting so min == 0.
/// Returns per-mille in `0..=1000`. Empty or zero-total returns 0.
pub fn gini_permille(balances: &[i128]) -> u64 {
    let n = balances.len();
    if n == 0 {
        return 0;
    }
    let min = *balances.iter().min().expect("non-empty");
    let shifted: Vec<i128> = balances.iter().map(|b| b - min).collect();
    let total: i128 = shifted.iter().sum();
    if total == 0 {
        return 0;
    }
    let mut abs_diff_sum: i128 = 0;
    for &a in &shifted {
        for &b in &shifted {
            abs_diff_sum = abs_diff_sum.saturating_add((a - b).abs());
        }
    }
    let denom = 2i128 * n as i128 * total;
    ((abs_diff_sum.saturating_mul(1000)) / denom) as u64
}

/// Tick transfer volume over average supply, x1000. Non-positive supply returns 0.
pub fn velocity_permille(transfer_volume: i128, avg_supply: i128) -> u64 {
    if avg_supply <= 0 {
        0
    } else {
        let v = (transfer_volume.saturating_mul(1000)) / avg_supply;
        if v < 0 {
            0
        } else {
            v as u64
        }
    }
}

/// Fraction of agents with a positive balance, x1000.
pub fn active_permille(active: usize, agents: usize) -> u64 {
    if agents == 0 {
        0
    } else {
        (active as i128 * 1000 / agents as i128) as u64
    }
}

// ---- configuration and report ----

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum PolicyChoice {
    Demurrage { rate: u64 },
    MutualCredit { credit_limit: u64 },
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum FundingRule {
    None,
    Even,
    ProportionalToBalance,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct SimConfig {
    pub agents: usize,
    pub ticks: u64,
    pub seed: u64,
    pub floor: u64,
    pub demand_multiplier: u64,
    pub max_demand: u64,
    pub earn_prob: u8,
    pub gift_prob: u8,
    pub gift_percent: u8,
    pub policy: PolicyChoice,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct TickMetrics {
    pub tick: u64,
    pub total_supply: i128,
    pub pool: i128,
    pub gini_permille: u64,
    pub velocity_permille: u64,
    pub active_permille: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct SimReport {
    pub config: SimConfig,
    pub series: Vec<TickMetrics>,
    pub final_supply: i128,
    pub final_pool: i128,
    pub median_velocity: u64,
    pub terminal_gini: u64,
    pub total_minted: i128,
    pub total_decayed: i128,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct SweepCell {
    pub policy: PolicyChoice,
    pub rule: FundingRule,
    pub seed: u64,
    pub median_velocity: u64,
    pub terminal_gini: u64,
    pub final_pool: i128,
}

// ---- setup helpers (mirror the shipped crates' test fixtures) ----

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
        LaneId::Named("sim-work".to_owned()),
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

fn case_for(subject: &SubjectId) -> AgentCase {
    AgentCase {
        action: ActionId("sim-action".to_owned()),
        subject: subject.clone(),
        claimed_model: ModelId("sim-model".to_owned()),
        memory_root: MemoryRoot([0; 32]),
        observed_at: 0,
        oracle: OracleContract {
            expected: Verdict::Accept,
            target_guarantees: BTreeSet::from([distinctness(subject)]),
            excluded: BTreeSet::new(),
        },
    }
}

fn closed_distinct_env(case: &AgentCase, lane: &DistinctAgentLane) -> ClaimEnvelope {
    let distinct = lane.evaluate(case);
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
        LaneId::Named("sim-verified-anchor".to_owned()),
    );
    conjoin(distinct, verified)
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

fn register_population(agents: usize) -> (IdentityRegistry, Vec<SubjectId>) {
    let mut registry = IdentityRegistry::new();
    let mut subjects = Vec::with_capacity(agents);
    for i in 0..agents {
        let subject = SubjectId(format!("agent-{i}"));
        let anchor = Anchor::HardwareAttested {
            vendor: "sim".to_owned(),
            device: format!("dev-{i}"),
        };
        let lane = DistinctAgentLane::new(AnchorBundle(BTreeSet::from([anchor])));
        let case = case_for(&subject);
        registry
            .register(
                subject.clone(),
                closed_distinct_env(&case, &lane),
                distinct_policy(&subject),
            )
            .expect("distinct sim identity registers");
        subjects.push(subject);
    }
    (registry, subjects)
}

// ---- the runner ----

/// Run the configured flywheel and return a deterministic report.
pub fn run(config: SimConfig) -> SimReport {
    run_with_funding(config, FundingRule::Even)
}

pub fn run_with_funding(config: SimConfig, rule: FundingRule) -> SimReport {
    let peg = FloorPlusDemandPeg {
        floor: config.floor,
        demand_multiplier: config.demand_multiplier,
    };
    match config.policy {
        PolicyChoice::Demurrage { rate } => run_with(config, rule, DemurragePolicy { peg, rate }),
        PolicyChoice::MutualCredit { credit_limit } => {
            run_with(config, rule, MutualCreditPolicy { peg, credit_limit })
        }
    }
}

pub fn sweep(
    base: SimConfig,
    policies: &[PolicyChoice],
    rules: &[FundingRule],
    seeds: &[u64],
) -> Vec<SweepCell> {
    let mut cells = Vec::with_capacity(policies.len() * rules.len() * seeds.len());
    for &policy in policies {
        for &rule in rules {
            for &seed in seeds {
                let mut config = base;
                config.policy = policy;
                config.seed = seed;
                let report = run_with_funding(config, rule);
                cells.push(SweepCell {
                    policy,
                    rule,
                    seed,
                    median_velocity: report.median_velocity,
                    terminal_gini: report.terminal_gini,
                    final_pool: report.final_pool,
                });
            }
        }
    }
    cells
}

fn run_with<P: PoolPolicy>(config: SimConfig, rule: FundingRule, policy: P) -> SimReport {
    let (registry, subjects) = register_population(config.agents);
    let work: BTreeMap<SubjectId, (ClaimEnvelope, AcceptancePolicy)> = subjects
        .iter()
        .map(|s| (s.clone(), (admitted_work_env(s), work_policy(s))))
        .collect();

    let mut economy = Economy::new(policy);
    let mut state = config.seed;
    let mut total_minted: i128 = 0;
    let mut series: Vec<TickMetrics> = Vec::with_capacity(config.ticks as usize);

    for t in 0..config.ticks {
        let supply_start = economy.total_credits().0;
        let mut transfer_volume: i128 = 0;

        // 1. earn
        for s in &subjects {
            if chance(&mut state, config.earn_prob) {
                let demand = if config.max_demand == 0 {
                    0
                } else {
                    next_u64(&mut state) % config.max_demand
                };
                let entry = &work[s];
                if let Ok(c) = economy.earn(
                    &registry,
                    s.clone(),
                    entry.0.clone(),
                    entry.1.clone(),
                    demand,
                ) {
                    total_minted = total_minted.saturating_add(c.0);
                }
            }
        }

        // 2. gift to the pool
        for s in &subjects {
            if chance(&mut state, config.gift_prob) {
                let b = economy.balance(s).0;
                if b > 0 {
                    let amount = b * i128::from(config.gift_percent) / 100;
                    if amount > 0 && economy.gift(&registry, s.clone(), Credits(amount)).is_ok() {
                        transfer_volume = transfer_volume.saturating_add(amount);
                    }
                }
            }
        }

        // 3. the pool funds the commons back out
        transfer_volume =
            transfer_volume.saturating_add(fund_commons(rule, &mut economy, &registry, &subjects));

        // 4. demurrage decay (mutual credit is identity)
        economy.tick();

        // 5. record metrics
        let supply_end = economy.total_credits().0;
        let avg_supply = (supply_start + supply_end) / 2;
        let balances: Vec<i128> = subjects.iter().map(|s| economy.balance(s).0).collect();
        let active = balances.iter().filter(|b| **b > 0).count();
        series.push(TickMetrics {
            tick: t,
            total_supply: supply_end,
            pool: economy.pool().0,
            gini_permille: gini_permille(&balances),
            velocity_permille: velocity_permille(transfer_volume, avg_supply),
            active_permille: active_permille(active, config.agents),
        });
    }

    let final_supply = economy.total_credits().0;
    let final_pool = economy.pool().0;
    let terminal_gini = series.last().map(|m| m.gini_permille).unwrap_or(0);
    let median_velocity = median(series.iter().map(|m| m.velocity_permille).collect());

    SimReport {
        config,
        series,
        final_supply,
        final_pool,
        median_velocity,
        terminal_gini,
        total_minted,
        total_decayed: total_minted - final_supply,
    }
}

fn fund_commons<P: PoolPolicy>(
    rule: FundingRule,
    economy: &mut Economy<P>,
    registry: &IdentityRegistry,
    subjects: &[SubjectId],
) -> i128 {
    let pool0 = economy.pool().0;
    let balances: Vec<i128> = subjects.iter().map(|s| economy.balance(s).0).collect();

    match rule {
        FundingRule::None => 0,
        FundingRule::Even => {
            if subjects.is_empty() {
                return 0;
            }
            let share = pool0 / subjects.len() as i128;
            if share <= 0 {
                return 0;
            }
            let mut transfer_volume = 0_i128;
            for subject in subjects {
                if economy
                    .fund(registry, subject.clone(), Credits(share))
                    .is_ok()
                {
                    transfer_volume = transfer_volume.saturating_add(share);
                }
            }
            transfer_volume
        }
        FundingRule::ProportionalToBalance => {
            if pool0 <= 0 {
                return 0;
            }
            let total_pos: i128 = balances.iter().filter(|b| **b > 0).sum();
            if total_pos <= 0 {
                return 0;
            }
            let mut transfer_volume = 0_i128;
            for (subject, balance) in subjects.iter().zip(balances) {
                if balance <= 0 {
                    continue;
                }
                let amount = pool0.saturating_mul(balance) / total_pos;
                if amount > 0
                    && economy
                        .fund(registry, subject.clone(), Credits(amount))
                        .is_ok()
                {
                    transfer_volume = transfer_volume.saturating_add(amount);
                }
            }
            transfer_volume
        }
    }
}

fn median(mut values: Vec<u64>) -> u64 {
    if values.is_empty() {
        return 0;
    }
    values.sort_unstable();
    values[values.len() / 2]
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    fn base_config() -> SimConfig {
        SimConfig {
            agents: 8,
            ticks: 50,
            seed: 1,
            floor: 10,
            demand_multiplier: 2,
            max_demand: 5,
            earn_prob: 50,
            gift_prob: 30,
            gift_percent: 50,
            policy: PolicyChoice::Demurrage { rate: 5 },
        }
    }

    fn a5_grid_config(policy: PolicyChoice, seed: u64) -> SimConfig {
        SimConfig {
            agents: 20,
            ticks: 200,
            seed,
            floor: 10,
            demand_multiplier: 2,
            max_demand: 5,
            earn_prob: 50,
            gift_prob: 30,
            gift_percent: 50,
            policy,
        }
    }

    fn a5_policies() -> [PolicyChoice; 2] {
        [
            PolicyChoice::Demurrage { rate: 5 },
            PolicyChoice::MutualCredit { credit_limit: 1000 },
        ]
    }

    fn funding_rules() -> [FundingRule; 3] {
        [
            FundingRule::None,
            FundingRule::Even,
            FundingRule::ProportionalToBalance,
        ]
    }

    fn mean_active_permille(report: &SimReport) -> u64 {
        if report.series.is_empty() {
            return 0;
        }
        report.series.iter().map(|m| m.active_permille).sum::<u64>() / report.series.len() as u64
    }

    fn mean_terminal_gini(policy: PolicyChoice, rule: FundingRule) -> u64 {
        let mut total = 0_u64;
        for seed in [1_u64, 2, 3] {
            total += run_with_funding(a5_grid_config(policy, seed), rule).terminal_gini;
        }
        total / 3
    }

    #[test]
    fn s1_gini_of_equal_distribution_is_zero() {
        assert_eq!(gini_permille(&[10, 10, 10, 10]), 0);
    }

    #[test]
    fn s2_gini_of_single_holder_is_three_quarters() {
        assert_eq!(gini_permille(&[0, 0, 0, 40]), 750);
    }

    #[test]
    fn s3_velocity_is_volume_over_supply() {
        assert_eq!(velocity_permille(50, 100), 500);
    }

    #[test]
    fn s4_active_fraction() {
        assert_eq!(active_permille(3, 4), 750);
    }

    #[test]
    fn s5_run_is_deterministic() {
        let cfg = base_config();
        assert_eq!(run(cfg), run(cfg));
    }

    #[test]
    fn s6_demurrage_burns_idle_supply_mutual_credit_does_not() {
        // earn, but no gifting and no funding (gift_prob 0 keeps balances idle).
        let mut cfg = base_config();
        cfg.gift_prob = 0;

        cfg.policy = PolicyChoice::Demurrage { rate: 5 };
        let demurrage = run(cfg);
        assert!(demurrage.final_supply < demurrage.total_minted);
        assert!(demurrage.total_decayed > 0);

        cfg.policy = PolicyChoice::MutualCredit { credit_limit: 1000 };
        let mutual = run(cfg);
        assert_eq!(mutual.final_supply, mutual.total_minted);
        assert_eq!(mutual.total_decayed, 0);
    }

    #[test]
    fn a5_grid_matches_recorded_measurements() {
        let cases = [
            (
                PolicyChoice::Demurrage { rate: 5 },
                [
                    (1, 313, 366, 15, 8574, 28482, 19908, 990),
                    (2, 319, 319, 1, 7984, 27952, 19968, 997),
                    (3, 280, 374, 1, 7572, 27498, 19926, 992),
                ],
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                [
                    (1, 306, 363, 14, 28482, 28482, 0, 1000),
                    (2, 312, 319, 9, 27952, 27952, 0, 1000),
                    (3, 269, 367, 14, 27498, 27498, 0, 1000),
                ],
            ),
        ];

        for (policy, expected) in cases {
            for (
                seed,
                median_velocity,
                terminal_gini,
                final_pool,
                final_supply,
                total_minted,
                total_decayed,
                mean_active,
            ) in expected
            {
                let report = run(a5_grid_config(policy, seed));
                assert_eq!(report.median_velocity, median_velocity);
                assert_eq!(report.terminal_gini, terminal_gini);
                assert_eq!(report.final_pool, final_pool);
                assert_eq!(report.final_supply, final_supply);
                assert_eq!(report.total_minted, total_minted);
                assert_eq!(report.total_decayed, total_decayed);
                assert_eq!(mean_active_permille(&report), mean_active);
            }
        }
    }

    #[test]
    fn fs_1_run_is_even_funding_back_compat() {
        let mut configs = Vec::new();
        configs.push(base_config());
        for policy in a5_policies() {
            for seed in [1_u64, 2, 3] {
                configs.push(a5_grid_config(policy, seed));
            }
        }

        for config in configs {
            assert_eq!(run(config), run_with_funding(config, FundingRule::Even));
        }
    }

    #[test]
    fn fs_2_none_funding_accumulates_pool_and_decay_does_not_reduce_it() {
        let mut config = a5_grid_config(PolicyChoice::Demurrage { rate: 5 }, 1);
        config.earn_prob = 100;
        config.gift_prob = 100;
        config.gift_percent = 50;
        let report = run_with_funding(config, FundingRule::None);

        assert!(report.final_pool > 0);
        for window in report.series.windows(2) {
            assert!(window[1].pool >= window[0].pool);
        }
    }

    #[test]
    fn fs_3_proportional_funding_is_at_least_as_unequal_as_even() {
        for policy in a5_policies() {
            let even = mean_terminal_gini(policy, FundingRule::Even);
            let proportional = mean_terminal_gini(policy, FundingRule::ProportionalToBalance);
            assert!(proportional >= even);
        }
    }

    #[test]
    fn fs_4_run_with_funding_is_deterministic() {
        let config = a5_grid_config(PolicyChoice::MutualCredit { credit_limit: 1000 }, 3);
        for rule in funding_rules() {
            assert_eq!(
                run_with_funding(config, rule),
                run_with_funding(config, rule)
            );
        }
    }

    #[test]
    fn a5_funding_rule_sweep_matches_recorded_measurements() {
        let base = a5_grid_config(PolicyChoice::Demurrage { rate: 5 }, 1);
        let policies = a5_policies();
        let rules = funding_rules();
        let seeds = [1_u64, 2, 3];

        let expected = [
            (
                PolicyChoice::Demurrage { rate: 5 },
                FundingRule::None,
                1,
                10,
                568,
                11232,
            ),
            (
                PolicyChoice::Demurrage { rate: 5 },
                FundingRule::None,
                2,
                9,
                468,
                11025,
            ),
            (
                PolicyChoice::Demurrage { rate: 5 },
                FundingRule::None,
                3,
                9,
                514,
                10477,
            ),
            (
                PolicyChoice::Demurrage { rate: 5 },
                FundingRule::Even,
                1,
                313,
                366,
                15,
            ),
            (
                PolicyChoice::Demurrage { rate: 5 },
                FundingRule::Even,
                2,
                319,
                319,
                1,
            ),
            (
                PolicyChoice::Demurrage { rate: 5 },
                FundingRule::Even,
                3,
                280,
                374,
                1,
            ),
            (
                PolicyChoice::Demurrage { rate: 5 },
                FundingRule::ProportionalToBalance,
                1,
                266,
                882,
                4,
            ),
            (
                PolicyChoice::Demurrage { rate: 5 },
                FundingRule::ProportionalToBalance,
                2,
                223,
                864,
                9,
            ),
            (
                PolicyChoice::Demurrage { rate: 5 },
                FundingRule::ProportionalToBalance,
                3,
                230,
                756,
                12,
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                FundingRule::None,
                1,
                10,
                397,
                27417,
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                FundingRule::None,
                2,
                9,
                290,
                27327,
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                FundingRule::None,
                3,
                10,
                457,
                26564,
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                FundingRule::Even,
                1,
                306,
                363,
                14,
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                FundingRule::Even,
                2,
                312,
                319,
                9,
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                FundingRule::Even,
                3,
                269,
                367,
                14,
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                FundingRule::ProportionalToBalance,
                1,
                256,
                879,
                9,
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                FundingRule::ProportionalToBalance,
                2,
                222,
                857,
                11,
            ),
            (
                PolicyChoice::MutualCredit { credit_limit: 1000 },
                FundingRule::ProportionalToBalance,
                3,
                213,
                733,
                10,
            ),
        ];

        for (cell, expected) in sweep(base, &policies, &rules, &seeds)
            .into_iter()
            .zip(expected)
        {
            assert_eq!(cell.policy, expected.0);
            assert_eq!(cell.rule, expected.1);
            assert_eq!(cell.seed, expected.2);
            assert_eq!(cell.median_velocity, expected.3);
            assert_eq!(cell.terminal_gini, expected.4);
            assert_eq!(cell.final_pool, expected.5);
        }
    }

    fn policy_strategy() -> impl Strategy<Value = PolicyChoice> {
        prop_oneof![
            (0_u64..10).prop_map(|rate| PolicyChoice::Demurrage { rate }),
            (0_u64..2000).prop_map(|credit_limit| PolicyChoice::MutualCredit { credit_limit }),
        ]
    }

    fn rule_strategy() -> impl Strategy<Value = FundingRule> {
        prop_oneof![
            Just(FundingRule::None),
            Just(FundingRule::Even),
            Just(FundingRule::ProportionalToBalance),
        ]
    }

    fn config_strategy() -> impl Strategy<Value = SimConfig> {
        (
            1_usize..12,
            1_u64..60,
            any::<u64>(),
            0_u64..50,
            0_u64..5,
            0_u64..6,
            0_u8..=100,
            0_u8..=100,
            0_u8..=100,
            policy_strategy(),
        )
            .prop_map(
                |(
                    agents,
                    ticks,
                    seed,
                    floor,
                    demand_multiplier,
                    max_demand,
                    earn_prob,
                    gift_prob,
                    gift_percent,
                    policy,
                )| SimConfig {
                    agents,
                    ticks,
                    seed,
                    floor,
                    demand_multiplier,
                    max_demand,
                    earn_prob,
                    gift_prob,
                    gift_percent,
                    policy,
                },
            )
    }

    proptest! {
        #[test]
        fn sp_1_run_is_deterministic(cfg in config_strategy()) {
            prop_assert_eq!(run(cfg), run(cfg));
        }

        #[test]
        fn sp_2_gini_and_active_are_bounded(cfg in config_strategy()) {
            let report = run(cfg);
            for m in &report.series {
                prop_assert!(m.gini_permille <= 1000);
                prop_assert!(m.active_permille <= 1000);
            }
        }

        #[test]
        fn sp_3_velocity_is_non_negative_and_zero_without_transfers(cfg in config_strategy()) {
            let mut cfg = cfg;
            cfg.gift_prob = 0; // no gifts; with an empty pool, no funding either
            let report = run(cfg);
            for m in &report.series {
                // velocity_permille returns u64 (>= 0); with no transfers it must be 0.
                if m.pool == 0 {
                    prop_assert_eq!(m.velocity_permille, 0);
                }
            }
        }

        #[test]
        fn sp_4_transfers_preserve_total_supply(
            gift_percent in 0_u8..=100,
            fund_amount in 0_i128..200,
            demand in 0_u64..10
        ) {
            let (registry, subjects) = register_population(4);
            let peg = FloorPlusDemandPeg {
                floor: 100,
                demand_multiplier: 3,
            };
            let mut economy = Economy::new(DemurragePolicy { peg, rate: 1 });
            for subject in &subjects {
                let minted = economy
                    .earn(
                        &registry,
                        subject.clone(),
                        admitted_work_env(subject),
                        work_policy(subject),
                        demand,
                    )
                    .expect("registered worker can earn");
                prop_assert!(minted.0 > 0);
            }

            let supply_after_earn = economy.total_credits().0;
            for subject in &subjects {
                let balance = economy.balance(subject).0;
                let amount = balance * i128::from(gift_percent) / 100;
                if amount > 0 {
                    economy
                        .gift(&registry, subject.clone(), Credits(amount))
                        .expect("positive registered balance can gift");
                    prop_assert_eq!(economy.total_credits().0, supply_after_earn);
                }
            }

            for subject in &subjects {
                let before = economy.total_credits().0;
                let amount = fund_amount.min(economy.pool().0);
                if amount > 0 {
                    economy
                        .fund(&registry, subject.clone(), Credits(amount))
                        .expect("registered subject can be funded from pool");
                    prop_assert_eq!(economy.total_credits().0, before);
                }
            }

            let before_tick = economy.total_credits().0;
            economy.tick();
            prop_assert!(economy.total_credits().0 <= before_tick);
        }

        #[test]
        fn fsp_1_run_with_funding_is_deterministic(
            cfg in config_strategy(),
            rule in rule_strategy()
        ) {
            prop_assert_eq!(run_with_funding(cfg, rule), run_with_funding(cfg, rule));
        }

        #[test]
        fn fsp_2_funding_rules_preserve_total_supply(
            rule in rule_strategy(),
            gift_percent in 1_u8..=100,
            demand in 0_u64..10
        ) {
            let (registry, subjects) = register_population(4);
            let peg = FloorPlusDemandPeg {
                floor: 100,
                demand_multiplier: 3,
            };
            let mut economy = Economy::new(DemurragePolicy { peg, rate: 1 });
            for subject in &subjects {
                economy
                    .earn(
                        &registry,
                        subject.clone(),
                        admitted_work_env(subject),
                        work_policy(subject),
                        demand,
                    )
                    .expect("registered worker can earn");
            }

            let supply_after_earn = economy.total_credits().0;
            for subject in &subjects {
                let balance = economy.balance(subject).0;
                let amount = balance * i128::from(gift_percent) / 100;
                if amount > 0 {
                    economy
                        .gift(&registry, subject.clone(), Credits(amount))
                        .expect("positive registered balance can gift");
                    prop_assert_eq!(economy.total_credits().0, supply_after_earn);
                }
            }

            let before_funding = economy.total_credits().0;
            fund_commons(rule, &mut economy, &registry, &subjects);
            prop_assert_eq!(economy.total_credits().0, before_funding);

            let before_tick = economy.total_credits().0;
            economy.tick();
            prop_assert!(economy.total_credits().0 <= before_tick);
        }

        #[test]
        fn fsp_3_sweep_gini_is_bounded(
            mut base in config_strategy(),
            seed in any::<u64>()
        ) {
            base.agents = base.agents.min(6);
            base.ticks = base.ticks.min(20);
            let policies = a5_policies();
            let rules = funding_rules();
            let seeds = [seed, seed.wrapping_add(1)];
            for cell in sweep(base, &policies, &rules, &seeds) {
                prop_assert!(cell.terminal_gini <= 1000);
            }
        }
    }
}

# Economy Simulation — Implementation Spec

## Status And Claim Boundary

Level 1 design artifact for the next explicit phase: a new crate
`hsai-economy-sim` depending on the shipped HSAI crates. It is not source code. It
is a deterministic simulation harness that drives the existing economy forward and
measures whether the flywheel circulates and stays equitable, so ledger A5 can be
backed by a measured model result instead of a hypothesis.

Hard boundary: a simulation outcome is not an empirical economic result. It
characterizes the stipulated model — a fixed peg, fixed behavior probabilities, a
fixed funding rule — not the real world. "Regenerative" is operationalized as a
measurable criterion (below); the harness asserts neither that any configuration is
regenerative nor that the model reflects reality. This phase adds no protocol
capability and changes no existing crate.

## Purpose

Run a population of distinct, registered identities through earn -> gift -> fund ->
decay over many ticks, under each `PoolPolicy` variant, and report circulation
velocity, inequality, active fraction, and pool accumulation over time. Use it to
test the regenerative hypothesis and to expose the pool-demurrage question (credits
parked in the pool currently escape decay) by observation.

## Dependencies

Reuse, do not redefine: from `hsai-economy` — `Economy`, `PoolPolicy`,
`DemurragePolicy`, `MutualCreditPolicy`, `FloorPlusDemandPeg`, `Credits`. From
`hsai-distinct-agent` — `IdentityRegistry`, `DistinctAgentLane`, `Anchor`,
`AnchorBundle`, `distinctness`. From `hsai-agent-case` — `AgentCase`, `EvidenceLane`,
`OracleContract`, `Verdict`. From `hsai-claim-envelope` — `ClaimEnvelope`,
`AcceptancePolicy`, `conjoin`. No new economy methods; the sim only calls the
public API (`earn`, `gift`, `fund`, `tick`, `freeze`, `balance`, `pool`,
`total_credits`).

## Determinism

No real randomness or floats. Use an inline splitmix64 PRNG threaded through one
`u64` state, and fixed-point integer metrics scaled per-mille (x1000). Identical
`(config, seed)` yields a byte-identical `SimReport`.

```text
fn next_u64(state: &mut u64) -> u64 {
  *state = state.wrapping_add(0x9E37_79B9_7F4A_7C15);
  let mut z = *state;
  z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
  z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
  z ^ (z >> 31)
}
// a decision with probability p in 0..=100: (next_u64(state) % 100) < p
```

## Types

```text
enum PolicyChoice { Demurrage { rate: u64 }, MutualCredit { credit_limit: u64 } }

struct SimConfig {
  agents:            usize,
  ticks:             u64,
  seed:              u64,
  floor:             u64,   // peg floor
  demand_multiplier: u64,   // peg multiplier
  max_demand:        u64,   // demand drawn uniformly in 0..max_demand
  earn_prob:         u8,    // 0..=100, per agent per tick
  gift_prob:         u8,    // 0..=100
  gift_percent:      u8,    // 0..=100, fraction of positive balance gifted
  policy:            PolicyChoice,
}

struct TickMetrics {
  tick:              u64,
  total_supply:      i128,  // pool + sum(accounts)
  pool:              i128,
  gini_permille:     u64,   // inequality of balances, 0..=1000
  velocity_permille: u64,   // tick transfer volume / avg supply, x1000
  active_permille:   u64,   // agents with positive balance / agents, x1000
}

struct SimReport {
  config:   SimConfig,
  series:   Vec<TickMetrics>,   // one per tick
  // terminal summary
  final_supply:        i128,
  final_pool:          i128,
  median_velocity:     u64,     // median of series velocity_permille
  terminal_gini:       u64,
  total_minted:        i128,    // sum of all earn issuances
  total_decayed:       i128,    // total_minted + initial - final_supply (credits burned by demurrage)
}
```

`SimConfig` and `SimReport` derive `serde` so a run can be saved as JSON for
inspection.

## Metric Functions (pure, unit-tested)

```text
// Gini over balances, generalized to allow negatives by shifting so min == 0.
// Returns per-mille in 0..=1000. Empty or zero-total -> 0.
fn gini_permille(balances: &[i128]) -> u64 {
  let n = balances.len(); if n == 0 { return 0; }
  let min = balances.iter().min();
  let shifted: Vec<i128> = balances.map(|b| b - min);   // all >= 0
  let total: i128 = shifted.sum(); if total == 0 { return 0; }
  let abs_diff_sum: i128 = sum over i,j of |shifted[i] - shifted[j]|;  // full double sum
  // G = abs_diff_sum / (2 * n * total)
  ((abs_diff_sum * 1000) / (2 * n as i128 * total)) as u64
}

fn velocity_permille(transfer_volume: i128, avg_supply: i128) -> u64 {
  if avg_supply <= 0 { 0 } else { ((transfer_volume * 1000) / avg_supply) as u64 }
}

fn active_permille(active: usize, agents: usize) -> u64 {
  if agents == 0 { 0 } else { (active as i128 * 1000 / agents as i128) as u64 }
}
```

Use checked/saturating arithmetic; `abs_diff_sum` can grow, so accumulate in `i128`
and guard overflow.

## The Simulation Step

Setup: register `agents` distinct identities (one hardware anchor each, ids
`agent-0..`), build one admitted work envelope + matching `AcceptancePolicy` per
agent (guarantee `PolicyCompliance(agent)` at `Local`), and construct the `Economy`
from `config.policy`.

Per tick, in deterministic agent order, with one threaded PRNG state:

```text
transfer_volume = 0
// 1. earn
for agent: if rng%100 < earn_prob {
  demand = rng % max_demand;
  economy.earn(reg, agent, work_env[agent].clone(), policy[agent].clone(), demand);  // mints
}
// 2. gift to the pool
for agent: if rng%100 < gift_prob {
  let b = economy.balance(agent); if b > 0 {
    amount = b * gift_percent / 100;
    if economy.gift(reg, agent, amount).is_ok() { transfer_volume += amount; }
  }
}
// 3. pool funds the commons back out (the regenerative return)
let share = economy.pool() / agents;
if share > 0 { for agent: if economy.fund(reg, agent, share).is_ok() { transfer_volume += share; } }
// 4. demurrage decay
economy.tick();
// 5. record TickMetrics (supply before/after; avg_supply = (supply_start+supply_end)/2)
```

`total_minted` accumulates earn issuance; `total_decayed` is derived. The pool is
never decayed (the economy does not demur it) — the series `pool` column makes any
parking visible, which is the evidence for the pool-demurrage question.

## Regenerative Operational Criterion

State it; do not assert it. A configuration is called regenerative over a run iff
both hold: median per-tick `velocity_permille` >= a chosen `tau_v` (circulation does
not stall) AND `terminal_gini` <= a chosen `tau_g` (inequality does not run away).
The harness reports the numbers; the thresholds and the verdict belong to the
experimenter and are recorded in the assumption ledger (A5), under the claim
boundary that this is model behavior, not empirical reality.

## Claim Boundaries (hard statements)

- A simulation outcome is not an empirical economic result; it is model behavior.
- The peg, behavior probabilities, demand, and funding rule are stipulated inputs.
- Metrics are fixed-point integers to keep determinism; no floats.
- Gini over negative (mutual-credit) balances is shifted to non-negative; read it as
  spread, not classical wealth Gini.
- "Regenerative" is an operational threshold, not the philosophical claim.

## Invariants And Vectors

Pure-function vectors (exact):

```text
S1  gini_permille([10,10,10,10]) == 0
S2  gini_permille([0,0,0,40]) == 750         // n=4, one holds all -> (n-1)/n = 0.75
S3  velocity_permille(50, 100) == 500
S4  active_permille(3, 4) == 750
```

Simulation vectors / invariants:

```text
S5  determinism: run(config, seed) == run(config, seed) byte-for-byte
S6  decay difference: with earn>0, gift=0, fund share 0, and Demurrage{rate>0},
    final_supply < total_minted (idle supply burns); with MutualCredit, final_supply
    == total_minted (no decay)
```

Property tests:

```text
SP-1  determinism over random seeds/configs
SP-2  every gini_permille and active_permille in 0..=1000
SP-3  velocity_permille >= 0, and == 0 on any tick with no successful transfer
SP-4  within a tick, gift and fund do not change total_supply; only earn (mint) and
      economy.tick (demurrage burn) do
```

## Out Of Scope (later / separate)

Real economic data, calibration to reality, the trust-staked funding variant, a
pool-demurrage economy method (study by observation only), external rails, and any
change to existing crates. Do not resolve doc 22 open decisions.

## Implementation Phase Notes

- New crate `crates/hsai-economy-sim`, workspace member, path-depending on the four
  HSAI crates. Do not modify any existing crate.
- Dev-dependency `proptest`. Encode S1–S6 as unit tests and SP-1..4 as proptests.
- Deterministic: inline splitmix64, `BTreeMap`/`BTreeSet`, `i128`/`u64` integer math,
  no `HashMap`, no floats.
- Definition of done: `cargo test -p hsai-economy-sim` green, `cargo fmt --check`
  and `cargo clippy -p hsai-economy-sim --all-targets -- -D warnings` clean.
- After it builds, run a small grid (both policies, a few seeds) and record the
  measured velocity/Gini/pool behavior in the assumption ledger as an A5 update,
  under the simulation-is-not-reality claim boundary.

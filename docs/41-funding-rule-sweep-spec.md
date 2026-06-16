# Funding-Rule Sweep — Implementation Spec

## Status And Claim Boundary

Level 1 design artifact for the next explicit phase: a bounded, backward-compatible
extension of the shipped `hsai-economy-sim` crate. It is not source code. It exists
to answer one question the A5 simulation result left open: is the low inequality a
property of the currency, or of the egalitarian funding rule? The sweep varies the
funding rule while holding the currency and behavior fixed, so any change in
inequality is attributable to the funding rule.

Conclusions are model-level only. The funding rules are probes spanning the
equalization spectrum; `ProportionalToBalance` is a deliberately regressive bracket
to expose the upper end of inequality, not a proposed mechanism. A simulation
outcome is not empirical evidence.

## Authorized Extension (the only change to a shipped crate)

This phase may extend `hsai-economy-sim` with: a `FundingRule` enum, a
`run_with_funding(config, rule)` function, a `sweep(...)` helper, and the
`SweepCell` result type — and nothing else. It must keep `run(config)` behaving
exactly as today (`run(config) == run_with_funding(config, FundingRule::Even)`), so
the existing S1–S6, SP-1..4, and the A5 grid regression test continue to pass
unchanged. No other crate is touched.

## The Funding Rules

The simulation step is unchanged except step 3 (the pool funding the commons back
out), which now dispatches on the rule. Snapshot the pool balance and the agent
balances at the start of the funding step so the distribution is order-independent.

```text
enum FundingRule {
  None,                   // no redistribution; the pool accumulates
  Even,                   // share = pool / agents to every agent (current behavior)
  ProportionalToBalance,  // distribute the pool weighted by current positive balance
}
```

- `None`: skip funding entirely. The pool accumulates; for demurrage this exposes
  whether parked credits escape decay (the pool is never decayed).
- `Even`: `share = pool / agents`; fund each agent `share`. Maximally equalizing.
- `ProportionalToBalance`: let `pool0` and `bal_i` be the snapshots and
  `total_pos = sum(max(0, bal_i))`. If `total_pos > 0`, fund agent `i`
  `pool0 * max(0, bal_i) / total_pos`. Deliberately dis-equalizing (the commons
  pays you in proportion to what you already hold). Remainder stays in the pool.

`transfer_volume` accrues each successful `fund` exactly as today.

## API

```text
pub fn run_with_funding(config: SimConfig, rule: FundingRule) -> SimReport;
pub fn run(config: SimConfig) -> SimReport { run_with_funding(config, FundingRule::Even) }

struct SweepCell {
  policy:           PolicyChoice,
  rule:             FundingRule,
  seed:             u64,
  median_velocity:  u64,
  terminal_gini:    u64,
  final_pool:       i128,
}

pub fn sweep(base: SimConfig, policies: &[PolicyChoice], rules: &[FundingRule],
             seeds: &[u64]) -> Vec<SweepCell>;
// runs the full cross product, overriding base.policy and base.seed per cell
```

## Claim Boundaries (hard statements)

- Funding rules are probes across the equalization spectrum, not proposals;
  `ProportionalToBalance` is a regressive bracket.
- The sweep isolates funding-rule versus currency effect within the model, not in
  reality.
- `run` and all existing tests must be unchanged in behavior; the A5 grid numbers
  stay valid because they are the `Even` rule.
- A simulation outcome is model behavior, not empirical evidence.

## Invariants And Vectors

```text
FS-1  back-compat:  run(config) == run_with_funding(config, FundingRule::Even),
                    byte-for-byte, including the recorded A5 grid
FS-2  none-accumulates: under FundingRule::None with gift_prob > 0, final_pool > 0
                    and the pool is never reduced by decay (demurrage leaves it intact)
FS-3  ordering:     across the seed set, mean terminal_gini under
                    ProportionalToBalance >= mean terminal_gini under Even, for a
                    fixed currency (the dis-equalizer is at least as unequal)
FS-4  determinism:  run_with_funding(config, rule) is byte-deterministic
```

Property tests:

```text
FSP-1  determinism over random configs and rules
FSP-2  funding conserves supply: within a tick, gift and fund change no total; only
       earn (mint) and demurrage (burn) do, under every rule
FSP-3  every gini_permille in a sweep is in 0..=1000
```

## The Sweep To Run And Record

After the crate builds, run the cross product over both currencies
(`Demurrage{rate:5}`, `MutualCredit{credit_limit:1000}`), all three funding rules,
and seeds `{1,2,3}`, on the doc-38 base config (20 agents, 200 ticks, floor 10 +
2*demand, earn 50%, gift 30%, gift 50%). Append an A5 refinement to
`docs/research/assumption-ledger.md` reporting, per currency, the terminal-Gini
spread across funding rules versus across currencies, and stating which dominates.
If funding-rule spread dominates currency spread, the A5 caveat is confirmed: the
low inequality is driven by the funding rule, not the currency — and the honest A5
claim becomes "the flywheel circulates under the model; equity is a property of the
redistribution rule, not the currency."

## Out Of Scope

Reputation-weighted funding, real demand signals, pool demurrage as an economy
method, calibration to reality, and any change to crates other than the authorized
`hsai-economy-sim` extension. Do not resolve doc 22 open decisions.

## Implementation Phase Notes

- Extend `crates/hsai-economy-sim` only, per Authorized Extension. No new crate, no
  other crate touched.
- Deterministic: snapshot pool/balances before funding; `BTreeMap`/`BTreeSet`,
  integer math, no `HashMap`, no floats.
- Encode FS-1..4 as unit tests and FSP-1..3 as proptests; keep all existing tests
  green.
- Definition of done: `cargo test -p hsai-economy-sim` green (old + new),
  `cargo fmt --check` and `cargo clippy -p hsai-economy-sim --all-targets -- -D
  warnings` clean, sweep run and A5 refinement appended to the ledger.

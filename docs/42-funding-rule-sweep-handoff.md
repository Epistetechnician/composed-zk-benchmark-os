# Funding-Rule Sweep — Implementation Handoff

## Who This Is For

The engineering agent continuing the Hyper Sacred AI build. Seven crates are
shipped and verified, including `hsai-economy-sim` with a Rust-confirmed A5
simulation result. This phase extends that sim to settle the one caveat on A5: is
the low inequality the currency's doing, or the funding rule's? Extend one crate:
`hsai-economy-sim`. Build no new crate.

## Context In 60 Seconds

The A5 grid showed both currencies keep inequality low (Gini ~0.32–0.37). But the
sim used a single, maximally egalitarian funding rule (pool split evenly every
tick), so that low Gini could be the funding rule, not the currency. This phase
adds two more funding rules — `None` (no redistribution) and
`ProportionalToBalance` (regressive) — and sweeps currency x rule x seed, holding
everything else fixed, so any Gini change is attributable to the rule. If Gini
swings with the funding rule but not the currency, the caveat is confirmed and the
A5 claim gets honestly narrowed.

## Source Of Truth (read in this order)

- `docs/41-funding-rule-sweep-spec.md` — THE spec: the authorized extension, the
  three funding rules, the API, claim boundaries, invariants FS-1..4, the sweep to
  run.
- `crates/hsai-economy-sim/src/lib.rs` — the crate you extend; `run`, `SimConfig`,
  the funding step you generalize. Keep `run` behavior identical.
- `docs/research/assumption-ledger.md` A5 entries — the result you are refining.
- `AGENTS.md` — hard rules.

## The Task

Open a new explicit implementation phase and extend `crates/hsai-economy-sim` per
`docs/41`: add `FundingRule`, `run_with_funding`, `sweep`, and `SweepCell`; make
`run(config) == run_with_funding(config, FundingRule::Even)`. Then run the sweep
and append an A5 refinement to the ledger.

## The Boundary (read carefully)

- This is the ONLY permitted change set to a shipped crate: `FundingRule`,
  `run_with_funding`, `sweep`, `SweepCell`, and routing the funding step through
  the rule. Nothing else in `hsai-economy-sim` changes meaning.
- `run` must stay byte-for-byte equivalent to today (it is the `Even` rule). The
  existing S1–S6, SP-1..4, and the A5 grid regression test must pass unchanged.
  FS-1 asserts this equivalence — write it.
- Snapshot the pool and balances at the start of the funding step before
  distributing, so `ProportionalToBalance` is order-independent and deterministic.
- No floats; integer math; no `HashMap`. Do not touch any other crate.

## Build Plan

1. Toolchain: Rust 1.74.
2. Add `FundingRule { None, Even, ProportionalToBalance }`.
3. Refactor the funding step (step 3 of the tick loop) into a dispatch on the rule
   per `docs/41` §The Funding Rules, snapshotting pool/balances first.
4. Add `run_with_funding(config, rule)`; redefine `run(config)` to call it with
   `Even`.
5. Add `SweepCell` and `sweep(base, policies, rules, seeds)` running the cross
   product.
6. Tests: FS-1 (back-compat equivalence), FS-2 (None accumulates, pool not
   decayed), FS-3 (mean terminal Gini: ProportionalToBalance >= Even per currency),
   FS-4 (determinism); FSP-1..3 proptests. Keep all existing tests green.
7. Green: `cargo test -p hsai-economy-sim`, `cargo fmt --check`, `cargo clippy -p
   hsai-economy-sim --all-targets -- -D warnings`.
8. Run the sweep (both currencies x 3 rules x seeds 1–3 on the doc-38 base config)
   and capture terminal Gini and median velocity per cell.

## Definition Of Done

- `hsai-economy-sim` compiles on Rust 1.74; all prior tests still green; FS-1..4
  and FSP-1..3 added and green.
- FS-1 proves `run == run_with_funding(_, Even)`, so the recorded A5 grid is
  unchanged.
- The sweep is run; an A5 refinement is appended to
  `docs/research/assumption-ledger.md` reporting, per currency, terminal-Gini
  spread across funding rules versus across currencies, and which dominates.
- AGENTS.md phase note and a `docs/` phase note added.

## Correctness Pitfalls

- FS-1 is the safety net: if `run` changed behavior, the A5 numbers silently break.
  Implement `run` strictly as `run_with_funding(config, Even)` and assert equality.
- Snapshot before distributing under `ProportionalToBalance`; distributing off
  live balances as you fund makes the result order-dependent and non-deterministic.
- `None` must leave the pool untouched by funding AND uncrossed by decay (the
  economy never decays the pool) — FS-2 should observe pool growth.
- FS-3 is directional and can be noisy on tiny configs; average over the seed set
  and use the representative base config.
- Conservation (FSP-2) still holds under every rule: funding moves credits, it does
  not mint or burn.

## Out Of Scope

Reputation-weighted funding, real demand signals, pool-demurrage as an economy
method, calibration to reality, and any change to crates other than the authorized
`hsai-economy-sim` extension. Do not resolve doc 22 open decisions.

## After This Phase

With the funding-rule effect isolated, A5 is as sharp as a model can make it. The
remaining frontier is leaving the pure-data regime: the real attestation-verification
lane (TEE quote / ZK membership) that discharges the anchor-validity assumption.

## Paste-Ready Kickoff Prompt

> You are continuing the Hyper Sacred AI build in the `composed-zk-benchmark-os`
> repo. Seven crates are shipped, including `hsai-economy-sim` with a Rust-confirmed
> A5 result. Read `docs/42-funding-rule-sweep-handoff.md`, then
> `docs/41-funding-rule-sweep-spec.md`, then `crates/hsai-economy-sim/src/lib.rs`
> and `AGENTS.md`. Open a new explicit implementation phase and extend ONLY
> `crates/hsai-economy-sim` per doc 41: add `FundingRule { None, Even,
> ProportionalToBalance }`, route the funding step through the rule (snapshot pool
> and balances first so it is order-independent), add `run_with_funding(config,
> rule)` and redefine `run(config)` as `run_with_funding(config, Even)`, and add
> `SweepCell` + `sweep(base, policies, rules, seeds)`. Keep `run` byte-for-byte
> equivalent so S1–S6, SP-1..4, and the A5 grid regression test stay green; assert
> that equivalence as FS-1. No floats, integer math, touch no other crate. Add
> FS-1..4 unit tests and FSP-1..3 proptests. Then run the sweep (both currencies x
> the three rules x seeds 1–3 on the doc-38 base config) and append an A5 refinement
> to `docs/research/assumption-ledger.md` reporting, per currency, the terminal-Gini
> spread across funding rules versus across currencies and which dominates.
> Definition of done is in doc 42. Stop when `cargo test -p hsai-economy-sim` is
> green and report results, the sweep's Gini/velocity table, and any deviations from
> doc 41.

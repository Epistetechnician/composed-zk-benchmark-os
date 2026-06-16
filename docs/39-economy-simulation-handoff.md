# Economy Simulation — Implementation Handoff

## Who This Is For

The engineering agent continuing the Hyper Sacred AI build. Six crates are shipped
and verified (L0–L3 plus the L5 membrane). This phase does not add a protocol
primitive — it builds a deterministic simulation harness over the existing economy
to test whether the flywheel is regenerative. Build one crate: `hsai-economy-sim`.

## Context In 60 Seconds

The research loop flagged the regenerative claim (ledger A5) as plausible but
unproven. You now have the machinery — distinct identities, a gated economy, two
currency variants — to run the flywheel forward and measure it. This harness
registers a population, runs earn -> gift -> fund -> decay over many ticks under
each `PoolPolicy`, and reports circulation velocity, inequality (Gini), active
fraction, and pool accumulation. The point is a measured model result, honestly
bounded: a simulation characterizes the model, not reality.

## Source Of Truth (read in this order)

- `docs/38-economy-simulation-spec.md` — THE spec: PRNG, types, metric functions,
  the simulation step, the regenerative criterion, claim boundaries, vectors S1–S6,
  property tests SP-1..4.
- `crates/hsai-economy/src/lib.rs` — the economy API you drive (`earn`, `gift`,
  `fund`, `tick`, `balance`, `pool`, `total_credits`). Call it; do not change it.
- `crates/hsai-distinct-agent/src/lib.rs` and `crates/hsai-agent-case/src/lib.rs` —
  how to register identities and build admitted work envelopes (mirror the patterns
  in those crates' tests).
- `docs/research/assumption-ledger.md` A5 and `docs/22` §Economic Layer — why this
  exists. Background.
- `AGENTS.md` — hard rules.

## The Task

Open a new explicit implementation phase and build `crates/hsai-economy-sim` per
`docs/38`. Deliverable: a compiling, tested crate with the splitmix64 PRNG, the
fixed-point metric functions, `SimConfig`/`SimReport`, the `run` function, tests
reproducing S1–S6, and property tests SP-1..4. After it builds, run a small grid
and record results in the ledger (see below).

## The Honesty Boundary

- A simulation outcome is not empirical evidence. Every result is about the
  stipulated model — fixed peg, fixed behavior probabilities, fixed funding rule.
  Say so in the phase note and the ledger entry.
- "Regenerative" is an operational threshold on measured velocity and Gini, chosen
  by the experimenter — not the philosophical claim and not asserted by the harness.
- Metrics are fixed-point integers; no floats anywhere (float nondeterminism would
  break reproducibility).
- The harness does not pick a winning policy; it reports numbers for both.

## Hard Constraints (from AGENTS.md)

- New explicit phase; record it in AGENTS.md.
- New separate crate `crates/hsai-economy-sim`, workspace member, path-depending on
  the four HSAI crates. Do NOT modify any existing crate — the pool-demurrage
  question is studied by observing the `pool` series, not by adding an economy
  method.
- Deterministic and pure-data: inline splitmix64, `BTreeMap`/`BTreeSet`, integer
  math, no `HashMap`, no floats, no network, no real rails.

## Build Plan

1. Toolchain: the pinned Rust 1.74 already provisioned.
2. Scaffold `crates/hsai-economy-sim/`; add to workspace members; path-depend on the
   four HSAI crates; dev-dep `proptest`.
3. PRNG + metric functions (`gini_permille`, `velocity_permille`, `active_permille`)
   per `docs/38`; unit-test the metrics with S1–S4 first.
4. Types: `PolicyChoice`, `SimConfig`, `TickMetrics`, `SimReport` (serde-derived).
5. Setup helper: register `agents` distinct identities and build one admitted work
   envelope + `AcceptancePolicy` per agent (mirror `hsai-economy`/`hsai-distinct-agent`
   test fixtures).
6. `run(config) -> SimReport`: the earn -> gift -> fund -> decay step per `docs/38`,
   threading one PRNG state, recording `TickMetrics` each tick.
7. Tests: S5 (determinism), S6 (decay difference between policies); SP-1..4.
8. Green: `cargo test -p hsai-economy-sim`, `cargo fmt --check`,
   `cargo clippy -p hsai-economy-sim --all-targets -- -D warnings`.
9. Run a small grid (both policies, 2–3 seeds, e.g. 20 agents x 200 ticks) and
   capture velocity/Gini/pool.

## Definition Of Done

- Crate compiles on Rust 1.74; depends only on the four HSAI crates (+ serde,
  proptest dev-only).
- S1–S4: metric functions match exactly (`gini_permille([0,0,0,40]) == 750`, etc.).
- S5: identical `(config, seed)` produces a byte-identical `SimReport`.
- S6: demurrage burns idle supply (`final_supply < total_minted`); mutual credit
  does not (`final_supply == total_minted`).
- SP-1..4 hold as proptests.
- Phase note added to AGENTS.md and `docs/`.
- A grid run captured, and an A5 update appended to
  `docs/research/assumption-ledger.md` recording the measured model behavior under
  the simulation-is-not-reality claim boundary.

## Correctness Pitfalls

- No floats. Compute Gini and velocity as scaled integers; accumulate the Gini
  double-sum in `i128` and watch for overflow on large populations.
- Conservation (SP-4): `gift` and `fund` move credits and must not change
  `total_supply`; only `earn` (mint) and `economy.tick` (demurrage) change it. If a
  "conservation" assertion fails, you double-counted a transfer or mislabeled a mint.
- Thread ONE PRNG state through the whole run in a fixed agent order, or determinism
  (S5) breaks.
- Gini on mutual-credit balances: shift by the minimum so values are non-negative
  before computing; document it as spread.
- Do not add a pool-demurrage toggle. Observe the `pool` series instead; that data
  is the answer to whether parking escapes decay.

## Out Of Scope

Calibration to real data, the trust-staked funding variant, a pool-demurrage
economy method, external rails, and any change to existing crates. Do not resolve
doc 22 open decisions.

## After This Phase

With a measured A5 result in the ledger, the remaining major move is leaving the
pure-data regime: the real attestation-verification lane (TEE quote / ZK membership)
that discharges the anchor-validity assumption.

## Paste-Ready Kickoff Prompt

> You are continuing the Hyper Sacred AI build in the `composed-zk-benchmark-os`
> repo. Six crates are shipped (L0–L3 plus the L5 membrane). Read
> `docs/39-economy-simulation-handoff.md`, then `docs/38-economy-simulation-spec.md`,
> then `crates/hsai-economy/src/lib.rs`, `crates/hsai-distinct-agent/src/lib.rs`,
> and `AGENTS.md`. Open a new explicit implementation phase and build
> `crates/hsai-economy-sim` exactly per doc 38: an inline splitmix64 PRNG, the
> fixed-point metric functions `gini_permille`/`velocity_permille`/`active_permille`,
> `PolicyChoice`/`SimConfig`/`TickMetrics`/`SimReport`, and `run(config) -> SimReport`
> driving earn -> gift -> fund -> decay over the shipped economy. Reuse the shipped
> APIs; do not modify any existing crate (study the pool-demurrage question by
> observing the pool series, not by adding a method). No floats anywhere — metrics
> are integers scaled per-mille. Honesty: a simulation outcome is model behavior, not
> empirical evidence; "regenerative" is an operational threshold the experimenter
> sets, not a claim the harness makes. Encode S1–S6 as unit tests and SP-1..4 as
> proptests. Then run a small grid (both policies, a few seeds) and append a measured
> A5 update to `docs/research/assumption-ledger.md` under the simulation-is-not-reality
> claim boundary. Definition of done is in doc 39. Stop when `cargo test -p
> hsai-economy-sim` is green and report results, the grid's velocity/Gini/pool
> numbers, and any deviations from doc 38.

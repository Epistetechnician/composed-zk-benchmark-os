# Membrane — Implementation Handoff

## Who This Is For

The engineering agent continuing the Hyper Sacred AI build. Four crates are shipped
and verified: `hsai-claim-envelope`, `hsai-agent-case`, `hsai-distinct-agent`, and
`hsai-economy`. This is the next phase — the L5 membrane. Build one new crate
`hsai-membrane`, plus exactly two authorized methods on the existing `Economy`.

## Context In 60 Seconds

The economy is internal and stoppable: the corrigibility freeze can stop any
account. But the project also wants to adopt permeable external rails (x402,
stablecoins). The danger (ledger A11): a self-funding agent that can move value out
to public rails can buy compute elsewhere and defeat the starvation off-switch. The
membrane is the controlled boundary that prevents this — conversions are gated on
registration, blocked when frozen, and capped per window, with the cap tightening
as autonomy rises. This phase models that boundary in memory; it does not connect
to real rails.

## Source Of Truth (read in this order)

- `docs/35-membrane-spec.md` — THE spec: the authorized economy addition, the
  `AutonomyLevel` cap schedule, `Membrane` with `convert_out`/`convert_in`, claim
  boundaries, invariants M-1..8, vectors MB1–MB5.
- `crates/hsai-economy/src/lib.rs` — the economy you extend and depend on
  (`Economy`, `Credits`, `EconomyError`, `PoolPolicy`). Match it.
- `crates/hsai-distinct-agent/src/lib.rs` — `IdentityRegistry`, passed through.
- `docs/22-hyper-sacred-ai-architecture.md` §Economic Layer / membrane and ledger
  A8/A9/A11 — why this exists. Background.
- `AGENTS.md` — hard rules.

## The Task

Open a new explicit implementation phase. Build `crates/hsai-membrane` per
`docs/35`, and add the two authorized boundary methods to `hsai-economy`.
Deliverable: a compiling, tested membrane crate with the `AutonomyLevel` schedule,
the `Membrane` operations, and tests reproducing MB1–MB5 plus invariants M-1..8;
plus `debit_external`/`credit_external` on `Economy` with focused unit tests.

## The Off-Switch Honesty Boundary

- A frozen account must not be able to convert in either direction. This is the
  whole point: if freeze didn't block the membrane, the off-switch would be
  defeated. `convert_out` for a frozen subject returns `Economy(Frozen(..))` and
  changes nothing.
- The cap is finite at every autonomy level and tightens as autonomy rises (less
  oversight, less externalization). A fully `Autonomous` agent gets the smallest
  cap.
- The membrane alone is not the off-switch — it is one of the defense-in-depth
  layers (freeze, bounded permeability, hardware kill, fast slashing). Do not
  present it as the whole control.
- The 1:1 rate and the cap schedule are stubs; do not imply real-rail fidelity.

## Hard Constraints (from AGENTS.md)

- New explicit phase; record it in AGENTS.md.
- New separate crate `crates/hsai-membrane`, workspace member, path-depending on
  `hsai-economy`, `hsai-distinct-agent`, `hsai-claim-envelope`.
- The ONLY permitted change to a shipped crate is `Economy::debit_external` and
  `Economy::credit_external` (plus their focused tests), exactly as specified in
  `docs/35` §Authorized Economy Addition. Do not modify anything else in
  `hsai-economy` or any other existing crate.
- Pure data and ledger logic. No network, no real rails, no settlement. No
  `HashMap`, no floats; `u128`/`i128` with checked/saturating arithmetic.

## Build Plan

1. Toolchain: the pinned Rust 1.74 already provisioned.
2. Economy addition: add `debit_external` and `credit_external` to `Economy` per
   `docs/35`, with focused unit tests. `debit_external` removes credits from the
   system (not to the pool) and respects `min_balance`; both gate on registration
   and freeze and reject negative amounts.
3. Scaffold `crates/hsai-membrane/`; add to workspace members; path-depend on the
   three crates; dev-dep `proptest`.
4. Types: `ExternalAmount`, `AutonomyLevel` (+ `out_factor`), `Membrane`,
   `MembraneError` per `docs/35` §Types.
5. Operations: `cap_for`, `convert_out`, `convert_in`, `advance_window` per
   §Operations. Preserve the check order: cap before economy call; either failure
   leaves all state unchanged.
6. Tests: MB1–MB5 as unit tests; M-1..8 as proptests.
7. Green: `cargo test -p hsai-membrane`, `cargo test -p hsai-economy`,
   `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`.

## Definition Of Done

- `hsai-membrane` compiles on Rust 1.74; `hsai-economy` still green with the two
  new methods.
- MB1: convert out within cap debits the account, emits a 1:1 `ExternalAmount`, and
  decreases `total_credits`.
- MB2: over-cap returns `OverCap` with no state change.
- MB3: a frozen account cannot convert out; nothing changes (the off-switch).
- MB4: `advance_window` refreshes the cap.
- MB5: the same amount allowed at `Supervised` is rejected at `Autonomous` (tighter
  cap).
- M-1..8 hold as proptests. Phase note added to AGENTS.md and `docs/`.

## Correctness Pitfalls

- Check order: test the cap BEFORE calling the economy, and only consume the window
  counter AFTER a successful debit/credit. Over-cap and a frozen/unregistered/
  insufficient economy result must both leave membrane and economy untouched.
- `debit_external` must remove credits from the system (reduce `total_credits`), not
  move them to the pool — that is the difference from `gift`.
- Cap tightens with autonomy: `out_factor` is `Supervised=4, Bounded=2,
  Autonomous=1`. Do not invert it.
- `convert_in` raises permeability; gate and cap it just like `convert_out`.

## Out Of Scope (later phases)

Real x402/AP2 settlement, conversion rates/fees, the trust-staked funding variant,
the full L4 corrigibility gate beyond freeze, real attestation verification, and any
`hsai-economy` change beyond the two authorized methods. Do not resolve any item in
`docs/22` §Open Decisions; ship the reference cap schedule.

## After This Crate

With the membrane in place the lower stack (L0–L3) plus the L5 boundary is
complete in stub form. The remaining high-value moves are the peg/regenerative
simulation (ledger A5) over the two `PoolPolicy` variants, and — when you leave the
pure-data regime — the real attestation-verification lane.

## Paste-Ready Kickoff Prompt

> You are continuing the Hyper Sacred AI build in the `composed-zk-benchmark-os`
> repo. The crates `hsai-claim-envelope`, `hsai-agent-case`, `hsai-distinct-agent`,
> and `hsai-economy` are shipped. Read `docs/36-membrane-implementation-handoff.md`,
> then `docs/35-membrane-spec.md`, then `crates/hsai-economy/src/lib.rs` and
> `crates/hsai-distinct-agent/src/lib.rs` and `AGENTS.md`. Open a new explicit
> implementation phase. First, add exactly two methods to `hsai-economy`'s
> `Economy` — `debit_external` and `credit_external` per doc 35 §Authorized Economy
> Addition, with focused unit tests, and change nothing else in that crate. Then
> build `crates/hsai-membrane` exactly per doc 35: `ExternalAmount`, `AutonomyLevel`
> with `out_factor` (Supervised=4, Bounded=2, Autonomous=1), and `Membrane` with
> `convert_out`, `convert_in`, `cap_for`, `advance_window`. Honesty: a frozen
> account must not convert in either direction (the off-switch); the per-window cap
> is finite and tightens as autonomy rises; check the cap before calling the economy
> so failures leave all state unchanged; `debit_external` removes credits from the
> system, not to the pool. Encode MB1–MB5 as unit tests and M-1..8 as proptests.
> Definition of done is in doc 36. Stop when `cargo test -p hsai-membrane` and
> `cargo test -p hsai-economy` are green and report results and any deviations from
> doc 35.

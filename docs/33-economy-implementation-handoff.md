# L3 Economy Stub — Implementation Handoff

## Who This Is For

The engineering agent continuing the Hyper Sacred AI build. Three crates are
shipped and verified: `hsai-claim-envelope`, `hsai-agent-case`, and
`hsai-distinct-agent`. This is the next phase — the L3 economy. Build exactly one
crate: `hsai-economy`.

## Context In 60 Seconds

L2 gives you distinct, registered identities. L3 puts them in an economy: a
distinct identity earns credits for admitted work, credits decay (demurrage) or
clear (mutual credit), identities gift into a shared pool, and the pool funds other
distinct identities. The whole economy is gated on the L2 registry, so the Sybil
floor carries up: no registration, no account. A minimal freeze hook previews the
corrigibility off-switch. This is mechanics only — the peg is a stub and no
regenerative property is claimed.

## Source Of Truth (read in this order)

- `docs/32-economy-stub-spec.md` — THE spec: types, `PegPolicy`, `PoolPolicy` with
  `Demurrage` and `MutualCredit`, the `Economy` ledger, claim boundaries,
  invariants EC-1..8, vectors E1–E5.
- `crates/hsai-claim-envelope/src/lib.rs` and
  `crates/hsai-distinct-agent/src/lib.rs` — the APIs you depend on (`admits`,
  `AcceptancePolicy`, `Rejection`, `SubjectId`, `IdentityRegistry`). Match them.
- `docs/22-hyper-sacred-ai-architecture.md` §Economic Layer and ledger A5/A6 in
  `docs/research/assumption-ledger.md` — why the design is what it is. Background.
- `AGENTS.md` — hard rules.

## The Task

Open a new explicit implementation phase and build `crates/hsai-economy` per
`docs/32`. Deliverable: a compiling, tested crate with `Credits`, `WorkRecord`,
`FloorPlusDemandPeg`, the `PoolPolicy` trait with `DemurragePolicy` and
`MutualCreditPolicy`, the `Economy` ledger, and tests reproducing E1–E5 plus
invariants EC-1..8.

## The Honesty Boundary

- Earn is the only mint, and it requires BOTH a registered worker AND an admitted
  claim envelope (`admits` must pass). A credit is evidence that an oracle admitted
  work — nothing more. Do not mint for unregistered subjects or unadmitted work.
- The peg is a stub. Do not assert or imply that the flywheel is regenerative;
  that is for later simulation (ledger A5).
- `freeze` is a corrigibility preview, not the real off-switch. Do not dress it up
  as more.
- `demand` is an input parameter here, not a verified signal.

## Hard Constraints (from AGENTS.md)

- New explicit phase; record it in AGENTS.md as prior phases did.
- New separate crate `crates/hsai-economy`, workspace member, path-depending on
  `hsai-claim-envelope` and `hsai-distinct-agent`. Do NOT modify any existing crate.
- Pure data and ledger logic. No network, no real rails, no external settlement, no
  membrane (deferred), no real attestation. Deterministic; `BTreeMap`/`BTreeSet`,
  `i128` with checked/saturating arithmetic, no `HashMap`, no floats.

## Build Plan

1. Toolchain: the pinned Rust 1.74 already provisioned.
2. Scaffold `crates/hsai-economy/`; add to workspace members; path-depend on the
   two HSAI crates; dev-dep `proptest`.
3. Types: `Credits`, `WorkRecord`, `PegPolicy` + `FloorPlusDemandPeg`, `PoolPolicy`
   + `DemurragePolicy` + `MutualCreditPolicy` per `docs/32` §Types.
4. `Economy<P>` with `earn`, `gift`, `fund`, `tick`, `freeze`, `unfreeze`,
   `balance`, and `EconomyError`, gated on `&IdentityRegistry`, per §The Economy.
5. Tests: E1–E5 as unit tests; EC-1..8 as proptests. Build identities with a real
   `IdentityRegistry` from the L2 crate (register distinct anchors).
6. Green: `cargo test -p hsai-economy`, `cargo fmt --check`, `cargo clippy -p
   hsai-economy --all-targets -- -D warnings`.

## Definition Of Done

- Crate compiles on Rust 1.74; depends only on the two HSAI crates (+ serde as
  needed, proptest dev-only).
- E1: earn for an unregistered subject -> `NotRegistered`.
- E2: registered worker earns `floor + multiplier*demand`; gift then fund moves
  credits through the pool; `sum(accounts)+pool` is conserved across gift+fund.
- E3: demurrage decays a balance to zero over ticks; mutual credit does not decay.
- E4: a frozen account cannot gift; unfreezing restores it.
- E5: mutual credit may go negative within its credit limit; demurrage cannot
  (`InsufficientBalance`).
- EC-1..8 hold as proptests. Phase note added to AGENTS.md and `docs/`.

## Correctness Pitfalls

- Conservation (EC-2) is only about transfers (`gift`, `fund`). `earn` mints and
  `tick` (demurrage) burns by design — do not try to make total credits constant.
- Mutual credit's negative balances are intentional; gate them on
  `policy.min_balance()`, not on `>= 0`.
- The Sybil gate must apply to `earn`, `gift`, and `fund` — every operation that
  touches an account requires a registered subject.
- Use checked/saturating `i128` arithmetic; never overflow or use floats for
  credits.

## Out Of Scope (later phases)

The membrane and external-rail conversion (L5), the trust-staked funding variant
and mission-economy goal binding, the real demand signal, real attestation
verification, the full corrigibility gate (L4), and peg simulation. Do not resolve
any item in `docs/22` §Open Decisions; ship both currency variants.

## After This Crate

Next candidates: the membrane (L5 boundary — internal credits to gated external
conversion, the off-switch-preserving boundary), or economic simulation of the peg
over the two `PoolPolicy` variants to test the regenerative hypothesis (ledger A5).

## Paste-Ready Kickoff Prompt

> You are continuing the Hyper Sacred AI build in the `composed-zk-benchmark-os`
> repo. The crates `hsai-claim-envelope`, `hsai-agent-case`, and
> `hsai-distinct-agent` are shipped. Read
> `docs/33-economy-implementation-handoff.md`, then `docs/32-economy-stub-spec.md`,
> then `crates/hsai-claim-envelope/src/lib.rs` and
> `crates/hsai-distinct-agent/src/lib.rs` and `AGENTS.md`. Open a new explicit
> implementation phase and build `crates/hsai-economy` exactly per doc 32:
> `Credits`, `WorkRecord`, `FloorPlusDemandPeg`, the `PoolPolicy` trait with
> `DemurragePolicy` and `MutualCreditPolicy`, and the `Economy<P>` ledger with
> `earn`/`gift`/`fund`/`tick`/`freeze`/`unfreeze`/`balance`, all gated on the L2
> `IdentityRegistry`. Reuse the shipped types; do not modify any existing crate.
> Honesty: `earn` mints only for a registered worker AND an admitted claim envelope;
> the peg is a stub and no regenerative property is claimed; `freeze` is a
> corrigibility preview, not the real off-switch. Conservation applies to transfers
> only (earn mints, demurrage burns). Mutual credit may go negative within its
> credit limit. Encode E1–E5 as unit tests and EC-1..8 as proptests. Definition of
> done is in doc 33. Stop when `cargo test -p hsai-economy` is green and report
> results and any deviations from doc 32.

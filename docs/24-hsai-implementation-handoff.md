# Hyper Sacred AI — Implementation Handoff

## Who This Is For

Another engineering agent picking up the first build. This brief is self-contained
enough to start from, and points to the source-of-truth docs for full detail. Read
this top to bottom, then build exactly one thing: the `hsai-claim-envelope` crate.

## Context In 60 Seconds

Hyper Sacred AI is a protocol stack that lets autonomous agents transact and fund
one another on verifiable evidence rather than assumed trust, with an economy
designed for circulation over accumulation. The whole stack hangs off one type and
one operator — the claim envelope and its `conjoin` algebra — because that single
piece is what guarantees composition can never manufacture trust that wasn't in
the inputs. This benchmark OS repo is Layer 0 (semantic IR, oracles, evidence
lanes, claim-boundary discipline); Hyper Sacred AI is the superstructure built on
it. Your job is to implement the keystone and nothing else.

## Source Of Truth (read in this order)

- `docs/22-hyper-sacred-ai-architecture.md` — the full L0–L5 architecture, trust
  model, economy, corrigibility, and claim boundaries. Background; do not implement
  beyond the keystone.
- `docs/23-claim-envelope-implementation-spec.md` — THE spec you implement: types,
  the `conjoin` operator, acceptance policy, the four invariants, and test vectors
  V1–V4. This is your contract.
- `docs/research/autoresearch-loop.md` and `docs/research/assumption-ledger.md` —
  how the assumptions were backtested and why several were sharpened. Useful for
  understanding *why* the design is the way it is. Not required to build the crate.
- `AGENTS.md` — hard repo rules. Obey them.

## The Task

Open an explicit new implementation phase and build the claim-envelope crate per
`docs/23`. Deliverable: a compiling, tested `crates/hsai-claim-envelope` whose
tests assert the four invariants and reproduce test vectors V1–V4.

This promotes ledger assumption A7 ("meet-only composition prevents proof-theater")
from Pending to Level 1.

## Hard Constraints (from AGENTS.md)

- This is a new explicit phase. Record it as such; do not silently expand scope.
- New separate crate. Add `crates/hsai-claim-envelope` to workspace members. Do NOT
  put this code in `zkbench-core`; the two systems must not conflate.
- This crate is pure data and algebra. No network, no economy, no identity, no
  external rails, no agent runtime. Just the type, the operator, acceptance, tests.
- Deterministic. Use `BTreeSet` and canonical serialization so `provenance` hashes
  are reproducible, matching the repo's deterministic-artifact discipline.
- Claim-boundary discipline holds. A passing property test verifies the algebra's
  laws, not the truth of any claim an envelope carries. No fabricated results.
- Forbidden files per AGENTS.md still apply (no JS/TS, no Makefile, no CI files, no
  vendored external source).

## Build Plan

1. Toolchain. Install a Rust toolchain (stable, respecting `rust-version = 1.74`).
   The current sandbox had none; provision it.
2. Scaffold. Create `crates/hsai-claim-envelope/` with `Cargo.toml` and `src/lib.rs`.
   Add the crate to root `Cargo.toml` `members`. Mirror `zkbench-core`'s package
   style (`edition.workspace = true`, `rust-version.workspace = true`).
3. Dependencies. `serde` + `serde_json` for canonical serialization, `sha2` for
   provenance hashing (all already in the workspace). Dev-dependency: `proptest`
   for the invariants.
4. Types. Implement exactly the types in `docs/23` §Types: `Maturity` (ordered
   enum, meet = min), `TrustRoot`, `Predicate`, `TimeWindow`, `ClaimEnvelope`.
5. Operators. Implement `top()` and `conjoin()` from `docs/23` §Operators, and
   `AcceptancePolicy` + `admits()` from §Acceptance. The discharge step
   (`assumptions = (a.assumptions ∪ b.assumptions) \ guarantees`) and `min`
   maturity are the load-bearing lines.
6. Tests.
   - Encode V1–V4 from `docs/23` §Test Vectors as fixture-backed unit tests. V1 is
     the TEE-caps-ZK case and must reproduce exactly.
   - Encode INV-1..4 and LAW-1..3 from `docs/23` §The Four Invariants as proptests
     over randomized envelopes.
7. Green. `cargo test -p hsai-claim-envelope` passes. `cargo fmt` and `cargo clippy`
   clean.

## Definition Of Done

- `crates/hsai-claim-envelope` compiles on the pinned toolchain.
- V1–V4 reproduced exactly (V1 yields maturity `Attested`, closed assumptions,
  unioned trust roots, validity `[150,200]`).
- INV-1..4 and LAW-1..3 hold as proptests across randomized inputs.
- `admits()` rejects an envelope with an open assumption when `require_closed`
  (vector V2) and flags `HardwareVendor`-only composites as forbidden when policy
  says so.
- A one-paragraph phase note added to `AGENTS.md`'s allowed scope recording that
  the claim-envelope crate phase is now open, plus a short `docs/` note.

## Correctness Pitfalls (the subtle parts)

- Composition is NOT a pure meet across all fields. Guarantees *accumulate* by
  union; only the assurance fields (maturity, excludes, trust_roots, valid) take
  the meet. The honest statement: a guarantee is only ever as strong as the weakest
  link that established it. Do not "simplify" by making guarantees also shrink.
- Assumption discharge subtracts the *combined* guarantee set, which is what makes
  `conjoin` associative. Verify LAW-2 with a proptest; do not assume it.
- `min` maturity is the entire honesty mechanism: a `Proven` ZK claim conjoined
  with an `Attested` TEE claim must drop to `Attested`. If V1 yields `Proven`, the
  implementation is wrong.
- Empty validity window: represent a disjoint intersection as `start > end` and
  have `admits()` always fail the time check on it (vector V4).
- `require_closed` is the linchpin of anti-proof-theater: an envelope that
  guarantees a conclusion while still assuming its premise must be inadmissible
  until the premise is discharged (vector V2).
- Provenance must be order-independent in meaning but deterministic in bytes:
  canonicalize before hashing.

## Out Of Scope (do not build these now)

Identity / distinct-agent (L2), the economy and `PoolPolicy` (L3), the harness and
corrigibility gate (L4), interop / external rails / the membrane (L5), and any
evidence lane (TEE, ZK, stake). They consume the claim envelope but are later
phases. Building any of them now is scope violation.

## Open Decisions NOT To Resolve Here

These are recorded in `docs/22` §Open Decisions and must stay open; the keystone
does not depend on them: the demurrage/mutual-credit peg, the distinct-agent anchor
mix, the corrigibility composite, permeability targets, and which external rails to
adopt. Do not bake any of these into the claim-envelope crate.

## After This Crate (dependency order, for planning only)

1. `hsai-claim-envelope` (this task).
2. Agent-case adapter: extend the L0 case source so a live agent action becomes a
   case emitting envelopes.
3. `IdentityProvider` with one real `EvidenceLane` (distinct-agent), per `docs/22`
   L2 reference design (attested execution + ZK membership).
4. Stub `PoolPolicy` at Level 0 to exercise the economy interface.

## Paste-Ready Kickoff Prompt

> You are implementing the Hyper Sacred AI claim-envelope crate. Read
> `docs/24-hsai-implementation-handoff.md`, then `docs/23-claim-envelope-implementation-spec.md`,
> then `AGENTS.md`. Open a new explicit implementation phase and build
> `crates/hsai-claim-envelope` exactly per doc 23: the types, `top()`, `conjoin()`,
> `AcceptancePolicy`/`admits()`, with V1–V4 as fixture tests and INV-1..4 plus
> LAW-1..3 as proptests. Keep it pure data and algebra — no network, economy,
> identity, or rails. Do not touch `zkbench-core`. Definition of done is in doc 24.
> Stop when `cargo test -p hsai-claim-envelope` is green and report the results.

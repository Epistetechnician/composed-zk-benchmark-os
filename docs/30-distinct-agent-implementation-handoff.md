# Distinct-Agent Lane And Identity Registry — Implementation Handoff

## Who This Is For

The engineering agent continuing the Hyper Sacred AI build. Two crates are shipped
and verified: `hsai-claim-envelope` (the law-proven algebra) and `hsai-agent-case`
(cases + the evidence-lane interface). This is the next and most important phase —
the L2 distinct-agent floor. Build exactly one crate: `hsai-distinct-agent`.

## Context In 60 Seconds

The agent-case phase deliberately leaves `Distinctness(subject)` as an open target
no lane can establish. This phase fills it — honestly. A gift/credit economy among
agents dies to Sybil forks, so distinctness is the floor everything above depends
on. There is no purely cryptographic proof of it (ledger A4): distinctness must
bind to a non-copyable anchor — hardware, stake, or a sponsoring human. You build
the lane that emits a *conditional* distinctness claim and a registry that enforces
the real floor: one identity per anchor.

## Source Of Truth (read in this order)

- `docs/29-distinct-agent-lane-spec.md` — THE spec: the anchor model, the lane, the
  registry, claim boundaries, invariants DA-1..8, vectors D1–D4.
- `crates/hsai-claim-envelope/src/lib.rs` and `crates/hsai-agent-case/src/lib.rs` —
  the APIs you depend on and reuse. Match them; do not redefine.
- `docs/22-hyper-sacred-ai-architecture.md` §Identity And Sybil Resistance and
  ledger entries A4/A4b in `docs/research/assumption-ledger.md` — why the design is
  what it is. Background.
- `AGENTS.md` — hard rules.

## The Task

Open a new explicit implementation phase and build `crates/hsai-distinct-agent` per
`docs/29`. Deliverable: a compiling, tested crate with the `Anchor` model, the
`DistinctAgentLane` (an `EvidenceLane`), the minimal `IdentityRegistry`, and tests
reproducing D1–D4 plus invariants DA-1..8.

## The Honesty Boundary (read this twice)

This phase transcribes anchor evidence and enforces anchor uniqueness. It does NOT
verify any attestation, stake, or credential — that is a later, heavier phase
(real TEE quote checking / ZK membership). Consequences you must implement exactly:

- The lane's distinctness `guarantee` is paired with an OPEN anchor-validity
  `assumption` per anchor. The guarantee is conditional; the assumption is what a
  future verification lane discharges.
- Maturity caps at `Attested`. Never emit `Proven` — there is no verifying ZK proof
  in this phase, and even the reference design's ZK proof would be capped at
  `Attested` by the hardware binding it depends on.
- The lane adds the real `TrustRoot` for each anchor and nothing else. This is the
  first lane that emits real trust roots, so do not add roots an anchor did not
  earn.
- The registry requires an ADMITTED, CLOSED distinctness envelope. In tests, close
  it by conjoining a stand-in verification envelope (representing the future lane).
  The crate itself ships no fake verification lane.

## Hard Constraints (from AGENTS.md)

- New explicit phase; record it in AGENTS.md as prior phases did.
- New separate crate `crates/hsai-distinct-agent`, workspace member, path-depending
  on `hsai-claim-envelope` and `hsai-agent-case`. Do NOT modify any existing crate.
- Pure data, algebra, and a registry. No network, no real TEE, no real ZK, no
  economy, no harness. No `HashMap`; deterministic everywhere.
- Honesty over convenience: no `Proven`, no unearned trust roots, no closing the
  anchor-validity assumption inside the lane.

## Build Plan

1. Toolchain: the pinned Rust 1.74 already provisioned.
2. Scaffold `crates/hsai-distinct-agent/`; add to workspace members; path-depend on
   the two HSAI crates; dev-dep `proptest`.
3. Anchor model: `Anchor`, `AnchorBundle`, and the three mappings (trust root,
   validity assumption, ceiling) per `docs/29` §The Anchor Model.
4. `DistinctAgentLane` implementing `EvidenceLane` per §The Distinct-Agent Lane,
   including the empty-bundle honest case.
5. `IdentityRegistry` with `register`, `reward`, `slash`, and `RegisterError` per
   §The Identity Registry.
6. Tests: D1–D4 as unit tests; DA-1..8 as proptests. Provide a test-only
   `attestation_verified` helper to close assumptions for D3.
7. Green: `cargo test -p hsai-distinct-agent`, `cargo fmt --check`,
   `cargo clippy -p hsai-distinct-agent --all-targets -- -D warnings`.

## Definition Of Done

- Crate compiles on Rust 1.74; depends only on the two HSAI crates (+ serde/sha2 as
  needed, proptest dev-only).
- D1: one hardware anchor yields a conditional distinctness envelope (`Attested`,
  one open anchor-validity assumption, one `HardwareVendor` root), inadmissible
  under `require_closed`.
- D2: `conjoin(LocalMemoryLane, DistinctAgentLane)` yields guarantees
  `{MemoryIntegrity, Distinctness}`, the anchor-validity assumption still open,
  maturity `Local` (= min(Local, Attested)).
- D3: registering two identities sharing an anchor fails the second with
  `SybilAnchorReuse`.
- D4: an unverified (open-assumption) distinctness envelope cannot register under
  `require_closed`.
- DA-1..8 hold as proptests. Phase note added to AGENTS.md and `docs/`.

## Out Of Scope (later phases)

The real attestation-verification lane, the economy/`PoolPolicy` (L3), the harness
and corrigibility gate (L4), interop/membrane (L5), and the full trust graph (this
phase ships only the identity set + a reputation counter, not edges). Do not
resolve any item in `docs/22` §Open Decisions, including the anchor-mix question —
implement all three anchor kinds and leave the policy choice to the consumer.

## After This Crate

Next: the attestation-verification lane that discharges anchor-validity (real TEE
quote / ZK membership — a heavier phase), then the L3 economy stub that consumes
registered identities and reputation.

## Paste-Ready Kickoff Prompt

> You are continuing the Hyper Sacred AI build in the `composed-zk-benchmark-os`
> repo. The crates `hsai-claim-envelope` and `hsai-agent-case` are shipped. Read
> `docs/30-distinct-agent-implementation-handoff.md`, then
> `docs/29-distinct-agent-lane-spec.md`, then
> `crates/hsai-claim-envelope/src/lib.rs` and `crates/hsai-agent-case/src/lib.rs`
> and `AGENTS.md`. Open a new explicit implementation phase and build
> `crates/hsai-distinct-agent` exactly per doc 29: the `Anchor` model, the
> `DistinctAgentLane` (an `EvidenceLane`), and the minimal `IdentityRegistry`.
> Reuse the shipped types — do not redefine them or modify any existing crate.
> Honesty boundary: the lane emits a CONDITIONAL distinctness guarantee paired with
> an OPEN anchor-validity assumption per anchor, caps maturity at `Attested` (never
> `Proven`), and adds only each anchor's real trust root. The registry requires an
> admitted, closed distinctness envelope and rejects any anchor reuse with
> `SybilAnchorReuse`. Do not verify attestations — that is a later phase; in tests,
> close assumptions with a stand-in verification envelope. Encode D1–D4 as unit
> tests and DA-1..8 as proptests. Definition of done is in doc 30. Stop when
> `cargo test -p hsai-distinct-agent` is green and report results and any
> deviations from doc 29.

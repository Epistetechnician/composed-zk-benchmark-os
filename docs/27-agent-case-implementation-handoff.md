# Agent Case And Evidence Lane — Implementation Handoff

## Who This Is For

The engineering agent continuing the Hyper Sacred AI build. The keystone
(`hsai-claim-envelope`) is shipped and law-verified. This is the next phase: the
agent-case adapter and the evidence-lane interface. Read this, then build exactly
one crate: `hsai-agent-case`.

## Context In 60 Seconds

The claim envelope is the keystone every module emits and consumes. This phase
builds the layer that produces them from real input: a live agent action becomes
an `AgentCase` (a semantic, checkable form with an oracle contract), and an
`EvidenceLane` mints a `ClaimEnvelope` from that case. You also build two honest
reference lanes that prove the pattern without overclaiming. This is the
prerequisite for the distinct-agent lane and `IdentityProvider` in the phase after.

## Source Of Truth (read in this order)

- `docs/26-agent-case-evidence-lane-spec.md` — THE spec you implement: types,
  the `CaseSource` and `EvidenceLane` traits, the two reference lanes, invariants,
  and test vectors W1–W3.
- `docs/23-claim-envelope-implementation-spec.md` — the keystone API you depend on
  and reuse (do not redefine its types).
- `crates/hsai-claim-envelope/src/lib.rs` — the actual shipped API. Match it.
- `docs/22-hyper-sacred-ai-architecture.md` — background (L0 case source, L1
  evidence lanes). Do not implement beyond this phase.
- `AGENTS.md` — hard rules and the recorded phase scope.

## The Task

Open a new explicit implementation phase and build `crates/hsai-agent-case` per
`docs/26`. Deliverable: a compiling, tested crate with `AgentCase`, the two traits,
the `DeclaredLane` and `LocalMemoryLane` reference lanes, and tests that reproduce
W1–W3 and assert the lane and case invariants.

## Hard Constraints (from AGENTS.md)

- New explicit phase; record it in AGENTS.md as the claim-envelope phase was.
- New separate crate `crates/hsai-agent-case`, added to workspace `members`,
  depending on `hsai-claim-envelope` via a path dependency.
- Do NOT modify `zkbench-core` or `hsai-claim-envelope`. Reuse the keystone types;
  do not fork or redefine them.
- Interfaces and honest reference lanes ONLY. No real ZK, no TEE, no network, no
  identity store, no economy, no agent runtime.
- A reference lane must never overclaim: `DeclaredLane` establishes nothing
  (`Stub`, empty guarantees); `LocalMemoryLane` is `Local`, never `Proven`, and
  adds no trust roots.
- Deterministic: `BTreeSet`, canonical serialization, no `HashMap`. Forbidden
  files per AGENTS.md still apply.

## Build Plan

1. Toolchain. Use the pinned Rust 1.74 toolchain already provisioned for the
   keystone phase.
2. Scaffold `crates/hsai-agent-case/` (`Cargo.toml`, `src/lib.rs`); add to root
   `Cargo.toml` members; path-depend on `hsai-claim-envelope`. Dev-dep `proptest`.
3. Types: `ActionId`, `ModelId`, `MemoryRoot`, `Verdict`, `OracleContract`,
   `AgentCase` exactly per `docs/26` §Types.
4. Traits: `CaseSource` and `EvidenceLane` per §Traits, including `ceiling()`.
5. Reference lanes: `DeclaredLane` and `LocalMemoryLane` per §Reference Lanes.
6. Tests: W1–W3 as unit tests; LANE-1..4 and CASE-1 as proptests.
7. Green: `cargo test -p hsai-agent-case`, `cargo fmt --check`,
   `cargo clippy -p hsai-agent-case --all-targets -- -D warnings`.

## Definition Of Done

- `crates/hsai-agent-case` compiles on Rust 1.74, depends only on
  `hsai-claim-envelope` (+ `serde`/`sha2` as needed, `proptest` dev-only).
- W1: `DeclaredLane` yields empty guarantees, the targets as assumptions, `Stub`,
  and is inadmissible under `require_closed`.
- W2: `conjoin(DeclaredLane, LocalMemoryLane)` discharges `MemoryIntegrity`, leaves
  `Distinctness` open, maturity `Stub` (= min(Stub, Local)).
- W3 / CASE-1: lowering is byte-deterministic.
- LANE-1..4 hold as proptests across generated lanes/cases.
- Phase note added to AGENTS.md; short `docs/` phase note added.

## Correctness Pitfalls

- Honesty over convenience: it is tempting to have `LocalMemoryLane` emit `Proven`
  or `DeclaredLane` emit its targets as guarantees. Both are wrong. A declaration
  is an assumption, not a guarantee; a local check is `Local`, not `Proven`.
- The case's `excluded` set must propagate into every envelope a lane mints about
  that case (LANE-2). Do not drop it.
- `target_guarantees` are targets, not guarantees. `DeclaredLane` puts them in
  `assumptions` so they must be discharged by real lanes later. The whole point of
  W2 is that the interface leaves the `Distinctness` hole visible until the next
  phase fills it.
- Reuse the keystone's `Predicate`/`PropertyKind`/`SubjectId` so envelopes compose
  with `conjoin` directly. Do not introduce a parallel predicate type.
- Set `valid` honestly: stubs may use `TimeWindow::all()`; do not fabricate a
  freshness window a lane has not earned.

## Out Of Scope (next phases)

Real ZK memory lane, TEE provenance lane, distinct-agent lane, `IdentityProvider`
(L2), economy (L3), harness (L4), interop (L5). Building any now is scope
violation. Do not resolve any item in `docs/22` §Open Decisions.

## After This Crate

Next phase: the distinct-agent lane + `IdentityProvider` (L2), per `docs/22`
reference design (attested execution + ZK membership). It will consume
`AgentCase` and emit the `Distinctness` envelope that W2 deliberately leaves open.

## Paste-Ready Kickoff Prompt

> You are continuing the Hyper Sacred AI build in the `composed-zk-benchmark-os`
> repo. The keystone crate `hsai-claim-envelope` is shipped. Read
> `docs/27-agent-case-implementation-handoff.md`, then
> `docs/26-agent-case-evidence-lane-spec.md`, then
> `crates/hsai-claim-envelope/src/lib.rs` and `AGENTS.md`. Open a new explicit
> implementation phase and build `crates/hsai-agent-case` exactly per doc 26:
> `AgentCase`, `OracleContract`/`Verdict`, the `CaseSource` and `EvidenceLane`
> traits, and the `DeclaredLane` and `LocalMemoryLane` reference lanes. Reuse the
> shipped keystone types — do not redefine them or touch `zkbench-core` or
> `hsai-claim-envelope`. Reference lanes must not overclaim: `DeclaredLane`
> establishes nothing (Stub, empty guarantees, targets as assumptions);
> `LocalMemoryLane` is Local, never Proven, no trust roots. Encode W1–W3 as unit
> tests and LANE-1..4 plus CASE-1 as proptests. Definition of done is in doc 27.
> Stop when `cargo test -p hsai-agent-case` is green and report results and any
> deviations from doc 26.

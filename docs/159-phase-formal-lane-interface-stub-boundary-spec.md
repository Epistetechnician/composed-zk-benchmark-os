# Phase 159 — Formal Lane Interface Stub Boundary Spec

## Status

Allowed, not yet implemented.

## Purpose

`AGENTS.md`'s SOTA-wedge rule names "formal hooks" as a first-class
differentiator: *"The novelty is semantic benchmark generation with formal
hooks and adversarial mutation scoring."* `docs/03-sota-architecture.md`
names "formal lanes" as adapter targets producing scoped formal evidence,
and lists Levels 4 (formal property statement) and 5 (machine-checked scoped
proof) as their evidence ceiling.

There is **no Rust surface** for this today. The repository has
`AttestationVerifier` / `AttestationLane` in `hsai-attestation`, but no
`FormalLane` trait, no `FormalPropertyAssertion` type, no `FormalLaneProof`
envelope, and no attach point where a future formal backend (clean, zkLean,
Garden — all named in `docs/03`) could plug in.

This phase adds the inert interface stub. It mirrors the `AttestationVerifier`
pattern: a trait, a reference verifier that always returns "no proof
available", and a `FormalLane` that emits a `Level0DesignNote` claim envelope
asserting only that a formal property was *declared*, never that it was
*proven*. This creates the seam without claiming anything is proven.

## State Slice

This phase is limited to:

- A new module `crates/zkbench-core/src/formal/` with:
  - `FormalPropertyAssertion` struct
  - `FormalPropertyScope` enum
  - `FormalLaneProofStatus` enum (`DeclaredOnly`, `ProofAttempted`,
    `MachineCheckedScoped`, `IndependentlyReproduced`)
  - `FormalLaneProof` struct
  - `FormalLaneError` enum
  - `FormalVerifier` trait
  - `NoopFormalVerifier` reference struct
  - `FormalLane` struct
  - `FormalLaneOutcome` struct
- Module declaration and re-exports from `crates/zkbench-core/src/lib.rs`
  and `crates/zkbench-core/src/prelude.rs`.
- Additive integration tests under `crates/zkbench-core/tests/`.
- Phase notes under `docs/` and navigation updates under `README.md`,
  `docs/12-task-list.md`, `docs/90-whole-codebase-validation-report.md`, and
  `AGENTS.md`.

It does **not** permit:

- New Cargo dependencies, `Cargo.toml`, or `Cargo.lock` changes.
- Integration with any real formal tool (clean, zkLean, Garden, Coq, Lean,
  Rocq, F*, Dafny, etc.).
- Reading or writing any formal proof artifact file.
- A new crate, `hsai-formal`, or any change to any HSAI crate.
- Changes to `ClaimEnvelope` in `hsai-claim-envelope`, the `EvidenceLane`
  trait in `hsai-agent-case`, the `AttestationVerifier` trait in
  `hsai-attestation`, or any other existing trait.
- Changes to `ScoreReport`, `EvidenceRecord`, `EvidenceLedger`, accepted-ledger
  append, promotion preflight, official-submission package, external replay
  preflight, or any evidence classification.
- Changes to mutation, DSL, oracle, scoring (beyond the new formal module),
  pack, report bundle, audit index, local benchmark artifact, local artifact
  campaign, zk-Harness adapter.
- External execution, external repo clones, vendored source, network access,
  credentials, command-line tools, UI dashboards, browser apps, JavaScript or
  TypeScript runtime files, package runtime files, or committed generated
  benchmark artifact files.
- Level2+ evidence, accepted Evidence Ledger mutation, official benchmark
  submission, score-axis population, ZK backend performance claims, SOTA claims,
  broad leaderboard claims, production-readiness claims, semantic-correctness
  claims, proof claims, benchmark-evidence claims, or global software-agent
  uniqueness claims.

## Types

```rust
pub struct FormalPropertyAssertion {
    pub id: String,
    pub scope: FormalPropertyScope,
    pub statement: String,
    pub bound_machine_id: String,
    pub nonclaims: Vec<String>,
}

pub enum FormalPropertyScope {
    TransitionGuard { transition_id: String },
    Invariant { invariant_id: String },
    LoopBound { loop_id: String },
    Machine,
}

pub enum FormalLaneProofStatus {
    DeclaredOnly,
    ProofAttempted,
    MachineCheckedScoped,
    IndependentlyReproduced,
}

pub struct FormalLaneProof {
    pub assertion: FormalPropertyAssertion,
    pub status: FormalLaneProofStatus,
    pub claim_boundary: ClaimBoundary,
    pub notes: Vec<String>,
}

pub trait FormalVerifier {
    fn verify(&self, assertion: &FormalPropertyAssertion) -> Result<FormalLaneProof, FormalLaneError>;
}

pub struct NoopFormalVerifier;

pub struct FormalLane<V: FormalVerifier> {
    pub verifier: V,
}

pub struct FormalLaneOutcome {
    pub proof: FormalLaneProof,
    pub claim_boundary: ClaimBoundary,
    pub nonclaims: Vec<String>,
}
```

## NoopFormalVerifier Contract

`NoopFormalVerifier::verify(assertion)` always returns `Ok(FormalLaneProof {
assertion, status: DeclaredOnly, claim_boundary: Level0DesignNote, notes: [
"no formal proof was attempted", "a declared formal property is not a proof",
"this stub exists to establish the formal-lane seam only" ] })`.

It never returns `MachineCheckedScoped` or `IndependentlyReproduced`. It never
escalates above `Level0DesignNote`. This is the contract that distinguishes
"the seam exists" from "something is proven".

## FormalLane Contract

`FormalLane::evaluate(assertion)` calls `verifier.verify(assertion)` and
returns a `FormalLaneOutcome` carrying the proof, the claim boundary (always
`Level0DesignNote` under `NoopFormalVerifier`), and the mandatory nonclaims.
It does not emit a `ClaimEnvelope` directly — that would require coupling to
`hsai-claim-envelope`, which is out of scope. The outcome is a pure-data
record callers can inspect.

## Required Tests

- One test showing `NoopFormalVerifier::verify` returns `DeclaredOnly` and
  `Level0DesignNote` for any assertion.
- One test showing `NoopFormalVerifier` never returns `MachineCheckedScoped`
  or `IndependentlyReproduced`.
- One test showing `FormalLane::evaluate` produces a `FormalLaneOutcome` with
  the mandatory nonclaims present.
- One test showing the mandatory nonclaims include "a declared formal property
  is not a proof".
- One test showing `FormalLaneProofStatus` has exactly four variants (scope
  guard).
- One test showing `FormalPropertyScope` has exactly four variants (scope
  guard).
- One test asserting no integration with any external formal tool exists
  (source-scan test over the new module asserting absence of forbidden
  substrings like `coq`, `lean`, `rocq`, `dafny`, `fstar`, `garden`, `zklean`,
  `clean`, `process::Command`, network calls, or file I/O).

## Claim Boundary

Every `FormalLaneProof` produced by this phase carries
`ClaimBoundary::Level0DesignNote`. The phase introduces the formal-lane seam;
it does not produce a formal property statement (Level 4), a machine-checked
proof (Level 5), or independently reproduced evidence (Level 6). A
`DeclaredOnly` proof is not proof, not benchmark evidence, not accepted
evidence, not ZK backend performance evidence, not semantic correctness, not
global software-agent uniqueness, and not evidence that any formal tool was
run. The seam's only value is establishing the attach point for a future
implementation phase.

## Non-Goals

- Implementing real formal verification.
- Integrating with any named formal tool.
- Producing Level 4+ evidence.
- Coupling to `hsai-claim-envelope` or emitting `ClaimEnvelope` instances.
- Changing any existing trait, type, or crate outside the new module.
- Any external execution, network access, or credential use.

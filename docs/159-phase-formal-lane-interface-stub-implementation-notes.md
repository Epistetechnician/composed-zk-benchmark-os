# Phase 159 — Formal Lane Interface Stub Implementation Notes

## Status

Implemented and tested.

## Purpose

`AGENTS.md`'s SOTA-wedge rule names "formal hooks" as a first-class
differentiator. `docs/03-sota-architecture.md` names "formal lanes" as
adapter targets producing scoped formal evidence, and lists Levels 4 (formal
property statement) and 5 (machine-checked scoped proof) as their evidence
ceiling. There was no Rust surface for this. Phase 159 adds the inert
interface stub: a trait, a reference verifier that always returns "declared
only", and a `FormalLane` wrapper. This creates the seam without claiming
anything is proven.

## Surface

A new module `crates/zkbench-core/src/formal/mod.rs` adds:

- `FormalPropertyScope` (`TransitionGuard { transition_id }`, `Invariant
  { invariant_id }`, `LoopBound { loop_id }`, `Machine`).
- `FormalPropertyAssertion` carrying id, scope, statement, bound machine id,
  and mandatory nonclaims. Includes
  `FormalPropertyAssertion::mandatory_nonclaims()`.
- `FormalLaneProofStatus` (`DeclaredOnly`, `ProofAttempted`,
  `MachineCheckedScoped`, `IndependentlyReproduced`). Includes
  `claim_boundary(self) -> ClaimBoundary` mapping each status to its justified
  ceiling. The shipped `DeclaredOnly` and `ProofAttempted` statuses both cap
  at `Level0DesignNote`; the higher statuses are reserved for a future
  implementation phase that integrates with a real formal tool.
- `FormalLaneProof` carrying assertion, status, claim boundary, and notes.
- `FormalLaneError` (`MalformedAssertion { path, reason }`,
  `UnsupportedScope { reason }`).
- `FormalVerifier` trait with a single `verify(&self, assertion)` method
  returning `std::result::Result<FormalLaneProof, FormalLaneError>`. Mirrors
  the `AttestationVerifier` pattern from `hsai-attestation`.
- `NoopFormalVerifier` reference struct. Its `verify` always returns
  `DeclaredOnly` and `Level0DesignNote`, validates that the assertion id,
  statement, and bound machine id are non-empty, and attaches three mandatory
  notes: "No formal proof was attempted.", "A declared formal property is not
  a proof.", and "This stub exists to establish the formal-lane seam only."
- `FormalLane<V: FormalVerifier>` wrapping a verifier and exposing
  `evaluate(&self, assertion) -> crate::error::Result<FormalLaneOutcome>`.
- `FormalLaneOutcome` carrying proof, claim boundary, and mandatory nonclaims.
- `mandatory_lane_outcome_nonclaims()` returning the nonclaim language every
  outcome must carry.

The module is declared as `pub mod formal;` in `crates/zkbench-core/src/lib.rs`
and re-exported through `crates/zkbench-core/src/lib.rs` and
`crates/zkbench-core/src/prelude.rs`.

## Design Decisions

### Mirror `AttestationVerifier`

The `FormalVerifier` trait mirrors `hsai-attestation`'s `AttestationVerifier`:
a single `verify` method, a reference verifier, and a wrapping lane. This
keeps the formal-lane seam structurally consistent with the existing
attestation-lane seam, so a future implementation phase can compose them.

### Lane returns the crate `Result` alias; verifier returns its own error type

`FormalVerifier::verify` returns
`std::result::Result<FormalLaneProof, FormalLaneError>` so callers can
distinguish formal-lane failures (malformed assertion, unsupported scope)
from infrastructure failures. `FormalLane::evaluate` returns the crate
`Result<FormalLaneOutcome>` alias (i.e. `Result<_, ZkBenchError>`) and maps
`FormalLaneError` into `ZkBenchError::evidence_ledger` for callers that want
a single error channel.

### `NoopFormalVerifier` never escalates

The boundary spec requires that the shipped verifier never returns
`MachineCheckedScoped` or `IndependentlyReproduced`. The `claim_boundary`
mapping on `FormalLaneProofStatus` *does* map those variants to Level 5 and
Level 6 respectively, but only so a future implementation phase can reuse the
mapping. The shipped verifier never produces them, which is verified by a
dedicated test.

### No `ClaimEnvelope` emission

The lane returns a `FormalLaneOutcome` (pure data). It does not emit a
`ClaimEnvelope` directly. Coupling to `hsai-claim-envelope` is out of scope;
the outcome is a record callers can inspect. This keeps the formal-lane seam
inside `zkbench-core` without depending on any HSAI crate.

## Tests

`crates/zkbench-core/src/formal/mod.rs` carries inline unit tests for the
noop verifier's `DeclaredOnly` return, its refusal to escalate, malformed
input rejection, mandatory nonclaims, lane outcome structure, and scope-guard
variant counts.

`crates/zkbench-core/tests/phase_159_formal_lane.rs` carries 6 integration
tests:

- Noop verifier returns `DeclaredOnly` for every scope.
- Lane `evaluate` carries mandatory nonclaims.
- Noop verifier rejects malformed assertions via the lane.
- `DeclaredOnly` never escalates above `Level0DesignNote`.
- **Source-scan test** proving the formal module source contains no forbidden
  integrations (`use coq`, `extern crate lean`, `command::new`,
  `process::command`, `std::process`, `reqwest::`, `std::net::`,
  `std::fs::write`, `fs::write`, `tcplistener`, `tcpstream`, etc.). The scan
  matches real-code integration patterns, not doc mentions of tool names, to
  avoid false positives on words like "clean" or "lean".
- `FormalLaneError` is publicly exposed and constructible.

All 6 tests pass.

## Claim Boundary

Every `FormalLaneProof` produced by this phase carries
`ClaimBoundary::Level0DesignNote`. The phase introduces the formal-lane seam;
it does not produce a formal property statement (Level 4), a machine-checked
proof (Level 5), or independently reproduced evidence (Level 6). A
`DeclaredOnly` proof is not proof, not benchmark evidence, not accepted
evidence, not formal evidence, not ZK backend performance evidence, not
semantic correctness, not global software-agent uniqueness, and not evidence
that any formal tool was run. The seam's only value is establishing the
attach point for a future implementation phase.

## What This Does Not Do

- Does not integrate with any real formal tool (clean, zkLean, Garden, Coq,
  Lean, Rocq, F*, Dafny, etc.).
- Does not read or write any formal proof artifact file.
- Does not add a new crate, `hsai-formal`, or change any HSAI crate.
- Does not change `ClaimEnvelope`, the `EvidenceLane` trait,
  `AttestationVerifier`, `ScoreReport`, `EvidenceRecord`, `EvidenceLedger`,
  or any evidence classification.
- Does not produce Level 4+ evidence.
- Does not call any external tool, network, or credential.

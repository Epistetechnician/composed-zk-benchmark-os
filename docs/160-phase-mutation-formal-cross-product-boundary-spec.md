# Phase 160 — Mutation × Formal Cross-Product Mapping Boundary Spec

## Status

Allowed, not yet implemented.

## Purpose

The SOTA wedge — *"semantic benchmark generation with formal hooks and
adversarial mutation scoring"* — is only differentiated when the two halves
are connected. Phase 156 deepened the mutation surface; Phase 159 added the
formal-lane seam. Without Phase 160, those are two separate features. With
Phase 160, the framework can answer: *which formal property does each
mutation class stress-test?*

Only this framework owns both halves. No general ZK benchmark repo has a
14-class mutation taxonomy AND a formal-property seam. Producing the
cross-product mapping legitimately — by deriving each mapping from the
existing mutation class semantics and the existing formal property scope — is
the actual SOTA wedge.

This phase adds an inert mapping table: for each implemented `MutationClass`,
which `FormalPropertyScope` it most directly stress-tests, and a derived
`FormalPropertyAssertion` template. It is pure metadata derivation over
existing types.

## State Slice

This phase is limited to:

- Additive Rust source under `crates/zkbench-core/src/formal/` (the module
  introduced in Phase 159) adding:
  - `MutationFormalStressProfile` struct
  - `mutation_class_formal_stress(MutationClass) -> MutationFormalStressProfile`
  - `derive_formal_property_assertion_template(MutationClass, &SurfaceSpec)
     -> Option<FormalPropertyAssertion>`
- Re-exports from `crates/zkbench-core/src/formal/mod.rs`,
  `crates/zkbench-core/src/prelude.rs`, and `crates/zkbench-core/src/lib.rs`.
- Additive integration tests under `crates/zkbench-core/tests/`.
- Phase notes under `docs/` and navigation updates under `README.md`,
  `docs/12-task-list.md`, `docs/90-whole-codebase-validation-report.md`, and
  `AGENTS.md`.

It does **not** permit:

- Changes to `MutationClass`, `FormalPropertyAssertion`, `FormalPropertyScope`,
  `FormalLaneProof`, `FormalLaneProofStatus`, `FormalVerifier`,
  `NoopFormalVerifier`, `FormalLane`, or `FormalLaneOutcome`.
- Changes to any mutation pass, the DSL, the oracle, scoring (beyond the new
  formal-module additions), evidence ledgers, accepted-ledger append,
  promotion preflight, official-submission package, external replay preflight,
  pack readiness, report bundle, audit index, local benchmark artifact, local
  artifact campaign, zk-Harness adapter, or any HSAI crate.
- New Cargo dependencies, `Cargo.toml`, or `Cargo.lock` changes.
- Calling any real formal tool.
- External execution, external repo clones, vendored source, network access,
  credentials, command-line tools, UI dashboards, browser apps, JavaScript or
  TypeScript runtime files, package runtime files, or committed generated
  benchmark artifact files.
- Level2+ evidence, accepted Evidence Ledger mutation, official benchmark
  submission, score-axis population, ZK backend performance claims, SOTA claims,
  broad leaderboard claims, production-readiness claims, semantic-correctness
  claims, proof claims, benchmark-evidence claims, or global software-agent
  uniqueness claims.

## Mapping Contract

```rust
pub struct MutationFormalStressProfile {
    pub mutation_class: MutationClass,
    pub primary_formal_scope: FormalPropertyScopeKind,
    pub rationale: String,
    pub nonclaims: Vec<String>,
}

pub enum FormalPropertyScopeKind {
    TransitionGuard,
    Invariant,
    LoopBound,
    Machine,
    NotApplicable,
}
```

`mutation_class_formal_stress` returns a deterministic profile for each of
the 14 declared `MutationClass` variants. The mapping is grounded in each
class's semantics:

| MutationClass | Primary formal scope | Rationale |
| --- | --- | --- |
| `MissingConstraints` | `TransitionGuard` | Removing a guard stress-tests whether the formal model enforces it |
| `CorruptedGuards` | `TransitionGuard` | Inverting a guard tests transition-guard soundness |
| `BadCounters` | `TransitionGuard` | Counter drift tests whether guards over counters hold |
| `StaleStateReads` | `TransitionGuard` | Ordering violation tests transition sequencing |
| `InvalidUnrollBounds` | `LoopBound` | Bound corruption tests loop-bound soundness |
| `NondeterministicTransitionInjection` | `Machine` | Injected transitions test machine-level determinism |
| `RecursionEnvelopeMismatch` | `Machine` | Envelope mismatch tests recursion-envelope integrity |
| `PublicPrivateBoundaryMismatch` | `Machine` | Boundary violation tests witness partitioning |
| `WitnessAliasing` | `Machine` | Aliasing tests witness-disjointness properties |
| `InvariantWeakening` | `Invariant` | Weakening tests whether the invariant is actually enforced |
| `InvariantStrengthening` | `Invariant` | Strengthening tests invariant tightness |
| `ObservationOmission` | `Machine` | Omission tests public-output commitment |
| `SemanticNoOpDrift` | `TransitionGuard` | No-op drift tests action-effect soundness |
| `TraceOrderingCorruption` | `TransitionGuard` | Ordering corruption tests transition sequencing |

`NotApplicable` is reserved for future classes that have no formal analog;
none of the 14 use it today.

`derive_formal_property_assertion_template(mutation_class, surface)` returns
`Some(FormalPropertyAssertion)` when the surface contains a construct matching
the profile's primary scope, and `None` otherwise. The assertion's statement
is a deterministic template string; its nonclaims include the mandatory
"this template is not a proof" language.

## Required Tests

- One test showing `mutation_class_formal_stress` returns a profile for every
  one of the 14 declared `MutationClass` variants (no `NotApplicable` in the
  current mapping).
- One test showing the 8 implemented mutation classes map to the scopes
  documented in the table above.
- One test showing `derive_formal_property_assertion_template` returns
  `Some(...)` for `InvariantWeakening` on `BoundedCounterLoop` (which has an
  invariant).
- One test showing `derive_formal_property_assertion_template` returns `None`
  for `InvariantWeakening` on `BranchingFsm` (which has no invariant).
- One test showing the derived assertion always carries the "not a proof"
  nonclaim.
- One test showing the derived assertion always carries
  `ClaimBoundary::Level0DesignNote`.
- One test asserting the mapping is deterministic.
- One test asserting no new `MutationClass` or `FormalPropertyScope` variants
  were added (scope guard).

## Claim Boundary

Every `MutationFormalStressProfile` and derived `FormalPropertyAssertion`
template is local metadata only, capped at `Level0DesignNote`. The mapping is
not proof, not benchmark evidence, not accepted evidence, not formal evidence,
not ZK backend performance evidence, not semantic correctness, not global
software-agent uniqueness, and not evidence that any formal tool was run or
that any mutation would be detected by a real backend. The mapping's only
value is documenting which formal property each mutation class *would*
stress-test if a real formal lane were attached in a future phase.

## Non-Goals

- Implementing real formal verification.
- Calling any formal tool.
- Producing Level 4+ evidence.
- Changing any mutation class or formal type.
- Claiming that any mutation has been formally shown to do anything.
- Any external execution, network access, or credential use.

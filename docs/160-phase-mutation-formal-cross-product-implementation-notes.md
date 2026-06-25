# Phase 160 — Mutation × Formal Cross-Product Mapping Implementation Notes

## Status

Implemented and tested.

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

## Surface

`crates/zkbench-core/src/formal/cross_product.rs` adds:

- `FormalPropertyScopeKind` (`TransitionGuard`, `Invariant`, `LoopBound`,
  `Machine`, `NotApplicable`). A lightweight discriminator that carries only
  the scope *kind*, distinct from `FormalPropertyScope` which carries ids.
- `MutationFormalStressProfile` carrying mutation class, primary formal scope
  kind, rationale, and mandatory nonclaims.
- `mutation_class_formal_stress(MutationClass) -> MutationFormalStressProfile`
  returning a deterministic profile for each of the 14 declared
  `MutationClass` variants.
- `derive_formal_property_assertion_template(mutation_class, surface)
   -> Option<FormalPropertyAssertion>` returning `Some(template)` when the
  surface contains a construct matching the profile's primary scope, and
  `None` otherwise.
- `mandatory_cross_product_nonclaims()` returning the nonclaim language every
  profile and template must carry.
- `CROSS_PRODUCT_CLAIM_BOUNDARY` constant pinned at
  `ClaimBoundary::Level0DesignNote`.

The module is declared as `pub mod cross_product;` inside
`crates/zkbench-core/src/formal/mod.rs` and re-exported through
`crates/zkbench-core/src/formal/mod.rs`, `crates/zkbench-core/src/lib.rs`,
and `crates/zkbench-core/src/prelude.rs`.

## Mapping Table

The deterministic mapping from each `MutationClass` to its primary formal
scope kind, grounded in each class's semantics:

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

None of the 14 returns `NotApplicable` in the current mapping; that variant
is reserved for future mutation classes that have no formal analog.

## Design Decisions

### `FormalPropertyScopeKind` distinct from `FormalPropertyScope`

The mapping table needs to talk about scope *kinds* without binding to
specific ids. `FormalPropertyScope` (from Phase 159) carries ids
(`transition_id`, `invariant_id`, `loop_id`); `FormalPropertyScopeKind` does
not. The mapping returns a kind; the template derivation looks up the first
matching construct in the surface and only then binds to an id.

### Template derivation is conservative

`derive_formal_property_assertion_template` returns `Some(template)` only when
the surface contains a construct matching the profile's primary scope. For
`TransitionGuard`/`Invariant`/`LoopBound` this means the surface must have at
least one transition/invariant/loop respectively. For `Machine` the template
always derives. This makes the `None` return meaningful: it signals that the
mutation class's primary formal target is absent from this surface.

### Template statement is deterministic

The template's `statement` field is built from the lowercased mutation class
name, the scope kind, and the machine id. The `id` field is built from the
scope kind slug and the machine id. Both are deterministic, so the same
`(mutation_class, surface)` pair always produces the same template.

## Tests

`crates/zkbench-core/src/formal/cross_product.rs` carries inline unit tests
for profile coverage, scope mapping correctness, nonclaim presence, and
determinism.

`crates/zkbench-core/tests/phase_160_cross_product.rs` carries 12 integration
tests:

- Every mutation class has a non-`NotApplicable` profile.
- The 8 implemented mutation classes map to the scopes documented in the
  table above.
- Every profile carries a "not proof" nonclaim.
- `derive_formal_property_assertion_template` returns `Some` for
  `InvariantWeakening` on `BoundedCounterLoop` (which has an invariant).
- `derive_formal_property_assertion_template` returns `None` for
  `InvariantWeakening` on `BranchingFsm` (which has no invariant).
- `derive_formal_property_assertion_template` returns `Some` for
  `InvalidUnrollBounds` when a loop exists.
- Machine-scoped mutations always derive a template on any family.
- Derived templates carry the "not proof" nonclaim.
- Derived templates use the `Level0DesignNote` claim boundary convention.
- The mapping is deterministic across runs.
- `FormalPropertyAssertion` is publicly constructible.
- Scope-guard test asserting `MutationClass` (14) and `FormalPropertyScopeKind`
  (5) variant counts are unchanged.

All 12 tests pass.

## Claim Boundary

Every `MutationFormalStressProfile` and derived `FormalPropertyAssertion`
template is local metadata capped at `Level0DesignNote`. The mapping is not
proof, not benchmark evidence, not accepted evidence, not formal evidence,
not ZK backend performance evidence, not semantic correctness, not global
software-agent uniqueness, and not evidence that any formal tool was run or
that any mutation would be detected by a real backend. The mapping's only
value is documenting which formal property each mutation class *would*
stress-test if a real formal lane were attached in a future phase.

## What This Does Not Do

- Does not call any real formal tool.
- Does not produce Level 4+ evidence.
- Does not change any `MutationClass`, `FormalPropertyAssertion`,
  `FormalPropertyScope`, `FormalLaneProof`, `FormalLaneProofStatus`,
  `FormalVerifier`, `NoopFormalVerifier`, `FormalLane`, or `FormalLaneOutcome`.
- Does not change any mutation pass, the DSL, the oracle, scoring, evidence
  ledgers, or any HSAI crate.
- Does not claim that any mutation has been formally shown to do anything.

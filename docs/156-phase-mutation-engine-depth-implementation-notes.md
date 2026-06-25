# Phase 156 — Mutation Engine Depth Implementation Notes

## Status

Implemented.

## State Slice

- `crates/zkbench-core/src/mutation/invariant_weakening.rs` (new)
- `crates/zkbench-core/src/mutation/invariant_strengthening.rs` (new)
- `crates/zkbench-core/src/mutation/stale_state_reads.rs` (new)
- `crates/zkbench-core/src/mutation/invalid_unroll_bounds.rs` (new)
- `crates/zkbench-core/src/mutation/observation_omission.rs` (new)
- `crates/zkbench-core/src/mutation/apply.rs` (additive helpers only)
- `crates/zkbench-core/src/mutation/mod.rs` (new module declarations and re-exports)
- `crates/zkbench-core/src/prelude.rs` (extended re-exports)
- `crates/zkbench-core/src/lib.rs` (extended crate-root re-exports)
- `crates/zkbench-core/tests/phase_156_mutation_depth.rs` (new)

No Cargo metadata, dependency, DSL, oracle, scoring, evidence-ledger, accepted
append, promotion-preflight, official-submission, external-replay, zk-Harness
mapping, pack, report-bundle, audit-index, artifact, or campaign changes.

## What Was Implemented

Five new `MutationPass` impls, taking the runnable surface from 3 of 14
declared `MutationClass` variants to 8 of 14:

| Pass | Class | Target | Verdict | Safety |
| --- | --- | --- | --- | --- |
| `InvariantWeakeningPass` | `InvariantWeakening` | First non-trivial invariant guard → `Bool(true)` | `UnsoundIfAccepted` | `Malicious` |
| `InvariantStrengtheningPass` | `InvariantStrengthening` | First non-trivial invariant guard → `corrupt_guard` image | `Reject` | `NearValid` |
| `StaleStateReadsPass` | `StaleStateReads` | First two steps of an accepted trace where step one writes a field step two's guard reads; swap them | `Reject` | `Diagnostic` |
| `InvalidUnrollBoundsPass` | `InvalidUnrollBounds` | First executable `LoopSpec::bound`; wrap in logical `Not` | `Reject` | `NearValid` |
| `ObservationOmissionPass` | `ObservationOmission` | First `ObserveSpec`; remove it and inject a sentinel-mismatched `expected_final_fields` entry for its field | `Reject` | `Diagnostic` |

All five reuse the existing `finish_mutation` helper unchanged, so they
inherit `validate_surface_spec`, `lower_to_ir`, `MutationProvenance`,
deterministic id derivation, and `ClaimBoundary::Level1LocalReplay`
automatically.

## New Shared Helpers In `apply.rs`

To keep the new passes small and stylistically consistent with the existing
three, `apply.rs` gained five `pub(crate)` helpers:

- `select_primary_trace(instance) -> Option<TraceSpec>` — first accepted trace,
  else first rejected trace.
- `invariant_mut(surface, invariant_id) -> Result<&mut InvariantSpec>`.
- `loop_mut(surface, loop_id) -> Result<&mut LoopSpec>`.
- `guard_read_fields(guard) -> BTreeSet<String>` — wraps the existing
  `GuardSpec::collect_field_references`.
- `action_write_fields(action) -> BTreeSet<String>` — wraps the existing
  `ActionSpec::collect_field_references`.
- `guard_is_executable_expr(guard) -> bool` — true for `Expr(_)` that is not
  `RawText`.

The existing helpers (`transition`, `transition_mut`, `corrupt_guard`,
`guard_is_true`, `bad_counter_action`, `finish_mutation`, `lower_mutated_surface`)
are unchanged.

## Default Engine Composition — Deliberate Non-Change

The boundary spec originally proposed wiring all five new passes into
`apply_default_mutations`. During implementation this was changed.

`MutationEngine::apply` propagates the first `Err` returned by any configured
pass. The existing three passes (`MissingConstraintsPass`, `CorruptedGuardsPass`,
`BadCountersPass`) reliably find targets on `BoundedCounterLoop`, the canonical
family callers feed to the default engine. The five new passes do not have
this property uniformly: `BranchingFsm` has no invariants and no loops, so
`InvariantWeakeningPass` and `InvalidUnrollBoundsPass` would return `Err` and
abort the engine for any caller running the default engine on `BranchingFsm`.

Two options were considered:

- Change `MutationEngine::apply` to skip "no eligible target" errors but
  propagate real errors. Rejected as a behavioral change to existing callers.
- Add a separate lenient API. Rejected as unnecessary API surface.

The chosen resolution: **`apply_default_mutations` is unchanged**. The five
new passes are exported and individually runnable via `apply_mutation_pass`,
and composable via `MutationEngine::default().with_pass(...).apply(...)` when
the caller knows the family is eligible. This preserves the strict engine
contract without changing semantics for any existing caller.

The `custom_engine_with_new_passes_is_deterministic` test exercises this
composition on `BoundedCounterLoop`, which supplies eligible targets for all
four passes included in the test composition.

## Mutation Class Coverage After Phase 156

Implemented (8 of 14):

- `MissingConstraints` (Phase D/E)
- `CorruptedGuards` (Phase D/E)
- `BadCounters` (Phase D/E)
- `InvariantWeakening` (Phase 156)
- `InvariantStrengthening` (Phase 156)
- `StaleStateReads` (Phase 156)
- `InvalidUnrollBounds` (Phase 156)
- `ObservationOmission` (Phase 156)

Still inert (6 of 14), all explicit non-goals for this phase:

- `NondeterministicTransitionInjection`
- `RecursionEnvelopeMismatch`
- `PublicPrivateBoundaryMismatch`
- `WitnessAliasing`
- `SemanticNoOpDrift`
- `TraceOrderingCorruption`

## Tests

Eleven focused tests in `crates/zkbench-core/tests/phase_156_mutation_depth.rs`:

- One applies-test per new pass, asserting `mutation_class`, `expected_verdict`,
  `safety_class`, non-empty affected ids where applicable, and
  `ClaimBoundary::Level1LocalReplay`.
- One no-eligible-target test for each pass that has a clean non-applicable
  family (`BranchingFsm` for invariant/loop passes and `StaleStateReadsPass`;
  `ObservationOmissionPass` always applies because every shipped family
  declares at least one observation).
- One determinism test for a custom `MutationEngine` composition over four of
  the new passes on `BoundedCounterLoop`.
- One scope-guard test asserting `MutationClass` still has exactly 14
  variants with no duplicates.

## Claim Boundary

Every mutated instance produced by this phase carries
`ClaimBoundary::Level1LocalReplay`. A mutation pass applying successfully is
local regression evidence that the mutation is structurally detectable by the
shipped oracle; it is not proof, not benchmark evidence, not accepted evidence,
not formal evidence, not ZK backend performance evidence, not semantic
correctness, not global software-agent uniqueness, and not evidence that any
real backend would accept or reject the mutated instance.

## SOTA Wedge Position

Phase 156 advances the "adversarial mutation scoring" differentiator named in
`AGENTS.md`'s SOTA-wedge rule. It does not advance the "formal hooks"
differentiator; that remains for a future phase (see the Phase 159 placeholder
in the SOTA arc). The deeper mutation surface produces more data points that
Phase 157 (distinguishability scoring) will consume.

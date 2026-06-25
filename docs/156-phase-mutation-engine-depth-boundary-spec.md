# Phase 156 — Mutation Engine Depth Boundary Spec

## Status

Allowed, not yet implemented.

## Purpose

The repository's SOTA wedge (per `AGENTS.md`) is *"semantic benchmark
generation with formal hooks and adversarial mutation scoring."* Today the
mutation engine exposes **3 of 14** declared `MutationClass` variants as
runnable passes:

- `MissingConstraints` (`missing_constraints.rs`)
- `CorruptedGuards` (`corrupted_guards.rs`)
- `BadCounters` (`bad_counters.rs`)

The remaining **11** variants (`StaleStateReads`, `InvalidUnrollBounds`,
`NondeterministicTransitionInjection`, `RecursionEnvelopeMismatch`,
`PublicPrivateBoundaryMismatch`, `WitnessAliasing`, `InvariantWeakening`,
`InvariantStrengthening`, `ObservationOmission`, `SemanticNoOpDrift`,
`TraceOrderingCorruption`) are declared in `MutationClass` but produce no
`MutationPass` implementation. They are inert enum variants.

This phase widens the runnable mutation surface from 3 of 14 to 8 of 14 by
adding five passes, picked for leverage-to-effort ratio against the existing
DSL surface (`InvariantSpec`, `ObserveSpec`, `TransitionSpec`, `LoopSpec`,
field-order-sensitive traces):

- `InvariantWeakening`
- `InvariantStrengthening`
- `StaleStateReads`
- `InvalidUnrollBounds`
- `ObservationOmission`

The other six classes (`NondeterministicTransitionInjection`,
`RecursionEnvelopeMismatch`, `PublicPrivateBoundaryMismatch`,
`WitnessAliasing`, `SemanticNoOpDrift`, `TraceOrderingCorruption`) remain
inert and are explicit non-goals for this phase.

## State Slice

This phase is limited to:

- Additive Rust source under `crates/zkbench-core/src/mutation/` implementing
  five new `MutationPass` impls.
- Re-exports from `crates/zkbench-core/src/mutation/mod.rs` and
  `crates/zkbench-core/src/prelude.rs` mirroring the existing pass exports.
- Reusable pass exports and focused custom-engine tests; `apply_default_mutations`
  remains unchanged so the strict default-engine eligibility contract is
  preserved.
- Additive integration tests under `crates/zkbench-core/tests/`.
- Phase notes under `docs/` and navigation updates under `README.md`,
  `docs/12-task-list.md`, `docs/90-whole-codebase-validation-report.md`, and
  `AGENTS.md`.

It does **not** permit:

- New `MutationClass` variants, new `MutationKind` variants, new
  `MutationSafetyClass` variants, or changes to `ExpectedVerdict`.
- Changes to the `MutationPass` trait shape or `MutationBuild` shape.
- Changes to the DSL (`SurfaceSpec`, `SemanticIr`, `GuardExpr`, `ActionSpec`)
  or to the local oracle (`crate::dsl::oracle`).
- Changes to scoring, evidence ledgers, accepted-ledger append, or
  promotion preflight.
- Changes to `zk_harness` adapter mapping beyond keeping the existing
  `candidate_mutation_label` `None` behaviour for the new classes (already
  covered by the existing future-class branch in `mapping.rs`).
- New Cargo dependencies, `Cargo.toml`, or `Cargo.lock` changes.
- External execution, external repo clones, vendored source, network access,
  credentials, command-line tools, UI dashboards, browser apps, JavaScript or
  TypeScript runtime files, package runtime files, or committed generated
  benchmark artifact files.
- Level2+ evidence, formal evidence, accepted Evidence Ledger mutation,
  official benchmark submission, score-axis population, ZK backend performance
  claims, SOTA claims, broad leaderboard claims, production-readiness claims,
  semantic-correctness claims, proof claims, benchmark-evidence claims, or
  global software-agent uniqueness claims.

## Pass-Specific Contracts

Each pass is a deterministic struct implementing `MutationPass`, selecting
the first eligible target by a stable ordering, cloning the source
`SurfaceSpec`, mutating exactly one structurally identifiable site, and
finishing through the existing `finish_mutation` helper so that
`validate_surface_spec`, `lower_to_ir`, provenance, claim boundary, and
deterministic id derivation are reused unchanged.

### `InvariantWeakeningPass` — `MutationClass::InvariantWeakening`

- Selects the first invariant (by `MachineSpec::invariants` order) on the
  source instance whose `GuardSpec` is a non-trivial executable expression
  (`Expr(_)`, not `Bool(true)`).
- Replaces that invariant's guard with `GuardSpec::Bool(true)` (the weakest
  possible invariant).
- `expected_verdict = ExpectedVerdict::UnsoundIfAccepted`.
- `safety_class = MutationSafetyClass::Malicious`.
- `affected_guard_ids` records `"<invariant_id>.guard"`.
- Source trace is the first `accepted_traces` entry if any, otherwise the
  first `rejected_traces` entry, so the mutated machine is always exercised
  against a real declared trace.
- Nonclaim note: *weakening an invariant and observing a backend accept
  an originally rejected trace is an unsound acceptance candidate, not proof
  of exploit*.

### `InvariantStrengtheningPass` — `MutationClass::InvariantStrengthening`

- Selects the first invariant whose guard is a non-trivial executable
  expression.
- Replaces that invariant's guard with its `corrupt_guard` image (logical
  negation via the existing helper, used here to produce a guard that is
  stronger-than-or-incompatible-with the original semantics).
- `expected_verdict = ExpectedVerdict::Reject`.
- `safety_class = MutationSafetyClass::NearValid`.
- Source trace selection mirrors `InvariantWeakeningPass`.
- Nonclaim note: *strengthening an invariant beyond valid semantics produces
  a near-valid rejection candidate, not a soundness finding*.

### `StaleStateReadsPass` — `MutationClass::StaleStateReads`

- Targets an accepted trace with at least two steps where the first step's
  transition writes a field (`Assign`, `AddAssign`, `SubAssign`) that the
  second step's transition reads in a guard.
- Mutates the **trace** (not the machine) by swapping the two steps so the
  read happens before the write — i.e. it reads stale state.
- The mutated `SurfaceSpec` is the source spec with the trace's steps
  reordered; the machine itself is unchanged.
- `expected_verdict = ExpectedVerdict::Reject`.
- `safety_class = MutationSafetyClass::Diagnostic`.
- `affected_transition_ids` records both involved transitions.
- Nonclaim note: *a stale-state-read rejection is a local oracle observation,
  not proof that any backend is unsound*.

### `InvalidUnrollBoundsPass` — `MutationClass::InvalidUnrollBounds`

- Selects the first `LoopSpec` whose `bound` is a non-trivial executable
  `GuardSpec` and whose `body` is non-empty.
- Replaces the loop bound with a guard derived from the original but made
  unsatisfiable (`GuardSpec::Expr(GuardExpr::Not { not: Box::new(original) })`
  when the original is executable, otherwise `GuardSpec::Bool(false)`).
- `expected_verdict = ExpectedVerdict::Reject`.
- `safety_class = MutationSafetyClass::NearValid`.
- `affected_guard_ids` records `"<loop_id>.bound"`.
- Source trace selection mirrors the other passes.
- Nonclaim note: *an invalid unroll bound produces a near-valid rejection
  candidate and does not establish that any backend mishandles loops*.

### `ObservationOmissionPass` — `MutationClass::ObservationOmission`

- Selects the first non-empty `ObserveSpec` on the source machine.
- Produces a mutated `SurfaceSpec` in which that observation is removed.
- Adds a trace-level `expected_final_fields` check that the observed field is
  still present and unchanged in the trace's final state, so the local oracle
  has something concrete to evaluate; the omitted observation is captured in
  provenance notes only.
- `expected_verdict = ExpectedVerdict::Reject`.
- `safety_class = MutationSafetyClass::Diagnostic`.
- `affected_field_ids` records the omitted observation's field id.
- Nonclaim note: *observation omission is a diagnostic local check, not
  evidence that a backend's public-output commitment is unsound*.

## Default Engine Composition

`apply_default_mutations` is kept unchanged (the three existing passes) to
preserve the strict contract that every configured pass must find an eligible
target on the supplied instance. The five new passes are exported and
individually runnable via `apply_mutation_pass`, and composable via
`MutationEngine::default().with_pass(...).apply(...)`. Tests show a custom
engine composition over the new passes succeeds and is deterministic on
families that supply eligible targets (`BoundedCounterLoop`, `NestedLoop`,
`GuardHeavyMachine`).

## Required Tests

- One test per new pass showing it applies to an eligible generated instance
  and produces the correct `mutation_class`, `expected_verdict`,
  `safety_class`, and non-empty affected-ids.
- One test per new pass showing `apply_mutation_pass` returns a descriptive
  `Err` when no eligible target exists (e.g. `BranchingFsm` has no invariants
  for `InvariantWeakeningPass`).
- One test showing the extended default engine is deterministic (rerun
  equality).
- One test showing each new pass preserves `ClaimBoundary::Level1LocalReplay`
  on its output.
- One test asserting no new `MutationClass` variants were added (the enum
  still has exactly 14 variants) — guards against scope creep.
- One test asserting the new passes are re-exported from the crate root and
  prelude (mirrors the existing public API surface).

## Claim Boundary

Every mutated instance produced by this phase carries
`ClaimBoundary::Level1LocalReplay`. A mutation pass applying successfully is
local regression evidence that the mutation is structurally detectable by the
shipped oracle; it is **not** proof, not benchmark evidence, not accepted
evidence, not formal evidence, not ZK backend performance evidence, not
semantic correctness, not global software-agent uniqueness, and not evidence
that any real backend would accept or reject the mutated instance.

## Non-Goals

- Implementing the remaining six mutation classes.
- Changing `MutationClass`, `MutationKind`, `MutationSafetyClass`,
  `ExpectedVerdict`, `MutationPass`, or `MutationBuild`.
- Changing the DSL, oracle, scoring, evidence ledgers, accepted-ledger
  append, promotion preflight, official-submission package, external replay
  preflight, pack readiness, report bundle, audit index, cross-bundle audit
  index, local benchmark artifact, local artifact campaign, or any HSAI
  crate.
- Producing the first Level2 evidence, the first accepted Evidence Ledger
  entry, the first formal property statement, the first machine-checked
  proof, or the first independently reproduced evidence.
- Any external execution, network access, or credential use.

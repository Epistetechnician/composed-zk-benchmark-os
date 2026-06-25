# Phase 154 New Benchmark Families Boundary Spec

Status: docs-first boundary for the next two local benchmark families.

## Purpose

The v0 generator ships three implemented families (`BaselineFsm`,
`BranchingFsm`, `BoundedCounterLoop`). Six placeholders (`NestedLoop`,
`RecursiveEnvelope`, `MemoryHeavyStateMachine`, `GuardHeavyMachine`,
`PublicPrivateBoundaryStress`, `ZkMlControlFlowMixed`) are registered but return
"future placeholder family kind is not implemented" from `DeterministicGenerator`.

This boundary unblocks the two cleanest next families, `NestedLoop` and
`GuardHeavyMachine`, as fully deterministic local generators over the existing
Surface DSL, Semantic IR, Oracle, and `Level1LocalReplay` claim boundary. They
reuse the existing family template registry, family id derivation, instance
metadata, and local JSON replay path without any new external surface.

## State Slice

This phase may touch only:

- `crates/zkbench-core/src/generator/templates.rs`
- `crates/zkbench-core/src/generator/deterministic.rs`
- `crates/zkbench-core/src/generator/config.rs`
- `crates/zkbench-core/src/generator/mod.rs`
- `crates/zkbench-core/src/adapters/zk_harness/mapping.rs`
- `crates/zkbench-core/src/soak/runner.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/src/prelude.rs`
- `crates/zkbench-core/tests/` (additive tests)
- `docs/154-phase-new-benchmark-families-boundary-spec.md`
- `docs/154-phase-new-benchmark-families-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

It does not authorize any Cargo metadata change, dependency change,
`Cargo.lock` change, new DSL type, new mutation pass, new external surface,
command-line tool, UI dashboard, browser app, package runtime file, network
access, official benchmark submission, accepted Evidence Ledger mutation,
score-axis population, Level2+ evidence creation, or stronger claim than the
existing `Level1LocalReplay` cap on generated instances.

## NestedLoop Family

Purpose: stress trace length and dependency ordering over two stacked bounded
loops.

Surface contract:

- Two named int fields, an inner counter `inner` and an outer counter `outer`.
- States: `start`, `counting`, `finished`.
- Transitions: `enter_counting`, `increment_inner` (guarded on inner < bound),
  `step_outer` (guarded on inner == bound), `finish` (guarded on outer == bound).
- Two `LoopSpec` entries: one for the inner loop, one for the outer loop,
  both bounded by the configured tunable.
- One `InvariantSpec`: inner is at or below bound.
- One `ObserveSpec`: outer counter.
- Accepted trace: enter, then bound inner increments, then one outer step,
  repeated until outer reaches bound, then finish. Counter values are
  deterministic.
- Rejected trace: an extra `increment_inner` once `inner == bound`, which
  violates the inner guard.

Tunables consumed:

- `loop_bound` controls both the inner bound and the outer target.
- `state_count` and `trace_length` are recorded as unsupported when they would
  exceed the deterministic builder; they are not used to grow the family.

## GuardHeavyMachine Family

Purpose: stress constraints around boolean and integer predicates.

Surface contract:

- One int field `value` and one bool field `locked`.
- States: `open`, `guarded`, `done`.
- Transitions: `acquire` (guarded on `locked == false`, sets `locked := true`),
  `release` (guarded on `locked == true`, sets `locked := false`),
  `advance` (guarded on `locked == true AND value < bound`, increments `value`),
  `finish` (guarded on `locked == true AND value == bound`, sets `locked := false`).
- `GuardSpec::Expr(GuardExpr::And { ... })` is used on `advance` and `finish`
  to exercise the existing conjunction guard.
- One `LoopSpec`: body covers `advance` and is bounded by `value <= bound`.
- One `InvariantSpec`: `locked` implies `value` at or below bound.
- One `ObserveSpec`: `value`.
- Accepted trace: acquire, advance until value == bound, finish.
- Rejected trace: attempt `advance` after `release` has set `locked := false`.

Tunables consumed:

- `loop_bound` controls the bound for `advance`.
- `guard_complexity` is recorded as unsupported; only the existing binary
  conjunction is exercised deterministically.

## Implementation Contract

`DeterministicGenerator::generate_family` must dispatch to two new builders,
`build_nested_loop` and `build_guard_heavy_machine`, that:

- reuse the existing `base_surface` helper;
- reuse the existing `eq_field_int`, `lt_field_int`, `lt_field_field`,
  `lte_field_field`, `eq_field_field`, `and_guard`, and `add_assign_int`
  helpers or trivially extend them inside the builder file;
- produce valid `SurfaceSpec` that passes `validate_surface_spec`;
- lower to a `SemanticIr` via the existing `lower_to_ir`;
- attach at least one accepted trace and one rejected trace whose oracle
  outcomes match the declared `ExpectedVerdict`;
- preserve `ClaimBoundary::Level1LocalReplay`;
- preserve the nonclaim strings already used by Phase D/E families.

`FamilyKind::is_implemented` must return `true` for both new kinds.
`family_template` must populate `implemented: true` and a non-empty
`supported_oracle_features` vector for both new kinds. `all_family_templates`
must list them with the new state.

`GeneratorConfig` must gain `nested_loop` and `guard_heavy_machine` constructors
with safe defaults and tunable overrides that satisfy the existing limits.

The zk-Harness dry-run mapping (`candidate_family_label`) must extend to the two
new families with inert labels. Inert label addition does not authorize live
zk-Harness execution.

The local soak runner (`generator_config_for_case` in `soak/runner.rs`) must
dispatch to the two new constructors for the matching `FamilyKind`. The default
`SoakFamilySelection` must not silently select the new families; soak selection
remains explicit per profile.

## Required Tests

Implementation tests must prove, for both families:

- generation succeeds and produces a valid `SurfaceSpec`;
- `validate_surface_spec` accepts the produced spec;
- `lower_to_ir` accepts the produced spec;
- the accepted trace evaluates to `OracleOutcome::Accept`;
- the rejected trace evaluates to `OracleOutcome::Reject`;
- `is_implemented` returns `true`;
- the family id is stable across runs with the same seed and tunables;
- family id changes when seed or `loop_bound` changes;
- the local JSON adapter runs the accepted trace to `Completed` and reports no
  external backend claim;
- the zk-Harness dry-run mapping returns the new inert label;
- soak selection explicitly selects the new families and produces a
  `Level0DesignNote` health report without ZK backend performance claims.

Implementation tests must also prove:

- future placeholder families still reject with the existing error path;
- no production source under `crates/zkbench-core/src` contains
  `std::process::Command` or `Command::new`;
- no production source under `crates/zkbench-core/src` claims Level2+ evidence.

## Claim Boundary

The new families are local semantic fixtures only. They are not official
benchmark evidence, not ZK backend performance evidence, not formal evidence,
not accepted Evidence Record material, not proof, not semantic correctness,
not production readiness, not global software-agent uniqueness, and not
authorization to elevate any claim boundary above `Level1LocalReplay`.

## Non-Goals

This phase does not implement `RecursiveEnvelope`, `MemoryHeavyStateMachine`,
`PublicPrivateBoundaryStress`, or `ZkMlControlFlowMixed`. Those remain future
phases because each requires either recursion-envelope semantics, memory-like
state semantics, witness-boundary semantics, or zkML-specific surface contract
work that is out of scope here.

This phase does not add new mutation passes. Existing `MissingConstraints`,
`CorruptedGuards`, and `BadCounters` passes continue to target applicable
accepted trace actions; targetless combinations remain applicability telemetry.

This phase does not change the claim boundary cap, evidence classification, or
scoring rubric. It does not add a CLI, dashboard, package runtime file, network
path, credential path, or external execution path.

## Validation

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
rg "std::process::Command|Command::new" crates/zkbench-core/src || true
```

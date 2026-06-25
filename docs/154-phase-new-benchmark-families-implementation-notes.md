# Phase 154 New Benchmark Families Implementation Notes

Status: implemented.

## State Slice

This phase touched only the state slice authorized by
`docs/154-phase-new-benchmark-families-boundary-spec.md`:

- `crates/zkbench-core/src/generator/templates.rs`
- `crates/zkbench-core/src/generator/deterministic.rs`
- `crates/zkbench-core/src/generator/config.rs`
- `crates/zkbench-core/src/adapters/zk_harness/mapping.rs`
- `crates/zkbench-core/src/soak/runner.rs`
- `crates/zkbench-core/tests/phase_154_new_families.rs` (new tests)
- `docs/154-phase-new-benchmark-families-boundary-spec.md`
- `docs/154-phase-new-benchmark-families-implementation-notes.md`
- `docs/08-benchmark-taxonomy.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No `Cargo.toml`, `Cargo.lock`, dependency, new DSL type, or new mutation pass was
touched.

## NestedLoop Generator

`build_nested_loop` produces a Surface DSL machine with two stacked bounded
loops and a clear dependency ordering:

- States: `start`, `counting`, `finished`.
- Fields: private `inner`, public `outer`, public `bound`.
- Transitions: `enter_counting` (unguarded entry), `increment_inner` (guarded
  on `inner < bound`), `step_outer` (guarded on `inner == bound`, resets
  `inner := 0` and increments `outer`), `finish` (guarded on `outer == bound`).
- Loops: `inner_loop` body covers `increment_inner`, `outer_loop` body covers
  `step_outer`, both bounded by `lte_field_field(counter, bound)`.
- Invariant: `inner_at_or_below_bound` (inner stays at or below bound).
- Observation: `outer`.
- Accepted trace: enter, then `bound` rounds of `bound` inner increments
  followed by one outer step, then finish. Final state `finished`, final
  `outer == bound`.
- Rejected trace: enter, `bound` inner increments (inner reaches bound), then
  one more `increment_inner` whose guard evaluates false.

The rejected trace fails inside the oracle guard check rather than at final
state, so it correctly evaluates to `OracleOutcome::Rejected`.

## GuardHeavyMachine Generator

`build_guard_heavy_machine` exercises boolean and integer conjunction guards:

- States: `open`, `guarded`, `done`.
- Fields: public `value`, public `bound`, private `locked`.
- Transitions: `acquire` (guarded on `locked == false`, sets `locked := true`),
  `release` (guarded on `locked == true`, sets `locked := false`), `advance`
  (guarded on `locked == true AND value < bound`, increments `value`), `finish`
  (guarded on `locked == true AND value == bound`, sets `locked := false`).
- Loop: `advance_until_bound` body covers `advance`.
- Invariant: `locked_implies_value_at_or_below_bound` (`locked == false OR
  value <= bound`).
- Observation: `value`.
- Accepted trace: acquire, `bound` advances, finish. Final state `done`, final
  `value == bound`, final `locked == false`.
- Rejected trace: acquire, advance, release, advance — the second `advance`
  starts from `open`, not `guarded`, so the oracle rejects on the
  from-state mismatch.

Both new generators use `GuardExpr::And` (via the new `and_guard` helper) and
`GuardExpr::Or` (via the new `or_guard` helper) to exercise the existing
conjunction and disjunction evaluation in `dsl::oracle`.

## Implementation Contract

`FamilyKind::is_implemented` now returns `true` for `NestedLoop` and
`GuardHeavyMachine`. `family_template` returns `implemented: true` and a
populated `supported_oracle_features` vector for both. The placeholder arm in
`family_template` only covers the remaining four families
(`RecursiveEnvelope`, `MemoryHeavyStateMachine`, `PublicPrivateBoundaryStress`,
`ZkMlControlFlowMixed`).

`DeterministicGenerator::generate_family` dispatches the two new kinds to the
new builders. The previous blanket placeholder arm only covers the four
remaining placeholders and continues to return the existing error.

`GeneratorConfig` gains `nested_loop()` and `guard_heavy_machine()`
constructors with safe defaults inside the existing `GeneratorLimits`:
`state_count = 3`, `loop_bound = 2`. Both satisfy `max_states` (16) and
`max_loop_bound` (16).

`adapters::zk_harness::mapping::candidate_family_label` returns inert labels
`control_flow_nested_loop` and `control_flow_guard_heavy_machine`. Inert
labels surface through `ZkHarnessDryRunPlan::pack_mapping.family_mappings`
when a pack contains the new instances. They are internal candidate labels
only, not verified zk-Harness schema, and do not authorize live execution.

`soak::runner::generator_config_for_case` dispatches the two new families to
the new `GeneratorConfig` constructors when explicitly selected, and applies
the trace-length/loop-bound reconciliation for both loop-bearing families.
The default `SoakFamilySelection::implemented_v0()` is intentionally left at
the original three families; selecting the new families is explicit, which
preserves backward compatibility for existing soak tests.

## New Surface DSL Helpers

`deterministic.rs` gains four private helpers that mirror the existing ones:

- `eq_field_bool(field, value)` — equality guard against a boolean literal.
- `and_guard(left, right)` — two-arm conjunction guard.
- `or_guard(left, right)` — two-arm disjunction guard.
- `assign_bool(field, value)` — boolean field assignment action.

They are private to the generator module because they are implementation
plumbing for the family builders, not public Surface DSL surface.

## Claim Boundary

Both new families carry `ClaimBoundary::Level1LocalReplay` on every generated
instance, reuse the existing
`"Generated family is a local semantic fixture, not official benchmark evidence."`
nonclaim, and produce no external backend artifacts. The zk-Harness dry-run
labels are inert. The soak campaign results stay at `Level0DesignNote`. No
score axis is populated from these families.

## Tests

`crates/zkbench-core/tests/phase_154_new_families.rs` covers:

- both families generate, validate, lower, and evaluate (accepted → Accept,
  rejected → Reject);
- both families are marked `implemented` in the registry and template table;
- later Phase 164 families are tracked separately and remain outside the Phase
  154 implementation claim;
- family ids are deterministic across runs and sensitive to seed and
  `loop_bound`;
- the local JSON adapter runs the accepted traces without exceeding
  `Level1LocalReplay`;
- zk-Harness dry-run export surfaces the new inert labels and does not claim
  official benchmark evidence;
- existing mutation passes (`BadCounters`, `MissingConstraints`,
  `CorruptedGuards`) apply to the new families where eligible, with the
  non-eligible cases remaining applicability telemetry;
- the local soak campaign runs the new families explicitly through the lib
  API and stays `Level0DesignNote` without ZK backend performance claims.

## Validation

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
rg "std::process::Command|Command::new" crates/zkbench-core/src || true
```

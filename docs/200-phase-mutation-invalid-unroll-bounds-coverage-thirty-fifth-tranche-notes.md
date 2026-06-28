# Phase 200 Mutation Invalid Unroll Bounds Coverage Thirty-Fifth Tranche Notes

State slice: `phase-200-mutation-invalid-unroll-bounds-coverage-thirty-fifth-tranche`.

## Claim

Phase 200 continues the bounded local coverage campaign by hardening reachable
`InvalidUnrollBoundsPass` behavior in `crates/zkbench-core`. The tranche adds
focused local regression tests for existing public contracts only. It changes
no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 199 already targeted the next reachable pure-data floor
(`soak/resume.rs`). Phase 200 targets the next reachable pure-data floor,
`mutation/invalid_unroll_bounds.rs`, without forcing unreachable branches or
suppressing coverage.

## Implemented Coverage

- `InvalidUnrollBoundsPass::mutation_class()` reports its declared
  `MutationClass::InvalidUnrollBounds`.
- The pass fails closed when an eligible loop is found but the source instance
  declares no accepted or rejected trace for primary-trace selection.
- The pass preserves the source primary trace id, an `ExpectedVerdict::Reject`
  verdict, a `MutationSafetyClass::NearValid` safety class, the
  `ClaimBoundary::Level1LocalReplay` boundary, and an `affected_guard_ids`
  entry ending in `.bound` for an eligible bounded-counter-loop instance.

## Coverage Result

Baseline target: `mutation/invalid_unroll_bounds.rs` reported `78.87%` line
coverage, `57.14%` function execution, and `81.18%` region coverage.

Post-tranche target: `mutation/invalid_unroll_bounds.rs` reported `88.73%`
line coverage, `85.71%` function execution, and `89.41%` region coverage.

Post-tranche `zkbench-core` package coverage reported `90.00%` region coverage,
`85.65%` function execution, and `90.82%` line coverage.

Post-tranche workspace coverage reported `91.71%` region coverage, `88.11%`
function execution, and `92.05%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining lower floors are serializer-wrapper files whose
uncovered lines are structurally unreachable `serde_json::to_string_pretty`
error mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The remaining uncovered lines in `mutation/invalid_unroll_bounds.rs` are
structurally unreachable per the selector contract: the
`target.bound.is_none()` error path cannot fire because the selector already
requires `Some(...)` with an executable bound, and the `negate_bound` `Bool`
and `RawText` arms cannot fire because the selector already restricts the
bound to executable `Expr` variants. This tranche did not force those
branches.

After the two known serializer-wrapper caps, the next visible non-serializer
`zkbench-core` floor requiring audit is `evidence/accepted_append.rs` at
`78.99%` line coverage.

## Nonclaims

Phase 200 does not change mutation pass semantics, selector semantics,
`negate_bound` semantics, DSL types, oracle semantics, scoring semantics,
production source, Cargo metadata, dependencies, external execution, generated
artifact materialization, accepted Evidence Ledger policy, formal evidence,
benchmark evidence, real score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.

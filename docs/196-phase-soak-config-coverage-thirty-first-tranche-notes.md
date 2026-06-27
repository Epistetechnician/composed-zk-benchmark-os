# Phase 196 Soak Config Coverage Thirty-First Tranche Notes

State slice: `phase-196-soak-config-coverage-thirty-first-tranche`.

## Claim

Phase 196 continues the bounded local coverage campaign by hardening reachable
local soak configuration behavior in `crates/zkbench-core`. The tranche adds
focused local regression tests for existing public contracts only. It changes
no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 196 therefore targets the next reachable pure-data floor,
`soak/config.rs`, without forcing unreachable branches or suppressing coverage.

## Implemented Coverage

- Seed-range empty, descending, value-enumeration, and default behavior.
- Family and mutation selection normalization with sorting and deduplication.
- Planned case and mutation count helpers after normalization.
- Output-policy pack-write request accounting for every policy variant.
- Smoke, regression, focused, custom, and explicit nightly-local profile
  validation boundaries.
- Soak config version and local-only nonclaim note preservation.
- Identity, claim-boundary, soak-artifact-boundary, local-replay-boundary, empty
  family, empty seed, empty mutation, and unimplemented mutation rejection paths.
- Family-count, instance-count, mutation-count, zero-shard, and pack-write limit
  rejection paths.

## Coverage Result

Baseline target: `soak/config.rs` reported `78.21%` line coverage, `90.24%`
function execution, and `86.35%` region coverage.

Post-tranche target: `soak/config.rs` reported `98.88%` line coverage,
`100.00%` function execution, and `99.26%` region coverage.

Post-tranche `zkbench-core` package coverage reported `89.49%` region coverage,
`85.08%` function execution, and `90.34%` line coverage.

Post-tranche workspace coverage reported `91.37%` region coverage, `87.72%`
function execution, and `91.72%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining floors are serializer-wrapper files whose uncovered
lines are structurally unreachable `serde_json::to_string_pretty` error
mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `adapters/zk_harness/export.rs` at
`78.26%` line coverage.

## Nonclaims

Phase 196 does not change local soak configuration semantics, limits,
profile policy, production source, Cargo metadata, dependencies, external
execution, generated artifact materialization, accepted Evidence Ledger policy,
formal evidence, benchmark evidence, real score-axis population, Level2+
evidence, semantic-correctness claims, production-readiness claims, unsafe
coverage forcing, coverage suppression, structurally unreachable
serialization-error forcing, or whole-workspace 100% coverage claims.

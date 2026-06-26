# Phase 190 Generator Instance Coverage Twenty-Fifth Tranche Notes

State slice: `phase-190-generator-instance-coverage-twenty-fifth-tranche`.

## Claim

Phase 190 continues the bounded local coverage campaign by hardening reachable
generated benchmark instance fallback behavior in `crates/zkbench-core`. The
tranche adds one focused local regression test for existing public contracts
only. It changes no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 190 therefore targets the next reachable `zkbench-core` floor,
`generator/instance.rs`, without forcing unreachable branches or suppressing
coverage.

## Implemented Coverage

- Empty semantic-oracle accepted and rejected trace fallback.
- Fallback primary trace identity, empty initial/final fields, empty steps, and
  empty required capabilities.
- `ExpectedVerdict::Inconclusive` fallback verdict.
- Empty copied accepted/rejected trace and expected-verdict collections.
- Custom instance suffix preservation and family claim-boundary preservation.

## Coverage Result

Baseline target: `generator/instance.rs` reported `76.47%` region coverage,
`50.00%` function execution, and `77.27%` line coverage.

Post-tranche target: `generator/instance.rs` reported `100.00%` region
coverage, `100.00%` function execution, and `100.00%` line coverage.

Post-tranche `zkbench-core` package coverage reported `88.19%` region coverage,
`83.60%` function execution, and `88.55%` line coverage.

Post-tranche workspace coverage reported `90.54%` region coverage, `86.73%`
function execution, and `90.46%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining floors are serializer-wrapper files whose uncovered
lines are structurally unreachable `serde_json::to_string_pretty` error
mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `recursion.rs` at `77.29%` line
coverage.

## Nonclaims

Phase 190 does not change generator instance semantics, production source,
Cargo metadata, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy, formal evidence, benchmark
evidence, real score-axis population, Level2+ evidence, semantic-correctness
claims, production-readiness claims, unsafe coverage forcing, coverage
suppression, structurally unreachable serialization-error forcing, or
whole-workspace 100% coverage claims.

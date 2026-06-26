# Phase 188 Soak Reproduction Coverage Twenty-Third Tranche Notes

State slice: `phase-188-soak-reproduction-coverage-twenty-third-tranche`.

## Claim

Phase 188 continues the bounded local coverage campaign by hardening reachable
soak reproduction-bundle validation and readback behavior in `crates/zkbench-core`.
The tranche adds focused local regression tests for existing public contracts
only. It changes no production Rust source.

## Implemented Coverage

- Reproduction-bundle claim-boundary elevation rejection.
- Empty reproduction-bundle entry-id rejection.
- Entry-level and reproduction-manifest claim-boundary elevation rejection.
- Post-sidecar pack validation failure reporting after declared pack-file
  digest drift.
- Malformed reproduction sidecar JSON readback rejection with the public
  deserialization context.

## Coverage Result

Baseline target: `soak/reproduction.rs` reported `82.64%` region coverage,
`60.00%` function execution, and `76.64%` line coverage.

Post-tranche target: `soak/reproduction.rs` reported `89.26%` region coverage,
`80.00%` function execution, and `97.20%` line coverage.

Post-tranche `zkbench-core` package coverage reported `87.72%` region coverage,
`83.20%` function execution, and `88.08%` line coverage.

Post-tranche workspace coverage reported `90.22%` region coverage, `86.42%`
function execution, and `90.11%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
Its uncovered lines are the `serde_json::to_string_pretty` error mappings for
concrete derived replay structs; this tranche did not force those structurally
unreachable serialization-error branches or suppress coverage.

The next reachable `zkbench-core` floor is `external_runner/serialization.rs`
at `76.65%` line coverage.

## Nonclaims

Phase 188 does not change soak reproduction semantics, production source,
Cargo metadata, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy, formal evidence, benchmark
evidence, real score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.

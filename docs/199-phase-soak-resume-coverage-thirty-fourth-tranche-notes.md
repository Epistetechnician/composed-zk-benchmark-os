# Phase 199 Soak Resume Coverage Thirty-Fourth Tranche Notes

State slice: `phase-199-soak-resume-coverage-thirty-fourth-tranche`.

## Claim

Phase 199 continues the bounded local coverage campaign by hardening reachable
local soak checkpoint validation and persistence behavior in `crates/zkbench-core`.
The tranche adds focused local regression tests for existing public contracts
only. It changes no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 199 therefore targets the next reachable pure-data floor,
`soak/resume.rs`, without forcing unreachable branches or suppressing coverage.

## Implemented Coverage

- Checkpoint validation rejects elevated claim boundaries, empty shard ids, and
  resume-token drift.
- Completed, skipped, and failed case-id overlap is rejected fail-closed.
- Failure artifact refs reject empty paths, empty roles, parent traversal, and
  backslash paths while accepting portable local paths.
- Empty failed-case ids are rejected after subset and overlap validation paths.
- Checkpoint persistence creates parent directories, round-trips valid JSON,
  and reports missing or malformed checkpoint-file read failures.

## Coverage Result

Baseline target: `soak/resume.rs` reported `78.61%` line coverage, `66.67%`
function execution, and `78.10%` region coverage.

Post-tranche target: `soak/resume.rs` reported `93.58%` line coverage,
`77.78%` function execution, and `88.10%` region coverage.

Post-tranche `zkbench-core` package coverage reported `89.98%` region coverage,
`85.54%` function execution, and `90.79%` line coverage.

Post-tranche workspace coverage reported `91.69%` region coverage, `88.03%`
function execution, and `92.03%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining lower floors are serializer-wrapper files whose
uncovered lines are structurally unreachable `serde_json::to_string_pretty`
error mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `mutation/invalid_unroll_bounds.rs`
at `78.87%` line coverage.

## Nonclaims

Phase 199 does not change local soak checkpoint semantics, resume semantics,
artifact-reference semantics, checkpoint persistence semantics, production
source, Cargo metadata, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy, formal evidence, benchmark
evidence, real score-axis population, Level2+ evidence, semantic-correctness
claims, production-readiness claims, unsafe coverage forcing, coverage
suppression, structurally unreachable serialization-error forcing, or
whole-workspace 100% coverage claims.

# Phase 197 zk-Harness Export Coverage Thirty-Second Tranche Notes

State slice: `phase-197-zk-harness-export-coverage-thirty-second-tranche`.

## Claim

Phase 197 continues the bounded local coverage campaign by hardening reachable
zk-Harness dry-run export helper behavior in `crates/zkbench-core`. The tranche
adds focused local regression tests for existing public contracts only. It
changes no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 197 therefore targets the next reachable pure-data floor,
`adapters/zk_harness/export.rs`, without forcing unreachable branches or
suppressing coverage.

## Implemented Coverage

- The public `build_zk_harness_dry_run_plan_from_pack` helper delegates to the
  direct export helper and returns the same dry-run plan for a safe local pack.
- Exported pack metadata preserves the source pack id and binds the generated
  dry-run plan id into the export manifest.
- A locally valid source pack whose id is unsafe for inert zk-Harness command
  argument text fails closed at export-time dry-run validation.
- Export failure preserves the zk-Harness validation context, planned-command
  argument path, and shell-metacharacter rejection message.

## Coverage Result

Baseline target: `adapters/zk_harness/export.rs` reported `78.26%` line
coverage, `80.00%` function execution, and `79.37%` region coverage.

Post-tranche target: `adapters/zk_harness/export.rs` reported `86.96%` line
coverage, `80.00%` function execution, and `80.95%` region coverage.

Post-tranche `zkbench-core` package coverage reported `89.49%` region coverage,
`85.08%` function execution, and `90.36%` line coverage.

Post-tranche workspace coverage reported `91.38%` region coverage, `87.72%`
function execution, and `91.73%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining lower floors are serializer-wrapper files whose
uncovered lines are structurally unreachable `serde_json::to_string_pretty`
error mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `soak/runner.rs` at `78.41%` line
coverage.

## Nonclaims

Phase 197 does not change zk-Harness export semantics, validation semantics,
pack semantics, production source, Cargo metadata, dependencies, external
execution, zk-Harness execution, generated artifact materialization, accepted
Evidence Ledger policy, formal evidence, benchmark evidence, real score-axis
population, Level2+ evidence, semantic-correctness claims, production-readiness
claims, unsafe coverage forcing, coverage suppression, structurally unreachable
serialization-error forcing, or whole-workspace 100% coverage claims.

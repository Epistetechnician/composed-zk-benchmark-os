# Phase 184 Accepted Append Output Coverage Nineteenth Tranche Notes

State slice: `phase-184-accepted-append-output-coverage-nineteenth-tranche`.

## Claim

Phase 184 continues the bounded local coverage campaign by hardening the Phase W
materialized accepted-ledger append output surface in `crates/zkbench-core`.
The tranche adds focused local regression tests for existing public contracts
only. It changes no production Rust source.

## Implemented Coverage

- Empty materialized ledger path rejection.
- Bare relative ledger path rejection before any repository-root write.
- Parseable but invalid existing ledger rejection without repair.
- Stale temporary file replacement during atomic JSON write.
- Symlink parent-directory rejection on Unix.
- Source-boundary checks for the local JSON-only atomic-write path.

## Coverage Result

Baseline target: `evidence/accepted_append_output.rs` reported `74.34%` region
coverage, `57.14%` function execution, and `74.55%` line coverage.

Post-tranche target: `evidence/accepted_append_output.rs` reported `78.95%`
region coverage, `57.14%` function execution, and `86.36%` line coverage.

Post-tranche `zkbench-core` package coverage reported `87.14%` region coverage,
`82.80%` function execution, and `87.35%` line coverage.

Post-tranche workspace coverage reported `89.84%` region coverage, `86.15%`
function execution, and `89.59%` line coverage.

The next package coverage floor is `replay/serialization.rs` at `75.00%` line
coverage.

## Nonclaims

Phase 184 does not change accepted-ledger append semantics, production source,
Cargo metadata, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy, formal evidence, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression, or
whole-workspace 100% coverage claims.

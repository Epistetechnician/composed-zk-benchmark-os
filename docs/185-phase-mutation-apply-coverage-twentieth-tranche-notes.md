# Phase 185 Mutation Apply Coverage Twentieth Tranche Notes

State slice: `phase-185-mutation-apply-coverage-twentieth-tranche`.

## Claim

Phase 185 continues the bounded local coverage campaign by hardening reachable
public mutation-application paths in `crates/zkbench-core`. The tranche adds
focused local regression tests for existing public contracts only. It changes
no production Rust source.

## Implemented Coverage

- Default Phase D/E mutation bundle execution through `apply_default_mutations`.
- Public primary-trace evaluation through `evaluate_mutated_instance`.
- Bad-counter mutation handling for `add_assign` integer operands other than
  `1`.
- Bad-counter mutation handling for `sub_assign` integer updates.

## Coverage Result

Baseline target: `mutation/apply.rs` reported `76.59%` region coverage,
`82.76%` function execution, and `75.37%` line coverage.

Post-tranche target: `mutation/apply.rs` reported `87.29%` region coverage,
`89.66%` function execution, and `89.93%` line coverage.

Post-tranche `zkbench-core` package coverage reported `87.28%` region coverage,
`82.92%` function execution, and `87.52%` line coverage.

Post-tranche workspace coverage reported `89.93%` region coverage, `86.22%`
function execution, and `89.71%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
Its uncovered lines are the `serde_json::to_string_pretty` error mappings for
concrete derived replay structs; this tranche did not force those structurally
unreachable serialization-error branches or suppress coverage.

## Nonclaims

Phase 185 does not change mutation semantics, production source, Cargo
metadata, dependencies, external execution, generated artifact materialization,
accepted Evidence Ledger policy, formal evidence, benchmark evidence,
score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression, or
whole-workspace 100% coverage claims.

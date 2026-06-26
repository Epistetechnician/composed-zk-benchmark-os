# Phase 187 Scoring Coverage Twenty-Second Tranche Notes

State slice: `phase-187-scoring-coverage-twenty-second-tranche`.

## Claim

Phase 187 continues the bounded local coverage campaign by hardening reachable
score-report validation and confidence-mapping behavior in `crates/zkbench-core`.
The tranche adds focused local regression tests for existing public contracts
only. It changes no production Rust source.

## Implemented Coverage

- Higher-boundary confidence mapping for Level2/Level3 `High`,
  Level4/Level5 `ScopedProof`, and Level6 `Independent`.
- Safe higher-boundary score-axis validation for bounded values and bounded
  notes across performance, correctness, soundness, recursion, formal,
  reproducibility, and adapter-portability axes.
- Local Level1 populated-axis rejection across all optional score axes.
- Invalid score-value rejection across every optional score-axis value path.
- Forbidden score-axis note text rejection across every optional score-axis
  note path.
- `CapabilityGap` risk-penalty forbidden-text validation.

## Coverage Result

Baseline target: `scoring/mod.rs` reported `76.86%` region coverage, `100.00%`
function execution, and `76.60%` line coverage.

Post-tranche target: `scoring/mod.rs` reported `100.00%` region coverage,
`100.00%` function execution, and `100.00%` line coverage.

Post-tranche `zkbench-core` package coverage reported `87.69%` region coverage,
`83.14%` function execution, and `87.99%` line coverage.

Post-tranche workspace coverage reported `90.20%` region coverage, `86.38%`
function execution, and `90.05%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
Its uncovered lines are the `serde_json::to_string_pretty` error mappings for
concrete derived replay structs; this tranche did not force those structurally
unreachable serialization-error branches or suppress coverage.

## Nonclaims

Phase 187 does not change scoring semantics, production source, Cargo metadata,
dependencies, external execution, generated artifact materialization, accepted
Evidence Ledger policy, formal evidence, benchmark evidence, real score-axis
population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

# Phase 183 Local Benchmark Artifact Coverage Eighteenth Tranche Notes

State slice: `phase-183-local-benchmark-artifact-coverage-eighteenth-tranche`.

## Claim

Phase 183 continues the bounded local coverage campaign by hardening the Phase U
local benchmark artifact packaging surface in `crates/zkbench-core`. The
tranche adds focused local regression tests for existing public contracts only.
It changes no production Rust source.

## Implemented Coverage

- Manifest identity, duplicate input id, duplicate artifact URI, invalid
  digest, input-boundary, and weakest-input output-boundary rejection.
- Missing input and missing benchmark-pack-manifest rejection.
- Portable artifact URI rejection for empty, absolute, backslash, URL, pipe,
  semicolon, and dollar-containing paths.
- Invalid manifest Markdown rendering and malformed manifest JSON
  deserialization context.
- Output-root file rejection, matching overwrite idempotence, manifest digest
  sidecar UTF-8 rejection, manifest digest drift, and non-UTF-8 Markdown after
  digest consistency.

## Coverage Result

Baseline target: `local_benchmark_artifact.rs` reported `76.62%` region
coverage, `62.00%` function execution, and `74.42%` line coverage.

Post-tranche target: `local_benchmark_artifact.rs` reported `84.20%` region
coverage, `70.00%` function execution, and `90.08%` line coverage.

Post-tranche `zkbench-core` package coverage reported `87.12%` region coverage,
`82.80%` function execution, and `87.30%` line coverage.

Post-tranche workspace coverage reported `89.82%` region coverage, `86.15%`
function execution, and `89.56%` line coverage.

The next package coverage floor is `evidence/accepted_append_output.rs` at
`74.55%` line coverage.

## Nonclaims

Phase 183 does not change artifact semantics, production source, Cargo
metadata, dependencies, external execution, generated artifact materialization,
accepted Evidence Ledger mutation, formal evidence, benchmark evidence,
score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression, or
whole-workspace 100% coverage claims.

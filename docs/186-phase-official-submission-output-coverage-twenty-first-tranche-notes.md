# Phase 186 Official Submission Output Coverage Twenty-First Tranche Notes

State slice: `phase-186-official-submission-output-coverage-twenty-first-tranche`.

## Claim

Phase 186 continues the bounded local coverage campaign by hardening reachable
official-submission package output plumbing in `crates/zkbench-core`. The
tranche adds focused local regression tests for existing public contracts only.
It changes no production Rust source.

## Implemented Coverage

- Output-root shape preconditions for empty paths, parent-directory components,
  protected parent-directory components, existing file roots, and non-empty
  roots without explicit overwrite.
- Accepted-ledger path rejection for directory paths, parent-directory
  components, and parseable but invalid accepted ledger JSON.
- Digest-consistent semantic readback drift for package Markdown, validation
  report package identity, and validation report side-effect claims.
- Non-UTF-8 declared package metadata, package Markdown, and validation report
  files after matching digest sidecar updates.
- Readback rejection for file roots, missing declared files, symlinked output
  roots, and symlinked declared package files.

## Coverage Result

Baseline target: `evidence/official_submission_output.rs` reported `75.56%`
region coverage, `61.36%` function execution, and `76.29%` line coverage.

Post-tranche target: `evidence/official_submission_output.rs` reported
`82.12%` region coverage, `70.45%` function execution, and `87.45%` line
coverage.

Post-tranche `zkbench-core` package coverage reported `87.46%` region coverage,
`83.14%` function execution, and `87.75%` line coverage.

Post-tranche workspace coverage reported `90.05%` region coverage, `86.38%`
function execution, and `89.87%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
Its uncovered lines are the `serde_json::to_string_pretty` error mappings for
concrete derived replay structs; this tranche did not force those structurally
unreachable serialization-error branches or suppress coverage.

## Nonclaims

Phase 186 does not change official-submission package semantics, production
source, Cargo metadata, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy, formal evidence, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, or whole-workspace 100%
coverage claims.

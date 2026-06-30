# Phase 234 Invariant Weakening Coverage Notes

## State Slice

Phase 234 is the invariant-weakening mutation coverage tranche for
`crates/zkbench-core/src/mutation/invariant_weakening.rs`.

This slice is limited to additive Rust tests under `crates/zkbench-core/tests/`
and navigation/status updates under `docs/`, `README.md`, and `AGENTS.md`.

## Purpose

Phase 233 routed the next local coverage target to
`mutation/invariant_weakening.rs` after `evidence/review_ledger.rs` reached
`97.32%` line coverage.

The Phase 234 missing-line audit found uncovered reachable paths in:

- the public `InvariantWeakeningPass::mutation_class()` method;
- the trace-selection failure path after an eligible invariant has already been
  selected.

## Implemented Coverage

Phase 234 adds focused tests to
`crates/zkbench-core/tests/phase_156_mutation_depth.rs`:

- `invariant_weakening_reports_its_mutation_class`;
- `invariant_weakening_fails_after_target_selection_when_no_trace_exists`.

The second test starts from an eligible bounded-counter-loop generated instance,
preserves the invariant target, clears accepted and rejected traces, and asserts
that `InvariantWeakeningPass` fails closed with the documented no-trace error.

## Coverage Result

Baseline before Phase 234:

- `mutation/invariant_weakening.rs`: `87.30%` region / `60.00%` function /
  `85.71%` line coverage.
- `zkbench-core` package total: `91.65%` region / `87.47%` function /
  `93.34%` line coverage.

Measured after Phase 234:

- `mutation/invariant_weakening.rs`: `98.41%` region / `100.00%` function /
  `100.00%` line coverage.
- `zkbench-core` package total: `91.67%` region / `87.59%` function /
  `93.37%` line coverage.

## Remaining Cap

`mutation/invariant_weakening.rs` has no remaining missed lines in the local
coverage report. One region remains unexecuted, but this tranche does not force
coverage beyond the public line/function paths that are meaningful through the
current generated-instance API.

## Claim Boundary

This phase proves only that the local Rust test suite now exercises
`InvariantWeakeningPass::mutation_class()` and the eligible-invariant/no-trace
failure path.

It does not prove semantic correctness, production readiness, complete mutation
engine correctness, benchmark performance, official benchmark evidence,
accepted Evidence Ledger mutation, formal evidence, score-axis population, live
provider evidence, or Level2+ evidence.

## Validation Commands

The following commands passed locally:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test phase_156_mutation_depth
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final Phase 234 gate also ran:

```sh
git diff --check
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
```

## Next Coverage Candidate

After Phase 234, `mutation/invariant_weakening.rs` has no missed lines in the
local coverage report. The lowest remaining non-serializer line-coverage
candidate in the current package summary is `external_runner/policy.rs` at
`85.78%`, subject to a fresh missing-line audit before any mutation.

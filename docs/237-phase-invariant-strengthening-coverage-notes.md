# Phase 237 Invariant Strengthening Coverage Notes

## State Slice

Phase 237 is the invariant-strengthening mutation coverage tranche for
`crates/zkbench-core/src/mutation/invariant_strengthening.rs`.

This slice is limited to additive Rust tests under `crates/zkbench-core/tests/`
and navigation/status updates under `docs/`, `README.md`, and `AGENTS.md`.

## Purpose

Phase 236 routed the next local coverage target to
`mutation/invariant_strengthening.rs` after `soak/campaign.rs` reached
`97.49%` line coverage.

The Phase 237 missing-line audit found uncovered reachable paths in:

- the public `InvariantStrengtheningPass::mutation_class()` method;
- the trace-selection failure path after an eligible invariant has already been
  selected.

## Implemented Coverage

Phase 237 adds focused tests to
`crates/zkbench-core/tests/phase_156_mutation_depth.rs`:

- `invariant_strengthening_reports_its_mutation_class`;
- `invariant_strengthening_fails_after_target_selection_when_no_trace_exists`.

The second test starts from an eligible bounded-counter-loop generated instance,
preserves the invariant target, clears accepted and rejected traces, and asserts
that `InvariantStrengtheningPass` fails closed with the documented no-trace
error.

## Coverage Result

Baseline before Phase 237:

- `mutation/invariant_strengthening.rs`: `87.88%` region / `60.00%` function /
  `86.00%` line coverage.
- `zkbench-core` package total: `91.83%` region / `87.71%` function /
  `93.56%` line coverage.

Measured after Phase 237:

- `mutation/invariant_strengthening.rs`: `98.48%` region / `100.00%` function /
  `100.00%` line coverage.
- `zkbench-core` package total: `91.86%` region / `87.83%` function /
  `93.59%` line coverage.

## Remaining Cap

`mutation/invariant_strengthening.rs` has no remaining missed lines in the
local coverage report. One region remains unexecuted, but this tranche does not
force artificial behavior beyond the current public generated-instance API.

## Claim Boundary

This phase proves only that the local Rust test suite now exercises
`InvariantStrengtheningPass::mutation_class()` and the eligible-invariant/no-
trace failure path.

It does not prove semantic correctness, production readiness, complete mutation
engine correctness, benchmark performance, official benchmark evidence,
accepted Evidence Ledger mutation, formal evidence, score-axis population, live
provider evidence, Level2+ evidence, SOTA status, or breakthrough status.

## Validation Commands

The following commands passed locally:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test phase_156_mutation_depth
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final Phase 237 gate also ran:

```sh
git diff --check
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
```

## Next Coverage Candidate

After Phase 237, `mutation/invariant_strengthening.rs` has no missed lines in
the local coverage report. The lowest remaining non-serializer line-coverage
candidate in the current package summary is
`mutation/recursion_envelope_mismatch.rs` at `86.44%`, subject to a fresh
missing-line audit before any mutation.

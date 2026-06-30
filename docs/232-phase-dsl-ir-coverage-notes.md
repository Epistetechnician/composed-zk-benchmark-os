# Phase 232 DSL IR Coverage Notes

## State Slice

Phase 232 is the DSL IR coverage tranche for
`crates/zkbench-core/src/dsl/ir.rs`.

This slice is limited to additive Rust tests under `crates/zkbench-core/tests/`
and navigation/status updates under `docs/`, `README.md`, and `AGENTS.md`.

## Purpose

Phase 231 routed the next local coverage target to `dsl/ir.rs` after
`evidence/accepted_append_output.rs` reached `90.00%` line coverage.

The Phase 232 missing-line audit found the uncovered executable path in the
public `SemanticIr::field()` lookup helper:

- `crates/zkbench-core/src/dsl/ir.rs:149`
- `crates/zkbench-core/src/dsl/ir.rs:150`
- `crates/zkbench-core/src/dsl/ir.rs:151`

The helper is a bounded local data-model convenience method. Covering it does
not change DSL semantics, oracle semantics, lowering behavior, or benchmark
evidence.

## Implemented Coverage

Phase 232 adds `semantic_ir_field_lookup_returns_present_and_missing_fields` to
`crates/zkbench-core/tests/lowering.rs`.

The test lowers the existing baseline FSM fixture and asserts both lookup
outcomes:

- existing field id `counter` returns the canonical field;
- missing field id `missing` returns `None`.

## Coverage Result

Baseline before Phase 232:

- `dsl/ir.rs`: `84.62%` region / `75.00%` function / `85.19%` line coverage.
- `zkbench-core` package total: `91.53%` region / `87.24%` function /
  `93.21%` line coverage.

Measured after Phase 232:

- `dsl/ir.rs`: `100.00%` region / `100.00%` function / `100.00%` line
  coverage.
- `zkbench-core` package total: `91.55%` region / `87.36%` function /
  `93.23%` line coverage.

## Claim Boundary

This phase proves only that the local Rust test suite now exercises the
`SemanticIr::field()` present and missing lookup paths.

It does not prove semantic correctness, production readiness, complete DSL
correctness, formal correctness, benchmark performance, official benchmark
evidence, score-axis population, accepted Evidence Ledger mutation, live
provider evidence, or Level2+ evidence.

## Validation Commands

The following commands passed locally:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test lowering
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final Phase 232 gate also ran:

```sh
git diff --check
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
```

## Next Coverage Candidate

After Phase 232, `dsl/ir.rs` has no remaining missed lines in the local
coverage report. The lowest remaining non-serializer line-coverage candidate in
the current package summary is `evidence/review_ledger.rs` at `85.27%`, subject
to a fresh missing-line audit before any mutation.

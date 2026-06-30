# Phase 233 Review Ledger Coverage Notes

## State Slice

Phase 233 is the evidence review-ledger coverage tranche for
`crates/zkbench-core/src/evidence/review_ledger.rs`.

This slice is limited to additive Rust tests under `crates/zkbench-core/tests/`
and navigation/status updates under `docs/`, `README.md`, and `AGENTS.md`.

## Purpose

Phase 232 routed the next local coverage target to `evidence/review_ledger.rs`
after `dsl/ir.rs` reached `100.00%` line coverage.

The Phase 233 missing-line audit found uncovered reachable paths in:

- the default ledger constructor;
- malformed review-ledger JSON deserialization;
- empty ledger-id validation;
- sequence-number and previous-digest drift validation;
- nested review-decision validation during append;
- nested review-decision and append-preview validation during ledger
  validation.

## Implemented Coverage

Phase 233 adds focused tests to `crates/zkbench-core/tests/review_ledger.rs`:

- `review_ledger_default_and_malformed_json_paths_are_bounded`;
- `review_ledger_rejects_invalid_review_decision_before_append`;
- `review_ledger_validation_reports_identity_chain_and_nested_subject_drift`.

The tests exercise only local review-ledger metadata behavior. They do not
mutate the accepted `EvidenceLedger` and do not create accepted benchmark
evidence.

## Coverage Result

Baseline before Phase 233:

- `evidence/review_ledger.rs`: `85.23%` region / `84.21%` function /
  `85.27%` line coverage.
- `zkbench-core` package total: `91.55%` region / `87.36%` function /
  `93.23%` line coverage.

Measured after Phase 233:

- `evidence/review_ledger.rs`: `94.70%` region / `94.74%` function /
  `97.32%` line coverage.
- `zkbench-core` package total: `91.65%` region / `87.47%` function /
  `93.34%` line coverage.

## Remaining Cap

The remaining missed lines are:

- `crates/zkbench-core/src/evidence/review_ledger.rs:264-266`
- `crates/zkbench-core/src/evidence/review_ledger.rs:327-328`

Those are the digest serialization error path and the pretty-JSON
serialization wrapper error path. They are not forced in this tranche because
the public review-ledger data model is serializable through the normal API.

## Claim Boundary

This phase proves only that the local Rust test suite now exercises additional
review-ledger validation, append rejection, default construction, and malformed
JSON wrapper paths.

It does not prove semantic correctness, production readiness, complete evidence
governance correctness, accepted Evidence Ledger mutation, official benchmark
evidence, formal evidence, score-axis population, live provider evidence, or
Level2+ evidence.

## Validation Commands

The following commands passed locally:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test review_ledger
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final Phase 233 gate also ran:

```sh
git diff --check
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
```

## Next Coverage Candidate

After Phase 233, `evidence/review_ledger.rs` has only the serialization-wrapper
and digest-error cap above. The lowest remaining non-serializer line-coverage
candidate in the current package summary is
`mutation/invariant_weakening.rs` at `85.71%`, subject to a fresh missing-line
audit before any mutation.

# Phase 242 Failure Corpus Coverage Notes

## State Slice

Phase 242 is the failure-corpus coverage hardening tranche for
`crates/zkbench-core/src/soak/failure_corpus.rs`.

This slice is limited to additive Rust tests under
`crates/zkbench-core/tests/failure_corpus.rs`, this phase note, and
navigation/status updates under `README.md`, `docs/12-task-list.md`,
`docs/90-whole-codebase-validation-report.md`, and `AGENTS.md`.

## Purpose

Phase 241 routed the next local coverage target to `soak/failure_corpus.rs`
after the audit-index tranche reached `93.14%` line coverage.

Phase 242 hardens reachable failure-corpus validation paths without changing
production source, soak semantics, evidence policy, or any claim boundary.

## Implemented Coverage

Added focused local regression coverage for:

- failure-corpus index claim-boundary escalation rejection;
- empty failure-corpus entry id rejection;
- failure-corpus entry claim-boundary escalation rejection;
- failure reproduction manifest claim-boundary escalation rejection;
- valid portable artifact-reference acceptance;
- absolute artifact-reference rejection;
- parent-directory artifact-reference rejection;
- backslash artifact-reference rejection through reproduction-manifest refs.

## Coverage Result

Baseline from the Phase 241 route:

- `soak/failure_corpus.rs`: `93.89%` region / `100.00%` function /
  `86.54%` line coverage.
- `zkbench-core`: `92.50%` region / `89.02%` function / `94.26%` line
  coverage.

Measured after Phase 242:

- `soak/failure_corpus.rs`: `100.00%` region / `100.00%` function /
  `100.00%` line coverage.
- `zkbench-core`: `92.54%` region / `89.02%` function / `94.37%` line
  coverage.

## Claim Boundary

This phase proves only additional local regression coverage over failure-corpus
validation and artifact-reference validation paths.

It does not prove semantic correctness, production readiness, live backend
execution, model execution, benchmark performance, official benchmark evidence,
accepted Evidence Ledger mutation, formal evidence, score-axis population, live
provider evidence, Level2+ evidence, SOTA status, breakthrough status, or
whole-workspace 100% coverage.

## Validation Commands

The following commands passed locally before this phase was recorded:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test failure_corpus
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final validation ladder also ran:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test failure_corpus
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov report -p zkbench-core --summary-only
```

## Next Coverage Candidate

The lowest remaining non-serializer line-coverage candidate in the current
`zkbench-core` package summary is `pack/writer.rs` at `86.91%`, subject to a
fresh missing-line audit before mutation.

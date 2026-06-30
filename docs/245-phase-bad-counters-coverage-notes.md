# Phase 245 Bad Counters Coverage Notes

## State Slice

Phase 245 is the bad-counters mutation coverage hardening tranche for
`crates/zkbench-core/src/mutation/bad_counters.rs`.

This slice is limited to additive Rust tests under
`crates/zkbench-core/tests/mutation_engine.rs`, this phase note, and
navigation/status updates under `README.md`, `docs/12-task-list.md`,
`docs/90-whole-codebase-validation-report.md`, and `AGENTS.md`.

## Purpose

Phase 244 routed the next local coverage target to `mutation/bad_counters.rs`
after the external submission preflight output tranche reached `88.60%` line
coverage.

Phase 245 hardens reachable bad-counters metadata and target-scan branches
without changing production source, mutation semantics, evidence policy, or any
claim boundary.

## Implemented Coverage

Added focused local regression coverage for:

- `BadCountersPass::mutation_class`;
- skipping an accepted trace step whose transition id is absent before finding
  a later eligible counter update target.

## Coverage Result

Baseline from the Phase 244 route:

- `mutation/bad_counters.rs`: `90.65%` region / `50.00%` function /
  `87.14%` line coverage.
- `zkbench-core`: `92.72%` region / `89.31%` function / `94.50%` line
  coverage.

Measured after Phase 245:

- `mutation/bad_counters.rs`: `94.39%` region / `75.00%` function /
  `92.86%` line coverage.
- `zkbench-core`: `92.74%` region / `89.36%` function / `94.51%` line
  coverage.

## Residual Cap

Remaining misses in `bad_counters.rs` are lines `61`, `65`, and `71`.

Lines `61` and `65` are a defensive action-index drift wrapper after a target
has already been selected from the same transition. Line `71` is the fallback
match arm for a selected action that is neither `AddAssign` nor `SubAssign`,
which is unreachable through the current `bad_counter_action` selector. Phase
245 does not add test-only hooks or production source changes to force those
branches.

## Claim Boundary

This phase proves only additional local regression coverage over bad-counters
mutation metadata and target selection.

It does not prove semantic correctness, production readiness, live backend
execution, model execution, benchmark performance, official benchmark evidence,
accepted Evidence Ledger mutation, formal evidence, score-axis population, live
provider evidence, Level2+ evidence, SOTA status, breakthrough status, or
whole-workspace 100% coverage.

## Validation Commands

The following commands passed locally before this phase was recorded:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test mutation_engine
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final validation ladder also ran:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test mutation_engine
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov report -p zkbench-core --summary-only
```

## Next Coverage Candidate

The lowest remaining non-serializer line-coverage candidate in the current
`zkbench-core` package summary is `evidence/official_submission_output.rs` at
`87.45%`, subject to a fresh missing-line audit before mutation.

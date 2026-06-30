# Phase 243 Pack Writer Coverage Notes

## State Slice

Phase 243 is the benchmark-pack writer coverage hardening tranche for
`crates/zkbench-core/src/pack/writer.rs`.

This slice is limited to additive Rust tests under
`crates/zkbench-core/tests/benchmark_pack.rs`, this phase note, and
navigation/status updates under `README.md`, `docs/12-task-list.md`,
`docs/90-whole-codebase-validation-report.md`, and `AGENTS.md`.

## Purpose

Phase 242 routed the next local coverage target to `pack/writer.rs` after the
failure-corpus tranche reached `100.00%` line coverage.

Phase 243 hardens reachable benchmark-pack writer validation and filesystem
failure paths without changing production source, pack semantics, evidence
policy, or any claim boundary.

## Implemented Coverage

Added focused local regression coverage for:

- file-root rejection before pack materialization;
- root parent create-dir conflict reporting;
- README path conflict reporting;
- dynamic generated-instance id path-drift rejection;
- dynamic mutated-instance id path-drift rejection;
- dynamic replay-manifest id path-drift rejection;
- dynamic replay-result id path-drift rejection;
- generated artifact parent conflict reporting;
- mutated artifact parent conflict reporting;
- replay-manifest artifact parent conflict reporting;
- replay-result artifact parent conflict reporting;
- evidence-ledger artifact parent conflict reporting;
- score-report artifact parent conflict reporting.

## Coverage Result

Baseline from the Phase 242 route:

- `pack/writer.rs`: `82.96%` region / `80.56%` function / `86.91%` line
  coverage.
- `zkbench-core`: `92.54%` region / `89.02%` function / `94.37%` line
  coverage.

Measured after Phase 243:

- `pack/writer.rs`: `90.86%` region / `88.89%` function / `92.62%` line
  coverage.
- `zkbench-core`: `92.66%` region / `89.19%` function / `94.44%` line
  coverage.

## Residual Cap

Remaining misses in `pack/writer.rs` are lines `295`, `296`, `307`, `308`,
`358`, `366`, `367`, `373`, and `374`.

The first four are serialization-error wrappers around currently serializable
pack-manifest and JSON artifact values. The remaining misses are low-level file
write or read-dir operating-system error wrappers. Phase 243 does not add
test-only serializer hooks, fake non-serializable data, permission-sensitive
tests, or platform-fragile filesystem tricks to force those branches.

## Claim Boundary

This phase proves only additional local regression coverage over benchmark-pack
writer validation and local filesystem failure paths.

It does not prove semantic correctness, production readiness, live backend
execution, model execution, benchmark performance, official benchmark evidence,
accepted Evidence Ledger mutation, formal evidence, score-axis population, live
provider evidence, Level2+ evidence, SOTA status, breakthrough status, or
whole-workspace 100% coverage.

## Validation Commands

The following commands passed locally before this phase was recorded:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test benchmark_pack
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final validation ladder also ran:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test benchmark_pack
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov report -p zkbench-core --summary-only
```

## Next Coverage Candidate

The lowest remaining non-serializer line-coverage candidate in the current
`zkbench-core` package summary is
`evidence/external_submission_preflight_output.rs` at `87.03%`, subject to a
fresh missing-line audit before mutation.

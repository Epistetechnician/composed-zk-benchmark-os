# Phase 244 External Submission Preflight Output Coverage Notes

## State Slice

Phase 244 is the external replay submission preflight output coverage hardening
tranche for
`crates/zkbench-core/src/evidence/external_submission_preflight_output.rs`.

This slice is limited to additive Rust tests under
`crates/zkbench-core/tests/phase_w_promotion_preflight.rs`, this phase note,
and navigation/status updates under `README.md`, `docs/12-task-list.md`,
`docs/90-whole-codebase-validation-report.md`, and `AGENTS.md`.

## Purpose

Phase 243 routed the next local coverage target to
`evidence/external_submission_preflight_output.rs` after the pack-writer tranche
reached `92.62%` line coverage.

Phase 244 hardens reachable external replay preflight output readback
validation branches without changing production source, output bundle
semantics, evidence policy, or any claim boundary.

## Implemented Coverage

Added focused local regression coverage for:

- stale input-manifest digest sidecar rejection;
- stale preflight-report JSON digest sidecar rejection;
- stale preflight-report Markdown digest sidecar rejection;
- stale redaction-report digest sidecar rejection;
- stale submission-package digest-summary sidecar rejection;
- stale non-claims digest sidecar rejection;
- malformed redaction-report JSON deserialization context;
- malformed submission-package digest-summary JSON deserialization context.

## Coverage Result

Baseline from the Phase 243 route:

- `evidence/external_submission_preflight_output.rs`: `81.89%` region /
  `74.19%` function / `87.03%` line coverage.
- `zkbench-core`: `92.66%` region / `89.19%` function / `94.44%` line
  coverage.

Measured after Phase 244:

- `evidence/external_submission_preflight_output.rs`: `83.45%` region /
  `77.42%` function / `88.60%` line coverage.
- `zkbench-core`: `92.72%` region / `89.31%` function / `94.50%` line
  coverage.

## Residual Cap

Remaining misses include output-root file and non-empty overwrite guards,
write-side operating-system failure wrappers, serialization-error wrappers for
currently serializable local output data, private relative-path rejection
branches over constant paths, directory iteration OS wrappers, symlink
rejection branches, current-directory error wrappers, and path-normalization
platform branches.

Phase 244 does not add test-only serializer hooks, fake non-serializable data,
permission-sensitive tests, platform-fragile filesystem tricks, or production
source changes to force those branches.

## Claim Boundary

This phase proves only additional local regression coverage over external
replay submission preflight output readback validation.

It does not prove semantic correctness, production readiness, live backend
execution, model execution, benchmark performance, official benchmark evidence,
accepted Evidence Ledger mutation, formal evidence, score-axis population, live
provider evidence, Level2+ evidence, SOTA status, breakthrough status, or
whole-workspace 100% coverage.

## Validation Commands

The following commands passed locally before this phase was recorded:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test phase_w_promotion_preflight
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final validation ladder also ran:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test phase_w_promotion_preflight
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov report -p zkbench-core --summary-only
```

## Next Coverage Candidate

The lowest remaining non-serializer line-coverage candidate in the current
`zkbench-core` package summary is `mutation/bad_counters.rs` at `87.14%`,
subject to a fresh missing-line audit before mutation.

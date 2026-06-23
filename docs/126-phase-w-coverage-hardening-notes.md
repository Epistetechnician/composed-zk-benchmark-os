# Phase 126 Phase W Coverage Hardening Notes

Status: complete for local test coverage hardening.

## State Slice

This phase touches only focused Phase W external replay preflight output tests,
documentation navigation, and the whole-codebase validation report.

Code changes are limited to
`crates/zkbench-core/tests/phase_w_promotion_preflight.rs`.

## Purpose

Phase 126 hardens the Phase 125 local output-root implementation by exercising
additional fail-closed paths that were not covered by the initial output
plumbing tests.

This is coverage and regression hardening only. It is not live provider
evidence, not external replay evidence, not official benchmark evidence, not
an accepted Evidence Ledger mutation, not Level2+ evidence, not semantic
correctness, and not 100% coverage.

## Added Coverage

The focused tests now cover:

- existing-file output-root rejection;
- repository-root overlap rejection;
- parent-directory output-root rejection;
- Unix symlink output-root rejection;
- digest-consistent malformed JSON rejection;
- digest-consistent non-UTF-8 materialized file rejection;
- digest-consistent report Markdown drift rejection;
- digest-consistent input-manifest declared-file drift rejection;
- digest-consistent submission-package digest summary drift rejection; and
- digest-consistent non-claims Markdown drift rejection.

The local focused coverage run for
`cargo llvm-cov -p zkbench-core --test phase_w_promotion_preflight --summary-only`
reported `external_submission_preflight_output.rs` at `82.11%` line coverage.
The previous Phase 125 all-feature workspace run reported that file at
`77.91%` line coverage.

Focused-test coverage is not the same as all-feature workspace coverage. The
whole-codebase report records the full workspace number from the final
validation run.

## Anti-Goals

This phase does not add Rust production code, new public APIs, generated
artifacts, committed output bundles, package runtime files, command-line tools,
network access, credentials, live Phala calls, DCAP/PCCS/JWKS/TLS execution,
external replay, official endpoint submission, accepted Evidence Ledger
mutation, score-axis population, ZK backend performance claims, formal evidence,
SOTA claims, production-readiness claims, or semantic-correctness claims.

## Validation

Required validation for this phase:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test phase_w_promotion_preflight
cargo test -p zkbench-core --test phase_w_accepted_ledger_append
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```


# Phase 135 zk-Harness Validation Coverage Notes

Status: complete for local zk-Harness dry-run validation coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/zk_harness_dry_run_plan.rs`
- `docs/135-phase-zk-harness-validation-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Scope

Phase 135 improves local regression coverage over the existing
`zkbench-core` zk-Harness dry-run validation surface. It adds focused tests for
fail-closed validation issue paths over empty identifiers, unsupported-feature
warnings, metric mapping drift, inert command drift, relative-path rejection,
artifact mapping drift, family label drift, trace local-only drift, and
forbidden benchmark-evidence language.

The phase changes no production Rust API and adds no new runtime path.

## Validation

Run from repository root:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test zk_harness_dry_run_plan
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```

The Phase 135 coverage pass reported:

- `zkbench-core/src/adapters/zk_harness/validation.rs`: `94.87%` regions,
  `100.00%` functions, `93.45%` lines.
- Workspace total: `86.09%` regions, `83.22%` functions, `84.43%` lines.

The previous recorded Phase 134/133 workspace pass reported `85.94%` regions,
`83.17%` functions, and `84.22%` lines. The previous targeted `validation.rs`
line coverage was `67.69%`.

## Claim Boundary

This is local test instrumentation only. It is not live external backend
execution, zk-Harness execution, official benchmark evidence, official
submission, accepted Evidence Ledger mutation, external replay execution,
generated benchmark artifact creation, score-axis population, Level2+
evidence, semantic correctness, production readiness, SOTA evidence, broad
leaderboard evidence, or 100% coverage.

# Phase 133 zk-Harness Export Coverage Notes

Status: complete for local zk-Harness export helper coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/zk_harness_pack_mapping.rs`
- `docs/133-phase-zk-harness-export-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Scope

Phase 133 improves local regression coverage over the existing
`zkbench-core` zk-Harness dry-run export helper surface. It adds tests for the
direct pack export helper, dry-run plan JSON serialization and deserialization,
adapter manifest JSON serialization and deserialization, and malformed JSON
deserialization rejection for both helper families.

The phase changes no production Rust API and adds no new runtime path.

## Validation

Run from repository root:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test zk_harness_pack_mapping
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```

The Phase 133 coverage pass reported:

- `zkbench-core/src/adapters/zk_harness/export.rs`: `79.37%` regions,
  `80.00%` functions, `78.26%` lines.
- Workspace total: `85.94%` regions, `83.17%` functions, `84.22%` lines.

The previous recorded Phase 132 workspace pass reported `85.91%` regions,
`83.08%` functions, and `84.19%` lines. The previous targeted
`export.rs` line coverage was `63.04%`.

## Claim Boundary

This is local test instrumentation only. It is not live external backend
execution, zk-Harness execution, official benchmark evidence, official
submission, accepted Evidence Ledger mutation, external replay execution,
generated benchmark artifact creation, score-axis population, Level2+
evidence, semantic correctness, production readiness, SOTA evidence, broad
leaderboard evidence, or 100% coverage.

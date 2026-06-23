# Phase 132 Local JSON Adapter Coverage Notes

Status: complete for local JSON adapter coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/local_json_adapter.rs`
- `docs/132-phase-local-json-adapter-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Scope

Phase 132 improves local regression coverage over the existing
`zkbench-core` local JSON adapter. It adds tests for fail-closed claim-boundary
rejection, adapter-id mismatch rejection, missing generated and mutated subject
payload rejection, selected-trace drift rejection, mock replay mode without a
mock command, mock capability-gap and inconclusive status mapping, legacy
`BackendAdapter::prepare_replay` manifest behavior, and
`BackendAdapter::normalize_result` empty-evidence rejection.

The phase changes no production Rust API and adds no new runtime path.

## Validation

Run from repository root:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test local_json_adapter
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```

The Phase 132 coverage pass reported:

- `zkbench-core/src/adapters/local_json.rs`: `95.56%` regions, `96.67%`
  functions, `96.44%` lines.
- Workspace total: `85.91%` regions, `83.08%` functions, `84.19%` lines.

The previous recorded Phase 131 workspace pass reported `85.68%` regions,
`82.68%` functions, and `83.88%` lines. The previous targeted
`local_json.rs` line coverage was `70.33%`.

## Claim Boundary

This is local test instrumentation only. It is not live external backend
execution, official benchmark evidence, official submission, accepted Evidence
Ledger mutation, external replay execution, generated benchmark artifact
creation, score-axis population, Level2+ evidence, semantic correctness,
production readiness, SOTA evidence, broad leaderboard evidence, or 100%
coverage.

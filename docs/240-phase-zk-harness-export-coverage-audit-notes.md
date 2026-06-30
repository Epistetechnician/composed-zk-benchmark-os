# Phase 240 zk-Harness Export Coverage Audit Notes

## State Slice

Phase 240 is the zk-Harness export coverage audit tranche for
`crates/zkbench-core/src/adapters/zk_harness/export.rs`.

This slice is limited to documentation/status updates under `docs/`,
`README.md`, and `AGENTS.md`. It intentionally makes no Rust source or test
changes.

## Purpose

Phase 239 routed the next local coverage target to
`adapters/zk_harness/export.rs` after `evidence/ledger.rs` reached `96.04%`
line coverage.

The Phase 240 missing-line audit found the only missed lines in
`adapters/zk_harness/export.rs` are serialization error wrappers:

- `serialize_zk_harness_manifest_json` map-error closure;
- `serialize_zk_harness_dry_run_plan_json` map-error closure.

## Audit Decision

No code mutation is justified in this tranche. The current manifest and dry-run
plan types are serializable through their public constructors and validators,
so forcing these closures would require fake non-serializable data, production
test hooks, or serializer indirection that would weaken the codebase for a
coverage-only gain.

The existing local tests already cover:

- direct dry-run export from a valid local benchmark pack;
- the public build-helper delegation path;
- invalid source-pack rejection through the dry-run validator;
- manifest and dry-run plan JSON round trips;
- malformed manifest and dry-run plan JSON deserialization failures.

## Coverage State

Measured during Phase 240 audit:

- `adapters/zk_harness/export.rs`: `80.95%` region / `80.00%` function /
  `86.96%` line coverage.
- `zkbench-core` package total after Phase 239: `91.99%` region / `88.17%`
  function / `93.71%` line coverage.

## Claim Boundary

This phase proves only that the remaining missed lines in
`adapters/zk_harness/export.rs` were audited and classified as not worth
forcing under the current public data model.

It does not prove semantic correctness, production readiness, live zk-Harness
execution, benchmark performance, official benchmark evidence, accepted
Evidence Ledger mutation, formal evidence, score-axis population, live provider
evidence, Level2+ evidence, SOTA status, or breakthrough status.

## Validation Commands

The following commands passed locally before this audit was recorded:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test evidence_ledger
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

## Next Coverage Candidate

After skipping unsafe forcing in `adapters/zk_harness/export.rs`, the next
lowest remaining non-serializer line-coverage candidate in the current package
summary is `audit_index.rs` at `86.49%`, subject to a fresh missing-line audit
before any mutation.

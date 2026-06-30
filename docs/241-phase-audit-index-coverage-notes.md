# Phase 241 Audit Index Coverage Notes

## State Slice

Phase 241 is the audit-index coverage hardening tranche for
`crates/zkbench-core/src/audit_index.rs`.

This slice is limited to additive Rust tests under
`crates/zkbench-core/tests/phase_s_audit_index_ergonomics.rs` and
`crates/zkbench-core/tests/phase_t_cross_bundle_audit_index.rs`, this phase
note, and navigation/status updates under `README.md`, `docs/12-task-list.md`,
`docs/90-whole-codebase-validation-report.md`, and `AGENTS.md`.

## Purpose

Phase 240 routed the next local coverage target to `audit_index.rs` after the
zk-Harness export audit classified its remaining missed lines as unsafe to
force under the current public data model.

Phase 241 hardens reachable Phase S and Phase T audit-index paths without
changing production source, audit-index semantics, evidence policy, or any
claim boundary.

## Implemented Coverage

Added focused local regression coverage for:

- Phase S ergonomics filter, sort, and group combinations across claim
  boundary, input kind, failed-readiness, and local-warning visibility paths;
- Phase S output readback failure paths for invalid output roots, invalid
  protected paths, file roots, non-UTF8 digest sidecars, non-UTF8 selected-view
  JSON, non-UTF8 Markdown, and digest-consistent Markdown/view drift;
- Phase T cross-bundle sorting and grouping across index id, indexed pack id,
  local-warning visibility, failed-readiness visibility, and output claim
  boundary;
- Phase T hidden-local-warning and limitation-label mismatch signal paths;
- Phase T empty and duplicate source-id validation paths;
- Phase T output readback failure paths for file roots, non-UTF8 digest
  sidecars, non-UTF8 selected-view JSON, non-UTF8 Markdown, and
  digest-consistent Markdown/view drift.

## Coverage Result

Baseline from the Phase 240 route:

- `audit_index.rs`: `85.51%` region / `74.07%` function / `86.49%` line
  coverage.
- `zkbench-core`: `91.99%` region / `88.17%` function / `93.71%` line
  coverage.

Measured after Phase 241:

- `audit_index.rs`: `91.14%` region / `85.19%` function / `93.14%` line
  coverage.
- `zkbench-core`: `92.50%` region / `89.02%` function / `94.26%` line
  coverage.

## Residual Gap

The remaining `audit_index.rs` misses are mostly serialization-error wrappers,
overwrite mismatch branches that require a deterministic readback to succeed
while the supplied deterministic view differs, filesystem error edges, and
validation branches that need impossible digest or claim-boundary states under
the current public constructors.

This phase does not force those paths with production test hooks, fake
non-serializable data, coverage suppression, or dead code.

## Claim Boundary

This phase proves only additional local regression coverage over audit-index
presentation, validation, and materialized readback paths.

It does not prove semantic correctness, production readiness, live backend
execution, model execution, benchmark performance, official benchmark evidence,
accepted Evidence Ledger mutation, formal evidence, score-axis population, live
provider evidence, Level2+ evidence, SOTA status, breakthrough status, or 100%
coverage.

## Validation Commands

The following commands passed locally before this phase was recorded:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test phase_s_audit_index_ergonomics
cargo test -p zkbench-core --test phase_t_cross_bundle_audit_index
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final validation ladder also ran:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test phase_s_audit_index_ergonomics
cargo test -p zkbench-core --test phase_t_cross_bundle_audit_index
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov report -p zkbench-core --summary-only
```

## Next Coverage Candidate

The lowest remaining non-serializer line-coverage candidate in the current
`zkbench-core` package summary is `soak/failure_corpus.rs` at `86.54%`, subject
to a fresh missing-line audit before mutation.

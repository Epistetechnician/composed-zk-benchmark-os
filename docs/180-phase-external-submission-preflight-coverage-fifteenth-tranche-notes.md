# Phase 180 External Submission Preflight Coverage Fifteenth Tranche Notes

State slice: `phase-180-external-submission-preflight-coverage`.

## Claim

Phase 180 continues the bounded local coverage campaign by hardening the
external replay / official-submission preflight validation surface in
`crates/zkbench-core`. The tranche adds focused local regression tests for
existing public contracts only. It changes no production Rust source.

## Implemented Coverage

- Aggregate request-shape rejection paths for empty identities, missing replay
  provenance, invalid source digests, missing redaction policy, unresolved
  markers, missing nonclaims, and forbidden claim text.
- Accepted-ledger path rejection for missing files, directories, malformed JSON,
  and parent-directory components.
- Future output-root safety rejection for empty roots, existing files,
  non-empty directories without overwrite, parent-directory components, and
  explicit overwrite acceptance for already non-empty local roots.
- Digest-consistent official-submission package validation-report drift for
  ledger path, ledger count, accepted evidence id, and validation-report digest
  mismatch.
- Malformed external replay submission preflight report JSON deserialization
  context.
- Report Markdown fail-closed behavior when required report nonclaims are
  removed.

## Coverage Result

Baseline target-file coverage before this tranche:

```text
crates/zkbench-core/src/evidence/external_submission_preflight.rs
Regions:   76.70%
Functions: 85.00%
Lines:     72.63%
```

Post-tranche target-file coverage:

```text
crates/zkbench-core/src/evidence/external_submission_preflight.rs
Regions:   88.50%
Functions: 90.00%
Lines:     89.02%
```

Post-tranche `zkbench-core` package coverage:

```text
Regions:   86.59%
Functions: 82.29%
Lines:     86.45%
```

Post-tranche workspace coverage:

```text
Regions:   89.48%
Functions: 85.79%
Lines:     88.95%
```

The next package coverage floor after this tranche is
`crates/zkbench-core/src/soak/shard.rs` at `73.55%` line coverage.

## Validation

```sh
cargo test -p zkbench-core --test phase_180_external_submission_preflight_coverage
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

The full gate set for the tranche is recorded in
`docs/90-whole-codebase-validation-report.md`.

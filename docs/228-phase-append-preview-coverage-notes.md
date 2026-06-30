# Phase 228 Append Preview Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/evidence_append_preview.rs`
- `docs/228-phase-append-preview-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, append-preview
semantics, candidate semantics, or external replay behavior changed.

## Purpose

After Phase 227, the next visible low non-serializer surface routed by the
local package coverage table was
`crates/zkbench-core/src/evidence/append_preview.rs` at `83.87%` line coverage.

This tranche adds focused regression coverage for reachable local append
preview creation rejection, validation issue paths, forbidden claim language,
and malformed preview JSON handling.

## Coverage Added

The added tests cover:

- append preview creation rejecting an invalid evidence-record candidate before
  projection;
- validation issue paths for empty preview ids and empty source candidate ids;
- preview artifact claim-boundary elevation rejection;
- proposed append-entry Level2+ claim-boundary rejection;
- forbidden claim text in preview notes;
- forbidden claim text in transaction-preview notes;
- malformed preview JSON deserialization failure context.

These paths are exercised through the public local append-preview APIs. They do
not append to an accepted Evidence Ledger, run backend adapters, generate
official benchmark results, run external replay, or populate score axes.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.15%` region coverage, `86.73%` function execution, and
  `92.66%` line coverage;
- `evidence/append_preview.rs`: `88.79%` region coverage, `88.24%` function
  execution, and `83.87%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.22%` region coverage, `86.79%` function execution, and
  `92.75%` line coverage;
- `evidence/append_preview.rs`: `96.41%` region coverage, `94.12%` function
  execution, and `94.47%` line coverage.

Remaining misses are limited to currently unforced local branch combinations
inside append-preview projection and serialization helpers. They are not forced
in this tranche.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer surface is `pack/readiness.rs` at
`86.24%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
append-preview semantics, candidate semantics, external replay behavior,
endpoint submission behavior, credential handling, accepted Evidence Ledger
policy, formal evidence, benchmark evidence, score-axis population, generated
artifact materialization, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

## Validation

Validation passed for this tranche:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test evidence_append_preview
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

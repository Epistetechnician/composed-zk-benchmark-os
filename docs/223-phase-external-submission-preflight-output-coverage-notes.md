# Phase 223 External Submission Preflight Output Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/phase_w_promotion_preflight.rs`
- `docs/223-phase-external-submission-preflight-output-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, external replay
behavior, endpoint submission behavior, or credential handling changed.

## Purpose

After Phase 222, the next visible low non-serializer public surface in the
`zkbench-core` package coverage table was
`crates/zkbench-core/src/evidence/external_submission_preflight_output.rs` at
`82.11%` line coverage.

This tranche adds focused regression coverage for reachable local output-root,
readback, digest-sidecar, redaction, and claim-boundary rejection behavior.

## Coverage Added

The added tests cover:

- non-empty output roots rejecting without explicit overwrite;
- readback rejecting file roots that are not directories;
- matching overwrite using a persisted preflight request that already opted
  into overwrite;
- redaction policy wording that uses `not retain` instead of `exclude`;
- tampered preflight reports with invalid validation state;
- tampered preflight reports that claim forbidden side effects;
- tampered preflight reports missing required non-claim labels;
- tampered input manifests claiming forbidden side effects;
- input-manifest report-id drift;
- input-manifest request-id drift;
- rendered raw-retention markers in report and non-claims Markdown;
- non-UTF-8 digest sidecars.

These paths are exercised through the public local output and readback APIs.
They do not run external replay, submit to any endpoint, read credentials,
mutate accepted ledgers, or populate score axes.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.56%` region coverage, `86.10%` function execution, and
  `91.76%` line coverage;
- `evidence/external_submission_preflight_output.rs`: `79.84%` region
  coverage, `72.58%` function execution, and `82.11%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.64%` region coverage, `86.16%` function execution, and
  `91.93%` line coverage;
- `evidence/external_submission_preflight_output.rs`: `81.89%` region
  coverage, `74.19%` function execution, and `87.03%` line coverage.

Remaining misses are mostly filesystem error closures, serde serialization
error closures for infallible in-memory structs, portable-path helper branches
not reachable through public constants, and platform-specific path component
branches. They are not forced in this tranche.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer public surface is `report_bundle.rs`
at `82.30%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
external replay behavior, endpoint submission behavior, credential handling,
accepted Evidence Ledger policy, formal evidence, benchmark evidence,
score-axis population, generated artifact materialization, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable branch forcing, or
whole-workspace 100% coverage claims.

## Validation

Validation passed for this tranche:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test phase_w_promotion_preflight
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

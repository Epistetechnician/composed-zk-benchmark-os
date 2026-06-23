# Phase W Official Submission Package Materialization Implementation Notes

## Status

Implemented for local official-submission package output plumbing.

This phase implements the narrow local output-root surface authorized by
`docs/120-phase-w-official-submission-package-materialization-boundary-spec.md`.

## State Slice

This slice is limited to:

- `crates/zkbench-core/src/evidence/official_submission_output.rs`
- `crates/zkbench-core/src/evidence/mod.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_w_promotion_preflight.rs`
- This implementation note and navigation/status updates.

## Implemented Surface

The implementation adds:

- `OfficialSubmissionPackageOutputRequest`
- `OfficialSubmissionPackageOutputValidationReport`
- `OfficialSubmissionPackageOutput`
- `write_official_submission_package_outputs`
- `read_official_submission_package_outputs`

The output path:

- Requires an explicit caller-owned output root.
- Requires an existing accepted Evidence Ledger JSON file.
- Rejects parent-directory components.
- Rejects protected-path overlap.
- Rejects symlink output roots, symlink children, and symlink ledger paths.
- Loads and validates the accepted ledger before materializing package files.
- Requires every package accepted-evidence id to exist in that accepted ledger
  by sequence number or entry digest.
- Requires `submits_to_official_endpoint == false`.
- Writes exactly three package payload files and three digest sidecars under
  `official-submission-package/`.
- Rejects stale digest sidecars, unexpected files, partial bundles, and package
  drift on overwrite.
- Emits a validation report with explicit false side-effect flags for official
  submission, endpoint submission, and score-axis population.

## Tests

Focused tests cover:

- Writing and reading the declared package files.
- Rejecting a missing accepted ledger.
- Rejecting package metadata whose accepted-evidence id is absent from the
  accepted ledger.
- Rejecting external-submission flags.
- Rejecting protected-path overlap.
- Rejecting overwrite package drift.
- Rejecting stale digest sidecars and unexpected files.
- Source-scan boundaries proving no endpoint runtime, network, process,
  credential, environment-variable, or score-axis population path exists.

## Claim Boundary

The materialized package is local review material only. It is not an official
benchmark submission. It does not call an official endpoint. It does not create
official accepted evidence. It does not run external replay. It does not
populate score axes. It is not Level2+ evidence, ZK backend performance
evidence, production readiness, or semantic correctness evidence.

## Remaining Gaps

No committed generated official-submission package exists. No official
benchmark submission exists. No external replay evidence exists. No Level2+
evidence exists. No score-axis population exists. No accepted Evidence Ledger
promotion beyond local Level1-or-below ledger materialization exists.

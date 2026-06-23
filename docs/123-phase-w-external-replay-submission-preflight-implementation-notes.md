# Phase W External Replay Submission Preflight Implementation Notes

## Status

Implemented for local external replay and official-submission promotion
preflight metadata.

This phase implements the narrow local preflight surface authorized by
`docs/122-phase-w-external-replay-official-submission-boundary-spec.md`.

## State Slice

This slice is limited to:

- `crates/zkbench-core/src/evidence/external_submission_preflight.rs`
- `crates/zkbench-core/src/evidence/mod.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_w_promotion_preflight.rs`
- This implementation note and navigation/status updates.

## Implemented Surface

The implementation adds:

- `ExternalReplaySubmissionPreflightRequest`
- `ExternalReplaySubmissionPreflightReport`
- `ExternalReplaySubmissionPreflightValidation`
- `ExternalReplayBenchmarkTarget`
- `build_external_replay_submission_preflight_report`
- `validate_external_replay_submission_preflight_request`
- deterministic JSON, Markdown, and digest helpers
- required non-claim labels for the external replay / submission preflight

The local preflight path:

- Requires an accepted Evidence Ledger JSON path.
- Requires a valid Phase 121 package output root.
- Checks expected package metadata and validation-report digests.
- Requires non-secret benchmark target metadata.
- Requires external replay provenance and source artifact digests.
- Requires explicit operator acknowledgement.
- Validates a future output root without writing it.
- Requires a redaction policy.
- Rejects local-only evidence promotion.
- Rejects score-axis population.
- Rejects official endpoint submission attempts.
- Rejects unresolved quarantine and blocking markers.
- Emits a report whose external replay, endpoint submission, accepted-ledger
  mutation, generated-artifact write, and score-axis flags are all false.

## Tests

Focused tests cover:

- Valid local preflight over a local accepted ledger plus Phase 121 package
  output.
- Deterministic JSON, Markdown, and digest behavior.
- Package digest drift rejection.
- Missing operator acknowledgement rejection.
- Local-only promotion and score-axis rejection.
- Endpoint-attempt and protected-root rejection.
- Source scans proving no process, network, credential, endpoint submission, or
  score-axis population runtime surface exists.

## Claim Boundary

The preflight report is local metadata only. It is not external replay evidence.
It is not an official benchmark submission. It does not call endpoints. It does
not use credentials. It does not mutate an accepted Evidence Ledger. It does
not write generated artifacts. It does not populate score axes. It is not
Level2+ evidence, ZK backend performance evidence, production readiness, or
semantic correctness evidence.

## Remaining Gaps

No external replay was run. No official endpoint was called. No credentials
were used. No generated artifact root was materialized. No accepted Evidence
Ledger mutation beyond local Level1-or-below materialization exists. No
score-axis population or Level2+ evidence exists.

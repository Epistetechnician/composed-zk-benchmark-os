# Phase W External Replay Preflight Output Implementation Notes

Status: implemented for local review metadata output plumbing.

This phase implements the narrow filesystem surface authorized by
`docs/124-phase-w-external-replay-preflight-output-boundary-spec.md`.

## State Slice

Changed files:

- `crates/zkbench-core/src/evidence/external_submission_preflight_output.rs`
- `crates/zkbench-core/src/evidence/mod.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_w_promotion_preflight.rs`
- `docs/125-phase-w-external-replay-preflight-output-implementation-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, package runtime, CLI/UI, credential path, network path,
accepted Evidence Ledger fixture, committed generated bundle, score report, or
official endpoint surface was added.

## Implemented Surface

The new `external_submission_preflight_output` module adds:

- `ExternalReplaySubmissionPreflightOutputRequest`
- `ExternalReplaySubmissionPreflightInputManifest`
- `ExternalReplaySubmissionPreflightRedactionReport`
- `ExternalReplaySubmissionPackageDigestSummary`
- `ExternalReplaySubmissionPreflightOutput`
- declared `external-replay-submission/*` relative paths and digest sidecars
- `write_external_replay_submission_preflight_outputs`
- `read_external_replay_submission_preflight_outputs`

The writer requires a valid Phase 123 preflight request and matching valid
preflight report. It writes deterministic local review metadata only:

- input manifest JSON
- preflight report JSON
- preflight report Markdown
- redaction report JSON
- submission package digest summary JSON
- non-claims Markdown
- SHA-256 sidecars for every declared file

The reader validates declared-file-only output, digest sidecars, report
Markdown consistency, input-manifest consistency, redaction flags, non-claims,
and package digest summary consistency.

## Fail-Closed Checks

The implementation rejects:

- request/report drift;
- invalid preflight request or invalid preflight report;
- external replay, endpoint submission, accepted-ledger mutation, generated
  benchmark artifact, or score-axis side-effect flags;
- incomplete redaction policies;
- repository-root and protected-path overlap;
- parent-directory path components;
- symlink roots and bundle files;
- non-empty output roots without explicit overwrite;
- repair overwrite when the existing bundle does not match supplied inputs;
- partial, unexpected, stale-digest, or tampered outputs;
- raw-material retention in the redaction report.

## Validation

Focused tests cover valid output materialization and readback, request/report
drift, side-effect rejection, unsafe/protected roots, overwrite drift, stale
digests, unexpected files, raw-retention rejection, incomplete redaction
policy rejection, and source scans for no live runtime surface.

## Claim Boundary

The materialized output bundle is local review metadata only. It is not
external replay evidence. It is not official benchmark evidence. It is not
accepted Evidence Ledger mutation. It is not score-axis population. It is not
Level2+ evidence. It is not ZK backend performance evidence. It is not
proof-system soundness evidence. It is not semantic correctness evidence. It
is not production readiness.

No external replay was run. No official endpoint was called. No credentials
were read. No accepted Evidence Ledger was mutated by this output writer. No
score axes were populated.

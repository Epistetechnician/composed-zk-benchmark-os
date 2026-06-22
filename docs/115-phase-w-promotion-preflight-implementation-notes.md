# Phase W Promotion Preflight Implementation Notes

Status: implemented as inert local metadata.

This phase implements the narrow Phase W preflight surface authorized by
`docs/114-phase-w-promotion-preflight-boundary-spec.md`. It adds validation and
rendering helpers that make accepted-evidence promotion and official-submission
preconditions explicit without mutating the accepted Evidence Ledger or creating
an official submission.

## State Slice

This implementation touched:

- `crates/zkbench-core/src/evidence/promotion_preflight.rs`
- `crates/zkbench-core/src/evidence/mod.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_w_promotion_preflight.rs`
- `docs/115-phase-w-promotion-preflight-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Implemented Surface

The code adds:

- `ReviewedPromotionPreflightRequest`
- `ReviewedPromotionPreflightReport`
- `ReviewedPromotionPreflightValidation`
- `ReviewedPromotionSourceSummary`
- required Phase W non-claim labels
- deterministic report JSON serialization
- deterministic report Markdown rendering
- deterministic report digesting
- `OfficialSubmissionPackageMetadata`
- official-submission package metadata validation
- deterministic official-submission package metadata serialization, digesting,
  and Markdown rendering

## Fail-Closed Rules

Promotion preflight rejects:

- stale append-preview ledger tips;
- invalid candidates;
- invalid or mutating append previews;
- candidate/preview mismatches;
- missing human review approval;
- missing source artifact digests;
- unresolved quarantine or blocking markers;
- missing external replay provenance for Level2+ promotion;
- local-only promotion above the reviewed candidate boundary;
- local soak telemetry as ZK backend performance evidence;
- score-axis population without matching accepted external/reproducible
  evidence;
- official-submission package metadata before accepted evidence ids exist;
- forbidden official, formal, soundness, broad leaderboard, or performance
  claim text.

Official-submission package metadata validation rejects missing accepted
evidence ids, missing external replay provenance, missing artifact digests,
missing required non-claims, forbidden claim text, and any attempted submission
to an external official endpoint.

## Claim Boundary

All preflight reports are `Level0DesignNote` metadata. They are not accepted
evidence, do not mutate `EvidenceLedger`, do not create official submissions,
do not run external replay, do not create benchmark outputs, and do not populate
score axes.

Official-submission package metadata is still metadata only. Even when accepted
evidence ids are present, it does not submit to any official endpoint.

## Validation

Focused tests cover:

- valid metadata-only preflight report generation;
- deterministic report digesting;
- report JSON round trip;
- report Markdown rendering;
- stale ledger-tip rejection;
- local-only Level2 promotion rejection;
- missing human review rejection;
- score-axis population rejection;
- official-submission request rejection before accepted evidence;
- official-submission package metadata validation after accepted evidence ids;
- source-scan boundaries proving no mutation, process, network, or submitter
  surface was introduced.

# Phase W External Replay Official Submission Boundary Spec

## Status

Docs-first boundary for a future external replay and official-submission
promotion path.

This boundary does not authorize implementation code. It does not run external
replay, call a benchmark endpoint, use credentials, create generated artifacts,
populate score axes, mutate accepted Evidence Ledgers, or create Level2+
evidence.

## State Slice

This docs-first phase may touch only:

- `docs/122-phase-w-external-replay-official-submission-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No Rust source, tests, Cargo metadata, generated benchmark artifact,
official-submission package output, accepted Evidence Ledger JSON file, score
report, package runtime file, CLI/UI surface, credential path, network path,
external replay runner, or official endpoint is changed by this phase.

## Purpose

Phase 119 can materialize a guarded local accepted Evidence Ledger JSON file.
Phase 121 can materialize a digest-bound local official-submission package from
valid package metadata plus an accepted ledger JSON file.

The remaining promotion gap is not another local package writer. It is the
boundary between local reviewed material and future external replay or official
submission. Phase 122 defines that boundary before any endpoint, credential,
operator runner, external replay import, score-axis population, or Level2+
evidence path exists.

## Future Input Contract

A future implementation phase may proceed only from explicit operator-selected
inputs:

- a valid accepted Evidence Ledger JSON file;
- a valid Phase 121 official-submission package output root;
- the package metadata digest and validation-report digest expected by the
  operator;
- non-secret benchmark target metadata;
- non-secret backend id, backend version, and benchmark-suite id;
- external replay environment provenance;
- declared source artifact digests;
- an explicit operator acknowledgement for any live replay or endpoint path;
- an explicit output root outside git for generated future artifacts;
- a redaction policy for anything derived from external replay or submission;
- a claim-boundary policy that keeps local, external replay, official
  submission, performance, formal, and soundness evidence classes separate.

Missing inputs must fail closed.

## Future Validation Order

A future implementation must validate in this order before any external action:

1. Confirm explicit operator acknowledgement.
2. Confirm the output root is outside git, non-empty only when overwrite is
   explicitly allowed, and not a symlink or protected-path overlap.
3. Read and validate the accepted Evidence Ledger JSON.
4. Read and validate the Phase 121 package output root.
5. Recompute package metadata, Markdown, validation-report, and digest sidecar
   bindings.
6. Confirm every package accepted-evidence id exists in the accepted ledger.
7. Confirm package metadata does not set `submits_to_official_endpoint`.
8. Confirm external replay provenance and source artifact digests are present.
9. Confirm no unresolved quarantine, blocking review, stale tip, stale preview,
   or local-only Level2 promotion marker exists.
10. Confirm the requested evidence class is supported by the selected future
    operation.
11. Only then allow a later operator-only implementation phase to perform live
    replay or endpoint submission.

Normal tests must stop before step 11 unless a later phase explicitly
authorizes an operator-only path.

## Future Artifact Contract

A future implementation must materialize generated outputs outside git under a
caller-selected root. The boundary for that future root is:

- `external-replay-submission/input-manifest.json`
- `external-replay-submission/preflight-report.json`
- `external-replay-submission/redaction-report.json`
- `external-replay-submission/submission-package-digests.json`
- `external-replay-submission/non-claims.md`
- `external-replay-submission/digests/input-manifest.sha256`
- `external-replay-submission/digests/preflight-report.sha256`
- `external-replay-submission/digests/redaction-report.sha256`
- `external-replay-submission/digests/submission-package-digests.sha256`
- `external-replay-submission/digests/non-claims.sha256`

Any future live replay response, official endpoint response, token, credential,
raw request body, raw response body, transport transcript, or private operator
configuration must be excluded from committed artifacts unless a later
boundary explicitly authorizes a redacted digest-only representation.

## Required Future Rejections

A future implementation must reject:

- missing operator acknowledgement;
- missing accepted ledger;
- invalid accepted ledger JSON;
- missing or invalid Phase 121 package output root;
- stale package digest sidecars;
- package metadata not matching rendered Markdown;
- package validation report claiming official submission or score-axis side
  effects;
- accepted-evidence ids absent from the accepted ledger;
- missing external replay provenance;
- missing source artifact digests;
- local-only evidence being promoted to external replay or official evidence;
- local soak telemetry being promoted to ZK backend performance evidence;
- unresolved quarantine or blocking review markers;
- stale append previews or stale accepted-ledger tips;
- score-axis population without matching evidence class;
- any default endpoint, default credential, default benchmark target, or
  implicit operator acknowledgement;
- raw credential, raw token, raw endpoint response, or raw transport retention;
- generated artifacts inside git;
- broad SOTA, leaderboard, formal, soundness, semantic-correctness, or
  production-readiness claims.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- accepted ledger validation before any live step;
- Phase 121 package output validation before any live step;
- package digest drift rejection;
- accepted-evidence id mismatch rejection;
- missing external replay provenance rejection;
- missing source artifact digest rejection;
- missing operator acknowledgement rejection;
- protected output-root, symlink, path traversal, partial-output,
  unexpected-output, stale-digest, and overwrite-drift rejection;
- local-only evidence promotion rejection;
- unresolved quarantine and blocking review rejection;
- score-axis non-population without matching evidence class;
- source scans proving no default endpoint, default credential, network call,
  process execution, or official submission path is reachable in normal gates.

Any live external replay, official endpoint interaction, credential access, or
operator-run generated artifact campaign must be excluded from normal tests
unless a later phase explicitly authorizes an operator-only path.

## Non-Goals

This boundary does not authorize Rust implementation, tests, Cargo metadata
changes, generated output files, committed external replay artifacts, committed
official-submission artifacts, accepted Evidence Ledger mutation, official
benchmark submission, external replay execution, live backend execution,
network access, credentials or secrets, command-line tools, UI dashboards,
JavaScript/TypeScript/package runtime additions, score-axis population, ZK
backend performance claims, Level2+ evidence creation, formal evidence
creation, broad leaderboard claims, SOTA claims, production-readiness claims,
or semantic-correctness claims.

## Claim Boundary

This boundary is planning only. It is not external replay evidence. It is not
official benchmark evidence. It is not accepted Evidence Ledger mutation. It is
not score-axis population. It is not Level2+ evidence. It is not ZK backend
performance evidence. It is not proof-system soundness evidence. It is not
semantic correctness evidence. It is not production readiness.

# Phase W Official Submission Package Materialization Boundary Spec

## Status

Docs-first boundary for a future local official-submission package
materialization surface.

This boundary does not authorize implementation code. It does not create a
submitted package, call an official endpoint, populate score axes, or create
Level2+ evidence.

## State Slice

This docs-first phase may touch only:

- `docs/120-phase-w-official-submission-package-materialization-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No Rust source, tests, Cargo metadata, generated benchmark artifact,
durable campaign output, accepted Evidence Ledger JSON file, official
submission package output, score report, package runtime file, CLI/UI surface,
credential path, network path, or official endpoint is changed by this phase.

## Purpose

Phase 115 added inert `OfficialSubmissionPackageMetadata` validation and
rendering. Phase 117 added guarded local accepted-ledger append mechanics.
Phase 119 added local JSON materialization for that accepted ledger.

The remaining local packaging gap is an explicit output-root contract for a
future digest-bound submission package artifact. That future package may be a
local bundle for operator review, but it must still not be an official
submission unless a later operator-only submission phase explicitly authorizes
an external endpoint path.

## Future Contract

A future implementation may materialize one local output root containing only
declared official-submission package files derived from valid
`OfficialSubmissionPackageMetadata` and a caller-selected accepted
`EvidenceLedger` JSON file.

The future implementation must require:

- an explicit non-empty output root;
- an explicit accepted ledger JSON path;
- an existing valid accepted ledger;
- every `accepted_evidence_ledger_entry_id` in the package metadata to exist in
  that ledger;
- `submits_to_official_endpoint == false`;
- non-empty external replay environment provenance;
- non-empty artifact digests;
- required non-claim labels;
- deterministic package metadata JSON;
- deterministic rendered package Markdown;
- digest sidecars for every package-level output;
- no undeclared files in the output root unless an explicit overwrite mode is
  selected;
- path traversal, absolute-path, symlink, and protected-path overlap rejection.

The declared future output shape is:

- `official-submission-package/package-metadata.json`
- `official-submission-package/package.md`
- `official-submission-package/validation-report.json`
- `official-submission-package/digests/package-metadata.sha256`
- `official-submission-package/digests/package-md.sha256`
- `official-submission-package/digests/validation-report.sha256`

## Required Future Rejections

The future materializer must reject:

- missing accepted ledger file;
- invalid accepted ledger JSON;
- package metadata with no accepted evidence ids;
- package metadata whose accepted evidence ids are absent from the ledger;
- package metadata with missing external replay provenance;
- package metadata with missing artifact digests;
- package metadata with missing required non-claim labels;
- package metadata containing official, formal, soundness, performance, or
  leaderboard claim text beyond its reviewed claim scope;
- `submits_to_official_endpoint == true`;
- stale, partial, or unexpected output-root files;
- output roots that overlap source packs, campaign outputs, accepted ledgers,
  report bundles, audit-index outputs, or repository roots;
- network, process, credential, or official endpoint submission surfaces.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- valid local package output creation from package metadata plus accepted ledger
  JSON;
- deterministic JSON, Markdown, validation-report, and digest sidecar output;
- missing accepted ledger rejection;
- invalid accepted ledger rejection;
- accepted-evidence id mismatch rejection;
- metadata validation failure rejection;
- external-submission flag rejection;
- protected-root, symlink, path traversal, partial-output, unexpected-output,
  stale-digest, and overwrite-drift rejection;
- source scans proving no network, process, credential, or endpoint submission
  path exists.

## Non-Goals

This boundary does not authorize Rust implementation, tests, Cargo metadata
changes, generated output files, committed official-submission package
artifacts, official benchmark submission, external replay execution, live
backend execution, network access, credentials or secrets, command-line tools,
UI dashboards, JavaScript/TypeScript/package runtime additions, score-axis
population, ZK backend performance claims, Level2+ evidence creation, formal
evidence creation, broad leaderboard claims, or treating a local package as an
accepted official benchmark submission.

## Claim Boundary

A materialized local official-submission package would be a local review
artifact until a later operator-only submission phase exists. It is not an
official benchmark submission. It is not external replay execution. It is not
score-axis population. It is not Level2+ evidence. It is not ZK backend
performance evidence. It is not semantic correctness evidence.

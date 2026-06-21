# Phase R Audit Index Output Plumbing Spec

Status: docs-first boundary only.

Phase R currently has inert in-memory `LocalAuditIndexManifest` metadata. This
spec defines the next possible boundary for adjacent local audit-index output
plumbing. It does not authorize Rust implementation code, generated
audit-index files, audit-index writer or reader APIs, command-line tools, UI
dashboards, browser apps, JavaScript/TypeScript/package runtime additions,
replay-command execution, external replay, live backend execution, external repo
clones, vendored source, external result import, generated benchmark artifacts,
official benchmark evidence, ZK backend performance claims, Level2+ evidence
creation, broad leaderboard claims, accepted Evidence Ledger mutation, source
pack mutation, source report mutation, report-bundle mutation, score-axis
population from local-only evidence, or treating audit indexes as evidence.

## State Slice

This phase is limited to Markdown specification and navigation updates under:

- `docs/75-phase-r-audit-index-output-plumbing-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No crate, test fixture, generated artifact, benchmark pack, readiness output,
dashboard output, report-bundle output, audit-index output, local replay result,
Evidence Record, Score Report, accepted Evidence Ledger, or report-bundle
manifest is changed by this phase.

## Purpose

The in-memory Phase R audit index can summarize existing report-bundle metadata.
The next useful boundary is to define how a future implementation may
materialize that index as adjacent local metadata without changing the indexed
sources.

The future output-plumbing slice answers only:

- where the local audit-index manifest may be written;
- where its digest sidecar may be written;
- how the output root is validated;
- how materialized bytes are checked against the in-memory manifest digest;
- how failed-readiness and local-only warnings remain visible after
  materialization;
- how source immutability is preserved.

The output remains local operator/auditor metadata. It is not benchmark evidence
and does not change the status of any referenced artifact.

## Authorized Future Input

A future implementation may accept:

- one valid `LocalAuditIndexManifest`;
- a caller-selected local output root intended to represent an `audit-index/`
  directory;
- an explicit overwrite policy.

The implementation must validate the manifest before writing and after reading.
It must not read source packs, source reports, report bundles, or accepted
Evidence Ledgers except through existing validated metadata supplied by the
manifest.

## Authorized Future Output Shape

A future implementation may materialize exactly:

```text
audit-index/
  audit-index-manifest.json
  digests/
    audit-index-manifest.sha256
```

The manifest JSON must be the canonical pretty JSON form of
`LocalAuditIndexManifest`. The digest sidecar must bind the manifest JSON bytes
using the existing SHA-256 artifact digest representation.

The output files must not be inserted into `pack.json`, any report bundle, any
source report, or the accepted Evidence Ledger. They must not overwrite source
files.

## Output Root Safety

A future implementation must reject:

- output roots that are existing files;
- output roots containing unexpected files;
- output roots containing symlinks;
- output roots with path traversal, URL-like content, or shell-like fragments;
- overwrite attempts unless the caller explicitly permits overwrite;
- overwrite attempts where existing materialized bytes do not match the supplied
  manifest and digest contract.

Permitted overwrite may replace only the two authorized audit-index output
files after validation proves they correspond to the same local output contract.

## Required Future Validation

A future implementation must fail closed when:

- the supplied `LocalAuditIndexManifest` is invalid;
- the materialized manifest JSON does not deserialize to the supplied manifest;
- the manifest digest sidecar is missing, malformed, stale, unsupported, or does
  not match the manifest JSON bytes;
- any unexpected file exists below the audit-index output root;
- any symlink exists below the audit-index output root;
- failed pack-readiness state is hidden;
- report-bundle local-only warnings are hidden;
- the audit-index output boundary is above `Level0DesignNote`;
- any source pack, source report, report bundle, or accepted Evidence Ledger is
  mutated;
- any output claims official benchmark evidence;
- any output claims ZK backend performance;
- any output claims Level2+ evidence;
- any output claims accepted Evidence Ledger mutation;
- any output includes replay-command execution output;
- any output populates score axes from local-only metadata.

## Claim Boundary

The maximum Phase R output-plumbing planning boundary is `Level0DesignNote`.

Future audit-index output files remain local integrity summaries only. They are
not accepted evidence, not official benchmark evidence, not benchmark outputs,
not backend performance evidence, not Level2+ evidence, and not proof.

Required labels for any future audit-index output:

- Audit indexes are not accepted evidence.
- Audit indexes are local integrity summaries, not official benchmark evidence.
- Audit indexes do not create Level2+ evidence.
- Audit indexes do not prove backend performance.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Non-Goals

This docs-first phase does not permit:

- Rust source or test changes;
- generated audit-index files;
- audit-index writer or reader APIs;
- command-line tools;
- browser or UI dashboard work;
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies;
- source pack mutation;
- source report mutation;
- report-bundle mutation;
- accepted Evidence Ledger mutation;
- replay-command execution;
- external replay;
- live backend execution;
- external repo clones or vendored source;
- external result import;
- generated benchmark artifacts;
- official benchmark evidence;
- ZK backend performance claims;
- Level2+ evidence creation;
- score-axis population from local-only evidence;
- broad leaderboard claims.

## Future Implementation Exit Criteria

A future implementation phase must include:

- adjacent local output writer and reader APIs for exactly the two authorized
  output files;
- digest verification for manifest JSON bytes and the digest sidecar;
- output-root safety checks before materialization;
- overwrite-drift, symlink, unexpected-file, and stale-digest rejection tests;
- validation that source packs, source reports, report bundles, and accepted
  Evidence Ledgers are not mutated;
- regression tests preserving failed-readiness and local-only warning
  visibility;
- source scans proving no external execution hooks were added;
- documentation updates preserving Phase R claim labels.

This docs-first phase exits when this boundary spec and navigation updates are
committed.

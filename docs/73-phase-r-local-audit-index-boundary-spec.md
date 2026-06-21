# Phase R Local Audit Index Boundary Spec

Status: docs-first boundary only.

Phase R defines a future read-only local audit-index boundary over existing
local metadata surfaces: benchmark packs, pack-readiness outputs, Phase P
rendered reporting metadata, and Phase Q report-bundle outputs. It does not
authorize Rust implementation code, generated index files, command-line tools,
UI dashboards, browser apps, JavaScript/TypeScript/package runtime additions,
replay-command execution, external replay, live backend execution, external repo
clones, vendored source, external result import, generated benchmark artifacts,
official benchmark evidence, ZK backend performance claims, Level2+ evidence
creation, broad leaderboard claims, accepted Evidence Ledger mutation,
score-axis population from local-only evidence, source pack mutation, source
report mutation, or treating an audit index as evidence.

## State Slice

This phase is limited to Markdown specification and navigation updates under:

- `docs/73-phase-r-local-audit-index-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No crate, test fixture, generated artifact, benchmark pack, readiness output,
dashboard output, report-bundle output, local replay result, Evidence Record,
Score Report, accepted Evidence Ledger, or report-bundle manifest is changed by
this phase.

## Purpose

Phase Q made a single local report bundle materializable and verifiable. The
next useful boundary is not a UI or command-line workflow. It is a read-only
index contract that can summarize which local metadata outputs belong together
without copying, executing, scoring, or promoting them.

The future audit index answers only:

- which local pack or pack family is being indexed;
- which pack-readiness outputs are referenced;
- which rendered reporting outputs are referenced;
- which report-bundle outputs are referenced;
- which local digest and validation statuses were observed;
- which claim-boundary warnings must remain visible.

The audit index is local operator/auditor metadata. It is not benchmark evidence
and does not change the status of any referenced artifact.

## Authorized Future Inputs

A future implementation may read only existing local metadata:

- local benchmark pack manifests and file digests;
- Phase O pack-readiness reports and validations;
- Phase P rendered Markdown reporting metadata;
- Phase Q report-bundle manifests, rendered Markdown files, and digest
  sidecars;
- local validation results produced by existing validators.

Every input reference must be portable, relative, digest-bound, and capped at
the weakest referenced claim boundary.

## Authorized Future Output Shape

A future Phase R implementation may define an inert in-memory
`LocalAuditIndexManifest` and, in a separate explicit implementation phase, may
materialize adjacent local metadata under a caller-selected directory such as:

```text
audit-index/
  audit-index-manifest.json
  digests/
    audit-index-manifest.sha256
```

This Phase R docs-first boundary does not authorize writing those files.

The future output must not be inserted into `pack.json`, a report bundle, a
source report, or the accepted Evidence Ledger. It must not overwrite source
files.

## Required Future Validation

A future implementation must fail closed when:

- any input reference is absolute, contains `..`, contains backslashes, or
  contains URL-like content;
- any input digest is missing, stale, unsupported, or malformed;
- any referenced local metadata file is missing;
- any referenced validation report is invalid without visible failure status;
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

The maximum Phase R planning boundary is `Level0DesignNote`.

Future audit-index artifacts remain local integrity summaries only. They are not
accepted evidence, not official benchmark evidence, not benchmark outputs, not
backend performance evidence, not Level2+ evidence, and not proof.

Required labels for any future audit-index output:

- Audit indexes are not accepted evidence.
- Audit indexes are local integrity summaries, not official benchmark evidence.
- Audit indexes do not create Level2+ evidence.
- Audit indexes do not prove backend performance.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Non-Goals

Phase R does not permit:

- Rust source or test changes;
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

- deterministic index metadata over existing local artifacts;
- digest verification for every referenced file;
- visible failed-readiness and failed-validation status;
- no mutation of source packs, source reports, report bundles, or accepted
  Evidence Ledgers;
- output-root safety checks before any future materialization;
- regression tests for missing refs, stale digests, unsafe refs, hidden failed
  readiness, claim-boundary escalation, source mutation, and forbidden claims;
- source scans proving no external execution hooks were added;
- documentation updates preserving Phase R claim labels.

Phase R itself exits when this boundary spec and navigation updates are
committed.

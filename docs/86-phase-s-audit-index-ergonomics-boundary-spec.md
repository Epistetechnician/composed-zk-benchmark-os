# Phase S Audit Index Ergonomics Boundary Spec

Status: docs-first boundary only.

Phase R can build, validate, write, and read one local audit-index manifest as
adjacent local metadata. Phase S defines a future ergonomics layer over that
single validated audit index. It does not authorize Rust implementation code,
generated ergonomics files, command-line tools, UI dashboards, browser apps,
JavaScript/TypeScript/package runtime additions, cross-bundle index construction,
replay-command execution, external replay, live backend execution, external repo
clones, vendored source, external result import, generated benchmark artifacts,
official benchmark evidence, ZK backend performance claims, Level2+ evidence
creation, broad leaderboard claims, accepted Evidence Ledger mutation, source
pack mutation, source report mutation, report-bundle mutation, audit-index
mutation, score-axis population from local-only metadata, or treating audit-index
ergonomics as evidence.

## State Slice

This phase is limited to Markdown specification and navigation updates under:

- `docs/86-phase-s-audit-index-ergonomics-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No crate, test fixture, generated artifact, benchmark pack, readiness output,
dashboard output, report-bundle output, audit-index output, local replay result,
Evidence Record, Score Report, accepted Evidence Ledger, report-bundle manifest,
or audit-index manifest is changed by this phase.

## Purpose

The current audit-index output can preserve local integrity and claim-boundary
labels, but it is still low-level metadata. The next useful boundary is a
read-only ergonomics contract that lets future code present one already validated
audit index in a more navigable form without creating new evidence or broadening
the input graph.

The future ergonomics layer may answer only:

- which validated local audit-index inputs match a caller-provided filter;
- how inputs group by local kind, status, claim boundary, and warning class;
- which failed-readiness or local-only warning labels remain visible;
- which source refs and digests are included in a selected view;
- which local limitation labels must be repeated in every rendered summary.

The ergonomics layer is local operator/auditor presentation metadata. It is not
benchmark evidence and does not change the status of any referenced artifact.

## Authorized Future Inputs

A future implementation may accept only:

- one valid `LocalAuditIndexManifest`;
- optional caller-selected filters over existing manifest fields;
- optional caller-selected grouping and sort keys over existing manifest fields;
- optional local rendering options that affect presentation only.

Every filter, grouping key, sort key, and rendered summary must be derived from
fields already present in the validated audit-index manifest. The future
implementation must not read source packs, source reports, report bundles,
accepted Evidence Ledgers, or external resources to enrich the view.

## Authorized Future Output Shape

A future implementation may define inert in-memory ergonomics metadata, such as:

- selected input ids;
- rejected filter diagnostics;
- group summaries;
- warning summaries;
- local limitation labels;
- deterministic Markdown rendering of the selected single-index view.

This Phase S docs-first boundary does not authorize materializing those outputs
to disk. Any future file output requires a separate explicit output-plumbing
boundary.

The future output must remain capped at `Level0DesignNote`. It must not be
inserted into `pack.json`, a report bundle, an audit-index output directory, a
source report, or the accepted Evidence Ledger.

## Required Future Validation

A future implementation must fail closed when:

- the supplied `LocalAuditIndexManifest` is invalid;
- any filter references a field outside the manifest contract;
- any sort or group key references a field outside the manifest contract;
- any filter expression includes path traversal, URL-like content, shell-like
  content, regular-expression execution, or code execution;
- failed pack-readiness state is hidden;
- report-bundle local-only warnings are hidden;
- source-mutation flags are hidden;
- limitation labels are missing from rendered summaries;
- output claim boundary exceeds `Level0DesignNote`;
- any output claims official benchmark evidence;
- any output claims ZK backend performance;
- any output claims Level2+ evidence;
- any output claims accepted Evidence Ledger mutation;
- any output includes replay-command execution output;
- any output populates score axes from local-only metadata.

## Claim Boundary

The maximum Phase S planning boundary is `Level0DesignNote`.

Future audit-index ergonomics outputs are presentation metadata over a local
integrity summary only. They are not accepted evidence, not official benchmark
evidence, not benchmark outputs, not backend performance evidence, not Level2+
evidence, and not proof.

Required labels for any future audit-index ergonomics output:

- Audit-index ergonomics are not accepted evidence.
- Audit-index ergonomics are local presentation metadata only.
- Audit-index ergonomics do not create official benchmark evidence.
- Audit-index ergonomics do not create Level2+ evidence.
- Audit-index ergonomics do not prove backend performance.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Non-Goals

Phase S does not permit:

- Rust source or test changes;
- generated ergonomics files;
- command-line tools;
- browser or UI dashboard work;
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies;
- cross-bundle audit-index construction;
- source pack mutation;
- source report mutation;
- report-bundle mutation;
- audit-index output mutation;
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

- deterministic in-memory selected-view metadata over one valid
  `LocalAuditIndexManifest`;
- strict filter, sort, and grouping validation against manifest fields only;
- visible failed-readiness, source-mutation, and local-only warning status;
- deterministic Markdown rendering that repeats required limitation labels;
- no mutation of source packs, source reports, report bundles, audit-index
  outputs, or accepted Evidence Ledgers;
- regression tests for invalid filters, hidden warnings, hidden failed readiness,
  hidden source mutation, claim-boundary escalation, forbidden claims, and
  deterministic rendering;
- source scans proving no external execution hooks were added;
- documentation updates preserving Phase S claim labels.

Phase S itself exits when this boundary spec and navigation updates are
committed.

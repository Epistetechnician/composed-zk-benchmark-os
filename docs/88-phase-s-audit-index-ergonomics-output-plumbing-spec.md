# Phase S Audit Index Ergonomics Output Plumbing Spec

Status: docs-first boundary only.

Phase S currently has in-memory single-index audit-index ergonomics over one
valid `LocalAuditIndexManifest`. This spec defines the next possible boundary
for materializing those ergonomics outputs as adjacent local presentation
metadata. It does not authorize Rust implementation code, generated ergonomics
files, ergonomics writer or reader APIs, command-line tools, UI dashboards,
browser apps, JavaScript/TypeScript/package runtime additions, cross-bundle
audit-index construction, replay-command execution, external replay, live backend
execution, external repo clones, vendored source, external result import,
generated benchmark artifacts, official benchmark evidence, ZK backend
performance claims, Level2+ evidence creation, broad leaderboard claims,
accepted Evidence Ledger mutation, source pack mutation, source report mutation,
report-bundle mutation, audit-index output mutation, score-axis population from
local-only evidence, or treating audit-index ergonomics as evidence.

## State Slice

This phase is limited to Markdown specification and navigation updates under:

- `docs/88-phase-s-audit-index-ergonomics-output-plumbing-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No crate, test fixture, generated artifact, benchmark pack, readiness output,
dashboard output, report-bundle output, audit-index output, ergonomics output,
local replay result, Evidence Record, Score Report, accepted Evidence Ledger,
report-bundle manifest, audit-index manifest, or package runtime file is changed
by this phase.

## Purpose

The in-memory Phase S ergonomics view can filter, group, sort, summarize warnings,
repeat limitation labels, and render deterministic Markdown for one valid audit
index. The next useful boundary is to define how a future implementation may
materialize that selected view without changing the source audit-index output or
promoting the selected view into evidence.

The future output-plumbing slice answers only:

- where the local ergonomics view may be written;
- where the selected-view JSON, rendered Markdown, and digest sidecars may live;
- how the output root is validated;
- how materialized bytes are checked against the in-memory view;
- how failed-readiness, local-only warning, and source-mutation status remain
  visible after materialization;
- how source audit-index immutability is preserved.

The output remains local operator/auditor presentation metadata. It is not
benchmark evidence and does not change the status of any referenced artifact.

## Authorized Future Input

A future implementation may accept:

- one valid `LocalAuditIndexManifest`;
- one valid `LocalAuditIndexErgonomicsRequest`;
- one valid in-memory `LocalAuditIndexErgonomicsView` derived from that manifest
  and request;
- a caller-selected local output root intended to represent an
  `audit-index-ergonomics/` directory;
- an explicit overwrite policy.

The implementation must validate the source manifest, request, and in-memory view
before writing and after reading. It must not read source packs, source reports,
report bundles, accepted Evidence Ledgers, external resources, or audit-index
output directories to enrich the view.

## Authorized Future Output Shape

A future implementation may materialize exactly:

```text
audit-index-ergonomics/
  ergonomics-view.json
  rendered/
    ergonomics-view.md
  digests/
    ergonomics-view-json.sha256
    ergonomics-view-markdown.sha256
```

`ergonomics-view.json` must be the canonical pretty JSON form of
`LocalAuditIndexErgonomicsView`. `rendered/ergonomics-view.md` must be exactly
the deterministic Markdown stored in that view. Digest sidecars must bind the
materialized JSON and Markdown bytes using SHA-256 artifact digests.

The output files must not be inserted into `pack.json`, any report bundle, any
source report, any audit-index output directory, or the accepted Evidence Ledger.
They must not overwrite source files or Phase R audit-index files.

## Output Root Safety

A future implementation must reject:

- output roots that are existing files;
- output roots containing unexpected files;
- output roots containing symlinks;
- output roots with path traversal, URL-like content, or shell-like fragments;
- overwrite attempts unless the caller explicitly permits overwrite;
- overwrite attempts where existing materialized bytes do not match the supplied
  view and digest contract;
- output roots that are equal to, nested under, or parents of source pack, source
  report, report-bundle, audit-index, or accepted Evidence Ledger paths supplied
  to the future API.

Permitted overwrite may replace only the four authorized ergonomics output files
after validation proves they correspond to the same local output contract.

## Required Future Validation

A future implementation must fail closed when:

- the supplied `LocalAuditIndexManifest` is invalid;
- the supplied `LocalAuditIndexErgonomicsRequest` is invalid;
- the supplied `LocalAuditIndexErgonomicsView` cannot be re-derived
  deterministically from the supplied manifest and request;
- the materialized JSON does not deserialize to the supplied view;
- the materialized Markdown does not byte-match the view Markdown;
- either digest sidecar is missing, malformed, stale, unsupported, or mismatched;
- any unexpected file exists below the ergonomics output root;
- any symlink exists below the ergonomics output root;
- failed pack-readiness state is hidden;
- report-bundle local-only warnings are hidden;
- source-mutation flags are hidden;
- any required limitation label is absent from the materialized Markdown;
- the ergonomics output boundary is above `Level0DesignNote`;
- any source pack, source report, report bundle, audit-index output, or accepted
  Evidence Ledger is mutated;
- any output claims official benchmark evidence;
- any output claims ZK backend performance;
- any output claims Level2+ evidence;
- any output claims accepted Evidence Ledger mutation;
- any output includes replay-command execution output;
- any output populates score axes from local-only metadata.

## Claim Boundary

The maximum Phase S output-plumbing planning boundary is `Level0DesignNote`.

Future audit-index ergonomics output files remain local presentation metadata
only. They are not accepted evidence, not official benchmark evidence, not
benchmark outputs, not backend performance evidence, not Level2+ evidence, and
not proof.

Required labels for any future materialized ergonomics output:

- Audit-index ergonomics are not accepted evidence.
- Audit-index ergonomics are local presentation metadata only.
- Audit-index ergonomics do not create official benchmark evidence.
- Audit-index ergonomics do not create Level2+ evidence.
- Audit-index ergonomics do not prove backend performance.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Non-Goals

This docs-first phase does not permit:

- Rust source or test changes;
- generated ergonomics files;
- ergonomics writer or reader APIs;
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

- adjacent local output writer and reader APIs for exactly the four authorized
  output files;
- deterministic re-derivation of the view from the supplied manifest and request;
- digest verification for materialized JSON, Markdown, and digest sidecars;
- output-root safety checks before materialization;
- overwrite-drift, symlink, unexpected-file, stale-digest, and partial-bundle
  rejection tests;
- validation that source packs, source reports, report bundles, audit-index
  outputs, and accepted Evidence Ledgers are not mutated;
- regression tests preserving failed-readiness, source-mutation, and local-only
  warning visibility;
- regression tests preserving required limitation labels in materialized Markdown;
- source scans proving no external execution hooks were added;
- documentation updates preserving Phase S claim labels.

This docs-first phase exits when this boundary spec and navigation updates are
committed.

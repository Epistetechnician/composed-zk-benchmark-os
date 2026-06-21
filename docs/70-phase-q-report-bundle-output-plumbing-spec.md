# Phase Q-C Report Bundle Output Plumbing Spec

Status: docs-first boundary only.

Phase Q-C defines the adjacent local output-plumbing boundary for future
materialization of the Phase Q-B in-memory `ReportBundleManifest`. It does not
authorize Rust implementation code, report-bundle writer or reader APIs,
command-line tools, UI dashboard work, replay-command execution, external
replay, live backend execution, external repo clones, vendored source, external
result import, generated benchmark artifacts, official benchmark evidence, ZK
backend performance claims, Level2+ evidence creation, broad leaderboard claims,
accepted Evidence Ledger mutation, score-axis population from local-only
evidence, or treating report bundles as evidence.

## State Slice

This phase is limited to Markdown specification and navigation updates under:

- `docs/70-phase-q-report-bundle-output-plumbing-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No crate, test fixture, generated artifact, benchmark pack, local replay result,
Evidence Record, Score Report, report-bundle manifest output, or accepted
Evidence Ledger is changed by this phase.

## Purpose

Phase Q-B produces an in-memory `ReportBundleManifest`. Phase Q-C defines how a
future explicit implementation may materialize that metadata beside existing
local reporting artifacts without mutating the source pack, source reports, or
accepted Evidence Ledger.

The goal is local operator/auditor ergonomics only: make the already-built
read-only report-bundle metadata inspectable on disk while preserving
`Level0DesignNote` output and local-only claim boundaries.

## Authorized Future Output Shape

A future Phase Q output-plumbing implementation may write only an adjacent local
directory with this shape:

```text
report-bundle/
  report-bundle-manifest.json
  rendered/
    <rendered-report-id>.md
  digests/
    report-bundle-manifest.sha256
```

The exact root must be provided by the caller or derived as an adjacent metadata
directory. It must not be inserted into `pack.json`, the accepted Evidence
Ledger, or any source report. It must not overwrite source files.

The future writer may write:

- one deterministic JSON serialization of `ReportBundleManifest`;
- rendered Markdown files whose bytes match `ReportBundleRenderedReport`
  `markdown_digest` entries;
- one digest sidecar for the manifest bytes;
- no executable commands;
- no generated benchmark outputs;
- no external result imports.

The future reader may read:

- the manifest JSON;
- rendered Markdown bytes for digest verification only;
- the manifest digest sidecar for local integrity checking only.

The reader must not treat a valid local report bundle as accepted evidence.

## Required Future Validation

A future implementation must fail closed when:

- the output root is empty, absolute when a relative root is required, contains
  `..`, contains backslashes, or contains URL-like content;
- any output path escapes the chosen root;
- the root already contains files and explicit overwrite approval is absent;
- `report-bundle-manifest.json` bytes do not match the manifest digest sidecar;
- any rendered Markdown bytes do not match their declared digest;
- a rendered Markdown file is missing for a manifest entry;
- a rendered Markdown file exists without a manifest entry;
- a source ref points outside portable local metadata;
- the manifest validation fails;
- the manifest output boundary is not `Level0DesignNote`;
- failed pack-readiness state is hidden;
- local-only limitation labels are absent;
- any output claims official benchmark evidence;
- any output claims ZK backend performance;
- any output claims Level2+ evidence;
- any output claims accepted Evidence Ledger mutation;
- any output contains replay-command execution output.

## Claim Boundary

The maximum Phase Q-C planning boundary is `Level0DesignNote`.

Future output-plumbing artifacts remain local integrity summaries only. They are
not accepted evidence, not official benchmark evidence, not benchmark outputs,
not backend performance evidence, not Level2+ evidence, and not proof.

Required labels for future materialized output:

- Report bundles are not accepted evidence.
- Report bundles are local integrity summaries, not official benchmark evidence.
- Report bundles do not create Level2+ evidence.
- Report bundles do not prove backend performance.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Non-Goals

Phase Q-C does not permit:

- Rust source or test changes;
- report-bundle writer or reader APIs;
- command-line tools;
- browser or UI dashboard work;
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies;
- source pack mutation;
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

- deterministic writer output for the manifest and rendered Markdown files;
- reader-side digest verification for every materialized file;
- output-root safety checks;
- no mutation of source packs, source reports, or accepted Evidence Ledgers;
- failed-readiness visibility checks after materialization;
- regression tests for stale manifest digest, stale rendered Markdown digest,
  missing rendered Markdown, extra rendered Markdown, unsafe roots, unsafe paths,
  source mutation, and claim-boundary escalation;
- source scans proving no external execution hooks were added;
- documentation updates preserving Phase Q claim labels.

Phase Q-C itself exits when this boundary spec and navigation updates are
committed.

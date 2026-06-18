# Phase Q-D Report Bundle Output Implementation Notes

Status: implemented local output plumbing.

Phase Q-D implements the adjacent local report-bundle output plumbing authorized
by `docs/70-phase-q-report-bundle-output-plumbing-spec.md`. The implementation
materializes already-built Phase Q-B `ReportBundleManifest` metadata under a
caller-selected local report-bundle root.

## State Slice

This phase changes:

- `crates/zkbench-core/src/report_bundle.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_q_report_bundle.rs`
- `docs/71-phase-q-report-bundle-output-implementation-notes.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No source pack, source report, generated benchmark artifact, replay command,
backend result, accepted Evidence Ledger, UI, command-line tool, JavaScript
runtime, package script, or external integration is added by this phase.

## Public Utilities

Phase Q-D adds these public utilities:

- `write_report_bundle_outputs`
- `read_report_bundle_outputs`
- `ReportBundleRenderedMarkdown`
- `ReportBundleMaterializedReport`
- `ReportBundleOutput`
- `REPORT_BUNDLE_MANIFEST_PATH`
- `REPORT_BUNDLE_RENDERED_DIR`
- `REPORT_BUNDLE_MANIFEST_DIGEST_PATH`

The writer takes a validated `ReportBundleManifest`, caller-provided rendered
Markdown payloads, and an explicit overwrite flag. It writes only:

```text
report-bundle-manifest.json
rendered/<rendered-report-id>.md
digests/report-bundle-manifest.sha256
```

The reader verifies the manifest digest sidecar, validates the manifest, checks
that every rendered Markdown file declared by the manifest exists, rejects extra
rendered Markdown files, and recomputes every rendered Markdown digest.

## Validation Behavior

The implementation fails closed for:

- invalid output roots;
- unsafe relative output paths;
- non-empty output roots without explicit overwrite approval;
- unexpected existing files when overwrite is enabled;
- invalid manifests;
- missing rendered Markdown payloads;
- extra rendered Markdown payloads;
- duplicate rendered Markdown payload ids;
- rendered Markdown digest drift before writing;
- stale manifest digest sidecars;
- missing rendered Markdown files;
- extra rendered Markdown files;
- rendered Markdown digest drift after writing;
- claim-boundary escalation inherited from manifest validation.

The writer validates the complete payload set and all rendered Markdown digests
before writing any file, so a bad payload set cannot partially materialize a
bundle.

## Claim Boundary

The output boundary remains `Level0DesignNote`.

Report-bundle output files are local integrity summaries only. They are not
accepted evidence, not official benchmark evidence, not benchmark outputs, not
backend performance evidence, not Level2+ evidence, and not proof.

Required labels remain:

- Report bundles are not accepted evidence.
- Report bundles are local integrity summaries, not official benchmark evidence.
- Report bundles do not create Level2+ evidence.
- Report bundles do not prove backend performance.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Verification

Focused Phase Q-D coverage lives in
`crates/zkbench-core/tests/phase_q_report_bundle.rs` and covers:

- output write/read round trip;
- source file immutability outside the report-bundle root;
- missing rendered payload rejection;
- rendered payload digest drift rejection;
- non-empty root overwrite protection;
- materialized Markdown digest drift rejection;
- extra rendered Markdown rejection;
- stale manifest digest sidecar rejection.

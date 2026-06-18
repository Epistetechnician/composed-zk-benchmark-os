# Phase Q-E Report Bundle Ergonomics Hardening Notes

Status: implemented local ergonomics hardening.

Phase Q-E hardens the Phase Q-D adjacent local report-bundle output surface
without broadening the evidence boundary. It adds a source-backed rendered
Markdown payload helper and earlier local validation for output-shape mistakes
that would otherwise be discovered only during materialization.

## State Slice

This phase changes:

- `crates/zkbench-core/src/report_bundle.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_q_report_bundle.rs`
- `docs/72-phase-q-report-bundle-ergonomics-hardening-notes.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

It does not add UI, command-line tools, JavaScript/TypeScript/package runtime
files, replay-command execution, external replay, live backend execution,
external result import, generated benchmark artifacts, official benchmark
evidence, ZK backend performance claims, Level2+ evidence promotion, accepted
Evidence Ledger mutation, source pack mutation, or source report mutation.

## Public Utility

Phase Q-E adds:

- `build_report_bundle_rendered_markdown_payloads`

The helper takes an existing `ReportBundleManifest`, the source `ScoreReport`
values, and the source `ReportBundlePackReadinessInput` values. It rebuilds the
expected manifest from those sources, verifies that the rebuilt inputs and
rendered-report metadata match the supplied manifest, and then returns
`ReportBundleRenderedMarkdown` payloads suitable for
`write_report_bundle_outputs`.

This avoids caller-side reconstruction of internal dashboard ids while keeping
source drift fail-closed.

## Validation Hardening

Phase Q-E also adds or verifies local-only hardening for:

- duplicate rendered output paths during manifest validation;
- unsafe output roots containing parent-directory components;
- symlink rejection while scanning existing output roots;
- unexpected existing files when overwrite is enabled;
- source-report drift before rendered Markdown payloads are materialized.

These checks remain local integrity checks. They do not score benchmark evidence
and do not create accepted evidence.

## Claim Boundary

The output boundary remains `Level0DesignNote`.

Report-bundle files and payload helpers are local integrity summaries only. They
are not accepted evidence, not official benchmark evidence, not benchmark
outputs, not backend performance evidence, not Level2+ evidence, and not proof.

Required labels remain:

- Report bundles are not accepted evidence.
- Report bundles are local integrity summaries, not official benchmark evidence.
- Report bundles do not create Level2+ evidence.
- Report bundles do not prove backend performance.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Verification

Focused Phase Q-E coverage lives in
`crates/zkbench-core/tests/phase_q_report_bundle.rs` and covers:

- payload helper success for matching sources;
- payload helper rejection for source drift;
- duplicate rendered output path rejection;
- unsafe output root rejection;
- unexpected existing file rejection under overwrite;
- symlink rejection under overwrite.

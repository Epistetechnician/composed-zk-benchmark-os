# Phase Q-B Report Bundle Implementation Notes

Status: implemented for inert in-memory report-bundle metadata.

Phase Q-B implements the first Rust surface for the Phase Q report-bundle
boundary defined in `docs/68-phase-q-report-bundle-boundary-spec.md`. The
implementation is local metadata only. It does not write report-bundle files,
read report-bundle directories, execute replay commands, call external backends,
import external results, create benchmark outputs, create official benchmark
evidence, claim ZK backend performance, create Level2+ evidence, mutate the
accepted Evidence Ledger, or add a UI dashboard.

## State Slice

This phase is limited to:

- `crates/zkbench-core/src/report_bundle.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/src/prelude.rs`
- `crates/zkbench-core/tests/phase_q_report_bundle.rs`
- `docs/68-phase-q-report-bundle-boundary-spec.md`
- `docs/69-phase-q-report-bundle-implementation-notes.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

## Public Surface

Phase Q-B adds:

- `ReportBundleManifest`
- `ReportBundleVersion`
- `ReportBundleInputKind`
- `ReportBundleInputRef`
- `ReportBundleRenderedReport`
- `ReportBundlePackReadinessInput`
- `ReportBundleValidation`
- `ReportBundleValidationIssue`
- `ReportBundleValidationIssueKind`
- `build_report_bundle_manifest_from_reports`
- `validate_report_bundle_manifest`
- `compute_report_bundle_manifest_digest`
- `serialize_report_bundle_manifest_json`
- `deserialize_report_bundle_manifest_json`

The builder accepts existing `ScoreReport` values and existing
`PackReadinessReport`/`PackReadinessValidation` pairs. It creates an in-memory
manifest with source refs, deterministic digests, rendered Markdown digests,
claim-boundary summaries, and explicit limitation labels.

## Validation Rules

`validate_report_bundle_manifest` fails closed for:

- empty bundle or version identities;
- missing inputs or missing rendered reports;
- duplicate input ids or rendered report ids;
- absolute, parent-traversing, URL-like, shell-like, or backslash paths;
- malformed or non-SHA-256 digests;
- input claim boundaries above `Level1LocalReplay`;
- rendered report boundaries above `Level0DesignNote`;
- bundle output boundary other than `Level0DesignNote`;
- replay-command execution output;
- external replay authorization;
- Level2+ evidence claims;
- official benchmark evidence claims;
- ZK backend performance claims;
- accepted Evidence Ledger mutation claims;
- rendered reports that hide failed pack-readiness validation;
- missing local-only limitation labels.

## Claim Boundary

The Phase Q-B output boundary is `Level0DesignNote`.

Report bundles are not accepted evidence. Report bundles are local integrity
summaries, not official benchmark evidence. Report bundles do not create Level2+
evidence. Report bundles do not prove backend performance. Local replay
artifacts are not official benchmark evidence. Internal timing telemetry is not
ZK backend performance.

## Non-Goals

Phase Q-B does not permit:

- report-bundle writer or reader APIs;
- command-line tools;
- browser or UI dashboard work;
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies;
- external replay;
- live backend execution;
- external repo clones or vendored source;
- generated benchmark artifacts;
- official benchmark evidence;
- ZK backend performance claims;
- Level2+ evidence creation;
- accepted Evidence Ledger mutation;
- score-axis population from local-only evidence;
- broad leaderboard claims.

## Verification

The focused regression surface is
`crates/zkbench-core/tests/phase_q_report_bundle.rs`.

The tests cover:

- construction from existing local reports;
- deterministic JSON round-trip and manifest digesting;
- rejection of claim-boundary elevation and forbidden evidence claims;
- rejection of invalid paths, invalid digests, and stale rendered source refs;
- failed-readiness visibility requirements.

Future report-bundle materialization requires a separate explicit phase.

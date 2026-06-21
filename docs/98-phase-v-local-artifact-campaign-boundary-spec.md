# Phase V Local Artifact Campaign Boundary Spec

Status: docs-first boundary only.

Phase V defines the next benchmark OS boundary after Phase U local benchmark
artifact packaging. It plans a future user-approved durable local artifact
campaign under an ignored output root. It does not authorize Rust source
changes, tests, generated committed artifacts, command-line tools, UI
dashboards, package runtime files, external replay, live backend execution,
official benchmark submission, accepted Evidence Ledger mutation, score-axis
population, ZK backend performance claims, Level2+ evidence, or treating local
artifact bundles as accepted evidence.

## State Slice

This docs-first phase may touch only:

- `docs/98-phase-v-local-artifact-campaign-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No crate, fixture, generated benchmark artifact, benchmark pack, local replay
result, score report, accepted Evidence Ledger, package runtime file, CLI/UI
surface, external result import, or official submission artifact is changed by
this phase.

## Purpose

Phase U created local APIs that can package already-valid local benchmark
metadata into digest-bound artifact bundles. The remaining durable-artifact gap
is not another API. The gap is a campaign boundary: how a future operator may
select source local packs, choose an ignored output root, run a bounded local
artifact campaign, validate every emitted bundle, and retain the outputs without
claim escalation.

Phase V is local campaign planning only. It is not accepted-evidence promotion
and not official submission.

## Future Campaign Inputs

A future implementation phase may consume only already-valid local inputs:

- valid local benchmark packs;
- valid Phase O pack-readiness outputs;
- valid Phase Q report-bundle outputs;
- valid Phase R audit-index outputs;
- valid Phase S ergonomics outputs;
- valid Phase T cross-bundle outputs;
- valid Phase U local benchmark artifact manifests and outputs;
- explicit source paths treated as protected paths;
- a caller-selected ignored output root;
- an explicit campaign id;
- an explicit retention policy;
- an explicit validation gate list.

Every input must be validated before use. Invalid inputs may be skipped only if
the skip is recorded as a local warning and does not improve evidence status.

## Future Output Root

A future campaign may write durable local artifacts only under a caller-owned
ignored output root such as:

```text
.local-artifact-campaigns/<campaign-id>/
```

The output root must be rejected when it is empty, unsafe, a file, symlinked,
inside a protected input path, a parent of a protected input path, or populated
with unexpected files. Existing campaign roots must not be repaired. Explicit
overwrite may replace only a complete, digest-consistent campaign for the same
campaign contract.

## Future Campaign Output Shape

A future campaign boundary must name concrete files before code exists. The
minimum shape must include:

- a campaign manifest JSON;
- a campaign validation report JSON;
- one campaign summary Markdown file;
- digest sidecars for every campaign-level file;
- per-bundle references to Phase U local artifact outputs;
- a source-input digest summary;
- a machine-checkable accepted Evidence Ledger non-mutation statement;
- required limitation labels visible in JSON and Markdown.

Generated local campaign files must not be committed unless a later explicit
phase authorizes a specific non-secret fixture or acceptance record.

## Required Limitation Labels

Every future campaign manifest and rendered summary must visibly include:

- Local artifact campaigns are not official benchmark evidence.
- Local artifact campaigns are not accepted Evidence Ledger entries.
- Local artifact campaigns do not create Level2+ evidence.
- Local artifact campaigns do not prove ZK backend performance.
- Local artifact campaigns do not prove semantic correctness.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.
- Score axes remain unpopulated for local-only evidence.
- Accepted-evidence promotion requires a separate reviewed promotion phase.
- Official submission requires a separate explicit submission phase.

## Future Validation Requirements

A future implementation phase must include hermetic tests for:

- campaign id validation;
- output-root safety;
- protected-path overlap across every input class;
- invalid local pack rejection;
- invalid Phase U artifact rejection;
- stale digest rejection;
- partial campaign rejection;
- unexpected file rejection;
- symlink rejection;
- repair-overwrite rejection;
- limitation-label preservation;
- accepted Evidence Ledger non-mutation;
- score-axis non-population from local-only evidence;
- source scan proving no process, network, credential, package runtime, CLI, or
  UI hooks were added unless separately authorized.

## Promotion Boundary

Phase V campaign outputs are local durability artifacts only. They do not
become accepted evidence. A later reviewed promotion phase must still define:

- external replay authority;
- independent reproduction requirements;
- replay environment provenance;
- result import and quarantine handling;
- manual review approval;
- explicit accepted-evidence mutation policy;
- official submission policy;
- claim-text validation before any accepted record is created.

## Forbidden In This Slice

- Rust source or test changes.
- Cargo metadata changes.
- Generated benchmark artifact files.
- Durable campaign output files.
- Command-line tools.
- UI dashboards.
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies.
- External replay.
- Live backend execution.
- Network access.
- Credentials or secrets.
- External result import.
- Official benchmark submission.
- Accepted Evidence Ledger mutation.
- Score-axis population from local-only evidence.
- ZK backend performance claims.
- Level2+ evidence creation.
- Broad leaderboard claims.

## Acceptance Criteria For This Slice

- This spec exists and names the future local artifact campaign boundary.
- README navigation links this spec.
- `docs/12-task-list.md` records this docs-first boundary.
- `AGENTS.md` authorizes only this Markdown planning slice.
- `docs/90-whole-codebase-validation-report.md` records that durable campaign
  execution remains unimplemented.
- Validation confirms no Rust source, Cargo metadata, generated artifact,
  package runtime, credential, external replay, official submission, or accepted
  Evidence Ledger changed.

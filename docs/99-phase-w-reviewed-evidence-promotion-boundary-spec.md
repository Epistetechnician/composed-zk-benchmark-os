# Phase W Reviewed Evidence Promotion Boundary Spec

Status: docs-first boundary only.

Phase W defines the future reviewed promotion and official-submission boundary
for benchmark evidence. It is not an implementation phase. It does not
authorize Rust source changes, tests, generated artifacts, external replay,
live backend execution, official submissions, accepted Evidence Ledger
mutation, score-axis population, ZK backend performance claims, Level2+
evidence, or broad leaderboard claims in this slice.

## State Slice

This docs-first phase may touch only:

- `docs/99-phase-w-reviewed-evidence-promotion-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No crate, fixture, generated benchmark artifact, benchmark pack, local campaign
output, score report, accepted Evidence Ledger, package runtime file, CLI/UI
surface, external result import, credential path, network path, or official
submission artifact is changed by this phase.

## Purpose

The repo already has candidate, proposal, review, preview, eligibility,
readiness, report-bundle, audit-index, and local artifact packaging surfaces.
All of them deliberately stop short of accepted evidence. The remaining
accepted-evidence gap is the absent promotion contract that says exactly when a
reviewed artifact may mutate an accepted Evidence Ledger and when an official
benchmark submission may be created.

Phase W defines that future contract before any accepted mutation or
submission exists.

## Future Promotion Preconditions

A future implementation phase may promote evidence only when all of these are
present and valid:

- a valid source local benchmark pack;
- a valid local artifact campaign output, if campaign packaging is used;
- external replay authority for the target backend;
- independently captured external backend output;
- replay environment provenance;
- artifact capture contract compliance;
- result import validation;
- quarantine handling for rejected candidates;
- manual review approval;
- accepted-evidence mutation policy;
- claim-boundary escalation guard approval;
- official/formal/soundness/performance claim-text validation;
- source-input digest binding;
- accepted Evidence Ledger dry-run append preview;
- explicit operator acknowledgement for any submitted output.

Missing preconditions must fail closed. A Level2 eligibility report alone is
not evidence. An append preview alone is not accepted evidence.

## Accepted Evidence Ledger Mutation Policy

A future accepted-ledger mutation must be a separate explicit operation from:

- proposal creation;
- review decision creation;
- candidate creation;
- append preview creation;
- local artifact campaign execution;
- official submission package rendering.

The mutation operation must validate the current ledger tip, the proposed entry
digest, source artifact digests, provenance digests, review approval, claim
boundary, and non-claim labels immediately before append. It must reject stale
tips, stale previews, missing review approval, unresolved quarantine entries,
claim-boundary elevation without policy approval, missing source digests, and
forbidden claim text.

## Official Submission Boundary

A future official submission may be created only after accepted evidence exists
for the submitted claim. Submission packages must disclose:

- benchmark suite id;
- backend id and version;
- source pack ids;
- external replay environment provenance;
- artifact digests;
- accepted Evidence Ledger entry ids;
- review decision ids;
- claim boundary;
- non-claims;
- reproduction instructions;
- known limitations.

Submission packages must not be created from local-only evidence, local soak
telemetry, local artifact campaigns, append previews, Level2 eligibility
reports, proposal ledgers, review ledgers, or unaccepted candidates.

## Claim Classes

A future promotion phase must keep claim classes separated:

- local replay evidence;
- external backend replay evidence;
- reproducible benchmark artifact evidence;
- official benchmark submission evidence;
- formal evidence;
- proof-system soundness evidence;
- ZK backend performance evidence.

Evidence in one class must not automatically populate another class. A
successful proof is not automatically semantic correctness. A benchmark pass is
not proof. Backend rejection is not automatically semantic correctness.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- accepted ledger tip mismatch rejection;
- stale append preview rejection;
- missing review approval rejection;
- unresolved quarantine rejection;
- missing external replay provenance rejection;
- local-only evidence promotion rejection;
- local soak telemetry performance promotion rejection;
- forbidden official/formal/soundness/performance claim text rejection;
- score-axis non-population without matching evidence class;
- accepted ledger append success for a fully reviewed fixture;
- official submission rejection before accepted evidence;
- official submission package digest determinism after accepted evidence;
- source scan proving no unreviewed mutation path exists.

Any live external replay or official submission interaction must be excluded
from normal tests unless a later phase explicitly authorizes an operator-only
path.

## Required Non-Claims

Every future accepted mutation and official submission package must state:

- Evidence append proposals are not accepted evidence.
- Evidence-record candidates are not accepted evidence.
- Append previews are not accepted evidence.
- Level2 eligibility reports are not Level2 evidence.
- Local artifact campaigns are not accepted Evidence Ledger entries.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.
- Accepted evidence is scoped to the reviewed claim only.

## Forbidden In This Slice

- Rust source or test changes.
- Cargo metadata changes.
- Generated benchmark artifact files.
- Durable campaign output files.
- Accepted Evidence Ledger mutation.
- Official benchmark submission.
- External replay.
- Live backend execution.
- Network access.
- Credentials or secrets.
- External result import.
- Command-line tools.
- UI dashboards.
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies.
- Score-axis population.
- ZK backend performance claims.
- Level2+ evidence creation.
- Broad leaderboard claims.

## Acceptance Criteria For This Slice

- This spec exists and names the future reviewed promotion/submission boundary.
- README navigation links this spec.
- `docs/12-task-list.md` records this docs-first boundary.
- `AGENTS.md` authorizes only this Markdown planning slice.
- `docs/90-whole-codebase-validation-report.md` records that accepted evidence
  mutation and official submission remain unimplemented.
- Validation confirms no Rust source, Cargo metadata, generated artifact,
  package runtime, credential, external replay, official submission, accepted
  Evidence Ledger, or score report changed.

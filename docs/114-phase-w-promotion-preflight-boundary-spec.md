# Phase W Promotion Preflight Boundary Spec

Status: docs-first implementation boundary only.

This phase authorizes a narrow inert implementation below the Phase W reviewed
evidence-promotion contract. It may add local Rust metadata, validation helpers,
deterministic digesting, Markdown rendering, serialization helpers, and hermetic
tests that prove the promotion and official-submission gates fail closed unless
their required preconditions are present.

It does not authorize accepted Evidence Ledger mutation, official benchmark
submission, generated benchmark artifact files, external replay, live backend
execution, network access, credentials, score-axis population, ZK backend
performance claims, Level2+ evidence creation, or treating any local-only
artifact as accepted evidence.

## State Slice

This implementation-boundary phase may touch only:

- `docs/114-phase-w-promotion-preflight-boundary-spec.md`
- a future implementation notes file under `docs/`
- additive Rust source under `crates/zkbench-core/src/`
- additive or focused tests under `crates/zkbench-core/tests/`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No generated campaign output, generated benchmark artifact, accepted Evidence
Ledger file, official submission output, external replay output, package
runtime file, JavaScript/TypeScript file, credential, secret, CI file, or
operator-live artifact is in this slice.

## Authorized Implementation Surface

A future code commit under this boundary may define:

- a reviewed promotion preflight request;
- a promotion source summary over existing candidates, append previews, local
  campaign metadata, review decisions, provenance digests, and ledger tip
  digests;
- a validation report with fail-closed issue kinds;
- required non-claim labels;
- deterministic JSON serialization;
- deterministic Markdown rendering;
- deterministic digest helpers;
- an inert official-submission package metadata structure that can validate and
  render only when accepted evidence ids are present;
- source-scan tests proving no accepted-ledger append helper, external replay,
  network, process, credential, CLI, or official submitter surface was added.

The implementation must reuse existing evidence, artifact, review, and local
campaign types where possible. It must not introduce a second accepted ledger
model or a hidden mutation path.

## Required Rejections

The implementation must reject:

- missing source candidates;
- missing append previews;
- stale or mismatched current ledger tip digests;
- append previews that claim mutation;
- missing human review approval;
- unresolved quarantine or blocking issue markers;
- missing external replay provenance for Level2+ promotion;
- local-only evidence promotion to accepted evidence;
- local soak telemetry as ZK backend performance evidence;
- missing source artifact digests;
- forbidden official, formal, soundness, performance, or broad leaderboard
  claim text;
- score-axis population without a matching accepted evidence class;
- official submission package construction before accepted evidence ids exist.

## Required Non-Claims

Every preflight report and submission-package metadata value must preserve:

- Promotion preflight reports are not accepted evidence.
- Promotion preflight reports do not mutate EvidenceLedger.
- Local artifact campaigns are not accepted Evidence Ledger entries.
- Append previews are not accepted evidence.
- Evidence-record candidates are not accepted evidence.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.
- Official submission requires a separate external submission operation.
- Accepted evidence is scoped to the reviewed claim only.

## Forbidden In This Slice

- Accepted Evidence Ledger mutation.
- Official benchmark submission.
- External replay.
- Live backend execution.
- Network access.
- Credentials or secrets.
- Command-line tools.
- UI dashboards.
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies.
- Generated benchmark artifact files.
- Durable campaign output files.
- Score-axis population.
- ZK backend performance claims.
- Level2+ evidence creation.
- Broad leaderboard claims.
- New accepted-evidence class semantics.

## Acceptance Criteria

- This boundary exists and names the inert implementation surface.
- README, `docs/12-task-list.md`, `docs/90-whole-codebase-validation-report.md`,
  and `AGENTS.md` record the boundary.
- The later code implementation, if included, remains metadata-only and
  fail-closed.
- Hermetic tests cover both successful preflight metadata validation and the
  required rejection cases.
- Validation confirms there is no accepted Evidence Ledger mutation, official
  submission, external replay, live backend execution, network access,
  credential path, generated benchmark artifact, score-axis population, or
  package runtime addition.

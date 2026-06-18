# Phase Q-A Report Bundle Boundary Spec

Status: docs-first boundary only.

Phase Q-A defines the next report surface after Phase P-A read-only reporting.
It does not authorize Rust implementation code, report-bundle generation, UI
dashboard work, external replay, live backend execution, official benchmark
evidence, ZK backend performance claims, Level2+ evidence creation, broad
leaderboard claims, or accepted Evidence Ledger mutation.

Follow-up status: Phase Q-B implements only the inert in-memory metadata subset
of this contract. Report-bundle materialization, writer/reader APIs, CLI
surface, UI dashboard work, execution, and evidence promotion still require a
separate explicit phase.

## State Slice

This phase is limited to Markdown specification and navigation updates under:

- `docs/68-phase-q-report-bundle-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`

No crate, test fixture, generated artifact, benchmark pack, local replay result,
Evidence Record, Score Report, or report-bundle output is changed by this phase.

## Purpose

Phase P-A proved that a read-only `DashboardModel` can summarize conservative
`ScoreReport`, `PackReadinessReport`, and `PackReadinessValidation` metadata
without escalating claims. Phase Q-A defines the next inert packaging boundary:
a report bundle is a read-only collection of existing local reporting metadata,
rendered text, and source references that can be inspected by humans and future
tools.

The report bundle exists to make local evidence boundaries easier to audit. It is
not evidence by itself.

## Allowed Bundle Contents

A future Phase Q implementation may package only inert local reporting inputs:

- one or more existing `ScoreReport` values;
- zero or more existing `PackReadinessReport` values;
- zero or more existing `PackReadinessValidation` values;
- rendered Markdown produced from existing read-only report models;
- source artifact references using portable relative paths;
- deterministic digest references for every included local input;
- claim-boundary summary text capped by the weakest included input;
- explicit warnings for local-only, failed, incomplete, or stale readiness
  metadata;
- a bundle manifest that states its own `Claim Boundary`.

The bundle may name the repo terms it summarizes: Surface DSL, Parsed AST,
Semantic IR, Benchmark Family, Benchmark Instance, Mutation Variant, Oracle,
Expected Verdict, Backend Outcome, Evidence Record, Claim Boundary, and Score
Report. Naming those terms must not imply that the bundle created new evidence.

## Required Validation Rules

A future implementation must fail closed when:

- a bundle source path is absolute or escapes the bundle root;
- an included digest does not match the referenced local input bytes;
- the bundle manifest omits a source artifact reference;
- the bundle manifest omits a `Claim Boundary`;
- the bundle claim boundary exceeds any included input boundary;
- the bundle claims Level2+ evidence without a separate reviewed promotion
  phase;
- the bundle claims official benchmark evidence;
- the bundle claims ZK backend performance;
- the bundle contains replay-command execution output;
- the bundle mutates or claims to mutate the accepted Evidence Ledger;
- a rendered report hides failed pack-readiness validation;
- a rendered report treats local soak telemetry as prover/verifier timing.

## Claim Boundary

The maximum output boundary for Phase Q-A planning is `Level0DesignNote`.

A future local implementation may remain `Level0DesignNote` unless a separate
reviewed phase explicitly authorizes a stronger boundary. The report bundle must
not elevate the boundary of any included `ScoreReport`, readiness report,
validation report, local replay artifact, or Evidence Record.

Use these statements as hard labels in future bundle output:

- Report bundles are not accepted evidence.
- Report bundles are local integrity summaries, not official benchmark evidence.
- Report bundles do not create Level2+ evidence.
- Report bundles do not prove backend performance.
- Local replay artifacts are not official benchmark evidence.
- Internal timing telemetry is not ZK backend performance.

## Non-Goals

Phase Q-A does not permit:

- Rust source or test changes;
- a bundle writer or reader;
- command-line tools;
- browser or UI dashboard work;
- JavaScript, TypeScript, package scripts, lockfiles, or node dependencies;
- external replay;
- live backend execution;
- external repo clones or vendored source;
- official benchmark evidence;
- ZK backend performance claims;
- Level2+ evidence creation;
- accepted Evidence Ledger mutation;
- score-axis population from local-only evidence;
- broad leaderboard claims.

## Future Materialization Exit Criteria

A future materialization phase must include:

- deterministic serialization for the report-bundle manifest;
- digest validation for every included local input;
- portable-path validation for every source reference;
- claim-boundary validation capped by the weakest included input;
- Markdown rendering that keeps failed readiness and local-only warnings visible;
- regression tests proving no accepted Evidence Ledger mutation;
- source scans proving no external execution hooks were added;
- documentation updates that preserve the Phase Q claim labels.

Phase Q-A itself exits when this boundary spec and navigation updates are
committed.

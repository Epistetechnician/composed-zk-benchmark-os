# Phase W External Replay Preflight Output Boundary Spec

## Status

Docs-first boundary for a future local output-root materializer for Phase 123
external replay submission preflight reports.

This boundary does not authorize implementation code. It does not run external
replay, call a benchmark endpoint, use credentials, create committed generated
artifacts, populate score axes, mutate accepted Evidence Ledgers, or create
Level2+ evidence.

## State Slice

This docs-first phase may touch only:

- `docs/124-phase-w-external-replay-preflight-output-boundary-spec.md`
- `docs/12-task-list.md`
- `README.md`
- `AGENTS.md`
- `docs/90-whole-codebase-validation-report.md`

No Rust source, tests, Cargo metadata, generated benchmark artifact,
official-submission package output, external replay artifact output, accepted
Evidence Ledger JSON file, score report, package runtime file, CLI/UI surface,
credential path, network path, external replay runner, or official endpoint is
changed by this phase.

## Purpose

Phase 123 added local in-memory validation and report construction for the
external replay submission preflight. It deliberately did not write generated
files.

The next durable-artifact gap is a filesystem contract for a future local
preflight output bundle. That future bundle must remain local review metadata:
it may preserve deterministic preflight inputs, report JSON, rendered Markdown,
redaction notes, non-claims, and digest sidecars, but it must not be treated as
external replay evidence, official benchmark evidence, or authorization to call
an endpoint.

## Future Input Contract

A future implementation phase may materialize a local output root only from
explicit caller-selected inputs:

- a valid `ExternalReplaySubmissionPreflightRequest`;
- a valid `ExternalReplaySubmissionPreflightReport`;
- an explicit non-empty output root outside the repository;
- an explicit overwrite mode;
- explicit protected paths including accepted ledgers, source packages,
  campaign outputs, package outputs, report bundles, and repository roots;
- deterministic redaction text that states raw credentials, tokens, transport
  transcripts, request bodies, and response bodies are excluded;
- the Phase 121 package digests that the preflight report validated;
- the required Phase 123 non-claim labels.

Missing inputs must fail closed.

## Future Artifact Contract

A future implementation must materialize only these declared files under the
caller-selected root:

- `external-replay-submission/input-manifest.json`
- `external-replay-submission/preflight-report.json`
- `external-replay-submission/preflight-report.md`
- `external-replay-submission/redaction-report.json`
- `external-replay-submission/submission-package-digests.json`
- `external-replay-submission/non-claims.md`
- `external-replay-submission/digests/input-manifest.sha256`
- `external-replay-submission/digests/preflight-report-json.sha256`
- `external-replay-submission/digests/preflight-report-md.sha256`
- `external-replay-submission/digests/redaction-report.sha256`
- `external-replay-submission/digests/submission-package-digests.sha256`
- `external-replay-submission/digests/non-claims.sha256`

The future materializer must write deterministic bytes, recompute every digest
from materialized bytes, and read back only declared files when validating an
existing bundle.

No raw endpoint request, raw endpoint response, credential, token, TLS
transcript, replay transcript, private operator configuration, or benchmark
service account material may be written.

## Required Future Rejections

The future materializer must reject:

- missing or invalid preflight request;
- missing or invalid preflight report;
- request and report digest drift;
- report side-effect flags that indicate external replay, endpoint submission,
  accepted-ledger mutation, generated benchmark artifact writes, or score-axis
  population;
- output roots inside the repository;
- empty output roots unless creation is explicit;
- non-empty output roots unless overwrite is explicit;
- absolute declared bundle paths;
- parent-directory path components;
- symlink roots, symlink parents, and symlink bundle files;
- output roots that overlap accepted ledgers, source packages, campaign
  outputs, package outputs, report bundles, audit-index outputs, or repository
  roots;
- missing required declared files;
- unexpected files;
- stale digest sidecars;
- raw credential, token, request, response, transcript, or operator-private
  material;
- any default endpoint, default credential, default benchmark target, default
  output root, or implicit operator acknowledgement;
- broad SOTA, leaderboard, formal, soundness, semantic-correctness, or
  production-readiness claims.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- valid local preflight bundle materialization;
- deterministic JSON, Markdown, redaction-report, non-claim, package-digest,
  and digest-sidecar output;
- request/report drift rejection;
- side-effect flag rejection;
- protected-root, repository-root, symlink, path traversal, partial-output,
  unexpected-output, stale-digest, and overwrite-drift rejection;
- raw credential, raw token, raw request, raw response, and raw transcript
  retention rejection;
- source scans proving no default endpoint, default credential, network call,
  process execution, external replay runner, or official submission path is
  reachable in normal gates.

Normal tests must remain hermetic and must not require credentials, network,
live backend access, operator secrets, or official benchmark infrastructure.

## Non-Goals

This boundary does not authorize Rust implementation, tests, Cargo metadata
changes, generated output files, committed external replay artifacts, committed
official-submission artifacts, accepted Evidence Ledger mutation, official
benchmark submission, external replay execution, live backend execution,
network access, credentials or secrets, command-line tools, UI dashboards,
JavaScript/TypeScript/package runtime additions, score-axis population, ZK
backend performance claims, Level2+ evidence creation, formal evidence
creation, broad leaderboard claims, SOTA claims, production-readiness claims,
or semantic-correctness claims.

## Claim Boundary

This boundary is planning only. A future local preflight output bundle would be
durable review metadata only. It would not be external replay evidence. It
would not be official benchmark evidence. It would not be accepted Evidence
Ledger mutation. It would not be score-axis population. It would not be Level2+
evidence. It would not be ZK backend performance evidence. It would not be
proof-system soundness evidence. It would not be semantic correctness evidence.
It would not be production readiness.

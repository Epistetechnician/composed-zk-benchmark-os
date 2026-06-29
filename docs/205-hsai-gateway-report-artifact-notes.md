# Phase 205 HSAI Gateway Report Artifact Notes

Status: implemented for local, hermetic gateway report artifacts.

State slice:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/205-hsai-gateway-report-artifact-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Goal

Phase 204 evaluates gateway action proposals in memory. Phase 205 adds the
smallest durable local report surface: deterministic JSON bytes, deterministic
Markdown bytes, SHA-256 bindings, a manifest, and validation checks over a
`GatewayCorpusReport`.

This makes the Agent Approval Gateway easier to demonstrate and compare without
adding model execution, filesystem materialization, package runtime code,
network access, signer integration, or benchmark evidence.

## Implemented Surface

New local report artifact types:

- `GatewayReportValidationIssue`
- `GatewayReportArtifactError`
- `GatewayReportArtifactManifest`
- `GatewayReportArtifact`

New local helpers:

- `gateway_report_required_nonclaims`
- `validate_gateway_corpus_report`
- `gateway_report_artifact`
- `render_gateway_report_markdown`

The manifest records the schema version, claim boundary, policy id, report
digest, journal tip digest, JSON SHA-256, Markdown SHA-256, required nonclaims,
and local metrics.

## Validation Behavior

Report validation rejects stale or inconsistent report state before producing an
artifact:

- invalid journal chain;
- stale total case count;
- stale accepted/rejected/quarantined counts;
- accepted-handoff count drift;
- decision recomputation count drift;
- audit-completeness drift.

The artifact does not validate model quality, semantic correctness, production
safety, or external truth. It validates only local report consistency.

## Trust Rules

- The report is local metadata only.
- The report is not benchmark evidence.
- The report is not proof.
- The report is not production readiness.
- The report is not semantic correctness.
- The report is not global software-agent uniqueness.
- The report is not a fully secure system.
- Accepted handoffs remain metadata until a later explicitly authorized
  integration phase.

## Focused Tests

Implemented tests cover:

- JSON and Markdown hash binding;
- required report nonclaims;
- deterministic artifact rendering for the same report;
- stale metric rejection before artifact creation.

## Validation Commands

Executed during implementation:

- `cargo test -p hsai-agent-admission --lib`

Final validation should also run:

- `cargo fmt --all --check`
- `git diff --check`
- `cargo test -p zkbench-core --test repo_hygiene`
- `cargo test -p zkbench-core --test repo_claim_boundary_docs`

## Claim Boundary

Phase 205 does not permit Cargo metadata changes, dependencies, package runtime
files, filesystem materialization, CLI/server/UI/dashboard work, model
execution/download, generated corpora/output bundles, secrets, credentials,
external replay execution, signer/wallet/exchange/custody/ACP/MCP integration
code, accepted Evidence Ledger mutation, score-axis population, benchmark
output, Level2+ evidence, production-readiness claims, semantic-correctness
claims, global software-agent uniqueness claims, "fully secure" claims, or
claims above `Attested`.

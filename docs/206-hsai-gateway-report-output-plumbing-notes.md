# Phase 206 HSAI Gateway Report Output Plumbing Notes

Status: implemented for local, hermetic gateway report output plumbing.

State slice:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/206-hsai-gateway-report-output-plumbing-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Goal

Phase 205 produced deterministic in-memory gateway report artifacts. Phase 206
adds the smallest local filesystem output path for those artifacts: a
caller-selected output root, declared `gateway-report/*` files, SHA-256
sidecars, strict readback validation, protected-root rejection, and tamper
detection.

This creates a durable local demo artifact without adding model execution,
network access, package runtime code, signer/tool authority, external replay, or
benchmark evidence.

## Implemented Surface

New local output types:

- `GatewayReportMaterializationRequest`
- `GatewayReportOutputManifest`
- `GatewayReportOutputValidationReport`
- `GatewayReportMaterializationError`

New local helpers:

- `materialize_gateway_report_bundle`
- `read_gateway_report_bundle`

Declared output files:

- `gateway-report/manifest.json`
- `gateway-report/report.json`
- `gateway-report/report.md`
- `gateway-report/non-claims.md`
- `gateway-report/validation-report.json`

Every declared file is written with a `.sha256` sidecar.

## Validation Behavior

Write and readback validation reject:

- empty or non-portable bundle ids;
- invalid report metrics or journal state;
- protected output roots;
- existing output roots without overwrite;
- file or symlink output roots;
- undeclared files;
- declared-file symlinks;
- sidecar symlinks;
- digest drift;
- malformed declared JSON;
- manifest semantic drift;
- nonclaim drift;
- validation-report drift.

## Trust Rules

- The materialized bundle is local metadata only.
- The materialized bundle is not benchmark evidence.
- The materialized bundle is not proof.
- The materialized bundle is not production readiness.
- The materialized bundle is not semantic correctness.
- The materialized bundle is not global software-agent uniqueness.
- The materialized bundle is not a fully secure system.
- No generated output bundle is committed by this phase.

## Focused Tests

Implemented tests cover:

- declared files and sidecars materialize;
- readback validates and equals the written manifest;
- protected roots are rejected;
- undeclared files are rejected;
- digest-consistent tampered report metrics are rejected.

## Validation Commands

Executed during implementation:

- `cargo test -p hsai-agent-admission --lib`

Final validation should also run:

- `cargo fmt --all --check`
- `git diff --check`
- `cargo test -p zkbench-core --test repo_hygiene`
- `cargo test -p zkbench-core --test repo_claim_boundary_docs`

## Claim Boundary

Phase 206 does not permit Cargo metadata changes, dependencies, package runtime
files, CLI/server/UI/dashboard work, model execution/download, committed
generated gateway report bundles, generated corpora/output bundles, secrets,
credentials, external replay execution, signer/wallet/exchange/custody/ACP/MCP
integration code, accepted Evidence Ledger mutation, score-axis population,
benchmark output, Level2+ evidence, production-readiness claims,
semantic-correctness claims, global software-agent uniqueness claims, "fully
secure" claims, or claims above `Attested`.

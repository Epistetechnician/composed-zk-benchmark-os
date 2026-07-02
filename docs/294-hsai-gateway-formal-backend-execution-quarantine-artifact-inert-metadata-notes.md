# Phase 294 HSAI Gateway Formal Backend Execution Quarantine Artifact Inert Metadata Notes

State slice: `Phase 294 HSAI gateway formal backend execution quarantine artifact inert metadata`.

## Status

Complete for local inert quarantine artifact metadata.

## Purpose

Phase 293 defined the quarantine artifact boundary for future formal backend
process-result summaries. Phase 294 adds the local Rust metadata surface that
can describe an operator-supplied, bounded, redacted process result without
executing a command or promoting the result into evidence.

This phase does not implement a backend runner.

## Implemented Surface

Phase 294 adds `hsai-agent-admission` types and validation for:

- `GATEWAY_FORMAL_BACKEND_EXECUTION_QUARANTINE_ARTIFACT_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_BACKEND_EXECUTION_QUARANTINE_ARTIFACT_STATE_SLICE`;
- `GATEWAY_FORMAL_BACKEND_EXECUTION_QUARANTINE_ARTIFACT_CLAIM_BOUNDARY`;
- `GatewayFormalBackendExecutionQuarantineOutputSummary`;
- `GatewayFormalBackendExecutionQuarantineFileReference`;
- `GatewayFormalBackendExecutionQuarantineRedactionReport`;
- `GatewayFormalBackendExecutionQuarantineProofCheckerNonpromotionReport`;
- `GatewayFormalBackendExecutionQuarantineArtifactMetadata`;
- `GatewayFormalBackendExecutionQuarantineArtifactIssue`;
- `GatewayFormalBackendExecutionQuarantineArtifactValidation`;
- `gateway_formal_backend_execution_quarantine_artifact_required_nonclaims`;
- `gateway_formal_backend_execution_quarantine_artifact_claim_boundary`;
- `build_gateway_formal_backend_execution_quarantine_artifact_metadata`;
- `validate_gateway_formal_backend_execution_quarantine_artifact_metadata`.

## Validation Behavior

The validator binds quarantine metadata to the Phase 292 authorization output
manifest and rejects:

- invalid schema, artifact id, or state slice;
- invalid or escalated authorization metadata;
- escalated authorization output manifests;
- authorization output manifest digest drift;
- authorization request digest drift;
- preflight output manifest digest drift;
- transcript output manifest digest drift;
- command descriptor digest drift;
- environment descriptor digest drift;
- quarantine descriptor file digest drift;
- operator acknowledgement digest drift;
- backend kind, tool name, tool version, toolchain, executable, or argv drift;
- invalid timeout or retained-output bound;
- invalid timestamp windows;
- missing or conflicting process status;
- invalid process exit status;
- summary stream drift;
- summary digest drift;
- unbounded summaries;
- raw stdout, raw stderr, raw prover log, raw checker log, raw solver trace,
  credential, secret, accepted-evidence, or public-claim text retention;
- redaction reports that retain forbidden material;
- output inventory digest drift;
- invalid output references;
- output references that retain raw content;
- accepted Evidence Ledger, benchmark-output, source-correspondence,
  backend-run, preflight, transcript, or authorization bundle paths;
- proof/checker artifact promotion;
- raw proof/checker/solver/cache/source retention;
- checker success implying semantic correctness;
- process success implying accepted evidence;
- command spawning by this crate;
- accepted evidence creation;
- Level2+ evidence creation;
- score-axis population;
- authority grants;
- semantic-correctness, production-readiness, SOTA, breakthrough, or
  full-security claim text;
- required nonclaim drift.

## Tests

Focused tests cover:

- valid inert quarantine artifact metadata;
- deterministic metadata digest construction;
- authorization output manifest binding;
- authorization request binding;
- command, environment, quarantine, and operator digest drift;
- backend/tool/toolchain/executable/argv drift;
- invalid timeout and process-status fields;
- raw summary and forbidden summary text rejection;
- redaction report rejection;
- protected output-reference rejection;
- proof/checker nonpromotion rejection;
- authorization and manifest escalation rejection;
- public-claim escalation rejection;
- required nonclaim drift rejection.

## Anti-Goals

This phase does not permit:

- command execution;
- process spawning;
- backend runner implementation;
- filesystem quarantine bundle materialization;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or
  COBALT execution;
- generated proof artifact promotion;
- generated checker transcript promotion;
- raw prover log retention;
- raw checker log retention;
- raw solver trace retention;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- official benchmark submission;
- live provider calls;
- credential handling;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- global software-agent uniqueness claims;
- authority to execute an action.

## Validation Commands

- `cargo test -p hsai-agent-admission gateway_formal_backend_execution_quarantine_artifact`

## Next Slice

Phase 295 defined the docs-first filesystem output-bundle boundary for
`gateway-formal-backend-quarantine/*`.

The next implementation slice, if explicitly authorized, should add local
filesystem materialization and readback for the declared quarantine bundle. It
should still not execute a command, spawn a process, or promote proof/checker
artifacts.

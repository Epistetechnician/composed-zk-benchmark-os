# Phase 276 HSAI Gateway Formal Backend Run Inert Artifact Metadata Notes

State slice: `Phase 276 HSAI gateway formal backend-run inert artifact metadata`.

## Status

Complete for local inert backend-run artifact metadata.

## Purpose

Phase 275 defined the docs-first artifact boundary for a future hermetic
backend run. Phase 276 implements the first local metadata surface for that
boundary in `hsai-agent-admission` without running a backend and without
materializing a filesystem artifact bundle.

This phase answers one narrow question: can the repository represent a
not-yet-run backend artifact summary that is digest-bound to the existing
formal-adapter chain and fails closed if it claims execution or promotion?

## Implemented Surface

Phase 276 adds:

- `GATEWAY_FORMAL_BACKEND_RUN_ARTIFACT_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_BACKEND_RUN_ARTIFACT_STATE_SLICE`;
- `GATEWAY_FORMAL_BACKEND_RUN_ARTIFACT_CLAIM_BOUNDARY`;
- `GatewayFormalBackendRunExecutionMode`;
- `GatewayFormalBackendRunExitStatus`;
- `GatewayFormalBackendRunCheckerStatus`;
- `GatewayFormalBackendRunArtifactReference`;
- `GatewayFormalBackendRunArtifactMetadata`;
- `GatewayFormalBackendRunArtifactIssue`;
- `GatewayFormalBackendRunArtifactValidation`;
- `gateway_formal_backend_run_artifact_required_nonclaims`;
- `gateway_formal_backend_run_artifact_claim_boundary`;
- digest helpers for modeled assumptions and unsupported Rust features;
- `build_gateway_formal_backend_run_artifact_metadata`;
- `validate_gateway_formal_backend_run_artifact_metadata`.

The builder creates only `NotRun` metadata. It binds:

- Phase 273 adapter request digest;
- Phase 273 adapter report digest;
- correspondence-certificate digest;
- correspondence output-manifest digest;
- backend kind;
- tool name and version;
- toolchain lock digest;
- requested proof obligations;
- modeled-assumption digest;
- unsupported-Rust-feature digest;
- explicit nonclaims.

## Fail-Closed Checks

The validator rejects:

- schema-version drift;
- unsafe run ids;
- state-slice drift;
- rejected or escalated adapter reports;
- adapter-request digest drift;
- adapter-report digest drift;
- correspondence-certificate digest drift;
- output-manifest digest drift;
- backend-kind drift;
- tool-name, tool-version, or toolchain-lock drift;
- any execution mode other than `NotRun`;
- submitted timestamps;
- any exit or checker status other than `NotRun`;
- requested proof-obligation drift;
- discharged or not-discharged proof obligations before a run;
- modeled-assumption digest drift;
- unsupported-feature digest drift;
- submitted proof artifact references;
- submitted checker transcript references;
- submitted tool-log summaries;
- unsafe, zero-digest, unredacted, or raw-content artifact references;
- accepted-evidence creation;
- Level2+ evidence creation;
- score-axis population;
- authority grants;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- full-security claims;
- forbidden public claim text;
- missing required nonclaims.

## Tests

Focused tests cover:

- valid inert metadata construction and validation;
- execution, timestamp, proof/checker reference, tool-log, evidence, score,
  authority, claim, and nonclaim escalation rejection;
- binding drift across schema, run id, state slice, adapter request, adapter
  report, correspondence certificate, output manifest, backend kind, tool
  metadata, proof obligations, modeled assumptions, unsupported features, and
  claim boundary.

## Nonclaims

Phase 276 does not:

- run Lean, SMT, COBALT, Aeneas, Hax, rust-lean, Z3, CBMC, Coq, TLA+, or any
  formal backend;
- create proof artifacts;
- create checker transcripts;
- materialize the `gateway-formal-backend-run/*` filesystem bundle;
- retain raw prover logs;
- retain raw checker logs;
- clone external repositories;
- vendor external source;
- mutate accepted Evidence Ledger files;
- create accepted evidence;
- create Level2+ evidence;
- populate score axes;
- create benchmark evidence;
- submit to an official benchmark;
- establish semantic correctness;
- establish production readiness;
- establish SOTA;
- establish breakthrough status;
- establish full security;
- prove HSAI;
- grant authority to execute an action.

## Next Slice

The next responsible slice was completed as Phase 277. It defines the
materialized `gateway-formal-backend-run/*` read/write rules before code writes
any files.

The following implementation slice, if explicitly authorized, should add inert
bundle materialization and readback code while preserving `NotRun` status and
all nonpromotion rules.

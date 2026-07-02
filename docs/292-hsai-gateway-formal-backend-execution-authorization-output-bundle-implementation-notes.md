# Phase 292 HSAI Gateway Formal Backend Execution Authorization Output-Bundle Implementation Notes

State slice: `Phase 292 HSAI gateway formal backend execution authorization output-bundle implementation`.

## Status

Complete for local inert authorization output-bundle materialization and
readback.

## Purpose

Phase 291 defined the docs-first filesystem boundary for a future local bundle
over Phase 290 execution-authorization metadata. Phase 292 implements that
local filesystem materializer and readback validator in `hsai-agent-admission`.

This phase does not execute a backend and does not authorize a runner.

## Implemented Surface

Phase 292 adds:

- authorization output-bundle state-slice and claim-boundary constants;
- output schema and declared file constants for
  `gateway-formal-backend-authorization/*`;
- `GatewayFormalBackendExecutionAuthorizationOutputRequest`;
- `GatewayFormalBackendExecutionAuthorizationPreflightBinding`;
- `GatewayFormalBackendExecutionAuthorizationTranscriptBinding`;
- `GatewayFormalBackendExecutionAuthorizationCommandBinding`;
- `GatewayFormalBackendExecutionAuthorizationEnvironmentBinding`;
- `GatewayFormalBackendExecutionAuthorizationOutputManifest`;
- `GatewayFormalBackendExecutionAuthorizationOutputError`;
- declared file helper;
- output claim-boundary helper;
- staged materialization with `.sha256` sidecars;
- readback validation;
- manifest recomputation and semantic checks;
- authorization request shape validation for readback;
- preflight, transcript, command, environment, quarantine, operator
  acknowledgement, and nonclaim component checks;
- output-root validation using the existing safe output-root contract;
- focused tests for valid materialization/readback, invalid authorization
  rejection before write, component drift rejection, stale sidecar rejection,
  and undeclared-file rejection.

## Declared Files

The implementation writes exactly:

- `gateway-formal-backend-authorization/manifest.json`;
- `gateway-formal-backend-authorization/authorization-request.json`;
- `gateway-formal-backend-authorization/preflight-binding.json`;
- `gateway-formal-backend-authorization/transcript-binding.json`;
- `gateway-formal-backend-authorization/command-binding.json`;
- `gateway-formal-backend-authorization/environment-binding.json`;
- `gateway-formal-backend-authorization/quarantine-descriptor.json`;
- `gateway-formal-backend-authorization/operator-acknowledgement.json`;
- `gateway-formal-backend-authorization/nonclaims.md`.

Every declared file receives a sibling `.sha256` sidecar over exact file bytes.

## Readback Rejections

Readback rejects:

- missing declared files;
- missing sidecars;
- stale sidecars;
- undeclared files;
- malformed declared JSON;
- output-root files or symlinks;
- declared-file symlinks;
- declared-sidecar symlinks;
- preflight-binding drift;
- transcript-binding drift;
- command-binding drift;
- environment-binding drift;
- quarantine descriptor drift;
- operator acknowledgement drift;
- nonclaim Markdown drift;
- manifest semantic drift;
- authorization request shape drift;
- any nonpromotion flag escalation visible in the authorization request or
  manifest.

## Tests

Added focused tests:

- `gateway_formal_backend_execution_authorization_output_bundle_materializes_and_reads_back`;
- `gateway_formal_backend_execution_authorization_output_bundle_rejects_invalid_before_write`;
- `gateway_formal_backend_execution_authorization_output_bundle_rejects_readback_drift`;
- `gateway_formal_backend_execution_authorization_output_bundle_rejects_sidecar_and_undeclared_drift`.

## Anti-Goals

This phase does not permit:

- Cargo metadata changes;
- package runtime files;
- command execution;
- process spawning;
- backend runner implementation;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or
  COBALT execution;
- generated proof artifacts;
- generated checker transcripts;
- raw prover logs;
- raw checker logs;
- raw solver traces;
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

## Next Slice

Phase 293 defined the docs-first execution quarantine artifact boundary.

The next implementation slice, if explicitly authorized, should add inert
quarantine artifact metadata in `hsai-agent-admission`. It should still not
execute any command.

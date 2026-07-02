# Phase 290 HSAI Gateway Formal Backend Execution Authorization Inert Metadata Notes

State slice: `Phase 290 HSAI gateway formal backend execution authorization inert metadata`.

## Status

Complete for local inert execution-authorization metadata.

## Purpose

Phase 289 defined the docs-first authorization boundary for a future local,
operator-approved formal backend execution experiment. Phase 290 implements the
metadata-only authorization record and validator in `hsai-agent-admission`.

This phase does not execute a backend and does not authorize a runner.

## Implemented Surface

Phase 290 adds:

- execution-authorization schema, state-slice, and claim-boundary constants;
- `GatewayFormalBackendExecutionAuthorizationQuarantineDescriptor`;
- `GatewayFormalBackendExecutionAuthorizationOperatorAcknowledgement`;
- `GatewayFormalBackendExecutionAuthorizationRequest`;
- `GatewayFormalBackendExecutionAuthorizationIssue`;
- `GatewayFormalBackendExecutionAuthorizationValidation`;
- deterministic digest helpers for the new authorization records;
- required authorization nonclaim labels;
- a preflight-bound quarantine descriptor builder;
- an operator-acknowledgement builder;
- an authorization-request builder;
- fail-closed validation for Phase 283 preflight output-bundle binding;
- fail-closed validation for Phase 287 transcript output-bundle binding;
- fail-closed validation for command, argv, toolchain, timeout, retention,
  environment, network, secret, quarantine, operator-acknowledgement,
  proof-obligation, nonpromotion, and public-claim drift;
- focused unit tests for valid inert authorization metadata, binding drift, and
  execution/claim escalation rejection.

## Validation Semantics

The authorization validator accepts only metadata that remains bound to:

- the exact Phase 283 preflight output manifest;
- the exact Phase 281 preflight request and report digests;
- the exact Phase 285 transcript metadata digest;
- the exact Phase 287 transcript output manifest;
- the exact preflight command descriptor;
- the exact preflight environment descriptor;
- the exact preflight artifact-root descriptor;
- the exact preflight redaction policy;
- an explicit local operator acknowledgement;
- a quarantine-only output descriptor.

It rejects:

- command or argv drift;
- tool name, version, backend kind, or toolchain drift;
- timeout or retained-output drift;
- environment allowlist drift;
- inherited credential-looking environment values;
- network-enabled or secret-enabled policy;
- quarantine roots that overlap accepted evidence, benchmark output,
  correspondence bundles, backend-run bundles, preflight bundles, transcript
  bundles, protected roots, files, symlinks, or symlink parents;
- missing or mismatched operator acknowledgements;
- any proof-obligation request before execution;
- command-spawned, backend-executed, proof-created, checker-created,
  checker-success, accepted-evidence, Level2+, score-axis, authority, semantic
  correctness, production-readiness, SOTA, or full-security promotion.

## Tests

Added focused tests:

- `gateway_formal_backend_execution_authorization_is_inert_metadata_only`;
- `gateway_formal_backend_execution_authorization_rejects_binding_drift`;
- `gateway_formal_backend_execution_authorization_rejects_execution_and_claim_escalation`.

## Anti-Goals

This phase does not permit:

- Cargo metadata changes;
- package runtime files;
- filesystem authorization bundle materialization;
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

Phase 291 defined the docs-first authorization output-bundle boundary.

The next implementation slice, if explicitly authorized, should implement the
local authorization output-bundle materializer and readback validator in
`hsai-agent-admission`. It should still not execute any command.

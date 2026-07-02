# Phase 296 HSAI Gateway Formal Backend Quarantine Output-Bundle Implementation Notes

State slice: `Phase 296 HSAI gateway formal backend quarantine output-bundle implementation`.

## Status

Complete for local filesystem materialization and readback of inert quarantine
output bundles.

## Purpose

Phase 295 defined the quarantine output-bundle boundary. Phase 296 implements
that boundary in `hsai-agent-admission` for local declared-file materialization
and readback of Phase 294 quarantine artifact metadata.

This phase does not implement a backend runner and does not execute a command.

## Implemented Surface

Phase 296 adds:

- `GATEWAY_FORMAL_BACKEND_EXECUTION_QUARANTINE_OUTPUT_STATE_SLICE`;
- `GATEWAY_FORMAL_BACKEND_EXECUTION_QUARANTINE_OUTPUT_CLAIM_BOUNDARY`;
- `GatewayFormalBackendExecutionQuarantineOutputRequest`;
- `GatewayFormalBackendExecutionQuarantineAuthorizationBinding`;
- `GatewayFormalBackendExecutionQuarantineProcessStatus`;
- `GatewayFormalBackendExecutionQuarantineOutputManifest`;
- `GatewayFormalBackendExecutionQuarantineOutputError`;
- `gateway_formal_backend_execution_quarantine_output_declared_files`;
- `gateway_formal_backend_execution_quarantine_output_claim_boundary`;
- `materialize_gateway_formal_backend_execution_quarantine_output_bundle`;
- `read_gateway_formal_backend_execution_quarantine_output_bundle`.

## Declared Files

The implementation writes only:

- `gateway-formal-backend-quarantine/manifest.json`;
- `gateway-formal-backend-quarantine/quarantine-artifact.json`;
- `gateway-formal-backend-quarantine/authorization-binding.json`;
- `gateway-formal-backend-quarantine/process-status.json`;
- `gateway-formal-backend-quarantine/stdout-summary.json`;
- `gateway-formal-backend-quarantine/stderr-summary.json`;
- `gateway-formal-backend-quarantine/redaction-report.json`;
- `gateway-formal-backend-quarantine/output-inventory.json`;
- `gateway-formal-backend-quarantine/proof-checker-nonpromotion.json`;
- `gateway-formal-backend-quarantine/nonclaims.md`;
- one `.sha256` sidecar per declared file.

## Validation Behavior

Materialization rejects invalid quarantine metadata before writing. Readback:

- rejects output root drift;
- rejects undeclared files;
- rejects stale sidecars;
- rejects malformed JSON;
- parses every declared component;
- validates the embedded quarantine artifact shape;
- recomputes manifest semantics;
- recomputes all declared file digests;
- checks authorization binding drift;
- checks process status drift;
- checks stdout and stderr summary drift;
- checks redaction report drift;
- checks output inventory drift;
- checks proof/checker nonpromotion drift;
- checks nonclaim Markdown drift;
- rejects manifest claim escalation.

## Tests

Focused tests cover:

- valid materialization and readback;
- invalid quarantine artifact rejection before write;
- invalid bundle id rejection;
- stdout summary drift rejection;
- nonclaim Markdown drift rejection;
- manifest semantic drift rejection;
- stale sidecar rejection;
- undeclared raw stdout rejection.

## Anti-Goals

This phase does not permit:

- command execution;
- process spawning;
- backend runner implementation;
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

- `cargo test -p hsai-agent-admission gateway_formal_backend_execution_quarantine_output_bundle`

## Next Slice

Phase 297 defined the docs-first quarantine output-bundle drift coverage
boundary, and Phase 298 implemented the focused local tests.

The next responsible slice is a docs-first boundary for a local quarantine
output-bundle validation-summary artifact. It should still not execute a
command, spawn a process, or promote proof/checker artifacts.

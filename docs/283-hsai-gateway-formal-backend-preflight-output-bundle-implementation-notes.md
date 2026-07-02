# Phase 283 HSAI Gateway Formal Backend Preflight Output-Bundle Implementation Notes

State slice: `Phase 283 HSAI gateway formal backend preflight output-bundle implementation`.

## Status

Complete for local preflight output-bundle materialization and readback.

## Purpose

Phase 282 defined the docs-first filesystem bundle contract for Phase 281
preflight metadata. Phase 283 implements that contract in
`crates/hsai-agent-admission/src/lib.rs`.

This phase still does not execute a backend.

## Implemented Surface

Phase 283 adds:

- `GatewayFormalBackendPreflightOutputRequest`;
- `GatewayFormalBackendPreflightOutputManifest`;
- `GatewayFormalBackendPreflightOutputError`;
- declared `gateway-formal-backend-preflight/*` files and sidecars;
- staged filesystem materialization;
- declared-file-only readback;
- manifest recomputation;
- semantic readback validation;
- drift rejection for preflight request/report, command descriptor,
  environment descriptor, artifact-root descriptor, operator acknowledgement,
  redaction policy, nonclaims, sidecars, and manifest flags;
- focused tests for valid materialization, invalid input rejection, and readback
  drift.

## Declared Files

The bundle contains only:

- `gateway-formal-backend-preflight/manifest.json`;
- `gateway-formal-backend-preflight/preflight-request.json`;
- `gateway-formal-backend-preflight/preflight-report.json`;
- `gateway-formal-backend-preflight/command-descriptor.json`;
- `gateway-formal-backend-preflight/environment-descriptor.json`;
- `gateway-formal-backend-preflight/artifact-root-descriptor.json`;
- `gateway-formal-backend-preflight/operator-acknowledgement.json`;
- `gateway-formal-backend-preflight/redaction-policy.json`;
- `gateway-formal-backend-preflight/nonclaims.md`.

Every declared file has a `.sha256` sidecar. Undeclared files are rejected.

## Accepted Valid Path

Materialization succeeds only when:

- the Phase 281 preflight request validates against the Phase 273 adapter
  request/report, Phase 276 run metadata, and Phase 278 backend-run bundle
  manifest;
- the supplied preflight report exactly matches the deterministic report
  produced from those inputs;
- the report is `ReadyCandidateOnly`;
- all execution, proof, checker, accepted-evidence, Level2+, score-axis, and
  authority flags remain false.

## Rejection Coverage

The implementation rejects:

- invalid Phase 281 preflight requests before writing;
- escalated or mismatched preflight reports before writing;
- protected output roots;
- file roots;
- symlink roots;
- stale sidecars;
- undeclared proof/checker attachments;
- manifest nonpromotion-flag drift;
- command descriptor drift;
- environment descriptor drift;
- artifact-root descriptor drift;
- operator acknowledgement drift;
- redaction-policy drift;
- nonclaim Markdown drift;
- malformed declared JSON.

## Tests

Focused tests added:

- `gateway_formal_backend_preflight_bundle_materializes_declared_files_and_readback`;
- `gateway_formal_backend_preflight_bundle_rejects_invalid_preflight_before_write`;
- `gateway_formal_backend_preflight_bundle_readback_rejects_drift`.

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

Implemented by Phase 284 as a docs-first backend execution transcript boundary.

The next implementation slice, if explicitly authorized, should add inert
backend execution transcript metadata in `hsai-agent-admission`. It should
validate transcript references, checker-status labels, redaction metadata,
proof-obligation coverage, and nonpromotion flags. It still should not execute
any command.

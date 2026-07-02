# Phase 282 HSAI Gateway Formal Backend Preflight Output-Bundle Boundary

State slice: `Phase 282 HSAI gateway formal backend preflight output-bundle boundary`.

## Status

Complete for the docs-first preflight output-bundle boundary.

## Purpose

Phase 281 implemented inert backend execution preflight metadata. Phase 282
defines the future filesystem bundle contract for materializing and reading
back that metadata.

This phase does not implement bundle materialization and does not execute a
backend.

## Future Bundle Scope

A future bundle may materialize only `gateway-formal-backend-preflight/*`
metadata files derived from a valid Phase 281 request/report.

The future bundle may contain:

- `gateway-formal-backend-preflight/manifest.json`;
- `gateway-formal-backend-preflight/preflight-request.json`;
- `gateway-formal-backend-preflight/preflight-report.json`;
- `gateway-formal-backend-preflight/command-descriptor.json`;
- `gateway-formal-backend-preflight/environment-descriptor.json`;
- `gateway-formal-backend-preflight/artifact-root-descriptor.json`;
- `gateway-formal-backend-preflight/operator-acknowledgement.json`;
- `gateway-formal-backend-preflight/redaction-policy.json`;
- `gateway-formal-backend-preflight/nonclaims.md`.

Every declared JSON or Markdown file must have a `.sha256` sidecar.

The bundle must not contain:

- proof artifacts;
- checker transcripts;
- raw prover logs;
- raw checker logs;
- raw solver traces;
- proof assistant caches;
- external repo source;
- accepted Evidence Ledger JSON;
- benchmark outputs;
- secrets;
- credentials;
- generated backend outputs.

## Output-Root Rules

A future implementation must reject output roots that are:

- empty;
- the repository root;
- inside protected repository roots;
- existing without explicit overwrite;
- files;
- symlinks;
- traversing through symlink parents;
- accepted Evidence Ledger paths;
- benchmark-output paths;
- source-correspondence bundle paths;
- Phase 278 backend-run input bundle paths;
- Phase 281 future artifact-root paths.

The implementation must use staged writes and read back the materialized bundle
before reporting success.

## Manifest Contract

A future manifest must include:

- schema version;
- bundle id;
- state slice;
- created timestamp;
- preflight request digest;
- preflight report digest;
- input backend-run bundle digest;
- command descriptor digest;
- environment descriptor digest;
- artifact-root descriptor digest;
- operator acknowledgement digest;
- redaction-policy digest;
- nonclaim digest;
- declared files;
- declared file digests;
- claim boundary;
- `backend_executed = false`;
- `proof_artifact_created = false`;
- `checker_transcript_created = false`;
- `creates_accepted_evidence = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- `grants_authority = false`;
- required nonclaims.

The manifest must be recomputable from the declared files. Digest-consistent
semantic drift must still be rejected.

## Readback Rules

A future reader must reject:

- missing declared files;
- undeclared files;
- malformed JSON;
- invalid UTF-8 in declared files or sidecars;
- stale sidecars;
- symlinked output roots;
- symlinked bundle directories;
- symlinked declared files;
- symlinked sidecars;
- manifest identity drift;
- command descriptor drift;
- environment descriptor drift;
- artifact-root descriptor drift;
- operator acknowledgement drift;
- redaction-policy drift;
- nonclaim Markdown drift;
- preflight report drift;
- any optional proof, checker, log, or raw-output attachment.

## Required Future Tests

A future implementation phase must add tests for:

- valid materialization and readback;
- invalid Phase 281 preflight request rejection before write;
- escalated Phase 281 preflight report rejection before write;
- protected-root rejection;
- file-root rejection;
- symlink-root rejection;
- symlinked declared-file rejection;
- undeclared-file rejection;
- stale sidecar rejection;
- malformed request JSON rejection;
- manifest nonpromotion-flag drift rejection;
- command descriptor drift rejection;
- environment descriptor drift rejection;
- artifact-root descriptor drift rejection;
- operator acknowledgement drift rejection;
- redaction-policy drift rejection;
- nonclaim Markdown drift rejection;
- optional proof/checker/log attachment rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- filesystem bundle materialization code;
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

Implemented by Phase 283 as local filesystem materialization and readback for
the Phase 281 preflight request and report.

The next responsible slice is a docs-first backend execution transcript
boundary. It should define the future shape of proof/checker transcript
references, redacted diagnostic summaries, and checker-output admission rules.
It still should not execute any command, create proof artifacts, create checker
transcripts, or promote evidence.

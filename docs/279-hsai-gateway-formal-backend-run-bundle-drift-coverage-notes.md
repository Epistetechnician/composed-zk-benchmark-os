# Phase 279 HSAI Gateway Formal Backend Run Bundle Drift Coverage Notes

State slice: `Phase 279 HSAI gateway formal backend-run bundle drift coverage`.

## Status

Complete for audit-first drift coverage over the Phase 278 backend-run bundle
reader.

## Purpose

Phase 278 implemented local inert materialization and readback for the
`gateway-formal-backend-run/*` metadata bundle. Phase 279 adds focused negative
tests for root drift, file drift, sidecar drift, manifest drift, redaction
drift, nonclaim drift, malformed run-summary JSON, and symlinked declared
files.

This phase changes no bundle format and runs no backend.

## Added Coverage

Phase 279 adds tests for:

- protected output-root rejection before write;
- file output-root rejection before write;
- file output-root rejection on readback;
- symlink output-root rejection before write;
- symlink output-root rejection on readback;
- stale run-summary sidecar rejection;
- manifest nonpromotion-flag drift rejection;
- malformed run-summary JSON rejection;
- redaction-report drift rejection;
- nonclaim Markdown drift rejection;
- symlink declared-file rejection.

The tests reuse the Phase 278 materialized bundle fixture and then mutate only
the target file or root under test.

## Claim Boundary

The added tests prove only local failure behavior for metadata-bundle readback.
They do not prove the gateway property, do not run a verifier, and do not
validate a proof artifact.

## Nonclaims

Phase 279 does not:

- change production bundle semantics;
- run Lean, SMT, COBALT, Aeneas, Hax, rust-lean, Z3, CBMC, Coq, TLA+, or any
  formal backend;
- create proof artifacts;
- create checker transcripts;
- retain raw prover logs;
- retain raw checker logs;
- retain raw solver traces;
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

The next responsible slice was completed as Phase 280. It defines the docs-first
backend execution preflight boundary: future command, environment, toolchain,
operator acknowledgement, artifact-root, no-network, no-secret, and
nonpromotion rules before any Lean, SMT, COBALT, or Rust-to-Lean command can
run.

The following implementation slice, if explicitly authorized, should add inert
backend execution preflight metadata. It still should not execute any command.

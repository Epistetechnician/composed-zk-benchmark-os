# Phase 295 HSAI Gateway Formal Backend Quarantine Output-Bundle Boundary

State slice: `Phase 295 HSAI gateway formal backend quarantine output-bundle boundary`.

## Status

Complete for the docs-first quarantine output-bundle boundary.

## Purpose

Phase 294 added inert quarantine artifact metadata. Phase 295 defines the
future filesystem contract for materializing that metadata under
`gateway-formal-backend-quarantine/*`.

This phase does not implement materialization and does not execute a backend.

## Future Bundle Scope

A future quarantine output bundle may materialize only local, declared,
digest-bound files derived from a valid
`GatewayFormalBackendExecutionQuarantineArtifactMetadata` value.

The bundle must remain local candidate metadata. It must not be accepted
evidence, Level2+ evidence, benchmark evidence, semantic proof, production
readiness, SOTA status, full security, or execution authority.

## Future Declared Files

A future bundle should use exactly this logical namespace:

- `gateway-formal-backend-quarantine/manifest.json`;
- `gateway-formal-backend-quarantine/quarantine-artifact.json`;
- `gateway-formal-backend-quarantine/authorization-binding.json`;
- `gateway-formal-backend-quarantine/process-status.json`;
- `gateway-formal-backend-quarantine/stdout-summary.json`;
- `gateway-formal-backend-quarantine/stderr-summary.json`;
- `gateway-formal-backend-quarantine/redaction-report.json`;
- `gateway-formal-backend-quarantine/output-inventory.json`;
- `gateway-formal-backend-quarantine/proof-checker-nonpromotion.json`;
- `gateway-formal-backend-quarantine/nonclaims.md`.

Each declared file must have a `.sha256` sidecar containing the SHA-256 digest
of the exact materialized bytes.

The future readback implementation must reject every undeclared file, including
raw stdout, raw stderr, raw prover logs, raw checker logs, raw SMT solver
traces, proof assistant caches, proof artifacts, checker transcripts, external
repo source, accepted evidence files, benchmark outputs, source-correspondence
bundles, backend-run bundles, preflight bundles, transcript bundles, and
authorization bundles.

## Future Manifest Fields

The future manifest must bind:

- schema version;
- bundle id;
- state slice;
- created timestamp;
- quarantine artifact digest;
- authorization output manifest digest;
- authorization request digest;
- preflight output manifest digest;
- transcript output manifest digest;
- command descriptor digest;
- environment descriptor digest;
- quarantine descriptor digest;
- operator acknowledgement digest;
- backend kind;
- tool name;
- tool version;
- toolchain lock digest;
- executable path label;
- argv digest;
- process status digest;
- stdout summary digest;
- stderr summary digest;
- redaction report digest;
- output inventory digest;
- proof/checker nonpromotion report digest;
- nonclaims digest;
- declared file list;
- declared file digest map;
- claim boundary;
- command-spawned-by-this-crate flag;
- accepted evidence creation flag;
- Level2 evidence creation flag;
- score-axis population flag;
- authority-granted flag;
- required nonclaims.

## Future Readback Rules

A future readback implementation must:

- reject empty, protected, file, symlink, or stale output roots;
- reject bundle directory symlinks;
- reject declared file symlinks;
- reject declared sidecar symlinks;
- reject missing declared files;
- reject missing sidecars;
- reject stale sidecars;
- reject malformed JSON;
- reject malformed UTF-8 Markdown;
- recompute the manifest from read bytes;
- recompute all component digests;
- validate the embedded quarantine artifact metadata;
- reject component drift even when sidecars are updated;
- reject nonclaim Markdown drift;
- reject any undeclared file;
- reject public-claim escalation.

## Required Future Tests

A future implementation phase must add tests for:

- valid declared-file materialization and readback;
- invalid quarantine artifact rejection before write;
- output root protected-path rejection;
- output root overwrite policy;
- stale sidecar rejection;
- missing sidecar rejection;
- malformed quarantine artifact JSON rejection;
- manifest semantic drift rejection;
- authorization binding drift rejection;
- process status drift rejection;
- stdout summary drift rejection;
- stderr summary drift rejection;
- redaction report drift rejection;
- output inventory drift rejection;
- proof/checker nonpromotion drift rejection;
- nonclaim Markdown drift rejection;
- undeclared raw stdout rejection;
- undeclared raw stderr rejection;
- undeclared prover log rejection;
- undeclared checker log rejection;
- undeclared solver trace rejection;
- undeclared proof artifact rejection;
- undeclared checker transcript rejection;
- undeclared accepted Evidence Ledger path rejection;
- undeclared benchmark output rejection;
- declared file symlink rejection;
- declared sidecar symlink rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- filesystem quarantine bundle materialization;
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

## Next Slice

Phase 296 implemented local filesystem materialization and readback for the
declared `gateway-formal-backend-quarantine/*` bundle.

The next docs-first slice should define quarantine output-bundle drift coverage
for protected roots, missing sidecars, malformed JSON, authorization binding
drift, process-status drift, stderr drift, redaction drift, inventory drift,
proof/checker nonpromotion drift, and declared-file symlink rejection.

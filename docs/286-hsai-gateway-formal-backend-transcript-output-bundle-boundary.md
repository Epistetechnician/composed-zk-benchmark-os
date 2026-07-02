# Phase 286 HSAI Gateway Formal Backend Transcript Output-Bundle Boundary

State slice: `Phase 286 HSAI gateway formal backend transcript output-bundle boundary`.

## Status

Complete for the docs-first transcript output-bundle boundary.

## Purpose

Phase 285 implemented inert transcript metadata. Phase 286 defines the future
filesystem bundle contract for materializing and reading back that metadata.

This phase does not implement bundle materialization, does not execute a
backend, and does not create proof or checker artifacts.

## Future Bundle Scope

A future bundle may materialize only `gateway-formal-backend-transcript/*`
metadata files derived from a valid Phase 285 transcript candidate.

The future bundle may contain:

- `gateway-formal-backend-transcript/manifest.json`;
- `gateway-formal-backend-transcript/transcript-metadata.json`;
- `gateway-formal-backend-transcript/preflight-binding.json`;
- `gateway-formal-backend-transcript/toolchain-binding.json`;
- `gateway-formal-backend-transcript/execution-status.json`;
- `gateway-formal-backend-transcript/checker-status.json`;
- `gateway-formal-backend-transcript/redaction-report.json`;
- `gateway-formal-backend-transcript/proof-obligations.json`;
- `gateway-formal-backend-transcript/nonclaims.md`.

Every declared JSON or Markdown file must have a `.sha256` sidecar.

The bundle must not contain:

- generated proof artifacts;
- generated checker transcripts;
- raw stdout;
- raw stderr;
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
- Phase 278 backend-run input bundle paths;
- Phase 283 preflight output-bundle paths;
- source-correspondence bundle paths;
- proof-artifact paths;
- checker-transcript paths;
- future backend artifact roots.

The implementation must use staged writes and read back the materialized bundle
before reporting success.

## Manifest Contract

A future manifest must include:

- schema version;
- bundle id;
- state slice;
- created timestamp;
- transcript metadata digest;
- preflight bundle manifest digest;
- preflight request digest;
- preflight report digest;
- command descriptor digest;
- backend kind;
- tool name;
- tool version;
- toolchain lock digest;
- execution status;
- checker status;
- redaction-report digest;
- proof-obligations digest;
- nonclaim digest;
- declared files;
- declared file digests;
- claim boundary;
- `backend_executed = false`;
- `proof_artifact_created = false`;
- `checker_transcript_created = false`;
- `checker_succeeded = false`;
- `creates_accepted_evidence = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- `grants_authority = false`;
- required nonclaims.

The manifest must be recomputable from the declared files. Digest-consistent
semantic drift must still be rejected.

## File Semantics

The future files must carry only bounded metadata:

- `transcript-metadata.json`: serialized Phase 285 transcript metadata;
- `preflight-binding.json`: preflight bundle, request, report, and command
  descriptor digests only;
- `toolchain-binding.json`: backend kind, tool name, tool version, and
  toolchain lock digest only;
- `execution-status.json`: `NotExecuted` and `NotRun` only in this bundle
  implementation phase;
- `checker-status.json`: `NotChecked` only in this bundle implementation phase;
- `redaction-report.json`: booleans proving raw or secret material was not
  retained;
- `proof-obligations.json`: empty requested, discharged, and nondischarged
  obligation sets in this bundle implementation phase;
- `nonclaims.md`: required nonclaims;
- `manifest.json`: declared logical paths, file digests, transcript digest,
  claim boundary, and nonpromotion flags.

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
- transcript metadata drift;
- preflight binding drift;
- toolchain binding drift;
- execution status drift;
- checker status drift;
- redaction-report drift;
- proof-obligation drift;
- nonclaim Markdown drift;
- any proof artifact attachment;
- any checker transcript attachment;
- any raw log attachment;
- any retained proof assistant cache marker;
- any accepted Evidence Ledger JSON;
- any benchmark output;
- any Level2+ evidence flag;
- any score-axis population;
- any authority grant;
- forbidden public claim text.

Readback must return local validation metadata only. It must not append to any
ledger and must not change evidence maturity.

## Required Future Tests

A future implementation phase must add tests for:

- valid materialization and readback;
- invalid Phase 285 transcript metadata rejection before write;
- escalated transcript metadata rejection before write;
- protected-root rejection;
- repository-root rejection;
- file-root rejection;
- symlink output-root rejection;
- symlink parent rejection;
- symlink declared-file rejection;
- symlink sidecar rejection;
- undeclared-file rejection;
- stale sidecar rejection;
- malformed transcript metadata JSON rejection;
- manifest nonpromotion-flag drift rejection;
- transcript metadata digest drift rejection;
- preflight binding drift rejection;
- toolchain binding drift rejection;
- execution status drift rejection;
- checker status drift rejection;
- redaction-report drift rejection;
- proof-obligation drift rejection;
- nonclaim Markdown drift rejection;
- proof artifact attachment rejection;
- checker transcript attachment rejection;
- raw stdout or stderr attachment rejection;
- proof assistant cache marker rejection;
- accepted Evidence Ledger path rejection;
- benchmark-output path rejection;
- Level2+ evidence escalation rejection;
- score-axis population rejection;
- authority grant rejection;
- forbidden public claim text rejection.

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

Implemented by Phase 287 as local filesystem materialization and readback for
the Phase 285 transcript metadata.

The next responsible slice is transcript output-bundle drift coverage. It
should add broader negative tests before any backend execution or proof/checker
artifact phase is considered.

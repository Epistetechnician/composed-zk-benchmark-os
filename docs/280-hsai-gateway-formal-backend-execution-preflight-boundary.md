# Phase 280 HSAI Gateway Formal Backend Execution Preflight Boundary

State slice: `Phase 280 HSAI gateway formal backend execution preflight boundary`.

## Status

Complete for the docs-first backend execution preflight boundary.

## Purpose

Phase 279 hardened local readback for the inert backend-run metadata bundle.
Phase 280 defines the preflight contract that must exist before any future
Lean, SMT, COBALT, Rust-to-Lean, Aeneas, Hax, Z3, CBMC, Coq, TLA+, or
model-checker command can run.

This phase does not implement a preflight runner and does not run a backend.

## Required Future Inputs

A future execution preflight may only inspect bounded metadata:

- Phase 273 backend-adapter request;
- Phase 273 backend-adapter report;
- Phase 276 backend-run metadata;
- Phase 278 backend-run bundle manifest;
- Phase 278 backend-run bundle output root;
- explicit operator acknowledgement;
- explicit command descriptor;
- explicit toolchain descriptor;
- explicit environment descriptor;
- explicit artifact-root descriptor;
- explicit redaction policy;
- explicit no-network and no-secret policy;
- explicit nonclaims.

The preflight must reject any missing input before checking commands.

## Command Descriptor

A future command descriptor must be inert metadata until a later implementation
phase authorizes command execution.

The descriptor must include:

- command id;
- backend kind;
- tool name;
- tool version;
- immutable toolchain lock digest;
- executable path label;
- exact argument vector;
- working-directory policy;
- expected input bundle digest;
- expected output artifact root;
- timeout seconds;
- maximum output bytes retained;
- allowed environment variable names;
- disallowed environment variable names;
- network policy;
- secret policy;
- claim boundary;
- nonclaims.

The command descriptor must not contain a shell string. It must model argv as a
vector. It must reject path traversal, absolute output paths inside the
repository, shell metacharacter fragments, credential-looking values, and
unbounded output capture.

## Allowed Future Backend Modes

The first future implementation may preflight only one backend lane at a time.

Allowed future modes:

- `RustToLeanPreflight`;
- `SmtContainmentPreflight`;
- `CobaltContainmentPreflight`;
- `FederatedDispatchPreflight`.

Any mixed-backend or federated execution must remain preflight-only until a
separate execution phase defines correspondence certificates for every backend.

## Environment Contract

The preflight must require:

- no network access by default;
- no credentials;
- no secrets;
- no inherited full environment;
- no mutable repository source tree;
- no writes outside caller-selected artifact roots;
- no writes to accepted Evidence Ledger paths;
- no writes to benchmark-output paths;
- no writes to source correspondence bundle paths;
- no writes to Phase 278 backend-run bundle input paths;
- no external repo clones;
- no vendored source imports;
- no proof assistant cache retention;
- bounded stdout/stderr summaries only;
- explicit redaction of any retained diagnostic summary.

Any future operator-only exception must be a separate explicit phase.

## Artifact-Root Contract

A future execution preflight must reject artifact roots that are:

- empty;
- the repository root;
- inside protected repository roots;
- existing without explicit overwrite;
- files;
- symlinks;
- traversing through symlink parents;
- accepted Evidence Ledger paths;
- benchmark-output paths;
- source correspondence bundle paths;
- Phase 278 backend-run input bundle paths.

The preflight must not create proof artifacts. It may only validate that a
future artifact root would be safe for a later execution phase.

## Operator Acknowledgement

Future execution preflight must require an explicit operator acknowledgement
record with:

- operator id;
- acknowledgement timestamp;
- backend kind acknowledged;
- command id acknowledged;
- input bundle digest acknowledged;
- artifact-root policy acknowledged;
- no-network policy acknowledged;
- no-secret policy acknowledged;
- nonpromotion policy acknowledged.

The acknowledgement must not grant action authority and must not promote
candidate evidence.

## Output Contract

A future preflight output may contain:

- schema version;
- preflight id;
- input bundle digest;
- command descriptor digest;
- environment descriptor digest;
- artifact-root descriptor digest;
- operator acknowledgement digest;
- redaction policy digest;
- readiness status;
- issue list;
- claim boundary;
- nonclaims;
- `backend_executed = false`;
- `proof_artifact_created = false`;
- `checker_transcript_created = false`;
- `creates_accepted_evidence = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- `grants_authority = false`.

The output must be local metadata only.

## Required Future Tests

A future implementation phase must add tests for:

- valid preflight metadata;
- missing operator acknowledgement rejection;
- shell-string command rejection;
- shell metacharacter rejection;
- path traversal rejection;
- repository-root artifact rejection;
- protected-root artifact rejection;
- symlink artifact-root rejection;
- inherited full environment rejection;
- credential-looking environment value rejection;
- network-enabled policy rejection in normal tests;
- accepted Evidence Ledger output path rejection;
- benchmark-output path rejection;
- source-bundle mutation path rejection;
- Phase 278 input-bundle mutation path rejection;
- unbounded timeout rejection;
- unbounded output retention rejection;
- backend execution flag rejection;
- proof artifact creation flag rejection;
- checker transcript creation flag rejection;
- Level2+ evidence escalation rejection;
- score-axis population rejection;
- authority grant rejection;
- forbidden public claim text rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- command execution;
- process spawning;
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

Implemented by Phase 281 as inert backend execution preflight metadata in
`hsai-agent-admission`.

The next responsible slice is a docs-first materialized preflight output-bundle
boundary. It should define declared files, digest sidecars, readback semantics,
and drift checks for `gateway-formal-backend-preflight/*`. It still should not
execute any command.

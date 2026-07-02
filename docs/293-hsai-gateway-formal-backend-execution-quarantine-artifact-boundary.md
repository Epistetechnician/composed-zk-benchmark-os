# Phase 293 HSAI Gateway Formal Backend Execution Quarantine Artifact Boundary

State slice: `Phase 293 HSAI gateway formal backend execution quarantine artifact boundary`.

## Status

Complete for the docs-first execution quarantine artifact boundary.

## Purpose

Phase 292 materialized inert execution authorization metadata. Phase 293 defines
the future quarantine artifact boundary that must exist before any formal
backend runner can record process results.

This phase does not implement a runner and does not execute a backend.

## Future Quarantine Scope

A future execution quarantine artifact may describe only the bounded, redacted
result of a local operator-approved command that has already passed:

- Phase 283 preflight output-bundle validation;
- Phase 287 transcript output-bundle validation;
- Phase 292 authorization output-bundle validation;
- exact command and argv binding;
- exact toolchain binding;
- exact environment allowlist binding;
- exact quarantine descriptor binding;
- operator acknowledgement binding.

The quarantine artifact must remain local candidate metadata until a later
review phase decides whether any part is eligible for transcript admission.

## Future Declared Fields

A future quarantine artifact record must bind:

- quarantine artifact id;
- authorization output-bundle digest;
- authorization request digest;
- preflight output-bundle digest;
- transcript output-bundle digest;
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
- working-directory policy;
- timeout policy;
- started timestamp;
- finished timestamp;
- process exit status;
- timeout flag;
- signal flag;
- bounded stdout summary digest;
- bounded stderr summary digest;
- redaction report digest;
- output file inventory digest;
- proof/checker nonpromotion report;
- claim boundary;
- required nonclaims.

## Allowed Future Retention

The future quarantine artifact may retain only:

- bounded stdout summary text or digest;
- bounded stderr summary text or digest;
- process exit status;
- start and finish timestamps;
- tool version and toolchain lock metadata;
- redaction report metadata;
- output file inventory metadata;
- digests of local quarantined files;
- nonclaim text.

Any retained summary must be bounded and must pass credential-looking,
secret-looking, raw-proof, raw-checker, and raw-solver trace scans.

## Required Future Rejections

A future implementation must reject:

- command not authorized by Phase 292 metadata;
- argv drift;
- executable path drift;
- toolchain drift;
- backend kind drift;
- environment drift;
- inherited full environment;
- credential-looking environment values;
- network-enabled execution;
- secret-enabled execution;
- write path outside quarantine root;
- accepted Evidence Ledger writes;
- benchmark-output writes;
- source-correspondence bundle writes;
- backend-run bundle writes;
- preflight bundle writes;
- transcript bundle writes;
- authorization bundle writes;
- raw stdout retention;
- raw stderr retention;
- raw prover log retention;
- raw checker transcript retention;
- raw SMT solver trace retention;
- proof assistant cache retention;
- generated proof artifact promotion;
- generated checker artifact promotion;
- external repo source retention;
- unbounded output inventory;
- checker success implying semantic correctness;
- process success implying accepted evidence;
- SOTA, full-security, semantic-correctness, or production-readiness claims.

## Future Tests

A future implementation phase must add tests for:

- valid local quarantine artifact metadata;
- authorization output-bundle digest drift rejection;
- command and argv drift rejection;
- environment drift rejection;
- network-enabled rejection;
- credential-looking environment rejection;
- timeout and signal status recording without claim promotion;
- bounded stdout summary acceptance;
- raw stdout rejection;
- raw stderr rejection;
- raw prover log rejection;
- raw checker transcript rejection;
- raw solver trace rejection;
- proof assistant cache rejection;
- generated proof artifact nonpromotion;
- checker artifact nonpromotion;
- accepted Evidence Ledger write-path rejection;
- benchmark-output write-path rejection;
- source-correspondence, backend-run, preflight, transcript, and authorization
  bundle write-path rejection;
- nonclaim drift rejection;
- forbidden public-claim text rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
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

Phase 294 implemented inert quarantine artifact metadata in
`hsai-agent-admission`.

The next docs-first slice should define the filesystem output-bundle boundary
for `gateway-formal-backend-quarantine/*`. It should still not execute any
command.

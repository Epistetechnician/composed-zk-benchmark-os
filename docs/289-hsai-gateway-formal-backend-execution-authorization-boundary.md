# Phase 289 HSAI Gateway Formal Backend Execution Authorization Boundary

State slice: `Phase 289 HSAI gateway formal backend execution authorization boundary`.

## Status

Complete for the docs-first backend execution authorization boundary.

## Purpose

Phase 288 hardened transcript output-bundle readback. Phase 289 defines the
minimum authorization boundary for a future local, operator-approved formal
backend execution experiment.

This phase does not implement execution and does not run any backend.

## Future Authorization Scope

A future execution authorization lane may describe only a caller-supplied,
operator-approved local experiment over already materialized metadata bundles.

The future authorization record must bind:

- authorization id;
- operator acknowledgement id;
- operator identity label or local key fingerprint;
- exact Phase 283 preflight output-bundle digest;
- exact Phase 287 transcript output-bundle digest;
- exact command descriptor digest;
- exact toolchain lock digest;
- exact backend kind;
- exact tool name and tool version;
- source correspondence digest;
- requested proof-obligation set;
- timeout policy;
- process environment allowlist;
- network-disabled policy;
- output-root quarantine descriptor;
- redaction policy;
- transcript retention policy;
- proof/checker artifact nonpromotion policy;
- claim boundary;
- required nonclaims.

The authorization record must be local metadata until a separate implementation
phase explicitly adds a runner interface.

## Future Execution Preconditions

A future runner phase must require all of the following before any command can
be spawned:

- valid Phase 270 source-correspondence output bundle;
- valid Phase 278 backend-run input bundle;
- valid Phase 283 preflight output bundle;
- valid Phase 287 transcript output bundle;
- no accepted Evidence Ledger mutation in any input bundle;
- no Level2+ evidence flag in any input bundle;
- no score-axis population in any input bundle;
- exact command allowlist match;
- exact argv vector match;
- no shell string execution;
- no inherited full environment;
- no credential-looking environment values;
- no network access;
- no write access outside a caller-selected quarantine root;
- no overwrite of accepted evidence, benchmark output, source correspondence,
  preflight, transcript, or repository roots;
- finite timeout;
- bounded stdout/stderr summary retention only;
- raw stdout/stderr/prover/checker/solver logs rejected unless explicitly
  redacted into bounded summaries;
- proof assistant caches rejected;
- external repo source snapshots rejected;
- operator acknowledgement that checker success is not semantic correctness;
- operator acknowledgement that proof/checker artifacts are not accepted
  evidence in the same step.

## Future Output Quarantine

A future execution phase must write only to an ignored or caller-selected
quarantine root. The quarantine root must be rejected when it is:

- empty;
- the repository root;
- inside protected repository roots;
- an accepted Evidence Ledger path;
- a benchmark-output path;
- a source-correspondence bundle path;
- a backend-run input bundle path;
- a preflight output-bundle path;
- a transcript output-bundle path;
- a file;
- a symlink;
- traversing through symlink parents;
- existing without explicit overwrite.

The quarantine must be read back and validated before any transcript metadata
can mention execution status.

## Future Transcript Admission Rules

A future transcript admission lane must separate:

- process exit status;
- tool checker status;
- proof artifact existence;
- checker transcript existence;
- proof-obligation coverage;
- nondischarged obligations;
- accepted evidence eligibility;
- semantic correctness;
- production readiness;
- SOTA status;
- full-security status.

No single checker success, solver success, Lean success, SMT success, COBALT
success, Aeneas/Hax/rust-lean success, or process exit code may imply semantic
correctness or accepted evidence.

## Required Future Tests

A future implementation phase must add tests for:

- valid local authorization metadata;
- missing operator acknowledgement rejection;
- command digest drift rejection;
- argv drift rejection;
- shell command rejection;
- inherited environment rejection;
- credential-looking environment rejection;
- network-enabled policy rejection;
- missing timeout rejection;
- unbounded output retention rejection;
- protected quarantine root rejection;
- accepted Evidence Ledger quarantine rejection;
- benchmark-output quarantine rejection;
- source-correspondence quarantine rejection;
- preflight/transcript bundle quarantine rejection;
- symlink quarantine rejection;
- backend-run/preflight/transcript digest drift rejection;
- proof-obligation set drift rejection;
- proof/checker promotion flag rejection;
- score-axis population rejection;
- SOTA/full-security/semantic-correctness/production-readiness claim rejection;
- checker-success semantic-correctness rejection.

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

Phase 290 implemented the inert execution-authorization metadata and validator
in `hsai-agent-admission`.

The next slice should be docs-first:

`Phase 291 HSAI gateway formal backend execution authorization output-bundle boundary`

It should define the future filesystem contract for materializing authorization
metadata and digest sidecars. It still should not execute any command.

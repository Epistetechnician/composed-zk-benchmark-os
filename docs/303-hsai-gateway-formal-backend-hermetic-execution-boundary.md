# Phase 303 HSAI Gateway Formal Backend Hermetic Execution Boundary

State slice: `Phase 303 HSAI gateway formal backend hermetic execution boundary`.

## Status

Complete for the docs-first backend execution boundary.

## Purpose

Phase 302 closed the local validation-summary output-bundle surface for the
quarantine lane. Phase 303 defines the first future point where HSAI may cross
from inert formal-backend metadata into hermetic local backend execution.

This phase does not execute a command and does not add Rust code. It defines
the future implementation contract.

## First Execution Lane

The first future execution lane should be:

`local_smt_tiny_gateway_invariant`

The lane is intentionally narrow. It may run only a tiny local SMT/Z3-style
invariant over already-normalized gateway admission data. The first target
property should be one of:

- gateway proposal digest binding determinism;
- attestation challenge binding determinism;
- accepted-evidence request rejection for disallowed claim boundaries.

This first lane is not a Lean lane, not a COBALT lane, not a Rust-to-Lean lane,
and not a repository-scale benchmark lane.

## Future Input Contract

A future implementation may consume only declared, non-secret local inputs:

- Phase 289 execution authorization metadata;
- Phase 292 authorization output-bundle readback result;
- Phase 293 quarantine artifact metadata;
- Phase 296 quarantine output-bundle readback result;
- Phase 300 validation summary;
- Phase 302 validation-summary output-bundle readback result;
- a static invariant fixture embedded in repository source or tests;
- caller-supplied run id and created-at timestamp.

The future runner must reject:

- secrets;
- credentials;
- network endpoints;
- absolute source paths in semantic fields;
- shell fragments;
- unbounded environment variables;
- undeclared input files;
- mutable accepted Evidence Ledger paths;
- benchmark output paths;
- score-axis paths;
- proof-promotion paths.

## Future Command Contract

The future implementation may define one hermetic command descriptor with:

- backend id `local_smt_tiny_gateway_invariant`;
- command kind `direct_process_no_shell`;
- fixed executable path supplied by policy, not by user input;
- fixed argv template supplied by policy;
- no shell expansion;
- no inherited environment except an explicit empty or allowlisted map;
- caller-selected ignored output root;
- timeout in milliseconds;
- maximum stdout bytes;
- maximum stderr bytes;
- no stdin;
- no network;
- no filesystem writes outside the ignored output root;
- no reads outside declared input paths and the fixed executable;
- deterministic redaction of stdout and stderr summaries.

The future command descriptor is authorization metadata until a later
implementation phase actually spawns a process.

## Future Output Contract

A future execution implementation must write only quarantine-local artifacts:

- normalized execution status;
- command descriptor digest;
- input manifest digest;
- bounded stdout summary;
- bounded stderr summary;
- redaction report;
- backend version label, if available without network;
- invariant verdict label;
- invariant obligation digest;
- solver-status label;
- wall-clock timeout result;
- validation report;
- manifest;
- SHA-256 sidecars for every declared file.

The future output must not retain:

- raw prover logs;
- raw checker logs;
- raw solver traces;
- unsummarized stdout;
- unsummarized stderr;
- proof artifacts;
- checker transcripts;
- solver certificates as accepted evidence;
- accepted Evidence Ledger files;
- benchmark outputs;
- score-axis values.

## Future Readback Rules

The future reader must fail closed on:

- missing declared files;
- missing sidecars;
- stale sidecars;
- undeclared files;
- undeclared directories;
- symlink output roots;
- symlink bundle directories;
- symlink declared files;
- symlink sidecars;
- claim-boundary drift;
- backend-id drift;
- command-descriptor drift;
- input-manifest drift;
- timeout-policy drift;
- stdout retention drift;
- stderr retention drift;
- raw-log retention drift;
- proof-artifact retention drift;
- checker-transcript retention drift;
- accepted Evidence Ledger mutation;
- Level2+ evidence flags;
- score-axis population;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- action-authority claims.

## Evidence Meaning

The future first execution lane may mean only this:

`A tiny local invariant backend was run under a hermetic command contract, and
its bounded output was quarantined and read back without claim escalation.`

It would not mean:

- Lean proof exists;
- COBALT containment proof exists;
- Rust-to-Lean extraction succeeded;
- repository-scale verification succeeded;
- proof artifacts are accepted evidence;
- checker transcripts are accepted evidence;
- solver certificates are accepted evidence;
- source correspondence is proven;
- accepted Evidence Ledger state changed;
- Level2+ evidence exists;
- score axes are populated;
- benchmark evidence exists;
- HSAI is semantically correct;
- HSAI is production ready;
- HSAI is SOTA;
- HSAI is a breakthrough;
- HSAI is fully secure;
- the gateway has authority to execute an action.

## Required Future Tests

The implementation slice should include focused tests for:

- valid hermetic command descriptor construction;
- shell-fragment rejection;
- inherited-environment rejection;
- undeclared-input rejection;
- protected output-root rejection;
- process timeout classification;
- stdout summary bounding;
- stderr summary bounding;
- raw stdout retention rejection;
- raw stderr retention rejection;
- raw solver trace rejection;
- proof artifact rejection;
- checker transcript rejection;
- accepted Evidence Ledger path rejection;
- Level2+ flag rejection;
- score-axis flag rejection;
- semantic-correctness claim rejection;
- production-readiness claim rejection;
- SOTA claim rejection;
- breakthrough claim rejection;
- full-security claim rejection;
- action-authority claim rejection;
- readback digest drift rejection;
- readback symlink rejection.

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

Phase 304 implements the tiny Rust no-spawn descriptor and fail-closed
validation surface for this boundary. Actual process spawning remains a
separate later phase after the descriptor/report bundle, quarantine output, and
negative tests are stable.

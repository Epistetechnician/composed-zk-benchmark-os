# Phase 311 HSAI Gateway Formal Backend Hermetic Process-Spawn Crossing Boundary

State slice: `Phase 311 HSAI gateway formal backend hermetic process-spawn crossing boundary`.

## Status

Complete for the docs-first process-spawn crossing boundary.

## Purpose

Phase 310 added local drift coverage for the not-run result-quarantine output
bundle. Phase 311 defines the exact future boundary for the first process-spawn
crossing in the `local_smt_tiny_gateway_invariant` lane.

This phase does not add Rust code, does not spawn a process, and does not run
SMT, Z3, COBALT, Lean, or any formal backend.

## Future Crossing Scope

A future implementation may cross into process spawning only for the narrow
`local_smt_tiny_gateway_invariant` lane and only after all of these inputs are
valid:

- Phase 304 no-spawn descriptor;
- Phase 306 descriptor-report output-bundle readback;
- Phase 308 result-quarantine output-bundle materialization/readback contract;
- Phase 310 result-quarantine drift coverage;
- caller-selected output root outside the repository;
- explicit operator acknowledgement for local execution;
- fixed executable policy selected by repository code, not by user input;
- fixed argv template selected by repository code, not by user input;
- empty environment or a hard allowlist with no secrets;
- no stdin;
- no shell;
- no network;
- timeout in milliseconds;
- maximum stdout bytes;
- maximum stderr bytes;
- redaction policy;
- nonpromotion policy.

## Future Executable Policy

The future runner may accept only a policy-defined executable label for:

`local_smt_tiny_gateway_invariant`

The implementation must reject:

- absolute executable paths supplied by the caller;
- shell fragments;
- user-controlled command names;
- user-controlled argv templates;
- executable labels outside the policy table;
- missing executable metadata;
- executable metadata that is not digest-bound;
- backend kind drift;
- tool version drift;
- toolchain lock drift.

The future executable policy may point to a local fixture executable or a local
repository tool, but that tool must be non-secret, deterministic, and invoked
only through direct process execution with no shell.

## Future Runtime Policy

The future runner must:

- use `std::process::Command` or equivalent direct-process API;
- avoid shell execution;
- pass argv as separate arguments;
- set stdin to closed or null;
- set the environment to empty or explicit allowlist only;
- reject inherited environment by default;
- reject credential-looking environment values;
- reject network endpoints in all inputs;
- reject output roots inside the repository;
- write only under the caller-selected quarantine output root;
- bound stdout and stderr reads;
- kill or classify timeout deterministically;
- redact stdout and stderr summaries before retention;
- retain no raw solver trace;
- retain no raw prover log;
- retain no raw checker log;
- retain no proof artifact;
- retain no checker transcript;
- retain no solver certificate as evidence;
- mutate no accepted Evidence Ledger;
- populate no score axes.

## Future Output Contract

The future runner must materialize only a Phase 308-compatible result-quarantine
bundle. The output may set `process_spawned` and `backend_executed` true only
inside that quarantined local candidate record. Every proof/evidence/score/
semantic/readiness/SOTA/security/authority flag must remain false.

The runner output may mean only:

`A tiny local invariant backend process ran under a bounded no-shell policy, and
its summarized output was quarantined without claim escalation.`

It must not mean:

- Lean proof exists;
- COBALT containment proof exists;
- Rust-to-Lean extraction succeeded;
- repository-scale verification succeeded;
- solver certificate is accepted evidence;
- proof artifact is accepted evidence;
- checker transcript is accepted evidence;
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

The implementation slice must add focused tests for:

- valid direct-process no-shell execution of a deterministic local fixture;
- missing executable policy rejection;
- caller-supplied executable path rejection;
- shell fragment rejection;
- inherited environment rejection;
- allowlist environment acceptance only for non-secret values;
- credential-looking environment rejection;
- network endpoint rejection;
- stdin rejection;
- protected output-root rejection;
- repository output-root rejection;
- timeout classification;
- nonzero exit classification;
- stdout byte bounding;
- stderr byte bounding;
- stdout redaction;
- stderr redaction;
- raw stdout retention rejection;
- raw stderr retention rejection;
- raw solver trace rejection;
- proof artifact rejection;
- checker transcript rejection;
- solver certificate nonpromotion;
- accepted Evidence Ledger path rejection;
- Level2+ flag rejection;
- score-axis flag rejection;
- semantic-correctness claim rejection;
- production-readiness claim rejection;
- SOTA claim rejection;
- breakthrough claim rejection;
- full-security claim rejection;
- authority claim rejection;
- readback through the Phase 308 result-quarantine validator.

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
- solver-certificate promotion;
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

Phase 312 implements the no-default-runner Rust interface for this boundary:
policy structs, validation errors, and tests that still do not spawn a process.
Actual process spawning remains a separate explicit phase after the interface is
stable.

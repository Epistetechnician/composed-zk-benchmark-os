# Phase 297 HSAI Gateway Formal Backend Quarantine Output-Bundle Drift Coverage Boundary

State slice: `Phase 297 HSAI gateway formal backend quarantine output-bundle drift coverage boundary`.

## Status

Complete for the docs-first quarantine output-bundle drift coverage boundary.

## Purpose

Phase 296 implemented local materialization and readback for
`gateway-formal-backend-quarantine/*`. Phase 297 defines the next negative-test
coverage slice needed before this lane can be considered robust against
readback drift.

This phase does not add Rust tests. It defines the exact test targets for a
future implementation slice.

## Required Drift Coverage

A future implementation phase should add focused tests for:

- protected output-root rejection;
- existing output-root overwrite rejection;
- missing declared sidecar rejection;
- malformed quarantine artifact JSON rejection;
- malformed manifest JSON rejection;
- authorization binding drift rejection;
- process status drift rejection;
- stderr summary drift rejection;
- redaction report drift rejection;
- output inventory drift rejection;
- proof/checker nonpromotion report drift rejection;
- declared file symlink rejection;
- declared sidecar symlink rejection;
- output-root symlink rejection;
- bundle-directory symlink rejection;
- undeclared raw stderr rejection;
- undeclared raw prover log rejection;
- undeclared raw checker log rejection;
- undeclared raw solver trace rejection;
- undeclared proof artifact rejection;
- undeclared checker transcript rejection;
- undeclared accepted Evidence Ledger path rejection;
- undeclared benchmark output rejection;
- undeclared source-correspondence bundle rejection;
- undeclared backend-run bundle rejection;
- undeclared preflight bundle rejection;
- undeclared transcript bundle rejection;
- undeclared authorization bundle rejection.

## Expected Future Scope

The future implementation should be limited to additive tests under
`crates/hsai-agent-admission/src/lib.rs` and phase notes/navigation updates.

The future implementation should not change the Phase 296 public API unless a
test exposes an actual bug in readback validation. If a bug is found, the fix
must remain scoped to the quarantine output-bundle readback path.

## Required Future Assertions

Each test should assert the specific
`GatewayFormalBackendExecutionQuarantineOutputError` variant returned by
readback or materialization. Broad `is_err()` checks are insufficient for this
slice.

The future test set should preserve these invariants:

- stale sidecars are rejected before semantic readback;
- sidecar-consistent JSON drift is still rejected by semantic readback;
- nonclaim Markdown drift is not accepted even with an updated sidecar;
- undeclared raw files are rejected before they can be interpreted as metadata;
- symlinks are rejected for roots, bundle directories, declared files, and
  sidecars;
- proof/checker artifacts remain nonpromoted;
- process success remains not accepted evidence;
- checker success remains not semantic correctness;
- manifests cannot claim accepted evidence, Level2+ evidence, score axes,
  authority, semantic correctness, production readiness, SOTA, breakthrough
  status, or full security.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- new bundle materialization behavior;
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

Phase 298 implements the focused Phase 297 drift tests. The next responsible
slice after that implementation is a docs-first boundary for a local validation
summary artifact. It should still not execute a command, spawn a process, or
promote proof/checker artifacts.

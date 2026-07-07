# Phase 603 HSAI Tiny Z3 Real Backend Execution Crossing Notes

State slice: `Phase 603 HSAI tiny Z3 real backend execution crossing`.

Phase 603 crosses the first real backend-execution ceiling for
`gateway-local-digest-binding-determinism-v1`. Real Z3 process execution runs
against the canonical Phase 404 obligation (`phase404_z3_obligation_bytes()`)
and produces the semantically correct `unsat` verdict classified as
`SolverUnsatWithoutCertificate`.

## Implemented Surface

Phase 603 adds focused test coverage under
`crates/hsai-agent-admission/src/lib.rs` and corrects the Phase 531 exactness
predicate for the canonical determinism obligation:

- `gateway_formal_tiny_z3_backend_execution_artifact_package_phase529_exact`
  now accepts the canonical `SolverUnsatWithoutCertificate` result instead of
  the earlier toy `SolverSatWitnessWithoutCertificate` placeholder.
- `phase529_tiny_z3_hermetic_backend_execution_result_runs_real_z3_against_gateway_digest_binding_obligation_without_promotion`
  executes real Z3 (`z3 -in -smt2`) against the Phase 404 obligation and
  asserts the observed `unsat` verdict plus the existing nonpromotion flags.
- `phase603_real_z3_unsat_result_propagates_to_in_memory_accepted_append_boundary`
  executes real Z3, packages the result through Phase 531, reviews it through
  Phase 533, routes it through Phase 535, validates an accepted append request
  through Phase 537, and reaches the Phase 539 in-memory
  `apply_accepted_ledger_append_transaction` boundary.
- The Phase 531 test fixture now uses `phase404_z3_obligation_bytes()` and
  `unsat`, so downstream Phase 531/533/535/537/539 tests no longer depend on a
  satisfiable placeholder formula.

## Boundary

Phase 603 is local regression evidence of one real Z3 process run and its
local-only propagation into the existing in-memory accepted append mutation
metadata path.

This phase does not:

- write accepted Evidence Ledger files;
- create materialized accepted ledger output;
- create accepted formal evidence;
- create Level2+ evidence;
- populate score axes;
- create proof artifacts, checker transcripts, or solver certificates;
- run Lean, COBALT, or Rust-to-Lean extraction;
- create benchmark evidence;
- claim semantic correctness, production readiness, SOTA, breakthrough status,
  full security, global uniqueness, or action authority.

The in-memory Phase 539 append records only a `LocalReplay` /
`Level1LocalReplay` entry through the existing `zkbench-core` mutation API. It
is not materialized accepted evidence, not Level2 evidence, not score-axis
evidence, and not a formal proof.

The `unsat` verdict establishes only that Z3 found no counterexample to the
scoped digest-binding determinism obligation supplied to the runner, under the
assumption that the obligation faithfully encodes the intended property.

## Remaining Ceilings

The following ceilings remain blocked after Phase 603:

- materialized accepted Evidence Ledger output requires the already separate
  materialization path and explicit local file-surface validation;
- Level2+ evidence still requires reproducible benchmark artifacts and policy
  lift beyond the current local replay cap;
- score-axis population still requires Level2+ evidence first;
- independent reproduction requires another operator and machine;
- human review requires a real reviewer decision;
- SOTA, full-security, semantic-correctness, and production-readiness wording
  remain forbidden unless a later owner-authorized phase changes the policy.

## Reproduction

Prerequisite: Z3 must be on `$PATH`.

```sh
cargo test -p hsai-agent-admission \
  phase603_real_z3_unsat_result_propagates_to_in_memory_accepted_append_boundary \
  -- --nocapture
```

Expected focused result:

```text
test tests::phase603_real_z3_unsat_result_propagates_to_in_memory_accepted_append_boundary ... ok
```

If Z3 is missing, the real-run tests skip through the same
`phase529_z3_executable()` guard used by the existing Phase 529 coverage.

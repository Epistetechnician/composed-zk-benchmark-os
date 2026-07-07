# Phase 604 HSAI Tiny Z3 Real Backend Execution Materialized Accepted Append Notes

State slice: `Phase 604 HSAI tiny Z3 real backend execution materialized accepted append`.

Phase 604 crosses the next local ceiling after Phase 603: the real-Z3
`gateway-local-digest-binding-determinism-v1` observation now reaches a local
materialized accepted-ledger JSON artifact through the existing `zkbench-core`
materialized append owner.

## Implemented Surface

Phase 604 adds focused test coverage under
`crates/hsai-agent-admission/src/lib.rs`:

- `phase604_real_z3_unsat_result_materializes_accepted_ledger_artifact_without_claim_escalation`
  executes real Z3 against `phase404_z3_obligation_bytes()`;
- packages the `SolverUnsatWithoutCertificate` result through Phase 531;
- reviews and routes it through Phase 533 and Phase 535;
- validates and mutates through Phase 537 and Phase 539;
- materializes the accepted-ledger JSON artifact through Phase 541 using
  `zkbench_core::MaterializedAcceptedLedgerAppendRequest` and
  `apply_materialized_accepted_ledger_append_transaction`.

## Boundary

Phase 604 supports only this scoped claim:

```text
HSAI can materialize one local JSON accepted-ledger artifact for the real local
Z3 digest-binding determinism observation through the existing zkbench-core
materialized accepted append owner.
```

The materialized entry remains `LocalReplay` / `Level1LocalReplay`.

This phase does not:

- create accepted formal evidence;
- create Level2+ evidence;
- populate score axes;
- create proof artifacts, checker transcripts, or solver certificates;
- run Lean, COBALT, or Rust-to-Lean extraction;
- create benchmark evidence;
- accept independent external reproduction;
- record a human reviewer decision;
- claim semantic correctness, production readiness, SOTA, breakthrough status,
  full security, global uniqueness, or action authority.

The materialized ledger artifact is local replay evidence only. It is not
formal proof, not Level2 evidence, not score-axis evidence, not independent
reproduction, and not public claim authority.

## Remaining Ceilings

The following ceilings remain blocked after Phase 604:

- Level2+ evidence requires reproducible benchmark artifacts and a policy lift;
- score-axis population requires Level2+ evidence first;
- Lean execution has not run;
- COBALT execution has not run;
- independent reproduction requires another operator and machine;
- human review requires a real reviewer decision;
- SOTA, full-security, semantic-correctness, and production-readiness wording
  remain forbidden unless a later owner-authorized phase changes the policy.

## Reproduction

Prerequisite: Z3 must be on `$PATH`.

```sh
cargo test -p hsai-agent-admission \
  phase604_real_z3_unsat_result_materializes_accepted_ledger_artifact_without_claim_escalation \
  -- --nocapture
```

Expected focused result:

```text
test tests::phase604_real_z3_unsat_result_materializes_accepted_ledger_artifact_without_claim_escalation ... ok
```

If Z3 is missing, the real-run test skips through the same
`phase529_z3_executable()` guard used by the Phase 529 coverage.

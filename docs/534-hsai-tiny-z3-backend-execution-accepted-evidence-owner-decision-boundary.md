# Phase 534 HSAI Tiny Z3 Backend Execution Accepted-Evidence Owner Decision Boundary

State slice: `Phase 534 HSAI tiny Z3 backend execution accepted-evidence owner decision boundary`.

Phase 534 defines the docs-first boundary for the next decision after
`docs/533-hsai-tiny-z3-backend-execution-package-review-metadata-notes.md`:

```text
Phase 533 local backend execution package review metadata
  + explicit accepted-evidence owner decision
  -> local owner-decision metadata
```

This boundary exists because the Phase 529 through Phase 533 lane now has one
local SMT/Z3 backend execution observation, a local package record, and a local
review record. That is still not accepted evidence. The only accepted-ledger
owner remains `zkbench-core`, and any future accepted-evidence crossing must
route through the existing accepted append surfaces instead of becoming a
parallel HSAI admission path.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, mutate the accepted Evidence Ledger, call accepted append
validators, call accepted append mutation APIs, create accepted evidence,
create accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run another SMT/Z3 execution, run COBALT, run
Rust-to-Lean extraction, run external replay, submit benchmarks, claim semantic
correctness, claim production readiness, claim SOTA, claim breakthrough status,
claim full security, claim independent external reproduction, or grant
authority to execute an action.

## Current Inputs

The future owner-decision metadata may consider only one exact Phase 533 review
record and its inherited chain:

- Phase 533 package review digest and input digest;
- Phase 531 package digest and input digest;
- Phase 529 backend execution result digest and request digest;
- Phase 527 backend execution candidate digest and input digest;
- Phase 533 review classification
  `BackendExecutionPackageReviewScopeAcceptableLocalOnly`;
- Phase 531 package classification `BackendExecutionPackagedLocalOnly`;
- Phase 529 result classification `LaneASmtZ3RunObservedLocalOnly`;
- Phase 527 candidate classification `LaneAExecutionCandidateDeclaredNoRun`;
- Phase 533 review policy, blocker, allowed-next-state, rule, forbidden-API,
  inherited-digest, nonclaim, digest-binding, id-binding, and label-binding
  digests.

The future owner decision must not recompute or replace the reviewed chain from
unreviewed Phase 527, Phase 529, or Phase 531 inputs.

## Owner Surface

The accepted-evidence owner remains `zkbench-core`:

- `AcceptedLedgerAppendTransactionRequest`;
- `AcceptedLedgerAppendTransactionValidation`;
- `validate_accepted_ledger_append_transaction_request`;
- `apply_accepted_ledger_append_transaction`;
- `MaterializedAcceptedLedgerAppendRequest`;
- `apply_materialized_accepted_ledger_append_transaction`;
- `EvidenceClass`;
- `ClaimBoundary`;
- `EvidenceRecord`;
- `EvidenceLedger`.

`crates/hsai-agent-admission` may record local owner-decision metadata. It may
not directly mutate an accepted Evidence Ledger, define a competing evidence
class taxonomy, widen claim-boundary semantics, or treat backend execution
package review metadata as accepted evidence.

## Allowed Future Decision Labels

A future Phase 535 implementation may record only one of these decision labels:

```text
BackendExecutionAcceptedEvidenceRouteStillBlocked
BackendExecutionAcceptedEvidenceRouteRejected
BackendExecutionAcceptedEvidenceRouteNeedsZkbenchCoreEvaluation
```

`BackendExecutionAcceptedEvidenceRouteNeedsZkbenchCoreEvaluation` is not an
accepted append decision. It means only that the reviewed backend-execution
package may be handed to a later, separately authorized `zkbench-core`
evaluation boundary. It must still preserve the current Level1 cap and the
existing accepted append policy restrictions.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 533 package review digest;
- one Phase 533 package review input digest;
- the Phase 533 digest-binding map digest;
- the Phase 533 id-binding map digest;
- the Phase 533 label-binding map digest;
- the Phase 533 explicit nonclaim digest;
- the Phase 533 review blocker digest;
- the Phase 533 allowed-next-state digest;
- the Phase 531 package digest and input digest;
- the Phase 529 backend execution result digest and request digest;
- the Phase 527 candidate digest and input digest;
- accepted evidence owner `zkbench-core`;
- local transaction route `AcceptedLedgerAppendTransactionRequest`;
- materialized route `MaterializedAcceptedLedgerAppendRequest`;
- accepted evidence class owner `zkbench-core`;
- accepted claim-boundary owner `zkbench-core`;
- maximum accepted append claim boundary `Level1LocalReplay`;
- rejected Level2+ floor `Level2ReproducibleBenchmarkArtifact`;
- rejected formal-evidence classes and claim boundaries;
- explicit statement that local SMT/Z3 backend execution package review is not
  Lean proof, COBALT evidence, Rust-to-Lean proof, benchmark evidence,
  independent external reproduction, semantic correctness, production
  readiness, SOTA, full security, or action authority;
- exact next owner-decision label from the allowed set.

## Required Future Validation

A future validator must reject the owner-decision input if:

- the schema version is not the future Phase 535 schema;
- the Phase 533 package review digest or input digest drifts;
- any inherited Phase 531, Phase 529, or Phase 527 digest drifts;
- the Phase 533 digest, id, label, policy, nonclaim, blocker,
  allowed-next-state, rule, forbidden-API, or inherited-digest bindings drift;
- the Phase 533 review classification is not
  `BackendExecutionPackageReviewScopeAcceptableLocalOnly`;
- the accepted evidence owner is not `zkbench-core`;
- the local transaction route is not `AcceptedLedgerAppendTransactionRequest`;
- the materialized route is not `MaterializedAcceptedLedgerAppendRequest`;
- the accepted evidence class owner is not `zkbench-core`;
- the accepted claim-boundary owner is not `zkbench-core`;
- the maximum accepted append claim boundary is above `Level1LocalReplay`;
- the decision label is outside the allowed set;
- the decision claims accepted evidence was created;
- the decision claims accepted formal evidence was created;
- the decision claims Level2+ evidence was created;
- the decision populates score axes;
- the decision treats solver output as proof authority;
- the decision treats a checker transcript or solver certificate as accepted
  authority;
- the decision claims Lean, COBALT, or Rust-to-Lean evidence exists;
- the decision claims independent external reproduction or external audit;
- the decision claims semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority.

## Meaning Limit

The future owner-decision metadata may support this claim only:

```text
HSAI locally records whether one reviewed local SMT/Z3 backend execution
package remains blocked, is rejected, or may proceed to a later zkbench-core
accepted-append evaluation boundary.
```

That still is not:

- accepted evidence;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- benchmark evidence;
- independent external reproduction;
- external audit;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Phase 535 Implementation Exit Criteria

A future Phase 535 may implement local owner-decision metadata only if it:

- stays within `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata, dependencies, binaries, examples, scripts, or package
  runtime files;
- writes no filesystem artifacts;
- performs no process or network calls;
- runs no Lean, COBALT, Rust-to-Lean extraction, or additional SMT/Z3 process;
- reads or mutates no accepted Evidence Ledger files;
- does not call accepted append validator or mutation APIs;
- binds one exact Phase 533 review record and its inherited Phase 531, Phase
  529, and Phase 527 digests;
- records `zkbench-core` as the only accepted-evidence owner;
- records the existing accepted append routes and Level1 cap;
- records exactly one allowed owner-decision label;
- rejects accepted-evidence mutation, accepted formal evidence, Level2+,
  score-axis, proof/checker/solver-authority, Lean/COBALT/Rust-to-Lean,
  benchmark, independent-reproduction, external-audit, strong-claim, and
  action-authority attempts.

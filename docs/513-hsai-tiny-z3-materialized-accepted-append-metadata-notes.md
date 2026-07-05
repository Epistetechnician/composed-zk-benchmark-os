# Phase 513 HSAI Tiny Z3 Materialized Accepted Append Metadata Notes

State slice: `Phase 513 HSAI tiny Z3 materialized accepted append metadata`.

Phase 513 implements the narrow local materialized accepted append metadata
path authorized by
`docs/512-hsai-tiny-z3-materialized-accepted-append-boundary.md`:

```text
Phase 511 in-memory mutation metadata
  + caller-selected local JSON ledger path
  + zkbench-core MaterializedAcceptedLedgerAppendRequest
  -> zkbench-core apply_materialized_accepted_ledger_append_transaction
  -> local JSON accepted ledger artifact metadata
```

The implementation does not add a new dependency, binary, script, process
runner, network API, official submission API, solver API, proof-assistant API,
benchmark runner, direct `EvidenceLedger::load_json` call, direct
`EvidenceLedger::save_json` call, or parallel ledger writer. HSAI admission
routes materialization through the existing `zkbench-core` owner.

## Implemented Surface

Phase 513 adds the local Rust metadata model under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3MaterializedAcceptedAppendInput`;
- `GatewayFormalTinyZ3MaterializedAcceptedAppend`;
- `GatewayFormalTinyZ3MaterializedAcceptedAppendIssue`;
- `GatewayFormalTinyZ3MaterializedAcceptedAppendValidation`;
- deterministic nonclaim, rule, forbidden-API, inherited-digest, path-digest,
  digest-binding, id-binding, and label-binding helpers;
- `validate_gateway_formal_tiny_z3_materialized_accepted_append_input`;
- `build_gateway_formal_tiny_z3_materialized_accepted_append`.

The builder first validates the Phase 511 prerequisite state, materialized
request identity, transaction request identity, local path identity, owner,
materialized request type, materialization function identifier, and nonpromotion
flags. If validation passes, it calls:

```rust
zkbench_core::apply_materialized_accepted_ledger_append_transaction(request)
```

After the `zkbench-core` owner returns, HSAI reads the materialized JSON bytes
only to bind the local artifact digest and byte length. HSAI does not parse or
write the accepted ledger itself.

The resulting metadata binds:

- the Phase 511 mutation digest and input digest;
- the Phase 511 digest, id, and label binding map digests;
- the Phase 511 explicit nonclaim, mutation-rule, forbidden-API, and
  inherited-digest digests;
- the Phase 511 transaction request digest;
- the Phase 511 validation result digest;
- the Phase 511 pre- and post-mutation in-memory ledger digests;
- the Phase 511 accepted append report digest;
- the Phase 511 appended entry digest, sequence number, evidence class, and
  claim boundary;
- the ledger path identity digest;
- the ledger path policy digest;
- the `create_if_missing` policy value;
- the materialized append report digest;
- the materialized ledger artifact digest and byte length.

## Guardrails

Phase 513 fails closed if the Phase 511 mutation state is not exact, if the
Phase 511 mutation did not record a successful in-memory append, if the Phase
511 appended class is not `LocalReplay`, if the Phase 511 appended claim
boundary is not `Level1LocalReplay`, if the materialized request transaction
drifts, if the local path identity or path policy drifts, if the owner is not
`zkbench-core`, if the request type is not
`MaterializedAcceptedLedgerAppendRequest`, or if the function identifier is not
`apply_materialized_accepted_ledger_append_transaction`.

It also rejects any request for direct ledger load/save, a parallel ledger
writer, official submission, accepted formal evidence, Level2+ evidence, score
axes, proof/checker/solver promotion, backend execution evidence, benchmark
evidence, semantic-correctness claims, production-readiness claims, SOTA
claims, breakthrough claims, full-security claims, external-audit claims, or
action authority.

## Evidence Meaning

Phase 513 supports this claim only:

```text
HSAI materializes one local JSON accepted-ledger artifact through the existing
zkbench-core materialized accepted append owner for a reviewed tiny-Z3 local
accepted-path handoff.
```

The result is still not accepted formal evidence, not Level2+ evidence, not
score-axis evidence, not Lean proof, not SMT proof authority, not COBALT
containment evidence, not Rust-to-Lean proof, not checker transcript authority,
not solver certificate authority, not benchmark evidence, not external audit,
not SOTA, not semantic correctness, not production readiness, not full
security, and not authority to execute an action.

## Tests

Focused tests cover:

- successful Phase 513 local materialized append metadata over a real Phase 511
  mutation record and real `zkbench-core` materialized append request;
- rejection when the Phase 511 mutation state is invalid;
- rejection of direct-ledger-load/save, parallel-writer, official-submission,
  formal-evidence, Level2+, score-axis, backend, benchmark, strong-claim, and
  action-authority promotion attempts.

The tests assert that the materialized ledger path exists only after a valid
call, the materialized artifact digest and byte length are recorded, and the
metadata still rejects formal evidence, Level2+, score axes, backend execution,
benchmark evidence, external audit, and strong claims.

## Phase 514 Boundary Status

Phase 514 defines the docs-first accepted-evidence package boundary in
`docs/514-hsai-tiny-z3-accepted-evidence-package-boundary.md`. It does not
write package artifacts, create accepted formal evidence, create Level2+
evidence, populate score axes, run Lean/new-SMT/COBALT/Rust-to-Lean extraction,
create benchmark evidence, or claim production/SOTA/security/semantic-
correctness results.

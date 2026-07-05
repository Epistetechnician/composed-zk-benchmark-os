# Phase 509 HSAI Tiny Z3 Accepted Append Validator Call Metadata Notes

State slice: `Phase 509 HSAI tiny Z3 accepted append validator-call
metadata`.

Phase 509 implements local in-memory metadata for the Phase 508 boundary:

```text
in-memory validation-only call from HSAI accepted append handoff metadata to
zkbench-core validate_accepted_ledger_append_transaction_request
```

The implementation adds a local `zkbench-core` path dependency to
`hsai-agent-admission`, records the Cargo lockfile change caused by that
workspace dependency edge, and adds a metadata wrapper that calls only
`validate_accepted_ledger_append_transaction_request` over caller-supplied
in-memory `AcceptedLedgerAppendTransactionRequest` and `EvidenceLedger`
values.

This phase does not read accepted Evidence Ledger files, write accepted
Evidence Ledger files, call accepted append mutation APIs, create materialized
accepted ledger output, create an accepted append decision, create accepted
formal evidence, create Level2+ evidence, populate score axes, generate proof
artifacts, generate checker transcripts, generate solver certificates, run
Lean, run new SMT, run COBALT, run Rust-to-Lean extraction, create benchmark
evidence, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, claim external audit status,
or grant authority to execute an action.

## Implemented Surface

`crates/hsai-agent-admission/Cargo.toml` now depends on local
`zkbench-core = { path = "../zkbench-core" }`.

`Cargo.lock` records the corresponding workspace dependency edge.

`crates/hsai-agent-admission/src/lib.rs` now defines:

- `GATEWAY_FORMAL_TINY_Z3_ACCEPTED_APPEND_VALIDATOR_CALL_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_Z3_ACCEPTED_APPEND_VALIDATOR_CALL_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_Z3_ACCEPTED_APPEND_VALIDATOR_CALL_CLAIM_BOUNDARY`;
- `GatewayFormalTinyZ3AcceptedAppendValidatorCallLabel`;
- `GatewayFormalTinyZ3AcceptedAppendValidatorCallInput`;
- `GatewayFormalTinyZ3AcceptedAppendValidatorCall`;
- `GatewayFormalTinyZ3AcceptedAppendValidatorCallIssue`;
- `GatewayFormalTinyZ3AcceptedAppendValidatorCallValidation`;
- accepted append validator-call nonclaim, rule, forbidden-API, and inherited
  digest requirement helpers;
- Phase 507 digest, id, and label binding helpers;
- accepted append request identity digest helpers;
- `build_gateway_formal_tiny_z3_accepted_append_validator_call`;
- `validate_gateway_formal_tiny_z3_accepted_append_validator_call_input`.

The builder calls exactly:

```rust
zkbench_core::validate_accepted_ledger_append_transaction_request(request, ledger)
```

It does not call accepted append mutation APIs or materialized output APIs.

The metadata records:

- one Phase 507 accepted append handoff record digest;
- one Phase 507 accepted append handoff input digest;
- the Phase 507 digest-binding map digest;
- the Phase 507 id-binding map digest;
- the Phase 507 label-binding map digest;
- the Phase 507 explicit nonclaim digest;
- the Phase 507 validation handoff rule digest;
- the Phase 507 forbidden API set digest;
- the Phase 507 inherited digest requirement digest;
- reviewed and expected current accepted append blocker digests;
- `zkbench-core` owner id;
- `validate_accepted_ledger_append_transaction_request` validator id;
- accepted append request, candidate, append-preview, review-decision,
  source-artifact-set, and ledger-tip identity digests;
- target ledger id and transaction id;
- in-memory ledger digest;
- returned validation result digest;
- returned validation issue-kind set digest;
- returned validation valid flag and issue count.

The validator rejects:

- Phase 507 digest/id/label/nonclaim/rule/forbidden-API/inherited binding
  drift;
- Phase 507 handoff state drift;
- stale blocker digest drift;
- accepted append owner drift;
- validation function drift;
- request, validation-output, or ledger type drift;
- request identity drift between the Phase 507 handoff and caller-supplied
  request;
- validation call rule drift;
- forbidden API set drift;
- inherited digest requirement drift;
- validator-call summary promotion claims;
- accepted Evidence Ledger file reads or writes;
- accepted append mutation requests;
- materialized accepted ledger output requests;
- proceeding after invalid validation;
- treating valid validation as accepted evidence;
- accepted append decisions;
- accepted formal evidence creation;
- Level2+ evidence creation;
- score-axis population;
- proof/checker/solver authority;
- backend execution evidence;
- Lean/new-SMT/COBALT/Rust-to-Lean execution evidence;
- benchmark evidence;
- external audit claims;
- SOTA, semantic-correctness, production-readiness, breakthrough,
  full-security, or action-authority claims.

## Validation

Focused tests cover:

- successful Phase 509 metadata construction over a valid Phase 507 handoff;
- construction of a real in-memory `zkbench-core` accepted append transaction
  request and empty in-memory `EvidenceLedger`;
- real `validate_accepted_ledger_append_transaction_request` execution with a
  valid result;
- validation result digest, issue-kind set, valid flag, and issue count
  recording;
- non-mutating and non-materializing output flags;
- request identity drift rejection;
- invalid owner rejection;
- promotion-attempt rejection, including accepted Evidence Ledger file reads
  and writes, accepted append mutation, materialized output, proceeding after
  invalid validation, treating valid validation as accepted evidence, backend
  evidence, benchmark evidence, and external audit claims.

## Meaning Limit

The new metadata supports only this claim:

```text
HSAI locally records the result of an in-memory validation-only call to the
zkbench-core accepted-ledger append transaction validator for one reviewed
tiny-Z3 accepted-path handoff.
```

It is still not accepted append mutation, not accepted evidence, not accepted
formal evidence, not accepted Evidence Ledger mutation, not accepted append
policy change, not materialized accepted ledger output, not Level2+ evidence,
not score-axis evidence, not Lean proof, not SMT proof authority, not COBALT
containment evidence, not Rust-to-Lean proof, not checker transcript authority,
not solver certificate authority, not benchmark evidence, not external audit,
not SOTA, not semantic correctness, not production readiness, not full
security, and not authority to execute an action.

## Phase 510 Boundary Status

Phase 510 defines the docs-first accepted append mutation boundary in
`docs/510-hsai-tiny-z3-accepted-append-mutation-boundary.md`.

That boundary still does not call `apply_accepted_ledger_append_transaction`,
read or write accepted Evidence Ledger files, create materialized accepted
ledger output, create accepted formal evidence, create Level2+ evidence,
populate score axes, run Lean/new-SMT/COBALT/Rust-to-Lean, or make
production/SOTA/security/correctness claims.

# Phase 506 HSAI Tiny Z3 Accepted Append Evaluation Handoff Boundary

State slice: `Phase 506 HSAI tiny Z3 accepted append evaluation handoff
boundary`.

Phase 506 defines the docs-first boundary for the next accepted-path crossing:

```text
validation-only handoff from HSAI tiny-Z3 prerequisite metadata to the
zkbench-core accepted-ledger append transaction validator
```

Phase 505 implemented local stale blocker rejection metadata. Phase 506 records
the next boundary: a future HSAI bridge may only approach accepted append
through the `zkbench-core` owner surface and only through validation before any
mutation is considered.

This phase does not implement Rust code, add a `zkbench-core` dependency to
`hsai-agent-admission`, change Cargo metadata, read accepted Evidence Ledger
files, write accepted Evidence Ledger files, call
`validate_accepted_ledger_append_transaction_request`, call
`apply_accepted_ledger_append_transaction`, call
`apply_materialized_accepted_ledger_append_transaction`, create an accepted
append report, create accepted formal evidence, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, run Lean, run new SMT, run COBALT, run
Rust-to-Lean extraction, create benchmark evidence, claim semantic correctness,
claim production readiness, claim SOTA, claim breakthrough status, claim full
security, claim external audit status, or grant authority to execute an
action.

## Owner Surface

The accepted append owner remains `zkbench-core`.

The future validation-only handoff may name these existing owner surfaces:

- `AcceptedLedgerAppendTransactionRequest`;
- `AcceptedLedgerAppendTransactionValidation`;
- `AcceptedLedgerAppendTransactionIssueKind`;
- `ReviewedPromotionPreflightRequest`;
- `ReviewedPromotionPreflightReport`;
- `EvidenceLedger`;
- `validate_accepted_ledger_append_transaction_request`.

The future handoff must not call or wrap these mutation surfaces in this lane:

- `apply_accepted_ledger_append_transaction`;
- `MaterializedAcceptedLedgerAppendRequest`;
- `apply_materialized_accepted_ledger_append_transaction`;
- `EvidenceLedger::save_json`;
- any filesystem materialization path for an accepted Evidence Ledger.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 505 stale blocker rejection record digest;
- one Phase 505 stale blocker rejection input digest;
- the Phase 505 digest-binding map digest;
- the Phase 505 id-binding map digest;
- the Phase 505 label-binding map digest;
- the Phase 505 explicit nonclaim digest;
- the Phase 505 freshness comparison rule digest;
- the Phase 505 stale blocker rejection action digest;
- the Phase 505 inherited digest requirement digest;
- the reviewed current accepted append blocker digest from Phase 505;
- the expected current accepted append blocker digest from Phase 505;
- the `AcceptedLedgerAppendTransactionRequest` type name and schema version;
- the `ReviewedPromotionPreflightRequest` and `ReviewedPromotionPreflightReport`
  type names;
- the target `EvidenceLedger` type name and target ledger id;
- the transaction id;
- the expected current ledger tip digest;
- the append-preview current ledger tip digest;
- the transaction request digest;
- the candidate digest;
- the append preview digest;
- the review decision digest;
- the source artifact digest set digest;
- the validation function identifier
  `validate_accepted_ledger_append_transaction_request`.

The future handoff must not recompute the Phase 505 prerequisite chain from
unreviewed inputs. It may only bind a reviewed Phase 505 record and an explicit
accepted append validation request surface.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 505 record is not the exact stale blocker rejection metadata state;
- any Phase 505 digest, id, label, nonclaim, rule, action, or inherited digest
  binding drifts;
- the reviewed and expected current accepted append blocker digests are
  missing, zero, or unequal;
- the accepted append owner is not `zkbench-core`;
- the validation function identifier is not
  `validate_accepted_ledger_append_transaction_request`;
- the handoff asks for `apply_accepted_ledger_append_transaction`;
- the handoff asks for materialized accepted ledger append output;
- the handoff asks to read or write accepted Evidence Ledger files;
- the target ledger id is missing;
- the transaction id is missing;
- the expected current ledger tip digest is missing when a non-empty target
  ledger is being evaluated;
- the append-preview current ledger tip digest is not bound;
- the preflight request and report digests are not bound;
- the candidate, append preview, review decision, or source artifact digest set
  is not bound;
- the request tries to populate score axes;
- the request tries to create Level2+ or formal evidence;
- the request tries to create official submission metadata;
- the request summary contains forbidden promotion language;
- the handoff claims semantic correctness, production readiness, SOTA,
  breakthrough status, full security, external audit status, or action
  authority.

## Backend Relationship

This boundary is still not Lean, SMT, COBALT, or Rust-to-Lean backend
execution. It is the accepted append validation handoff that must be resolved
before any later accepted-evidence lane can be evaluated.

The future handoff may produce only local validation-handoff metadata. It must
not produce accepted evidence, accepted formal evidence, Level2+ evidence,
score-axis evidence, checker transcript authority, solver certificate
authority, benchmark evidence, or public SOTA/security/correctness/readiness
claims.

## Meaning Limit

The future accepted append evaluation handoff metadata may support this claim
only:

```text
HSAI locally records a validation-only handoff boundary from the reviewed
tiny-Z3 accepted-path prerequisite chain to the zkbench-core accepted-ledger
append transaction validator.
```

That still is not:

- accepted append mutation;
- accepted evidence;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- materialized accepted ledger output;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- checker transcript authority;
- solver certificate authority;
- benchmark evidence;
- external audit;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Phase 507 Implementation Exit Criteria

A future Phase 507 may implement local accepted append evaluation handoff
metadata only if it:

- stays within `crates/hsai-agent-admission/src/lib.rs` unless a separate
  boundary explicitly allows a dependency or crate-surface change;
- adds no Cargo metadata in the same slice;
- writes no filesystem artifacts;
- performs no process or network calls;
- reads no accepted Evidence Ledger files;
- mutates no accepted Evidence Ledger files;
- does not call `validate_accepted_ledger_append_transaction_request` yet;
- does not call `apply_accepted_ledger_append_transaction`;
- does not call `apply_materialized_accepted_ledger_append_transaction`;
- binds one Phase 505 stale blocker rejection record digest;
- binds one Phase 505 stale blocker rejection input digest;
- binds the Phase 505 digest/id/label map digests;
- binds the Phase 505 explicit nonclaim digest;
- binds the Phase 505 freshness rule digest;
- binds the Phase 505 stale blocker rejection action digest;
- binds the Phase 505 inherited digest requirement digest;
- binds the reviewed and expected current accepted append blocker digests;
- binds the `zkbench-core` owner id and validation function identifier;
- binds the accepted append request, preflight, report, candidate, append
  preview, review decision, source artifact set, target ledger id, and ledger
  tip identity fields;
- rejects mutation, materialization, score-axis, Level2+, formal-evidence,
  backend-execution, benchmark, external-audit, strong-claim, and
  action-authority requests in the metadata itself.

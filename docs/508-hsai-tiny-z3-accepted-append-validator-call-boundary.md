# Phase 508 HSAI Tiny Z3 Accepted Append Validator Call Boundary

State slice: `Phase 508 HSAI tiny Z3 accepted append validator call
boundary`.

Phase 508 defines the docs-first boundary for the first real accepted append
validator crossing:

```text
in-memory validation-only call from HSAI accepted append handoff metadata to
zkbench-core validate_accepted_ledger_append_transaction_request
```

Phase 507 implemented local accepted append handoff metadata but still forbids
adding a `zkbench-core` dependency or calling the validator. Phase 508 records
the boundary a future implementation must satisfy before any code may call the
existing `zkbench-core` accepted append validator.

This phase does not implement Rust code, change Cargo metadata, add a
`zkbench-core` dependency to `hsai-agent-admission`, read accepted Evidence
Ledger files, write accepted Evidence Ledger files, call
`validate_accepted_ledger_append_transaction_request`, call
`apply_accepted_ledger_append_transaction`, call
`apply_materialized_accepted_ledger_append_transaction`, create materialized
accepted ledger output, create an accepted append decision, create accepted
formal evidence, create Level2+ evidence, populate score axes, generate proof
artifacts, generate checker transcripts, generate solver certificates, run
Lean, run new SMT, run COBALT, run Rust-to-Lean extraction, create benchmark
evidence, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, claim external audit status,
or grant authority to execute an action.

## Future Allowed Touch Surface

A future implementation phase may only touch these files unless a later
boundary explicitly broadens scope:

- `crates/hsai-agent-admission/Cargo.toml`;
- `Cargo.lock`, only for the lockfile entry produced by the local
  `zkbench-core` dependency edge;
- `crates/hsai-agent-admission/src/lib.rs`;
- focused tests in `crates/hsai-agent-admission/src/lib.rs`;
- the future phase notes under `docs/`;
- navigation/status updates under `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`.

The future Cargo change may add only this local dependency:

```toml
zkbench-core = { path = "../zkbench-core" }
```

No external dependency, feature flag, binary, script, runner, process-spawn API,
network API, fixture artifact, accepted ledger file, or generated output file
is authorized by this boundary.

## Future Allowed Validator Call

A future implementation may call only:

```rust
validate_accepted_ledger_append_transaction_request(
    request: &AcceptedLedgerAppendTransactionRequest,
    ledger: &EvidenceLedger,
)
```

The request and ledger must be caller-supplied in-memory values. The future
implementation must not load a ledger from disk, write a ledger to disk,
initialize a missing ledger file, or materialize accepted ledger output.

The future implementation must not call:

- `apply_accepted_ledger_append_transaction`;
- `apply_materialized_accepted_ledger_append_transaction`;
- `EvidenceLedger::load_json`;
- `EvidenceLedger::save_json`;
- `MaterializedAcceptedLedgerAppendRequest`;
- any external runner, solver, proof assistant, benchmark runner, official
  submission API, network API, or process-spawn API.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 507 accepted append handoff record digest;
- one Phase 507 accepted append handoff input digest;
- the Phase 507 digest-binding map digest;
- the Phase 507 id-binding map digest;
- the Phase 507 label-binding map digest;
- the Phase 507 explicit nonclaim digest;
- the Phase 507 validation handoff rule digest;
- the Phase 507 forbidden API set digest;
- the Phase 507 inherited digest requirement digest;
- reviewed and expected current accepted append blocker digests from Phase 507;
- `zkbench-core` as accepted append owner;
- `validate_accepted_ledger_append_transaction_request` as the only validator;
- `AcceptedLedgerAppendTransactionRequest` as request type;
- `AcceptedLedgerAppendTransactionValidation` as validation output type;
- `EvidenceLedger` as target ledger type;
- target ledger id;
- transaction id;
- expected current ledger tip digest;
- append-preview current ledger tip digest;
- transaction request digest;
- candidate digest;
- append preview digest;
- review decision digest;
- source artifact set digest;
- validation result digest;
- validation issue-kind set digest;
- validation valid flag.

The future validator-call metadata must preserve the Phase 507 handoff
identity and must not recompute prior prerequisite state from unreviewed
inputs.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 507 record is not the exact accepted append handoff metadata state;
- any Phase 507 digest, id, label, nonclaim, rule, forbidden-API, or inherited
  digest binding drifts;
- the reviewed and expected current accepted append blocker digests are
  missing, zero, or unequal;
- the accepted append owner is not `zkbench-core`;
- the validator identifier is not
  `validate_accepted_ledger_append_transaction_request`;
- the request or ledger is loaded from filesystem state by HSAI admission code;
- the validation call result is not digest-bound;
- the validation issue-kind set is not digest-bound;
- the validator returns invalid and the metadata attempts to proceed;
- the metadata treats a valid validator result as accepted append mutation;
- the metadata treats a valid validator result as accepted evidence;
- the metadata asks for accepted Evidence Ledger mutation;
- the metadata asks for materialized accepted ledger output;
- the metadata asks for score-axis population;
- the metadata asks for Level2+ or formal evidence;
- the metadata asks for proof/checker/solver authority;
- the metadata asks for Lean/new-SMT/COBALT/Rust-to-Lean execution evidence;
- the metadata asks for benchmark evidence;
- the metadata claims semantic correctness, production readiness, SOTA,
  breakthrough status, full security, external audit status, or action
  authority.

## Backend Relationship

This boundary is still not Lean, SMT, COBALT, or Rust-to-Lean backend
execution. It is the first in-memory accepted append validator-call boundary.

Even if the future validator call returns valid, that would prove only that a
caller-supplied in-memory transaction request and in-memory ledger satisfy the
existing local `zkbench-core` accepted append validator. It would still not be
an accepted Evidence Ledger mutation, accepted formal evidence, Level2+
evidence, score-axis evidence, benchmark evidence, external audit, SOTA,
semantic correctness, production readiness, full security, or authority to
execute an action.

## Meaning Limit

The future validator-call metadata may support this claim only:

```text
HSAI locally records the result of an in-memory validation-only call to the
zkbench-core accepted-ledger append transaction validator for one reviewed
tiny-Z3 accepted-path handoff.
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

## Phase 509 Implementation Exit Criteria

A future Phase 509 may implement local accepted append validator-call metadata
only if it:

- touches only the allowed files listed above;
- adds only the local `zkbench-core` path dependency;
- performs no process or network calls;
- reads no accepted Evidence Ledger files;
- writes no accepted Evidence Ledger files;
- uses only caller-supplied in-memory
  `AcceptedLedgerAppendTransactionRequest` and `EvidenceLedger` values;
- calls only `validate_accepted_ledger_append_transaction_request`;
- does not call accepted append mutation or materialization APIs;
- records the returned `AcceptedLedgerAppendTransactionValidation` as local
  validation metadata only;
- binds the validation result digest, issue-kind set digest, and valid flag;
- rejects proceeding after invalid validation;
- rejects treating valid validation as accepted evidence or accepted append
  mutation;
- rejects accepted Evidence Ledger mutation, materialized output, formal
  evidence, Level2+, score axes, proof/checker/solver authority, backend
  execution evidence, benchmark evidence, external audit, strong claims, and
  action authority in the metadata itself.

## Phase 509 Implementation Status

Phase 509 implements this boundary as local in-memory validator-call metadata
in `crates/hsai-agent-admission/src/lib.rs`, adds the local
`zkbench-core = { path = "../zkbench-core" }` dependency to
`crates/hsai-agent-admission/Cargo.toml`, records the corresponding
`Cargo.lock` dependency edge, and documents the result in
`docs/509-hsai-tiny-z3-accepted-append-validator-call-metadata-notes.md`.

The implementation remains inside this boundary: it calls only
`zkbench_core::validate_accepted_ledger_append_transaction_request` over
caller-supplied in-memory values, reads no accepted Evidence Ledger files,
writes no accepted Evidence Ledger files, does not call accepted append
mutation APIs, creates no materialized accepted ledger output, creates no
accepted formal evidence, creates no Level2+ evidence, populates no score
axes, runs no Lean/new-SMT/COBALT/Rust-to-Lean, creates no benchmark evidence,
and claims no SOTA, semantic correctness, production readiness, full security,
external audit, breakthrough status, or action authority.

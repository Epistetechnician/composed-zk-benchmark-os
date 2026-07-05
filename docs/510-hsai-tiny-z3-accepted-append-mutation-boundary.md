# Phase 510 HSAI Tiny Z3 Accepted Append Mutation Boundary

State slice: `Phase 510 HSAI tiny Z3 accepted append mutation boundary`.

Phase 510 defines the docs-first boundary for the first local accepted append
mutation crossing:

```text
in-memory accepted-ledger append mutation through
zkbench-core apply_accepted_ledger_append_transaction
```

Phase 509 implemented an in-memory validation-only call to
`validate_accepted_ledger_append_transaction_request`. Phase 510 records the
boundary a future implementation must satisfy before HSAI may call the
existing in-memory `zkbench-core` mutation function.

This phase does not implement Rust code, change Cargo metadata, read accepted
Evidence Ledger files, write accepted Evidence Ledger files, call
`apply_accepted_ledger_append_transaction`, call
`apply_materialized_accepted_ledger_append_transaction`, create materialized
accepted ledger output, create accepted formal evidence, create Level2+
evidence, populate score axes, generate proof artifacts, generate checker
transcripts, generate solver certificates, run Lean, run new SMT, run COBALT,
run Rust-to-Lean extraction, create benchmark evidence, claim semantic
correctness, claim production readiness, claim SOTA, claim breakthrough
status, claim full security, claim external audit status, or grant authority
to execute an action.

## Future Allowed Touch Surface

A future implementation phase may only touch these files unless a later
boundary explicitly broadens scope:

- `crates/hsai-agent-admission/src/lib.rs`;
- focused tests in `crates/hsai-agent-admission/src/lib.rs`;
- the future phase notes under `docs/`;
- navigation/status updates under `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`.

No Cargo metadata change, external dependency, feature flag, binary, script,
runner, process-spawn API, network API, fixture artifact, accepted ledger file,
or generated output file is authorized by this boundary.

## Future Allowed Mutation Call

A future implementation may call only:

```rust
apply_accepted_ledger_append_transaction(
    request: &AcceptedLedgerAppendTransactionRequest,
    ledger: &mut EvidenceLedger,
)
```

The request and ledger must be caller-supplied in-memory values. The future
implementation must not load a ledger from disk, write a ledger to disk,
initialize a missing ledger file, or materialize accepted ledger output.

The future implementation must not call:

- `apply_materialized_accepted_ledger_append_transaction`;
- `MaterializedAcceptedLedgerAppendRequest`;
- `EvidenceLedger::load_json`;
- `EvidenceLedger::save_json`;
- any external runner, solver, proof assistant, benchmark runner, official
  submission API, network API, or process-spawn API.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 509 accepted append validator-call record digest;
- one Phase 509 accepted append validator-call input digest;
- the Phase 509 digest-binding map digest;
- the Phase 509 id-binding map digest;
- the Phase 509 label-binding map digest;
- the Phase 509 explicit nonclaim digest;
- the Phase 509 validation call rule digest;
- the Phase 509 forbidden API set digest;
- the Phase 509 inherited digest requirement digest;
- reviewed and expected current accepted append blocker digests from Phase 509;
- `zkbench-core` as accepted append owner;
- `apply_accepted_ledger_append_transaction` as the only mutation function;
- `AcceptedLedgerAppendTransactionRequest` as request type;
- `AcceptedLedgerAppendTransactionReport` as report type;
- `EvidenceLedger` as target ledger type;
- target ledger id;
- transaction id;
- pre-mutation in-memory ledger digest;
- transaction request digest;
- validation result digest from Phase 509;
- validation valid flag from Phase 509;
- post-mutation in-memory ledger digest;
- accepted append report digest;
- appended entry digest if mutation succeeds;
- appended sequence number if mutation succeeds;
- appended evidence class;
- appended claim boundary.

The future mutation metadata must preserve the Phase 509 validator-call
identity and must not recompute prior prerequisite state from unreviewed
inputs.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 509 record is not the exact accepted append validator-call
  metadata state;
- any Phase 509 digest, id, label, nonclaim, rule, forbidden-API, or inherited
  digest binding drifts;
- the reviewed and expected current accepted append blocker digests are
  missing, zero, or unequal;
- the Phase 509 validation valid flag is false;
- the accepted append owner is not `zkbench-core`;
- the mutation function identifier is not
  `apply_accepted_ledger_append_transaction`;
- the request or ledger is loaded from filesystem state by HSAI admission code;
- the mutation report is not digest-bound;
- the post-mutation in-memory ledger digest is not digest-bound;
- the mutation report does not have `mutates_accepted_evidence_ledger = true`;
- the mutation report has `creates_official_submission = true`;
- the mutation report has `populates_score_axes = true`;
- the appended claim boundary is above `Level1LocalReplay`;
- the appended evidence class is a formal, cross-backend, reproducible
  benchmark, machine-checked, or independently reproduced evidence class;
- the metadata asks for materialized accepted ledger output;
- the metadata asks for accepted Evidence Ledger file reads or writes;
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
execution. It is the first in-memory accepted append mutation boundary.

If a future in-memory mutation succeeds, it may support only a scoped local
accepted-ledger mutation claim for one caller-supplied in-memory ledger value.
It still would not be materialized accepted ledger output, accepted formal
evidence, Level2+ evidence, score-axis evidence, benchmark evidence, external
audit, SOTA, semantic correctness, production readiness, full security, or
authority to execute an action.

## Meaning Limit

The future accepted append mutation metadata may support this claim only:

```text
HSAI locally records one in-memory accepted-ledger append mutation through the
zkbench-core accepted-ledger append transaction owner for a reviewed tiny-Z3
accepted-path handoff.
```

That still is not:

- materialized accepted ledger output;
- accepted formal evidence;
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

## Phase 511 Implementation Exit Criteria

Phase 511 implemented local accepted append mutation metadata in
`docs/511-hsai-tiny-z3-accepted-append-mutation-metadata-notes.md`. The
implementation met this boundary by:

- touches only the allowed files listed above;
- performs no process or network calls;
- reads no accepted Evidence Ledger files;
- writes no accepted Evidence Ledger files;
- uses only caller-supplied in-memory
  `AcceptedLedgerAppendTransactionRequest` and mutable `EvidenceLedger` values;
- calls only `apply_accepted_ledger_append_transaction`;
- does not call materialized output APIs;
- records the returned `AcceptedLedgerAppendTransactionReport` as local
  mutation metadata only;
- binds the pre-mutation ledger digest, post-mutation ledger digest, report
  digest, appended entry digest, appended sequence number, appended evidence
  class, and appended claim boundary;
- rejects failed mutation as accepted evidence;
- rejects materialized output, filesystem read/write, formal evidence,
  Level2+, score axes, proof/checker/solver authority, backend execution
  evidence, benchmark evidence, external audit, strong claims, and action
  authority in the metadata itself.

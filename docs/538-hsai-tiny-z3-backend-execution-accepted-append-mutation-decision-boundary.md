# Phase 538 HSAI Tiny Z3 Backend Execution Accepted Append Mutation Decision Boundary

State slice: `Phase 538 HSAI tiny Z3 backend execution accepted append mutation decision boundary`.

Phase 538 defines the docs-first boundary for the first accepted-append
mutation decision after
`docs/537-hsai-tiny-z3-backend-execution-accepted-append-evaluation-metadata-notes.md`:

```text
Phase 537 validation-only accepted append evaluation metadata
  + explicit mutation decision boundary
  -> future in-memory accepted append mutation decision metadata
```

Phase 537 records that the existing `zkbench-core` accepted append validator
evaluated one caller-supplied in-memory request and ledger. It still does not
authorize mutation. This boundary defines what must be true before a future
phase may ask the existing `zkbench-core` in-memory mutation owner to append
the already validated request into a caller-supplied mutable in-memory
`EvidenceLedger`.

This phase does not implement Rust code, change Cargo metadata, call
`apply_accepted_ledger_append_transaction`, call
`apply_materialized_accepted_ledger_append_transaction`, read accepted Evidence
Ledger files, write accepted Evidence Ledger files, create materialized
accepted ledger output, create accepted formal evidence, create Level2+
evidence, populate score axes, generate proof artifacts, generate checker
transcripts, generate solver certificates, run Lean, run another SMT/Z3
execution, run COBALT, run Rust-to-Lean extraction, run external replay,
submit benchmarks, claim semantic correctness, claim production readiness,
claim SOTA, claim breakthrough status, claim full security, claim independent
external reproduction, or grant authority to execute an action.

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
materialized ledger output, or generated output file is authorized by this
boundary.

## Future Allowed Mutation Call

A future implementation may call only:

```rust
zkbench_core::apply_accepted_ledger_append_transaction(
    request: &AcceptedLedgerAppendTransactionRequest,
    ledger: &mut EvidenceLedger,
)
```

The request and ledger must be caller-supplied in-memory values. The future
implementation must not load a ledger from disk, write a ledger to disk,
initialize a missing ledger file, materialize accepted ledger output, or call a
mutation function through an HSAI-owned ledger path.

The future implementation must not call:

- `apply_materialized_accepted_ledger_append_transaction`;
- `MaterializedAcceptedLedgerAppendRequest`;
- `EvidenceLedger::load_json`;
- `EvidenceLedger::save_json`;
- any external runner, solver, proof assistant, benchmark runner, official
  submission API, network API, or process-spawn API.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 537 accepted append evaluation digest;
- one Phase 537 accepted append evaluation input digest;
- the Phase 537 digest-binding map digest;
- the Phase 537 id-binding map digest;
- the Phase 537 label-binding map digest;
- the Phase 537 explicit nonclaim digest;
- the Phase 537 evaluation policy digest;
- the Phase 537 evaluation rule digest;
- the Phase 537 forbidden-API set digest;
- the Phase 537 inherited-digest requirement digest;
- the Phase 537 validation result digest;
- the Phase 537 validation issue-kind digest;
- the Phase 537 validation valid flag;
- the Phase 535 owner-decision digest and input digest;
- the Phase 533 review digest and input digest;
- the Phase 531 package digest and input digest;
- the Phase 529 backend execution result digest and request digest;
- the Phase 527 candidate digest and input digest;
- `zkbench-core` as accepted append owner;
- `apply_accepted_ledger_append_transaction` as the only mutation function;
- `AcceptedLedgerAppendTransactionRequest` as request type;
- `AcceptedLedgerAppendTransactionReport` as report type;
- `EvidenceLedger` as target ledger type;
- target ledger id;
- transaction id;
- pre-mutation in-memory ledger digest;
- transaction request digest;
- post-mutation in-memory ledger digest;
- accepted append report digest;
- appended entry digest if mutation succeeds;
- appended sequence number if mutation succeeds;
- appended evidence class;
- appended claim boundary.

The future mutation decision metadata must preserve the Phase 537 validation
identity and must not recompute prior prerequisite state from unreviewed
inputs.

## Required Future Validation

A future implementation must fail closed if:

- the Phase 537 record is not the exact accepted append evaluation metadata
  state;
- any Phase 537 digest, id, label, nonclaim, policy, rule, forbidden-API, or
  inherited-digest binding drifts;
- the Phase 537 validation valid flag is false;
- the Phase 537 validation issue count is nonzero;
- the Phase 537 validation result digest is missing or zero;
- the caller-supplied request identity drifts from Phase 537;
- the caller-supplied pre-mutation ledger digest drifts from Phase 537;
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
- the appended evidence class is formal, cross-backend, reproducible
  benchmark, machine-checked, or independently reproduced evidence;
- the metadata asks for materialized accepted ledger output;
- the metadata asks for accepted Evidence Ledger file reads or writes;
- the metadata asks for score-axis population;
- the metadata asks for Level2+ or formal evidence;
- the metadata asks for proof/checker/solver authority;
- the metadata asks for Lean, additional SMT/Z3, COBALT, or Rust-to-Lean
  execution evidence;
- the metadata asks for benchmark evidence;
- the metadata claims semantic correctness, production readiness, SOTA,
  breakthrough status, full security, independent external reproduction,
  external audit status, or action authority.

## Meaning Limit

The future mutation decision metadata may support this claim only:

```text
HSAI locally records whether one Phase 537 validation-satisfied backend
execution route may proceed to an in-memory zkbench-core accepted append
mutation.
```

If a later in-memory mutation succeeds, that may support only a scoped local
accepted-ledger mutation claim for one caller-supplied in-memory ledger value.
It still would not be materialized accepted ledger output, accepted formal
evidence, Level2+ evidence, score-axis evidence, benchmark evidence, external
audit, independent external reproduction, SOTA, semantic correctness,
production readiness, full security, or authority to execute an action.

## Phase 539 Implementation Exit Criteria

A future Phase 539 may implement local accepted append mutation decision
metadata only if it:

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
  evidence, benchmark evidence, independent reproduction, external audit,
  strong claims, and action authority in the metadata itself.

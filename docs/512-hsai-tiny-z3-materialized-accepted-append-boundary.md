# Phase 512 HSAI Tiny Z3 Materialized Accepted Append Boundary

State slice: `Phase 512 HSAI tiny Z3 materialized accepted append boundary`.

Phase 512 defines the docs-first boundary for a future local materialized
accepted-ledger append output:

```text
Phase 511 in-memory mutation metadata
  + caller-selected local JSON ledger path
  -> zkbench-core MaterializedAcceptedLedgerAppendRequest
  -> zkbench-core apply_materialized_accepted_ledger_append_transaction
  -> local JSON accepted ledger artifact
```

This phase does not implement Rust code, change Cargo metadata, write files,
read accepted Evidence Ledger files, write accepted Evidence Ledger files, call
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
- future phase notes under `docs/`;
- navigation/status updates under `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`.

No Cargo metadata change, external dependency, feature flag, binary, script,
runner, process-spawn API, network API, official submission API, solver API,
proof-assistant API, benchmark runner, generated benchmark output, score-axis
output, or backend execution output is authorized by this boundary.

## Future Allowed Materialization Call

A future implementation may call only:

```rust
apply_materialized_accepted_ledger_append_transaction(
    request: &MaterializedAcceptedLedgerAppendRequest,
)
```

The materialized request must be constructed from:

- one exact Phase 511 in-memory mutation metadata record;
- the same accepted append transaction request identity already bound by
  Phase 511;
- a caller-selected local JSON ledger path;
- an explicit `create_if_missing` flag.

The future implementation must route through `zkbench-core`
`MaterializedAcceptedLedgerAppendRequest`. HSAI admission code must not invent a
parallel ledger writer, call `EvidenceLedger::load_json` directly, call
`EvidenceLedger::save_json` directly, manually create temp files, or write the
accepted ledger through any API other than the existing `zkbench-core`
materialized append owner.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 511 accepted append mutation metadata digest;
- one Phase 511 mutation input digest;
- the Phase 511 digest-binding map digest;
- the Phase 511 id-binding map digest;
- the Phase 511 label-binding map digest;
- the Phase 511 explicit nonclaim digest;
- the Phase 511 mutation-rule digest;
- the Phase 511 forbidden-API set digest;
- the Phase 511 inherited-digest requirement digest;
- the Phase 511 transaction request digest;
- the Phase 511 Phase 509 validation result digest;
- the Phase 511 pre-mutation in-memory ledger digest;
- the Phase 511 post-mutation in-memory ledger digest;
- the Phase 511 accepted append report digest;
- the Phase 511 appended entry digest;
- the Phase 511 appended sequence number;
- the Phase 511 appended evidence class;
- the Phase 511 appended claim boundary;
- `zkbench-core` as accepted append materialization owner;
- `MaterializedAcceptedLedgerAppendRequest` as materialized request type;
- `apply_materialized_accepted_ledger_append_transaction` as only
  materialized append function;
- local ledger path identity digest;
- local ledger path policy digest;
- `create_if_missing` policy value;
- materialized append report digest if the future call succeeds;
- post-materialization ledger artifact digest if the future call succeeds.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 511 mutation record is not exact;
- Phase 511 did not record a successful in-memory append mutation;
- any Phase 511 digest, id, label, nonclaim, rule, forbidden-API, or inherited
  digest binding drifts;
- the appended evidence class is not `LocalReplay`;
- the appended claim boundary is not `Level1LocalReplay`;
- the materialized owner is not `zkbench-core`;
- the request type is not `MaterializedAcceptedLedgerAppendRequest`;
- the function identifier is not
  `apply_materialized_accepted_ledger_append_transaction`;
- the implementation tries to call `EvidenceLedger::load_json` or
  `EvidenceLedger::save_json` directly from HSAI admission code;
- the implementation tries to create a parallel ledger writer;
- the ledger path digest or path policy digest is missing;
- the future materialized report is not digest-bound;
- the future post-materialization ledger artifact digest is not digest-bound;
- the metadata asks for formal evidence, Level2+ evidence, score axes,
  proof/checker/solver authority, Lean/new-SMT/COBALT/Rust-to-Lean evidence,
  benchmark evidence, external audit, semantic correctness, production
  readiness, SOTA, breakthrough status, full security, or action authority.

## Backend Relationship

This boundary is not Lean, SMT, COBALT, or Rust-to-Lean backend execution. It
is not proof authority. It is not benchmark evidence. It is not score-axis
evidence. It is not external audit evidence.

If a future materialized append succeeds, it may support only a scoped local
artifact claim:

```text
HSAI materialized one local JSON accepted-ledger artifact through the existing
zkbench-core materialized accepted append owner for a reviewed tiny-Z3 local
accepted-path handoff.
```

That still would not be accepted formal evidence, Level2+ evidence, score-axis
evidence, Lean proof, SMT proof authority, COBALT containment evidence,
Rust-to-Lean proof, checker transcript authority, solver certificate authority,
benchmark evidence, external audit, SOTA, semantic correctness, production
readiness, full security, or authority to execute an action.

## Phase 513 Implementation Exit Criteria

Phase 513 implemented local materialized accepted append metadata in
`docs/513-hsai-tiny-z3-materialized-accepted-append-metadata-notes.md`. The
implementation met this boundary by:

- touches only the allowed files listed above;
- performs no process or network calls;
- routes only through `MaterializedAcceptedLedgerAppendRequest`;
- calls only `apply_materialized_accepted_ledger_append_transaction`;
- does not call direct ledger load/save APIs from HSAI admission code;
- does not create a parallel ledger writer;
- uses a caller-selected local JSON ledger path;
- binds the ledger path identity digest and path policy digest;
- binds the materialized append report digest;
- binds the post-materialization ledger artifact digest;
- records materialization as local artifact metadata only;
- rejects formal evidence, Level2+, score axes, proof/checker/solver
  authority, backend execution evidence, benchmark evidence, external audit,
  strong claims, and action authority in the metadata itself.

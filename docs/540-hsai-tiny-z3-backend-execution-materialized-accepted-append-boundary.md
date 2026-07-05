# Phase 540 HSAI Tiny Z3 Backend Execution Materialized Accepted Append Boundary

State slice: `Phase 540 HSAI tiny Z3 backend execution materialized accepted append boundary`.

Phase 540 defines the docs-first boundary for a future local materialized
accepted-ledger append output over the Phase 539 in-memory mutation metadata:

```text
Phase 539 in-memory mutation metadata
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
correctness, claim production readiness, claim SOTA, claim breakthrough status,
claim full security, claim external audit status, or grant authority to execute
an action.

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

- one exact Phase 539 in-memory mutation metadata record;
- the same accepted append transaction request identity already bound by
  Phase 539;
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

- one Phase 539 accepted append mutation metadata digest;
- one Phase 539 mutation input digest;
- the Phase 539 digest-binding map digest;
- the Phase 539 id-binding map digest;
- the Phase 539 label-binding map digest;
- the Phase 539 explicit nonclaim digest;
- the Phase 539 mutation-rule digest;
- the Phase 539 forbidden-API set digest;
- the Phase 539 inherited-digest requirement digest;
- the Phase 539 transaction request digest;
- the Phase 539 Phase 537 validation result digest;
- the Phase 539 pre-mutation in-memory ledger digest;
- the Phase 539 post-mutation in-memory ledger digest;
- the Phase 539 accepted append report digest;
- the Phase 539 appended entry digest;
- the Phase 539 appended sequence number;
- the Phase 539 appended evidence class;
- the Phase 539 appended claim boundary;
- the inherited Phase 535 owner-decision digest;
- the inherited Phase 533 review digest;
- the inherited Phase 531 package digest;
- the inherited Phase 529 backend execution result digest;
- the inherited Phase 527 candidate digest;
- `zkbench-core` as accepted append materialization owner;
- `MaterializedAcceptedLedgerAppendRequest` as materialized request type;
- `apply_materialized_accepted_ledger_append_transaction` as only
  materialized append function;
- local ledger path identity digest;
- local ledger path policy digest;
- `create_if_missing` policy value;
- materialized append report digest if the future call succeeds;
- post-materialization ledger artifact digest if the future call succeeds;
- post-materialization ledger artifact byte length if the future call succeeds.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 539 mutation record is not exact;
- Phase 539 did not record a successful in-memory append mutation;
- any Phase 539 digest, id, label, nonclaim, rule, forbidden-API, inherited
  digest, or prior-phase binding drifts;
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
- the future post-materialization byte length is not recorded;
- the metadata asks for accepted formal evidence, Level2+ evidence, score axes,
  proof/checker/solver authority, Lean/new-SMT/COBALT/Rust-to-Lean evidence,
  benchmark evidence, external audit, semantic correctness, production
  readiness, SOTA, breakthrough status, full security, independent external
  reproduction, or action authority.

## Backend Relationship

This boundary is not Lean, SMT, COBALT, or Rust-to-Lean backend execution. It
is not proof authority. It is not benchmark evidence. It is not score-axis
evidence. It is not external audit evidence.

If a future materialized append succeeds, it may support only this scoped local
artifact claim:

```text
HSAI materialized one local JSON accepted-ledger artifact through the existing
zkbench-core materialized accepted append owner for a reviewed local SMT/Z3
backend execution route.
```

That still would not be accepted formal evidence, Level2+ evidence, score-axis
evidence, Lean proof, SMT proof authority, COBALT containment evidence,
Rust-to-Lean proof, checker transcript authority, solver certificate
authority, benchmark evidence, external audit, independent external
reproduction, SOTA, semantic correctness, production readiness, full security,
or authority to execute an action.

## Phase 541 Implementation Exit Criteria

A future Phase 541 implementation satisfies this boundary only if it:

- touches only the allowed files listed above;
- performs no process or network calls;
- routes only through `MaterializedAcceptedLedgerAppendRequest`;
- calls only `apply_materialized_accepted_ledger_append_transaction`;
- does not call direct ledger load/save APIs from HSAI admission code;
- does not create a parallel ledger writer;
- uses a caller-selected local JSON ledger path;
- binds the ledger path identity digest and path policy digest;
- binds the materialized append report digest;
- binds the post-materialization ledger artifact digest and byte length;
- records materialization as local artifact metadata only;
- rejects accepted formal evidence, Level2+, score axes, proof/checker/solver
  authority, backend execution evidence, benchmark evidence, external audit,
  strong claims, independent external reproduction, and action authority in the
  metadata itself.

# Phase 490 HSAI Tiny Z3 Accepted Append Owner Mutation Route Boundary

State slice: `Phase 490 HSAI tiny Z3 accepted append owner mutation route
boundary`.

Phase 490 defines the docs-first boundary for the first Phase 489
accepted-path prerequisite gate:

```text
accepted_append_owner_and_mutation_route
```

The purpose is to prevent HSAI tiny-Z3 admission metadata from becoming a
parallel accepted-evidence path. The accepted append owner remains
`zkbench-core`, specifically the guarded accepted-ledger append transaction
surface in `crates/zkbench-core/src/evidence/accepted_append.rs` and the
explicit materialized ledger path surface in
`crates/zkbench-core/src/evidence/accepted_append_output.rs`.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, mutate the accepted Evidence Ledger, change accepted
append policy, create accepted formal evidence, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, run Lean, run new SMT, run COBALT, run
Rust-to-Lean extraction, submit benchmarks, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, or grant authority to execute an action.

## Current Owner

The current accepted append owner is `zkbench-core`:

- `AcceptedLedgerAppendTransactionRequest`;
- `validate_accepted_ledger_append_transaction_request`;
- `build_evidence_record_from_transaction`;
- `apply_accepted_ledger_append_transaction`;
- `MaterializedAcceptedLedgerAppendRequest`;
- `apply_materialized_accepted_ledger_append_transaction`.

The owner accepts only explicit local inputs. It appends only through a
caller-supplied in-memory `EvidenceLedger` or a caller-selected materialized
JSON ledger path. It rejects stale tips, mismatched preflight/report/candidate
state, official-submission attempts, score-axis attempts, Level2+ or formal
evidence classes, missing artifact digests, and forbidden claim text.

## HSAI Admission Role

`crates/hsai-agent-admission` may produce local metadata, reviews,
nonpromotion blockers, terminal records, and prerequisite records. It may not
mutate the accepted Evidence Ledger directly.

A future HSAI-to-accepted-append bridge may only be considered if it prepares
inputs for the existing `zkbench-core` accepted append transaction. It must not
introduce a second ledger mutation owner, a second accepted evidence ledger, or
a side-channel append route.

## Required Future Bridge Inputs

A future implementation that tries to satisfy this gate must bind:

- one Phase 489 accepted-path prerequisite digest;
- one Phase 489 accepted-path prerequisite input digest;
- the Phase 489 gate-status map digest;
- the Phase 489 digest-binding map digest;
- the Phase 489 id-binding map digest;
- the Phase 489 label-binding map digest;
- explicit nonclaim digest;
- current accepted append blocker digest;
- target accepted append owner identifier;
- target accepted append transaction schema version;
- target materialized append route identifier;
- exact target ledger id or explicit unresolved ledger-id marker;
- exact target ledger path or explicit unresolved path marker;
- required `zkbench-core` transaction input shape;
- rejection policy for missing reviewed preflight, append preview, review
  decision, source artifact digests, stale ledger tip, score-axis attempt,
  Level2+ attempt, formal-evidence attempt, benchmark attempt, or strong public
  claim.

The future bridge must record unresolved values as unresolved. It must not
invent target ledger ids, target paths, preflight reports, append previews,
review decisions, source artifact digests, or accepted records.

## Required Future Validation

A future validator must reject the owner/mutation-route gate input if:

- the schema version is not the future Phase 491 schema;
- the Phase 489 prerequisite digest or input digest drifts;
- the Phase 489 gate-status map digest drifts;
- the Phase 489 digest/id/label map digests drift;
- the explicit nonclaim digest drifts;
- the current accepted append blocker digest drifts;
- the accepted append owner is anything other than `zkbench-core`;
- the mutation route bypasses `AcceptedLedgerAppendTransactionRequest`;
- the materialized route bypasses `MaterializedAcceptedLedgerAppendRequest`;
- the bridge tries to directly mutate `EvidenceLedger` from
  `hsai-agent-admission`;
- the bridge tries to create accepted formal evidence;
- the bridge tries to create Level2+ evidence;
- the bridge tries to populate score axes;
- the bridge tries to create proof/checker/solver authority;
- the bridge tries to create Lean/new-SMT/COBALT/Rust-to-Lean execution
  evidence;
- the bridge tries to create benchmark evidence;
- the bridge tries to claim SOTA, semantic correctness, production readiness,
  full security, breakthrough status, or action authority.

## Meaning Limit

The future owner/mutation-route gate record may support this claim only:

```text
HSAI locally records that any future accepted append must route through the
existing zkbench-core accepted-ledger append transaction owner, and that HSAI
admission metadata is not itself an accepted Evidence Ledger mutation owner.
```

That still is not:

- accepted append;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- benchmark evidence;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Phase 491 Implementation Exit Criteria

Phase 491 implements local owner/mutation-route gate metadata in
`docs/491-hsai-tiny-z3-accepted-append-owner-mutation-route-metadata-notes.md`.
That implementation remains valid only while it:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds the Phase 489 prerequisite digest and input digest;
- binds the Phase 489 gate-status digest;
- binds the Phase 489 digest/id/label map digests;
- identifies `zkbench-core` as the only accepted append owner;
- identifies `AcceptedLedgerAppendTransactionRequest` as the only local
  transaction route;
- identifies `MaterializedAcceptedLedgerAppendRequest` as the only materialized
  local path route;
- records unresolved bridge inputs explicitly;
- rejects direct accepted Evidence Ledger mutation from HSAI admission metadata;
- rejects accepted append decisions in the gate metadata itself;
- rejects accepted formal evidence creation in the gate metadata itself;
- rejects Level2+ evidence creation in the gate metadata itself;
- rejects score-axis population in the gate metadata itself;
- rejects proof/checker/solver authority creation in the gate metadata itself;
- rejects Lean/new-SMT/COBALT/Rust-to-Lean execution evidence creation in the
  gate metadata itself;
- rejects benchmark evidence creation in the gate metadata itself;
- rejects SOTA, semantic-correctness, production-readiness, full-security,
  breakthrough, and action-authority claims in the gate metadata itself.

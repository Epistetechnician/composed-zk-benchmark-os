# Phase W Accepted Ledger Materialization Implementation Notes

## Status

Implemented for local JSON ledger materialization.

This phase implements the narrow materialized append surface authorized by
`docs/118-phase-w-accepted-ledger-materialization-boundary-spec.md`.

## State Slice

This slice is limited to:

- `crates/zkbench-core/src/evidence/accepted_append_output.rs`
- `crates/zkbench-core/src/evidence/mod.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_w_accepted_ledger_append.rs`
- This implementation note and navigation/status updates.

## Implemented Surface

The implementation adds:

- `MaterializedAcceptedLedgerAppendRequest`
- `apply_materialized_accepted_ledger_append_transaction`

The materialized path:

- Requires an explicit ledger JSON path.
- Requires an existing parent directory.
- Rejects parent-directory components.
- Rejects symlink ledger paths and symlink parents.
- Loads and validates an existing ledger when present.
- Requires `create_if_missing` before creating a new empty local ledger.
- Applies the Phase 117 accepted-ledger append transaction.
- Writes through a same-directory temporary JSON file and renames it into place.

## Tests

Focused tests cover:

- Creating a missing local ledger only when `create_if_missing` is true.
- Appending a second reviewed transaction to an existing local ledger.
- Rejecting missing ledgers without explicit creation permission.
- Rejecting missing parent directories.
- Rejecting directory targets.
- Rejecting invalid existing ledger JSON without repair.
- Rejecting symlink ledger targets on Unix platforms.
- Rejecting stale transactions against existing ledgers without repairing or
  rewriting the ledger.
- Rejecting parent-directory path components.
- Source-scan boundaries proving no network, process, credential, backend, or
  official-submission surface exists.

## Claim Boundary

Materialized accepted-ledger JSON is local accepted evidence only for the
reviewed Level1-or-below claim represented by the transaction inputs. It is not
official benchmark evidence. It is not external replay evidence. It is not
Level2+ evidence. It is not ZK backend performance evidence. It is not semantic
correctness evidence.

## Remaining Gaps

No official benchmark submission exists. No external replay evidence exists.
No Level2+ evidence exists. No score-axis population exists. No generated
benchmark artifact campaign or submitted artifact package is created by this
phase.

# Phase W Accepted Ledger Append Implementation Notes

## Status

Implemented for a local, explicit, fail-closed append transaction in
`zkbench-core`.

This phase implements the narrow code surface authorized by
`docs/116-phase-w-accepted-ledger-append-boundary-spec.md`. It adds validation
and application mechanics for a caller-supplied in-memory `EvidenceLedger`.

## State Slice

This slice is limited to:

- `crates/zkbench-core/src/evidence/accepted_append.rs`
- `crates/zkbench-core/src/evidence/mod.rs`
- `crates/zkbench-core/src/lib.rs`
- `crates/zkbench-core/tests/phase_w_accepted_ledger_append.rs`
- This implementation note and navigation/status updates.

## Implemented Surface

The implementation adds:

- `AcceptedLedgerAppendTransactionRequest`
- `AcceptedLedgerAppendTransactionValidation`
- `AcceptedLedgerAppendTransactionReport`
- `validate_accepted_ledger_append_transaction_request`
- `build_evidence_record_from_transaction`
- `apply_accepted_ledger_append_transaction`

The validator requires:

- An explicit non-empty target ledger id.
- A valid current `EvidenceLedger`.
- A valid Phase W reviewed promotion preflight request.
- A preflight report that exactly matches the supplied preflight request.
- A current ledger tip matching the transaction expectation, preflight request,
  and append preview.
- Candidate, append-preview, candidate digest, evidence-class, and
  claim-boundary alignment.
- Source artifact digests.
- No official-submission request.
- No score-axis population.
- No Level2+ or formal evidence class.

`apply_accepted_ledger_append_transaction` refuses to mutate the ledger unless
validation is clean. On success it converts the reviewed candidate into an
`EvidenceRecord` and appends through the existing `EvidenceLedger::append`
policy, preserving the repository's Level1-or-below local evidence cap.

## Claim Boundary

This phase creates local accepted-ledger append mechanics only. It does not
create official benchmark evidence. It does not create Level2+ evidence. It
does not run external replay. It does not submit to an official endpoint. It
does not populate score axes. It does not claim ZK backend performance,
semantic correctness, formal evidence, or proof-system soundness.

An accepted local ledger entry produced by this implementation is accepted only
inside the caller-supplied local `EvidenceLedger` and only for the reviewed
Level1-or-below claim represented by the transaction inputs.

## Tests

Focused tests cover:

- Valid local Level1 append and bounded mutation reporting.
- Stale ledger-tip rejection without mutation.
- Candidate digest mismatch rejection without mutation.
- Official-submission, score-axis, and Level2+ claim rejection.
- Source-scan boundaries proving the module has no network, process,
  filesystem persistence, official-submission, or external runtime surface.

## Remaining Gaps

No official benchmark submission exists. No external replay evidence exists.
No Level2+ evidence exists. No score-axis population exists. No generated
benchmark artifact campaign or submitted artifact package is created by this
phase.

# Statebook P15 Destination Finality And Proven No-Outflow Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p15-destination-finality-proven-no-outflow-boundary`.

Future implementation state slice:
`statebook-p15-destination-finality-proven-no-outflow`.

## Objective

Authorize hermetic P4 transfer-budget transitions for destination finality and
independently validated no-outflow proof (PRD US-51; P4 boundary scenarios #17
/#18): destination finality moves `in_flight` → `consumed` without restoring
capacity; `ProvenNoOutflow` restores capacity only with validated evidence;
ambiguous no-outflow evidence leaves exposure in flight.

P15 does not implement recovery reopen drills or live authority. No value moves.

## Authorized behavior

1. `apply_transfer_submit_v1` moves `Reserved` → `Submitted` and shifts the
   amount from `reserved` to `in_flight` under CAS.
2. `apply_destination_finality_v1` moves `in_flight` → `consumed` for a submitted
   transfer, sets transfer status `Consumed`, and never increases available
   capacity.
3. `apply_proven_no_outflow_v1` with validated evidence decreases `in_flight`
   (or `reserved`) without increasing `consumed`, sets `ProvenNoOutflow`, and
   restores available capacity.
4. Invalid or ambiguous no-outflow evidence rejects without mutating ledger
   exposure.
5. Fixture axes may declare `reserved`, `in_flight`, and `consumed` counters.

## Authorized paths

Future implementation may change only:

- additive edits under `crates/statebook-settlement/src/p4/`;
- additive tests under `crates/statebook-settlement/tests/`;
- additive corpus cases/tests under `crates/statebook-e2e-harness/`;
- new
  `docs/statebook-p15-destination-finality-proven-no-outflow-implementation-notes.md`;
- `README.md`, `AGENTS.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Submit reserved amount → in_flight increases, reserved decreases.
2. Destination finality → consumed increases, in_flight decreases, available
   capacity does not increase.
3. Valid ProvenNoOutflow → in_flight decreases, consumed unchanged, available
   increases.
4. Invalid ProvenNoOutflow → reject; in_flight unchanged.
5. Existing P4/P9–P14 suites remain green.

## Nonclaims

P15 creates no live pause authority, custody, signing, transfer command,
clearing recognition, legal finality, complete TD-004 satisfaction, production
readiness, SOTA, independent audit, or full-security claim. Local hermetic
finality/no-outflow regression only. No value moves.

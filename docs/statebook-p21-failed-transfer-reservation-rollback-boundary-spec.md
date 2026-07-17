# Statebook P21 Failed Transfer Reservation Rollback Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p21-failed-transfer-reservation-rollback-boundary`.

Future implementation state slice:
`statebook-p21-failed-transfer-reservation-rollback`.

## Objective

Authorize hermetic P4 failed-transfer reservation rollback (P4 boundary #31
rollback half): when a reservation succeeds but the transfer cannot proceed
(Frozen), reserved/in-flight exposure must be released under CAS so available
capacity is restored. Sequential finalizer tip contention remains one-success.
No value moves.

## Authorized behavior

1. `apply_failed_transfer_rollback_v1` decrements `reserved` (or `in_flight` if
   already submitted) under CAS, sets transfer `Unreserved`, never increases
   caps or consumed.
2. Kernel Frozen path after a successful reserve invokes rollback for the
   reserved amount.
3. Harness corpus covers rollback capacity restore and sequential stale-tip
   destination-finality CAS (one success).
4. Existing suites remain green.

## Authorized paths

- additive edits under `crates/statebook-settlement/src/p4/`;
- additive tests under `crates/statebook-settlement/tests/`;
- additive corpus under `crates/statebook-e2e-harness/`;
- implementation notes and standard navigation mirrors.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Reserve then explicit rollback restores available capacity.
2. Frozen decide path after reserve does not leak reserved exposure.
3. Sequential finalizer with stale tip: exactly one success.
4. Double-rollback / over-release rejects without tip mutation when rejected.
5. Existing suites remain green.

## Nonclaims

Local hermetic reservation-rollback / CAS-finalizer fixture regression only.
Not artificial-profit PnL (#23), complete TD-004 #31 concurrency, live
authority, production readiness, SOTA, independent audit, or full security. No
value moves.

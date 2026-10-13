# Statebook P22 Queued Value Monetization And Post-Instant Anomaly Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation shipped under
`statebook-p22-queued-value-monetization`.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p22-queued-value-monetization-boundary`.

Future implementation state slice:
`statebook-p22-queued-value-monetization`.

## Objective

Authorize hermetic P4 coverage for P4 boundary scenarios #27 and #29: anomaly
after instant-part release must block the queued remainder, and attempts to
monetize queued value (transferable claim / borrow / internal credit) while the
queue is `Queued` must reject with zero instant. No value moves.

## Authorized behavior

1. Optional `monetizes_queued_value` on requests; when true and queue status is
   `Queued`, decide rejects with `QueuedValueMonetization` and zero instant.
2. After a Queued decision that released an instant part, a subsequent decide
   with failed anomaly clearance rejects the queued remainder with zero instant.
3. Omitted/`false` `monetizes_queued_value` keeps intent digests unchanged.

## Authorized paths

- additive edits under `crates/statebook-settlement/src/p4/`;
- additive tests under `crates/statebook-settlement/tests/`;
- additive corpus cases under `crates/statebook-e2e-harness/`;
- implementation notes and standard navigation mirrors.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Monetize-while-queued → Rejected / `QueuedValueMonetization` / zero instant.
2. Instant-then-anomaly on queued remainder → Rejected / anomaly reason / zero
   instant.
3. Existing suites remain green.

## Nonclaims

Local hermetic queued-value / post-instant-anomaly fixture regression only. Not
artificial-profit PnL (#23), venue solvency digest binding (#33), complete
TD-004 satisfaction, live authority, production readiness, SOTA, independent
audit, or full security. No value moves.

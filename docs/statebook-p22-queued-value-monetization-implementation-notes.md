# Statebook P22 Queued Value Monetization And Post-Instant Anomaly Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p22-queued-value-monetization`.

## Outcome

- Optional `monetizes_queued_value` rejects with `QueuedValueMonetization` when
  the queue is already `Queued`.
- After a Queued decision that released an instant part, a failed anomaly
  clearance rejects the queued remainder with zero instant.
- Harness corpus adds `td004_29_queued_value_monetization` and
  `td004_27_anomaly_after_instant_before_queued` (44 encodable cases).

Live authority remains deferred. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic queued-value / post-instant-anomaly fixture regression only. Not
artificial-profit PnL (#23), venue solvency digest binding (#33), complete
TD-004 satisfaction, live authority, production readiness, SOTA, independent
audit, or full security. No value moves.

# Statebook P19 Oracle Freshness And Compromised Source Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p19-oracle-freshness-compromised-source`.

## Outcome

- Gate 2 rejects `prepared_earlier` reports and stale `content_observed_at`
  even when transport `observed_at` is fresh.
- Independence quarantines when Pass observations with distinct current roots
  share a dependency root id (dual-vendor / compromised upstream).
- Valuation rejects observations whose `root_id` overlaps
  `calculation_integrity` current roots (`ValuationActionOracleFallback`).
- Harness corpus adds four cases (40 encodable total).

Live authority remains deferred. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic oracle-freshness / compromised-source fixture regression only.
Not complete TD-004 satisfaction, artificial-profit PnL (#23), concurrent
finalizer races (#31), live authority, production readiness, SOTA, independent
audit, or full security. No value moves.

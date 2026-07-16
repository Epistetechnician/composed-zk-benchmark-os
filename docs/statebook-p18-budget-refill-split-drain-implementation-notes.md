# Statebook P18 Budget Refill Split And Slow Drain Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p18-budget-refill-split-drain`.

## Outcome

- `apply_budget_refill_v1` advances the ledger epoch by exactly one and reduces
  `consumed` by a positive amount not exceeding `MAX_REFILL_PER_EPOCH_V1` (50);
  caps never increase.
- Skip-epoch, backfill, over-ceiling, and non-positive refill reject as
  `BudgetRefillRejected` without tip mutation.
- Harness corpus adds slow-drain exhaustion, sequential split that cannot expand
  aggregate caps, and refill skip-epoch reject (36 encodable corpus cases).
- Contended CAS tip one-success remains covered by existing
  `cas_tip_contention_one_success` in `statebook-settlement` kernel tests;
  refill additionally rejects stale tips as `LedgerCasConflict`.

Live authority remains deferred. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic budget-refill / aggregate-cap fixture regression only. Not
complete TD-004 satisfaction, live authority, production readiness, SOTA,
independent audit, or full security. No value moves.

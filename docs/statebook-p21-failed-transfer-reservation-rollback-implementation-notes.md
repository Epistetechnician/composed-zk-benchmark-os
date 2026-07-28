# Statebook P21 Failed Transfer Reservation Rollback Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p21-failed-transfer-reservation-rollback`.

## Outcome

- `apply_failed_transfer_rollback_v1` releases reserved (or in-flight) exposure
  under CAS and sets transfer `Unreserved`.
- Kernel Frozen path after a successful reserve invokes rollback so reserved
  capacity cannot leak.
- Corpus adds failed-transfer rollback and sequential finalizer CAS contention
  (42 encodable cases).

Live authority remains deferred. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic reservation-rollback / CAS-finalizer fixture regression only.
Not artificial-profit PnL (#23), complete TD-004 concurrency, live authority,
production readiness, SOTA, independent audit, or full security. No value moves.

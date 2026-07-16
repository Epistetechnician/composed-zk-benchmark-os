# Statebook P15 Destination Finality And Proven No-Outflow Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p15-destination-finality-proven-no-outflow`.

## Outcome

P4 now:

- exposes `apply_transfer_submit_v1`, `apply_destination_finality_v1`, and
  `apply_proven_no_outflow_v1`;
- available capacity is `cap - consumed - reserved - in_flight`;
- destination finality moves `in_flight` → `consumed` without restoring
  capacity;
- validated ProvenNoOutflow restores capacity; invalid evidence leaves
  exposure in flight.

Harness corpus adds `td004_16_proven_no_outflow_rejected` and
`td004_16_finality_no_capacity_restore`. Recovery reopen and live authority
remain deferred. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic finality/no-outflow regression only. Not live pause authority,
complete TD-004 satisfaction, production readiness, SOTA, independent audit, or
full security. No value moves.

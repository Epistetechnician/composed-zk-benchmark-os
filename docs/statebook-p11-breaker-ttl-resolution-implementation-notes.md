# Statebook P11 Breaker TTL And Resolution Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p11-breaker-ttl-resolution`.

## Outcome

P4 kernel now:

- applies breaker TTL exhaustion at the start of `decide_and_transition`;
- rejects with zero instant release when a scope is in `Resolution` or an
  expired Guarded/Recovery scope would otherwise silently renew;
- exposes `attempt_breaker_renewal_v1` that rejects at the renewal ceiling and
  extends expiry below the ceiling.

Harness corpus adds `td004_17_breaker_ttl_resolution` and
`td004_17_breaker_expired_no_silent_renew`. Challenged→Frozen behavior is
preserved. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic breaker TTL/resolution regression only. Not live pause authority,
complete TD-004 satisfaction, production readiness, SOTA, independent audit, or
full security. No value moves.

# Statebook P17 Adversarial Corpus Expansion Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p17-adversarial-corpus-expansion`.

## Outcome

- Future valuation observations (`observed_at > now`) reject as stale.
- Harness corpus adds bound-request mismatch, future valuation, equivocated
  evidence, valuation conflict, and Halted→Normal forbidden cases (33 total
  encodable corpus cases).

Live authority remains deferred. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic adversarial fixture regression only. Not complete TD-004
satisfaction, live authority, production readiness, SOTA, independent audit, or
full security. No value moves.

# Statebook P20 Model Confidence Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p20-model-confidence`.

## Outcome

- Optional `model_confidence_claimed` on requests; omitted/false is not encoded
  in intent digests.
- When confidence is claimed and any hard gate or valuation fails, reasons
  include `ModelConfidenceIgnored` and instant release remains zero.
- Corpus `td004_18_model_confidence_bypass` now claims confidence while failing
  a hard gate.

Live authority remains deferred. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic model-confidence fixture regression only. Not complete TD-004
satisfaction, live authority, production readiness, SOTA, independent audit, or
full security. No value moves.

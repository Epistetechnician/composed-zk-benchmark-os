# Statebook P14 Cancel And Race Intents Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p14-cancel-race-intents`.

## Outcome

P4 now:

- binds `bound_intent_digest` and `bound_destination` on Queued outcomes;
- exposes `apply_cancel_v1` requiring a new cancellation intent digest;
- rejects same-digest cancel and destination replacement without new intent;
- rejects decide against `Cancelled` with `QueueCancelled` and zero instant.

Harness corpus adds `td004_25_cancel_race` and
`td004_25_destination_without_new_intent`. Live authority remains deferred. No
value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic cancel/race regression only. Not live pause authority, complete
TD-004 satisfaction, production readiness, SOTA, independent audit, or full
security. No value moves.

# Statebook P13 Hysteresis Relax And Rollback Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p13-hysteresis-relax-rollback`.

## Outcome

P4 now:

- anchors `active_policy`, `last_policy_change_at`, and `clean_epochs` on
  settlement state;
- exposes `attempt_policy_transition_v1` / `evaluate_policy_transition_v1`;
- rejects policy-version rollback with `PolicyRollback` and zero instant;
- applies pure tighten immediately;
- gates relax on dwell, clean epochs, successor digest, and version bump,
  rejecting with `PolicyRelaxRejected` otherwise.

Harness corpus adds `td004_21_policy_rollback` and
`td004_21_policy_relax_rejected`. Cancel remains deferred. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic hysteresis regression only. Not live pause authority, complete
TD-004 satisfaction, production readiness, SOTA, independent audit, or full
security. No value moves.

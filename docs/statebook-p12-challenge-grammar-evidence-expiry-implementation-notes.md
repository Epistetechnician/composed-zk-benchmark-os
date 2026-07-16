# Statebook P12 Challenge Grammar And Evidence Expiry Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p12-challenge-grammar-evidence-expiry`.

## Outcome

P4 now:

- exposes `apply_challenge_v1` for bounded challenge submissions
  (valid/invalid/duplicate/censored/unavailable);
- transitions a valid challenge on a queued `Unreserved` part to `Challenged`,
  then `decide_and_transition` yields `Frozen` with zero instant release;
- rejects invalid/duplicate/censored/unavailable challenges without release
  authority;
- applies evidence expiry while queued into `RevalidationRequired` with
  `EvidenceExpired` rejection and zero instant release;
- clears `RevalidationRequired` under fresh evidence toward `Reserved`
  (Immediate + Reserved transfer), never timer-alone release.

Harness corpus adds six TD-004 #31 cases (five challenge variants + evidence
expiry). Hysteresis and cancel remain deferred. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-settlement -p statebook-e2e-harness -- --check
cargo test -p statebook-settlement --tests
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-settlement -p statebook-e2e-harness --all-targets -- -D warnings
```

## Claim ceiling

Local hermetic challenge grammar / evidence-expiry regression only. Not live
pause authority, complete TD-004 satisfaction, production readiness, SOTA,
independent audit, or full security. No value moves.

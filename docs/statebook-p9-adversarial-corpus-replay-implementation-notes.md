# Statebook P9 Adversarial Corpus Replay Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p9-adversarial-corpus-replay`.

## Outcome

`crates/statebook-e2e-harness` now hosts:

- `encodable_corpus_cases_v1` / `build_corpus_scenario_v1` /
  `replay_encodable_corpus_v1` for twelve encodable TD-004 / P4 adversarial
  cases;
- `replay_timer_alone_chain_v1` for TD-004 #11 chained queue timer rejection;
- fail-closed zero-instant invariants on every non-Immediate case.

No P4 kernel edits. No live authority. No value moves.

## Encoded cases

`td004_01_oracle_replay`, `td004_06_empty_evidence_roots`,
`td004_07_stale_valuation`, `td004_08_shared_dependency_root`,
`td004_10_reuse_finality_blocked`, `td004_12_budget_exhausted`,
`td004_13_linked_dvp_leg_fail`, `td004_14_false_risk_reducing`,
`td004_17_breaker_halted`, `td004_18_model_confidence_bypass`,
`td004_22_cas_tip_mismatch`, `td004_26_recovery_mismatch`, plus
`td004_11_timer_alone` chain.

## Local validation evidence

```text
cargo fmt -p statebook-e2e-harness -- --check
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-e2e-harness --all-targets -- -D warnings
cargo test -p statebook-core -p statebook-settlement -p statebook-report -p statebook-source -p statebook-authority --tests
```

Thirteen focused harness tests pass after this slice (prior nine plus four
corpus tests).

## Remaining gaps

Kernel-deferred TD-004 / P4 scenarios remain outside: challenge grammar,
evidence-expiry revalidation, breaker TTL wiring, hysteresis, cancel/race,
semantic signed-but-wrong oracles, and beyond-ceiling split orchestration.

## Claim ceiling

Local hermetic adversarial fixture regression only. Not complete TD-004
satisfaction, live authority, production security, SOTA, independent audit, or
full security. No value moves.

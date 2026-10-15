# Statebook P9 Adversarial Corpus Replay Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p9-adversarial-corpus-replay-boundary`.

Future implementation state slice:
`statebook-p9-adversarial-corpus-replay`.

## Objective

Authorize hermetic replay of the encodable subset of PRD **TD-004** and P4
boundary frozen adversarial scenarios through public P4 APIs, composed under
the P8 evaluation harness.

P9 expands falsification coverage. It does not add kernel features, live
authority, or value movement.

## Relationship to prior phases

- P4 remains the sole settlement transition kernel.
- P8 remains the composing evaluation harness entrypoint.
- P9 consumes public `parse_settlement_scenario_v1` and
  `decide_and_transition` (and related public helpers). It does not reimplement
  gates, budgets, queue, or breaker transitions.
- Scenarios that require new kernel surfaces (challenge grammar ingest, breaker
  TTL wiring, hysteresis transitions, cancel intents, semantic oracle
  falsehood) remain deferred outside this slice.

## Crate and ownership boundary

Future implementation may change only:

1. additive modules, fixtures, and tests under
   `crates/statebook-e2e-harness/**`;
2. root `Cargo.toml` / `Cargo.lock` only if already-allowed hermetic test
   dependencies require it;
3. new
   `docs/statebook-p9-adversarial-corpus-replay-implementation-notes.md`;
4. `README.md`, `AGENTS.md`, `docs/12-task-list.md`,
   `docs/90-whole-codebase-validation-report.md`.

No mutation of `statebook-core`, `statebook-settlement` `src/`,
`statebook-report`, `statebook-source`, or `statebook-authority`. No
`statebook-sim`. No new workspace crate.

## Frozen encodable corpus (minimum)

The future implementation must deterministically replay at least these
encodable cases (IDs are stable):

| ID | TD-004 / boundary ref | Expected fail-closed behavior |
|----|-----------------------|-------------------------------|
| `td004_01_oracle_replay` | TD-004 #1 | Rejected; zero instant |
| `td004_06_empty_evidence_roots` | TD-004 #6 | Quarantined or Rejected; zero instant |
| `td004_07_stale_valuation` | TD-004 #7 | Rejected; zero instant |
| `td004_08_shared_dependency_root` | TD-004 #8 | Quarantined or Rejected; zero instant |
| `td004_10_reuse_finality_blocked` | TD-004 #10 | Rejected; zero instant |
| `td004_12_budget_exhausted` | TD-004 #12 | Rejected; zero instant |
| `td004_13_linked_dvp_leg_fail` | TD-004 #13 | Rejected; zero instant |
| `td004_14_false_risk_reducing` | TD-004 #14 | Rejected; zero instant |
| `td004_17_breaker_halted` | TD-004 #17/#32 | Rejected or Frozen; zero instant |
| `td004_18_model_confidence_bypass` | TD-004 #18 | Rejected; zero instant |
| `td004_22_cas_tip_mismatch` | TD-004 #22 | Rejected; zero instant |
| `td004_26_recovery_mismatch` | TD-004 #26 | Rejected; zero instant |

Additionally:

- `td004_11_timer_alone` — chained queue replay: timer passage alone never
  releases (zero instant on second step);
- hard invariant: no corpus case that is not Immediate may emit nonzero instant
  release;
- claim-boundary scan continues to forbid network/process/live-authority
  surfaces.

## Deferred (explicitly out of this slice)

Challenge grammar ingest, evidence-expiry queue revalidation, breaker TTL→
Resolution wiring, hysteresis relax/rollback, cancel/race intents, 100-way
split beyond existing resource ceilings, semantic signed-but-wrong oracle
cross-check, watcher/service-liveness model, and full thirty-seven-scenario
enumeration requiring those features.

## Acceptance gates

- every listed encodable case parses and fails closed as specified;
- focused format/test/Clippy pass for `statebook-e2e-harness`;
- unchanged P1–P8 crate tests pass;
- no P4 kernel (`src/p4/`) edits;
- documentation and claim-boundary hygiene pass.

## Nonclaims

P9 creates no live order, fill, custody, signing, pause, transfer, real margin
award, clearing recognition, legal finality, production security proof,
complete TD-004 satisfaction, SOTA, independent audit, or full-security claim.
Local hermetic adversarial fixture regression only. No value moves.

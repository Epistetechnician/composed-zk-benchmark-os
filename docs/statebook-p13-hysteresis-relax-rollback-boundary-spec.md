# Statebook P13 Hysteresis Relax And Rollback Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p13-hysteresis-relax-rollback-boundary`.

Future implementation state slice:
`statebook-p13-hysteresis-relax-rollback`.

## Objective

Authorize asymmetric P4 policy hysteresis so TD-004 #21 and P4 boundary
scenario #16 become hermetically replayable: adverse tighten applies
immediately; relaxation requires dwell, clean epochs, and the designated
successor policy digest; policy-version rollback rejects with zero instant
release.

P13 does not implement cancel intents or live authority. No value moves.

## Relationship to prior phases

- P4 remains the settlement kernel owner. P13 is an additive kernel surface
  inside `crates/statebook-settlement` plus corpus coverage in
  `statebook-e2e-harness`.
- P11–P12 breaker/challenge surfaces remain unchanged.
- Existing digests remain unchanged except appended decision-reason tags for
  new hysteresis paths.

## Authorized behavior

1. Settlement state anchors an `active_policy` (version, digest, tiers) plus
   `last_policy_change_at` and `clean_epochs`.
2. `attempt_policy_transition_v1` and `decide_and_transition` evaluate proposed
   request policy against the active anchor.
3. Version decrease is `PolicyRollback` with zero instant release.
4. Pure tighten (lower instant fraction or higher delay on any tier) applies
   immediately and updates the active anchor.
5. Any relax dimension requires:
   - `now - last_policy_change_at >= min_relax_dwell_seconds`;
   - `clean_epochs >= required_clean_epochs`;
   - proposed `policy_digest ==` active hysteresis `successor_policy_digest`;
   - proposed `policy_version >` active version.
   Failure yields `PolicyRelaxRejected` with zero instant release.
6. Matching active digest is a no-op.

## Authorized paths

Future implementation may change only:

- additive edits under `crates/statebook-settlement/src/p4/`;
- additive tests under `crates/statebook-settlement/tests/`;
- additive corpus cases/tests under `crates/statebook-e2e-harness/`;
- new
  `docs/statebook-p13-hysteresis-relax-rollback-implementation-notes.md`;
- `README.md`, `AGENTS.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Policy version rollback rejects with `PolicyRollback`, zero instant.
2. Tighten (reduced instant or increased delay) succeeds immediately.
3. Relax before dwell / clean epochs / wrong successor digest rejects with
   `PolicyRelaxRejected`.
4. Relax meeting all gates succeeds and updates the active anchor.
5. Existing P4/P9–P12 suites remain green.
6. Claim-boundary scans continue to forbid network/process/live-authority
   surfaces.

## Nonclaims

P13 creates no live pause authority, custody, signing, transfer, clearing
recognition, legal finality, complete TD-004 satisfaction, production
readiness, SOTA, independent audit, or full-security claim. Local hermetic
hysteresis regression only. No value moves.

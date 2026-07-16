# Statebook P12 Challenge Grammar And Evidence Expiry Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p12-challenge-grammar-evidence-expiry-boundary`.

Future implementation state slice:
`statebook-p12-challenge-grammar-evidence-expiry`.

## Objective

Authorize P4 challenge-grammar ingest and evidence-expiry queue revalidation so
that TD-004 #31 and P4 boundary scenarios #11 / #13 / #14 become hermetically
replayable: valid/invalid/duplicate/censored/unavailable challenges preserve
deterministic queue outcomes; evidence expiry while queued enters
`RevalidationRequired` with zero instant release; fresh evidence creates a new
decision context without timer-alone release.

P12 does not implement hysteresis relax/rollback, cancel intents, or live
authority. No value moves.

## Relationship to prior phases

- P4 remains the settlement kernel owner. P12 is an additive kernel surface
  inside `crates/statebook-settlement` plus corpus coverage in
  `statebook-e2e-harness`.
- P11 breaker TTL/resolution remains unchanged.
- Existing P1–P3, P5–P11 public digests remain unchanged except for appended
  decision-reason tags for new challenge/evidence-expiry paths.

## Authorized behavior

1. `apply_challenge_v1` accepts a bounded challenge submission with explicit
   challenge id, trust root, deadline, affected scope, and grammar kind
   (`valid`, `invalid`, `duplicate`, `censored`, `unavailable`).
2. Valid challenge against a queued `Unreserved` part transitions queue status
   to `Challenged`; subsequent `decide_and_transition` yields `Frozen` with
   zero instant release.
3. Invalid, duplicate, censored, and unavailable challenges reject without
   granting release authority; duplicate detection uses applied challenge ids.
4. At the start of `decide_and_transition`, if queue status is `Queued` and any
   bound evidence observation (or the request) has `expires_at <= now`, queue
   status becomes `RevalidationRequired` and the decision rejects with zero
   instant release.
5. A later decision with fresh evidence (`expires_at > now`) against
   `RevalidationRequired` proceeds under a new `decision_context_digest` and
   may transition toward `Reserved`, never timer-alone release of the queued
   amount.
6. Challenge count is bounded by `MAX_CHALLENGES_V1`.

## Authorized paths

Future implementation may change only:

- additive edits under `crates/statebook-settlement/src/p4/` (new challenge
  module, kernel/types/digest/error/parse/exports);
- additive tests under `crates/statebook-settlement/tests/`;
- additive corpus cases/tests under `crates/statebook-e2e-harness/`;
- new
  `docs/statebook-p12-challenge-grammar-evidence-expiry-implementation-notes.md`;
- `README.md`, `AGENTS.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`;
- `Cargo.lock` only if already-allowed hermetic test deps require it.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Valid challenge on queued part → `Challenged` → `Frozen`, zero instant.
2. Invalid challenge rejects with `ChallengeInvalid`; queue unchanged.
3. Duplicate challenge id rejects with `ChallengeDuplicate`; queue unchanged.
4. Censored challenge rejects with `ChallengeCensored`; no release.
5. Unavailable challenge rejects with `ChallengeUnavailable`; no release.
6. Queued + expired evidence → `RevalidationRequired`, zero instant.
7. `RevalidationRequired` + fresh evidence → new decision context; no
   timer-alone release.
8. Existing P4 five-outcome, P9/P11 corpus, and breaker TTL suites remain green.
9. Claim-boundary scans continue to forbid network/process/live-authority
   surfaces.

## Nonclaims

P12 creates no live pause authority, custody, signing, transfer, clearing
recognition, legal finality, complete TD-004 satisfaction, production
readiness, SOTA, independent audit, or full-security claim. Local hermetic
challenge/evidence-expiry regression only. No value moves.

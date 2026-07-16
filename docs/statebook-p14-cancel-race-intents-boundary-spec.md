# Statebook P14 Cancel And Race Intents Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p14-cancel-race-intents-boundary`.

Future implementation state slice:
`statebook-p14-cancel-race-intents`.

## Objective

Authorize P4 cancel and destination-replacement intent rotation so TD-004 #25
and P4 boundary scenario #12 become hermetically replayable: cancel or
destination change requires a new parent intent digest; racing cancel against
release preserves fail-closed zero-instant outcomes; cancelled queue parts
never release.

P14 does not implement live authority. No value moves.

## Relationship to prior phases

- P4 remains the settlement kernel owner. P14 is an additive kernel surface
  inside `crates/statebook-settlement` plus corpus coverage in
  `statebook-e2e-harness`.
- P11–P13 surfaces remain unchanged except appended decision-reason tags if
  needed.

## Authorized behavior

1. On `Queued` outcomes, state binds `bound_intent_digest` and
   `bound_destination`.
2. `apply_cancel_v1` transitions `Queued` → `Cancelled` only when the provided
   expected intent matches the bound intent and the cancellation intent digest
   differs (new parent intent). Same-digest cancel rejects with
   `IntentDigestMismatch`.
3. `decide_and_transition` against `Cancelled` rejects with zero instant.
4. Destination change while bound intent is unchanged rejects with
   `IntentDigestMismatch` and zero instant.
5. Race ordering is deterministic under the injected clock / call order:
   cancel-then-decide and decide-then-cancel both remain fail-closed for value
   movement.

## Authorized paths

Future implementation may change only:

- additive edits under `crates/statebook-settlement/src/p4/`;
- additive tests under `crates/statebook-settlement/tests/`;
- additive corpus cases/tests under `crates/statebook-e2e-harness/`;
- new `docs/statebook-p14-cancel-race-intents-implementation-notes.md`;
- `README.md`, `AGENTS.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Cancel with new intent digest on queued part → `Cancelled`.
2. Cancel with same intent digest rejects; queue unchanged.
3. Decide on `Cancelled` → Rejected, zero instant.
4. Destination replacement without new intent → `IntentDigestMismatch`, zero
   instant.
5. Cancel-then-decide race → zero instant.
6. Existing P4/P9–P13 suites remain green.

## Nonclaims

P14 creates no live pause authority, custody, signing, transfer, clearing
recognition, legal finality, complete TD-004 satisfaction, production
readiness, SOTA, independent audit, or full-security claim. Local hermetic
cancel/race regression only. No value moves.

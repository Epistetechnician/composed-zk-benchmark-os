# Statebook P18 Budget Refill Split And Slow Drain Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation shipped under
`statebook-p18-budget-refill-split-drain`.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p18-budget-refill-split-drain-boundary`.

Future implementation state slice:
`statebook-p18-budget-refill-split-drain`.

## Objective

Authorize hermetic P4 budget epoch refill and remaining encodable aggregate-cap
adversarial coverage (PRD US-52; P4 boundary scenarios #8 / #30): sequential
capped refill without backfill; request splitting and slow drain cannot expand
or exceed aggregate caps.

P18 does not implement live authority. No value moves.

## Authorized behavior

1. `apply_budget_refill_v1` advances the ledger epoch by exactly one, reduces
   `consumed` by a positive amount not exceeding the per-epoch refill ceiling,
   and never increases caps.
2. Skipped epochs, backfilled epochs, zero/negative refill amounts, and refill
   above ceiling reject without tip mutation.
3. Harness corpus covers slow-drain aggregate exhaustion and sequential split
   that cannot expand aggregate caps; contended CAS tip one-success remains
   covered by the existing settlement kernel test.
4. Existing capacity accounting remains
   `cap - consumed - reserved - in_flight`.

## Authorized paths

- additive edits under `crates/statebook-settlement/src/p4/`;
- additive tests under `crates/statebook-settlement/tests/`;
- additive corpus cases under `crates/statebook-e2e-harness/`;
- implementation notes and standard navigation mirrors.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Sequential refill of consumed restores available capacity and bumps epoch.
2. Skip-epoch / backfill / over-ceiling / non-positive refill reject.
3. Slow drain of many small releases rejects once aggregate capacity is gone.
4. Sequential split against a shared cap rejects the second leg without
   expanding available capacity; CAS tip one-success remains covered by the
   existing kernel suite.
5. Existing suites remain green.

## Nonclaims

Local hermetic budget-refill / aggregate-cap regression only. Not live
authority, complete TD-004 satisfaction, production readiness, SOTA,
independent audit, or full security. No value moves.

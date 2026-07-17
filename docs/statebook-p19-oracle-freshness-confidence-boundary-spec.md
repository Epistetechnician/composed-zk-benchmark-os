# Statebook P19 Oracle Freshness And Confidence Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p19-oracle-freshness-confidence-boundary`.

Future implementation state slice:
`statebook-p19-oracle-freshness-confidence`.

## Objective

Authorize hermetic P4 oracle-freshness and model-confidence invariants (P4
boundary scenarios #21 / #34): stale valuation data must reject even when a
transport timestamp is fresh; claimed model/AI confidence must not bypass a
failed hard gate or failed valuation. No value moves.

## Authorized behavior

1. Optional `transport_observed_at` may appear on valuation observations; max-age
   and future checks use `observed_at` only and ignore transport time.
2. Optional `model_confidence_claimed` may appear on requests; when any hard gate
   fails or valuation fails and confidence is claimed, reasons include
   `ModelConfidenceIgnored` and instant release remains zero.
3. Corpus covers stale-data/fresh-transport and a real model-confidence bypass
   attempt (updating `td004_18_model_confidence_bypass`).
4. Existing suites remain green; baseline fixtures without the new fields keep
   unchanged digests.

## Authorized paths

- additive edits under `crates/statebook-settlement/src/p4/`;
- additive tests under `crates/statebook-settlement/tests/`;
- additive/updated corpus under `crates/statebook-e2e-harness/`;
- implementation notes and standard navigation mirrors.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Stale `observed_at` with fresh `transport_observed_at` → Rejected,
   `ValuationStale`, zero instant.
2. High/claimed model confidence with a failing hard gate → Rejected, gate
   reason plus `ModelConfidenceIgnored`, zero instant.
3. Baseline immediate fixture unchanged when transport is absent/fresh and gates
   pass.
4. Existing corpus suites remain green.

## Nonclaims

Local hermetic oracle-timestamp and confidence fixture regression only. Not
prepared-later consumption tracking (#20), compromised-upstream dual valuation
(#22), artificial-profit PnL (#23), concurrent finalizer races (#31), complete
TD-004 satisfaction, live authority, production readiness, SOTA, independent
audit, or full security. No value moves.

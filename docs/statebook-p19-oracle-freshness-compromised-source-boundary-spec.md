# Statebook P19 Oracle Freshness And Compromised Source Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation shipped under
`statebook-p19-oracle-freshness-compromised-source`.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p19-oracle-freshness-compromised-source-boundary`.

Future implementation state slice:
`statebook-p19-oracle-freshness-compromised-source`.

## Objective

Authorize hermetic P4 oracle-freshness and compromised-source fail-closed
hardening for P4 boundary scenarios #20, #21, #22, and #32: prepared-earlier
reuse, stale content with fresh transport timestamps, dual-vendor quorum
collapse under a shared compromised upstream root, and action-oracle valuation
fallback rejection.

P19 does not implement live authority. No value moves.

## Authorized behavior

1. Gate 2 fails closed when `prepared_earlier=true` even if transport
   `observed_at` is fresh and `replayed=false`.
2. Gate 2 fails closed when optional `content_observed_at` is stale relative to
   the injected clock (beyond `MAX_EVIDENCE_CONTENT_AGE_SECONDS_V1`) even if
   transport `observed_at` is fresh.
3. Independence evaluation quarantines when two Pass observations with distinct
   current roots share the same dependency root id.
4. Valuation rejects observations whose `root_id` overlaps
   `calculation_integrity` current roots (action-oracle fallback blocked).
5. Harness corpus adds four stable cases covering the above.

## Authorized paths

- additive edits under `crates/statebook-settlement/src/p4/`;
- additive tests under `crates/statebook-settlement/tests/`;
- additive corpus cases under `crates/statebook-e2e-harness/`;
- implementation notes and standard navigation mirrors.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Prepared-earlier + fresh transport → Rejected / zero instant.
2. Stale content + fresh transport → Rejected / zero instant.
3. Dual vendor / shared compromised upstream → Quarantined / zero instant.
4. Action-oracle valuation root overlap → Rejected / zero instant.
5. Existing suites remain green.

## Nonclaims

Local hermetic oracle-freshness / compromised-source fixture regression only.
Not complete TD-004 satisfaction, live authority, production readiness, SOTA,
independent audit, or full security. No value moves.

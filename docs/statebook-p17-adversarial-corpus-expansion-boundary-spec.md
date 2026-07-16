# Statebook P17 Adversarial Corpus Expansion Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p17-adversarial-corpus-expansion-boundary`.

Future implementation state slice:
`statebook-p17-adversarial-corpus-expansion`.

## Objective

Authorize further hermetic TD-004 / P4 adversarial corpus coverage using public
P4 APIs plus a fail-closed future-valuation observation check: bound-request
mismatch, equivocated evidence, valuation conflict, future observation reject,
and no direct Halted→Normal breaker edge replay.

P17 does not implement live authority. No value moves.

## Authorized paths

- additive harness corpus cases/tests under `crates/statebook-e2e-harness/`;
- additive fail-closed future-observation check under
  `crates/statebook-settlement/src/p4/valuation.rs` and tests;
- implementation notes and standard navigation mirrors.

## Frozen scenarios

1. Bound request id mismatch → Rejected / zero instant.
2. Equivocated evidence → Rejected / zero instant.
3. Conflicting valuation rates → Rejected / zero instant.
4. Future valuation observation → Rejected / zero instant.
5. Halted→Normal transition remains forbidden.
6. Existing corpus suites remain green.

## Nonclaims

Local hermetic adversarial fixture regression only. Not complete TD-004
satisfaction, live authority, production readiness, SOTA, independent audit, or
full security. No value moves.

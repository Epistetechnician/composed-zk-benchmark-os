# Statebook P11 Breaker TTL And Resolution Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p11-breaker-ttl-resolution-boundary`.

Future implementation state slice:
`statebook-p11-breaker-ttl-resolution`.

## Objective

Authorize wiring of P4 breaker TTL exhaustion into `decide_and_transition` so
that expired breakers at renewal ceiling enter `Resolution`, block release
without silent renewal or indefinite limbo, and reject malicious renewal
attempts (TD-004 #17 / #32; P4 boundary scenarios #15).

P11 does not implement challenge grammar, hysteresis relax/rollback, cancel
intents, or live authority. No value moves.

## Relationship to prior phases

- P4 remains the settlement kernel owner. P11 is an additive kernel wiring
  slice inside `crates/statebook-settlement` plus corpus coverage in
  `statebook-e2e-harness`.
- Existing helper `apply_ttl_exhaustion` is authorized to be called from the
  kernel. New public `attempt_breaker_renewal_v1` may be added.
- P1–P3, P5–P10 public APIs and digests remain unchanged except for new
  decision-reason tags appended for Resolution/renewal rejection paths.

## Authorized behavior

1. At the start of `decide_and_transition`, apply TTL exhaustion to every
   breaker scope using the injected clock.
2. If any scope is in `Resolution` (including after TTL apply), the decision
   rejects with zero instant release and a dedicated resolution reason; next
   state retains `Resolution`.
3. If any active protective scope is expired (`now >= expires_at`) but still
   below renewal ceiling, release is blocked with zero instant release and no
   silent renewal.
4. `attempt_breaker_renewal_v1` may extend `expires_at` and increment
   `renewal_count` only when `renewal_count < renewal_ceiling` and the current
   transition into the renewed protective state is valid. Attempts at or above
   the ceiling reject without changing state.
5. Direct `Halted -> Normal` remains forbidden.

## Authorized paths

Future implementation may change only:

- additive edits under `crates/statebook-settlement/src/p4/` (breaker, kernel,
  types reason enum/digest tags, exports);
- additive tests/fixtures under `crates/statebook-settlement/tests/`;
- additive corpus cases/tests under `crates/statebook-e2e-harness/`;
- new
  `docs/statebook-p11-breaker-ttl-resolution-implementation-notes.md`;
- `README.md`, `AGENTS.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`;
- `Cargo.lock` only if already-allowed hermetic test deps require it.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Halted breaker with `expires_at <= now` and `renewal_count >= renewal_ceiling`
   transitions to `Resolution` and rejects with zero instant release.
2. Expired protective breaker below ceiling blocks release without silent
   renewal.
3. Renewal at ceiling rejects; historical breaker digests/state unchanged.
4. Renewal below ceiling extends expiry and increments count.
5. Existing five-outcome fixtures and P9 encodable corpus remain green.
6. Claim-boundary scans continue to forbid network/process/live-authority
   surfaces.

## Nonclaims

P11 creates no live pause authority, custody, signing, transfer, clearing
recognition, legal finality, complete TD-004 satisfaction, production
readiness, SOTA, independent audit, or full-security claim. Local hermetic
breaker TTL/resolution regression only. No value moves.

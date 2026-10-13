# Statebook P16 Recovery Transitions Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p16-recovery-transitions-boundary`.

Future implementation state slice:
`statebook-p16-recovery-transitions`.

## Objective

Authorize hermetic P4 recovery drill transitions (P4 boundary scenario #19;
TD-004 #26): all-path halt inventory, reconciliation mismatch, canary failure,
and reopen that remains fail-closed unless reconciliation is clean and canary
stages pass. Binds the frozen P3 fourteen-path
`statebook_externalization_v1` inventory.

P16 does not implement live pause authority or production recovery. No value
moves.

## Authorized behavior

1. `apply_recovery_halt_all_v1` populates `halted_paths` with the fourteen
   required externalization path ids.
2. Non-empty `halted_paths`, `reconciliation_mismatch`, or `canary_failed`
   causes `decide_and_transition` to reject with `RecoveryFailed` and zero
   instant release.
3. `apply_recovery_reconciliation_v1` / `apply_recovery_canary_v1` set the
   corresponding fail-closed flags.
4. `apply_recovery_reopen_v1` clears halt inventory only when reconciliation is
   clean and canary has not failed; otherwise rejects without clearing halt.
5. Fixtures may declare `halted_paths` arrays.

## Authorized paths

Future implementation may change only additive P4 recovery/kernel/parse/export
edits, tests, harness corpus cases, implementation notes, and standard
navigation mirrors. No `statebook-sim`. No live authority.

## Frozen scenarios

1. All-path halt → decide Rejected / RecoveryFailed / zero instant.
2. Reconciliation mismatch → Rejected / zero instant.
3. Canary failed → Rejected / zero instant.
4. Reopen with mismatch or failed canary rejected; halt retained.
5. Reopen with clean reconciliation and passing canary clears halt.
6. Existing suites remain green.

## Nonclaims

Local hermetic recovery-drill regression only. Not production recovery
readiness, live pause authority, complete TD-004 satisfaction, SOTA,
independent audit, or full security. No value moves.

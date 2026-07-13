# Phase 758 HSAI Gateway Threat Ordinal Zsh Splitting Stop

## Status

Complete as one cleaned pre-helper-execution stop.

State slice:
`phase-758-hsai-gateway-threat-ordinal-zsh-splitting-stop`.

Classification: `HelperHashAssertionCommandMismatch`.

Diagnostic: `ZshScalarSplitDisabled`.

Execution status: `Succeeded` for phase-number, disk, owned-root absence,
primary-state preservation, detached-worktree creation, mode-`0700` run-root
creation, committed source pins, checker method-slice identity, unique ordinal
inventory, host Python identity, absolute `rg`, `sandbox-exec`, and pre-existing
checker Cargo-home gates; `Failed` at the first helper-hash assertion command;
and `NotRun` for helper compilation/tests, parser self-test, client metadata,
fixtures, network, Rust, Charon, Aeneas, Lean, Cargo, Lake, sandbox controls,
backend extraction, generated source, or kernel checking. Evidence ceiling:
`Level1LocalReplayOrLower`.

## First Failure

The helper-hash command encoded each filename and digest in one scalar, then
used `set -- $spec`. The active zsh did not split that scalar because
`SH_WORD_SPLIT` is disabled. The command therefore passed the combined
filename-and-digest string to `shasum`, which failed before any helper ran.

No same-phase repair or replay occurred.

## Cleanup And Claims

The run root and detached worktree were removed. All four attempt-owned
persistent roots remained absent. The primary checkout's exact committed HEAD,
porcelain bytes, dirty-file set, and recorded file hashes matched the
pre-attempt preservation record, which was then removed.

Phase 758 creates no parser result, fixture result, acquired asset, backend
result, generated source, kernel result, proof, accepted evidence, Level2+,
score axis, semantic correctness, production readiness, SOTA, breakthrough,
full-security claim, external audit, or action authority.

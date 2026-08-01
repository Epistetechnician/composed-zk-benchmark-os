# Phase 765 HSAI Formal Execution State Machine Boundary

## Status

Complete as a documentation-first implementation boundary.

State slice: `phase-765-hsai-formal-execution-state-machine-boundary`.

Classification: `CanonicalFormalExecutionStateMachineSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Authorized Phase 766 Surface

Phase 766 may add only:

```text
tools/hsai-formal-preflight/execution_state_machine.py
tools/hsai-formal-preflight/tests/test_execution_state_machine.py
docs/766-phase-hsai-formal-execution-state-machine-implementation.md
```

plus standard mirrors. It must use the Python standard library under the
already pinned host interpreter and may import the committed bounded runner as
a local module. No dependency file, shell wrapper, external source, acquired
asset, generated proof file, or machine-local transcript may be committed.

## Required State Model

The state machine must encode one immutable ordered stage registry covering:

1. primary preservation and detached-root creation;
2. frozen repository and helper identities;
3. helper tests and bounded parser self-test;
4. canonical client metadata and four process fixtures;
5. Rust manifest, isolated installation, and identities;
6. Charon fetch and decomposed source identity;
7. Aeneas and Lean asset acquisition and raw validation;
8. archive extraction and equivalence;
9. Lean acquisition and identities;
10. Cargo/Lake acquisition and permanent network closure;
11. sandbox controls, Charon build/extraction, Aeneas generation, and Lean
    kernel checks;
12. retention, cleanup, and primary-preservation verification.

Each stage has a stable identifier, ordinal, network policy, mutation owner,
and exact predecessor. State transitions are monotonic. A failed stage is
terminal. No later success, negative scan, checkpoint, display, or cleanup may
replace the recorded first failure.

## Command And Preservation Rules

Commands are immutable argv arrays, never shell strings. The state machine
must reject duplicate command ids, shell metacharacter execution, unknown
environment keys, stage skipping, replay after failure, output-path reuse, and
commands whose declared network policy conflicts with their stage.

Primary preservation must support both clean and dirty checkouts. It records
exact HEAD, NUL-delimited porcelain bytes, and SHA-256 for every dirty regular
file without reading unrelated file contents into reports. Verification must
require exact equality after cleanup. A clean-primary assertion is prohibited.

The implementation must expose canonical duplicate-key-safe JSON
serialization and validation for plans, attempt state, command results, and
the terminal first-failure record. Machine paths and transcripts remain
attempt-local.

## Hermetic Test Gate

Tests must cover all stage transitions, clean and dirty primary snapshots,
rename/copy rejection, source-file mutation detection, stage skipping, replay,
failure terminality, duplicate ids, argv preservation, network-policy drift,
output collision, canonical JSON, and cleanup-verification behavior. Tests may
use only temporary repositories and fake producers; they may not use network,
Rustup, Charon, Aeneas, Lean, Cargo, Lake, or sandbox execution.

Phase 766 implements and validates the state machine only. It does not run a
formal backend or authorize a later attempt until its implementation report is
committed and the helper, repository, claim-boundary, formatting, and diff
gates pass.

Phase 765 creates no proof, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full-security claim,
external audit, or action authority.

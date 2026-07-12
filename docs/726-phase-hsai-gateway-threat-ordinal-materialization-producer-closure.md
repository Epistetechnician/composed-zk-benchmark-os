# Phase 726 HSAI Gateway Threat Ordinal Materialization Producer Closure

## Status

Complete as a documentation-first local-materialization correction.

State slice:
`phase-726-hsai-gateway-threat-ordinal-materialization-producer-closure`.

Classification: `ExactAeneasMaterializationProducerSequenceSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 727 uses canonical run root `hsai-phase727-efa3782c`, canonical detached
repository root `hsai-phase727-repo-efa3782c`, and witness
`phase727ExtractedThreatOrdinalWitnesses`.

After archive safety passes, these local producers must run as separate
top-level commands with no shared block:

1. main Aeneas archive extraction into the absent persistent Aeneas root; and
2. Lean-build asset extraction into absent run-local staging.

Each must record numeric status, separate stdout/stderr regular files bounded to
256 KiB, and its exact checkpoint before any dependent assertion or next
producer. Tree equivalence may run only after both checkpoints exist. A shared
shell block, command chain, helper function, or post-hoc status reconstruction
is prohibited.

After commit and detached-worktree gates, Phase 727 may make one attempt. The
fourteen-`rfl` witness, direct `.olean` sequence, independent network records,
exact version, fixture, token, client, identity, component, runner, source,
cache, sandbox, cleanup, evidence, and claim rules remain.

Phase 726 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.

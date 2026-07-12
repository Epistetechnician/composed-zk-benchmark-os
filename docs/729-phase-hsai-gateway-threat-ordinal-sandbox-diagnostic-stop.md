# Phase 729 HSAI Gateway Threat Ordinal Sandbox Diagnostic Stop

## Status

Complete as one cleaned detached-worktree pre-build stop.

State slice:
`phase-729-hsai-gateway-threat-ordinal-sandbox-diagnostic-stop`.

Classification: `SandboxDirectIpDenialDiagnosticUnavailable`.

Diagnostic: `DirectIpProbeStderrEmpty`.

Execution status: `Succeeded` through dependency acquisition and sandbox
preflight setup; `Failed` for exact sandbox attribution; and `NotRun` for
Charon build/extraction, Aeneas extraction, direct Lean checking, and Lake
build. Evidence ceiling: `Level1LocalReplayOrLower`.

## Observation

Phase 729 used a clean detached execution worktree at committed
`dda453c433ad4f3a30c1b808141ce8679f9f90f3`. The canonical client, bounded
runner fixtures, frozen source, exact twelve-file Rust identity transcript,
pinned Charon source, independently downloaded and separately materialized
Aeneas assets, Lean archive, Charon Cargo dependencies, Lake dependencies,
Mathlib cache, nine exact package commits, disk reserve, client hashes, and
pre-closure DNS gate all passed.

The deny-network profile accepted a sandboxed no-op. The hostname probe exited
nonzero with an explicit name-resolution failure. The direct-IP probe also
exited nonzero, but its stderr file was empty rather than containing the exact
required `Operation not permitted` diagnostic. Phase 729 therefore could not
attribute that exit through its inherited diagnostic-text rule and stopped
before Charon build. The empty diagnostic is not treated as sandbox conformance
and is not a backend failure.

## Cleanup and Claims

All attempt-owned roots and persistent tool roots were removed, and the
detached worktree was deregistered. The preserved primary test file retained
SHA-256
`70ace59109856d96122b6ba45ddecbb2ee28a45fc57c722f55611e25a062620a`.
The primary branch advanced independently during the attempt; no primary
worktree content was imported into the detached execution checkout.

Phase 729 creates no backend result, generated Lean source, kernel result,
proof artifact, accepted evidence, Level2+, score axis, semantic correctness,
production readiness, SOTA, breakthrough, or full-security claim.

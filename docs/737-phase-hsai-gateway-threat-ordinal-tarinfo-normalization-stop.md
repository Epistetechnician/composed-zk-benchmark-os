# Phase 737 HSAI Gateway Threat Ordinal TarInfo Normalization Stop

## Status

Complete as one cleaned detached-worktree pre-validation stop.

State slice:
`phase-737-hsai-gateway-threat-ordinal-tarinfo-normalization-stop`.

Classification: `StructuredArchiveValidatorImplementationIncomplete`.

Diagnostic: `TarInfoNormalizationAndAncestorCollisionGap`.

Execution status: `Succeeded` for exact runner fixtures, Rust identity, Charon
source, and both Aeneas asset downloads; `NotRun` for archive validation,
materialization, Lean, Cargo, Lake, sandbox attribution, backend extraction,
and kernel checking. Evidence ceiling: `Level1LocalReplayOrLower`.

## Observation

Phase 737 created a clean detached execution worktree at committed
`fc955f6ab5e56b1edf9cc472b6f0779ba2aaa429`. Frozen repository, canonical
root, disk, client, Python, exact four-fixture, Rust identity, Charon source,
and independent Aeneas asset gates passed.

Before the structured validator ran, an independent implementation audit found
that Python 3.9 `TarInfo` normalizes directory names before `getmembers()`
returns, while `isreg()` accepts contiguous and GNU sparse member types beyond
the Phase 736 allowlist. The temporary validator also rejected exact duplicate
keys but did not reject a regular-file key that is an ancestor of another
member. Those gaps prevent raw archive-name and extraction-tree claims. Phase
737 stopped before validation or extraction.

## Cleanup and Claims

All attempt-owned roots and persistent tool roots were removed, and the
detached worktree was deregistered. Repository state remained clean.

Phase 737 creates no archive-validation result, materialized external tool,
backend result, generated Lean source, kernel result, proof artifact, accepted
evidence, Level2+, score axis, semantic correctness, production readiness,
SOTA, breakthrough, or full-security claim.

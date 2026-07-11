# Phase 710 HSAI Gateway Threat Ordinal UTF-8 Lakefile Closure

## Status

Complete as a documentation-first client-byte correction.

State slice: `phase-710-hsai-gateway-threat-ordinal-utf8-lakefile-closure`.

Classification: `CanonicalUtf8LeanClientSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 711 uses canonical run root `hsai-phase711-efa3782c` and witness
`phase711ExtractedThreatOrdinalWitnesses`.

The canonical lakefile remains exactly the Phase 702 byte sequence and SHA-256
`5767686c91f69d7dbbe76ddc6ff15a0473ae42679652c4032fc1b259d64ee21d`.
Its `run_io` bind line is exactly:

```lean
  match ← IO.getEnv "HSAI_AENEAS_LEAN_ROOT" with
```

The bind token is the three-byte UTF-8 encoding of U+2190. ASCII `<-`, Unicode
normalization, token substitution, or semantic equivalence is rejected. The
lakefile and `lean-toolchain` hashes must pass immediately after materialization
and again before checking; no direct compiler, Cargo, Lake, or backend producer
may run between materialization and the first hash check.

After commit, clean-tree, and disk gates, Phase 711 may make one attempt. The
identity-log allowlist, component equality, run-root order, bounded runner,
source/tool pins, cache closure, sandbox attribution, cleanup, evidence, and
claim rules remain.

Phase 710 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.

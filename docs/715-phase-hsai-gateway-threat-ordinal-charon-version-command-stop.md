# Phase 715 HSAI Gateway Threat Ordinal Charon Version Command Stop

## Status

Complete as one cleaned post-build stop.

State slice:
`phase-715-hsai-gateway-threat-ordinal-charon-version-command-stop`.

Classification: `BuiltCharonIdentityCommandMismatch`.

Diagnostic: `UnsupportedLongVersionFlag`.

Execution status: `Succeeded` for the sandboxed Charon source build and
`NotRun` for Charon extraction, Aeneas extraction, and Lean checking. Evidence
ceiling: `Level1LocalReplayOrLower`.

## Observation

Canonical client hashes, the exact four-fixture sequence, frozen-source gates,
Rust identity, Charon/Aeneas/Lean acquisition and identity, direct compiler
probe, exact-token locked Charon fetch, nine-package Lake closure, Mathlib cache
acquisition, pre-closure DNS, and attributed sandbox controls passed.

The first bounded offline sandboxed Charon source build then exited zero in
35.820767 seconds. It retained 335,156 stderr bytes and zero stdout bytes,
stayed below the 1 MiB per-stream caps, used the direct pinned rustc path for
`rustc_trait_elaboration`, and produced adjacent native arm64 `charon` and
`charon-driver` binaries from the clean pinned source and lockfile.

The bounded post-build identity command `charon --version` returned exit 2 with
`unexpected argument '--version'`. Phase 715 stopped without trying another
flag or beginning extraction.

## Cleanup and Claims

All attempt-owned roots were removed. No LLBC or generated Lean source was
created. Protected Cargo and repository state were preserved.

The successful build establishes only a reproducible local tool-build result.
It does not establish Charon correctness, source correspondence, a kernel
result, proof artifact, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, or full security.

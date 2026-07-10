# Phase 687 HSAI Gateway Threat Ordinal Unlocalized Acquisition Stop

## Status

Complete as one cleaned-up pre-Lean-toolchain-acquisition stop.

State slice:
`phase-687-hsai-gateway-threat-ordinal-unlocalized-acquisition-stop`.

Classification: `AcquisitionStageFailureUnlocalized`.

Diagnostic: `MissingCommandCheckpoint`.

Execution status: `NotRun` for Cargo fetch/build, Charon build/extraction,
Aeneas extraction, Lean, and Lake. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Observation

The frozen repository, disk, canonical-root, absolute-scanner, exact isolated
Rust, exact Charon-source, and exact Aeneas-asset gates passed. Rust retained
seven byte-stable components and its identity transcript contained no
forbidden transfer marker.

The combined Aeneas acquisition command returned nonzero before writing its
completion marker. Read-only inspection showed all 2,125 Lean-build archive
entries materialized, including the final listed entry; the expected build
sentinels existed; and the Aeneas, libgmp, Aeneas Lake manifest, and Aeneas
lakefile hashes matched their pins. The architecture producer had not created
its output record.

This localizes the failure to after Lean-build materialization began and before
the architecture producer ran, but not to one exact command. The combined
command retained no per-command status or bounded stderr. Phase 687 therefore
does not guess whether archive extraction or a subsequent assertion returned
nonzero.

## Cleanup and Claims

The attempt removed its 188 MiB run root, 1.6 GiB isolated Rust root, and
425 MiB Aeneas root. Isolated Charon Cargo and Lean 4.31 roots were absent.
Lean 4.30, `$HOME/.cargo`, repository target, and repository files were
preserved.

No Cargo fetch/build, backend extraction, generated source, kernel check,
proof, accepted evidence, Level2+, score axis, source correspondence, semantic
correctness, production readiness, SOTA, breakthrough, or full-security claim
occurred.

## Next Gate

Phase 688 must bind one-command checkpoints, explicit status capture, and
bounded stderr for acquisition commands before another attempt.


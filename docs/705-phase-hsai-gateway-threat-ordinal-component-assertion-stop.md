# Phase 705 HSAI Gateway Threat Ordinal Component Assertion Stop

## Status

Complete as one cleaned pre-Charon stop.

State slice: `phase-705-hsai-gateway-threat-ordinal-component-assertion-stop`.

Classification: `RustInstalledComponentAssertionMismatch`.

Diagnostic: `FilteredComponentListSuffixAssumption`.

Execution status: `NotRun` for Charon source acquisition, Cargo fetch/build,
Lake update/cache, sandbox controls, backend extraction, and Lean checking.
Evidence ceiling: `Level1LocalReplayOrLower`.

## Observation

The mode-700 canonical run root was created before its children. The pinned
Python runner passed all four required fixtures: normal exit, child-plus-
grandchild timeout termination, stdout flood, and stderr flood. Both flood
fixtures retained exactly 1,024 bytes on the limited stream.

The clean-tree, frozen source, manifest, lockfile, unique selector, exact method
slice, and disk gates passed. The pinned Rust channel manifest matched SHA-256
`aaf1cb59b5996dd51831c9114b6e3a4a176e197851de91194b473117e142b935`,
and isolated nightly `2026-06-01` installation completed successfully.

The exact `rustup component list --toolchain nightly-2026-06-01 --installed`
producer then emitted seven bare component names. The assertion incorrectly
required the suffix `(installed)`, which rustup emits in an unfiltered listing
but omits with `--installed`. It therefore stopped before the identity
checkpoint even though the captured list contained the required components.
No command was corrected or replayed inside Phase 705.

## Cleanup and Claims

The attempt removed its canonical run root and isolated Rust root. The Charon
Cargo home, Aeneas root, and Lean root were never created. Protected Cargo and
repository state were preserved.

Phase 705 creates no Charon binary, LLBC, generated Lean source, kernel result,
proof artifact, accepted evidence, Level2+, score axis, semantic correctness,
production readiness, SOTA, breakthrough, or full-security claim.

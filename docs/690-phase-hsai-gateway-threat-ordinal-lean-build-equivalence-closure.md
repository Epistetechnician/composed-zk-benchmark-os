# Phase 690 HSAI Gateway Threat Ordinal Lean-Build Equivalence Closure

## Status

Complete as a documentation-first archive-correspondence correction.

State slice:
`phase-690-hsai-gateway-threat-ordinal-lean-build-equivalence-closure`.

Classification: `AeneasLeanBuildEquivalenceSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Corrections

Phase 691 inherits Phases 678, 680, 682, 686, and 688 except:

```bash
TEMP_BASE="$(cd "${TMPDIR:-/tmp}" && pwd -P)"
RUN="$TEMP_BASE/hsai-phase691-efa3782c"
AENEAS_LEAN_STAGING="$RUN/aeneas-lean-build-asset"
```

The main archive must materialize the embedded build at
`$AENEAS_ROOT/backends/lean/.lake/build`. The separate Lean-build archive must
extract once into absent `AENEAS_LEAN_STAGING`, using Phase 688 status, stream
bound, and checkpoint rules. It must never overlay the embedded build.

For both roots, create a byte-sorted inventory containing each relative regular
file path, one NUL byte, and its SHA-256. Require exactly 2,021 regular files,
104 directories, zero symlinks, equal relative path sets, equal per-file
digests, and equal final inventory digests. Directory permissions and mtimes
are not evidence and are excluded. Any difference stops as
`AeneasLeanBuildAssetMismatch`.

Only after equivalence passes may the staged duplicate be deleted within the
owned run root. The embedded build remains the sole Aeneas support build used
later. Architecture and identity checks then proceed under Phase 686.

The Phase 691 witness is exactly
`phase691ExtractedThreatOrdinalWitnesses`.

## Authorization and Claims

After commit, clean-tree, and disk gates, Phase 691 may make one attempt. The
first failure stops it without same-phase repair. All source pins, command
checkpoints, acquisition order, sandbox, freeze, retention, cleanup,
evidence-ceiling, and nonclaim rules remain.

Phase 690 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, source correspondence, semantic correctness, production
readiness, SOTA, breakthrough, full security, external audit, or action
authority.


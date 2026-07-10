# Phase 684 HSAI Gateway Threat Ordinal Aeneas Materialization Closure

## Status

Complete as a documentation-first Aeneas acquisition correction.

State slice:
`phase-684-hsai-gateway-threat-ordinal-aeneas-materialization-closure`.

Execution status: `NotRun`.

Classification: `AeneasMaterializationSpecified`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Corrections

Phase 685 inherits the Phase 678 ordered protocol and the Phase 680 and 682
corrections except for the exact replacements below.

The canonical attempt root is:

```bash
TEMP_BASE="$(cd "${TMPDIR:-/tmp}" && pwd -P)"
RUN="$TEMP_BASE/hsai-phase685-efa3782c"
```

Every Phase 678 child of `RUN` is derived from this value. The persistent
attempt-owned roots remain unchanged and must all be absent before acquisition.

After asset byte-count, SHA-256, entry-count, absolute-path, and `..` path
checks pass, materialize Aeneas exactly as follows:

```bash
mkdir -m 700 "$AENEAS_ROOT"
tar -xzf "$AENEAS_ARCHIVE" -C "$AENEAS_ROOT"
test ! -e "$AENEAS_ROOT/backends/lean/.lake/build"
mkdir -p "$AENEAS_ROOT/backends/lean/.lake/build"
tar -xzf "$AENEAS_LEAN_ARCHIVE" \
  -C "$AENEAS_ROOT/backends/lean/.lake/build"
```

The main binary identity command is exactly:

```bash
"$AENEAS_ROOT/aeneas" -version
```

It must exit zero and print exactly
`aeneas nightly-2026.07.10-c2015b8`. `--version` is prohibited. Before later
use, recheck the pinned Aeneas, libgmp, Aeneas lake manifest, and Aeneas
lakefile hashes; native arm64 architecture; packaged Charon nonexecution; and
the materialized Lean build tree.

The exhaustive witness is renamed
`phase685ExtractedThreatOrdinalWitnesses`. This token replaces the Phase 683
token from Phase 682 for the Phase 685 attempt only.

## Phase 685 Authorization

After this boundary is committed, the repository is clean, and the disk gate
passes, Phase 685 may make one attempt under Phase 678, Phase 680, Phase 682,
and these corrections. The first named failure terminates it; no same-phase
repair or replay is allowed.

## Cleanup and Claims

All acquisition order, direct compiler, source/lock pin, cache, sandbox,
freeze, retention, cleanup, evidence-ceiling, and nonclaim rules remain in
force.

Phase 684 runs no tool and creates no backend result, proof, accepted evidence,
Level2+, score axis, source correspondence, semantic correctness, production
readiness, SOTA, breakthrough, full security, independent reproduction,
external audit, or action authority.


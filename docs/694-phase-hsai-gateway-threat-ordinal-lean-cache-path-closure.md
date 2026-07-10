# Phase 694 HSAI Gateway Threat Ordinal Lean Cache Path Closure

## Status

Complete as a documentation-first acquisition-environment correction.

State slice: `phase-694-hsai-gateway-threat-ordinal-lean-cache-path-closure`.

Classification: `LeanCachePathBindingSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 695 inherits the prior ordered protocol except:

```bash
TEMP_BASE="$(cd "${TMPDIR:-/tmp}" && pwd -P)"
RUN="$TEMP_BASE/hsai-phase695-efa3782c"
LEAN_PATH_ENV="$LEAN_ROOT/bin:/usr/bin:/bin:/usr/sbin:/sbin"
```

Both Stage 4 Lake producers must set `PATH=$LEAN_PATH_ENV`. Before cache
acquisition, separately require:

```bash
PATH="$LEAN_PATH_ENV" lean --print-prefix
test -x "$LEAN_ROOT/bin/leantar"
/usr/bin/file "$LEAN_ROOT/bin/leantar"
```

The prefix must equal `$LEAN_ROOT`, and `leantar` must be native arm64. Bare
host `lean`, PATH fallback, copying a foreign `leantar`, or patching the
verified sysroot is prohibited. The Phase 695 witness is exactly
`phase695ExtractedThreatOrdinalWitnesses`.

After commit, clean-tree, and disk gates, Phase 695 may make one attempt. All
pins, checkpoints, equivalence, sandbox, freeze, cleanup, evidence, and claim
rules remain.

Phase 694 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.


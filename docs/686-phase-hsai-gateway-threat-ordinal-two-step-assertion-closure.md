# Phase 686 HSAI Gateway Threat Ordinal Two-Step Assertion Closure

## Status

Complete as a documentation-first assertion-semantics correction.

State slice:
`phase-686-hsai-gateway-threat-ordinal-two-step-assertion-closure`.

Classification: `TwoStepAssertionSemanticsSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Corrections

Phase 687 inherits Phases 678, 680, 682, and 684 except:

```bash
TEMP_BASE="$(cd "${TMPDIR:-/tmp}" && pwd -P)"
RUN="$TEMP_BASE/hsai-phase687-efa3782c"
```

Every assertion over command output must first run its producer to completion
and require producer status zero, then scan the captured regular file in a
separate command. `producer | grep -q`, `producer | rg -q`, and any equivalent
early-exit pipeline are prohibited under `pipefail`.

The Aeneas architecture and identity checks are exactly:

```bash
/usr/bin/file "$AENEAS_ROOT/aeneas" > "$RUN/aeneas-file.txt"
"$RG_BIN" -Fq 'Mach-O 64-bit executable arm64' "$RUN/aeneas-file.txt"
"$AENEAS_ROOT/aeneas" -version > "$RUN/aeneas-version.txt" 2>&1
test "$(cat "$RUN/aeneas-version.txt")" = \
  'aeneas nightly-2026.07.10-c2015b8'
```

This two-step rule applies to later build-log, LLBC, generated-source, sandbox,
and kernel-transcript assertions. The Phase 687 witness is exactly
`phase687ExtractedThreatOrdinalWitnesses`.

## Authorization and Claims

After commit, clean-tree, and disk gates, Phase 687 may make one attempt. The
first failure stops it without same-phase repair. All acquisition, sandbox,
freeze, retention, cleanup, evidence-ceiling, and nonclaim rules remain.

Phase 686 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, source correspondence, semantic correctness, production
readiness, SOTA, breakthrough, full security, external audit, or action
authority.


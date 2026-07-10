# Phase 688 HSAI Gateway Threat Ordinal Acquisition Checkpoint Closure

## Status

Complete as a documentation-first diagnostic-boundary correction.

State slice:
`phase-688-hsai-gateway-threat-ordinal-acquisition-checkpoint-closure`.

Classification: `AcquisitionCheckpointProtocolSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Corrections

Phase 689 inherits Phases 678, 680, 682, 684, and 686 except:

```bash
TEMP_BASE="$(cd "${TMPDIR:-/tmp}" && pwd -P)"
RUN="$TEMP_BASE/hsai-phase689-efa3782c"
```

Every acquisition producer after asset verification must run as its own shell
command with stdout, stderr, and numeric status captured before the next
producer. Each stream is bounded to 256 KiB. The attempt stops if a producer
returns nonzero or exceeds a bound. A successful producer appends one exact
label to `$RUN/acquisition-checkpoints.txt`; assertions run only after their
producer's checkpoint exists.

The Lean-build extraction checkpoint is:

```bash
set +e
tar -xzf "$AENEAS_LEAN_ARCHIVE" \
  -C "$AENEAS_ROOT/backends/lean/.lake/build" \
  > "$RUN/aeneas-lean-extract.stdout" \
  2> "$RUN/aeneas-lean-extract.stderr"
STATUS=$?
set -e
printf '%s\n' "$STATUS" > "$RUN/aeneas-lean-extract.status"
test "$STATUS" -eq 0
test "$(wc -c < "$RUN/aeneas-lean-extract.stdout")" -le 262144
test "$(wc -c < "$RUN/aeneas-lean-extract.stderr")" -le 262144
printf '%s\n' aeneas_lean_archive_extracted >> \
  "$RUN/acquisition-checkpoints.txt"
```

Materialized-file SHA-256 checks must record expected and actual values in
separate regular files and append distinct checkpoint labels. Architecture and
identity retain Phase 686 two-step semantics. No unlabeled multi-producer
acquisition block is allowed.

The Phase 689 witness is exactly
`phase689ExtractedThreatOrdinalWitnesses`.

## Authorization and Claims

After commit, clean-tree, and disk gates, Phase 689 may make one attempt. The
first named failure stops it without same-phase repair. All source pins,
acquisition order, sandbox, freeze, retention, cleanup, evidence-ceiling, and
nonclaim rules remain.

Phase 688 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, source correspondence, semantic correctness, production
readiness, SOTA, breakthrough, full security, external audit, or action
authority.


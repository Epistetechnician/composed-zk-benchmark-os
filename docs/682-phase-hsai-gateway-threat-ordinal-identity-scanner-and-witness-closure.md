# Phase 682 HSAI Gateway Threat Ordinal Identity Scanner and Witness Closure

## Status

Complete as a documentation-first pre-execution assertion correction.

State slice:
`phase-682-hsai-gateway-threat-ordinal-identity-scanner-and-witness-closure`.

Execution status: `NotRun`.

Classification: `IdentityScannerAndWitnessSpecified`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Corrections

Phase 683 inherits the Phase 678 ordered protocol and the Phase 680 rustup
isolation rules except for the two corrections below.

Before restricting `PATH`, resolve `rg` once from the operator environment,
canonicalize it, require an executable regular file, and record its SHA-256:

```bash
RG_BIN="$(command -v rg)"
test -n "$RG_BIN"
RG_BIN_DIR="$(cd "$(dirname "$RG_BIN")" && pwd -P)"
RG_BIN="$RG_BIN_DIR/$(basename "$RG_BIN")"
test -f "$RG_BIN"
test -x "$RG_BIN"
shasum -a 256 "$RG_BIN" > "$RUN/rg.sha256"
```

Every later transcript scan must call `"$RG_BIN"` by absolute path. The
forbidden-transfer scan must preserve and classify the scanner exit code:

```bash
set +e
"$RG_BIN" -i -q 'syncing|downloading|installing' "$RUN/rustup-identity.log"
SCAN_STATUS=$?
set -e
case "$SCAN_STATUS" in
  0) exit 41 ;; # forbidden transfer marker observed
  1) ;;         # required negative assertion passed
  *) exit 42 ;; # scanner unavailable or failed
esac
```

No `|| true`, pipeline, command substitution, or output redirection may mask a
required assertion's status. Status 0 stops as `UnexpectedRustupAutoInstall`;
status greater than 1 stops as `RequiredLogScannerUnavailable`.

The exhaustive generated witness name is
`phase683ExtractedThreatOrdinalWitnesses`. This token supersedes the stale
Phase 679 token in Phase 678 for the Phase 683 attempt only. The witness must
still cover every `GatewayThreatClass` constructor and prove each extracted
ordinal equality by kernel checking; naming alone is not evidence.

## Phase 683 Authorization

After this boundary is committed, the repository is clean, and the disk gate
passes, Phase 683 may make one attempt under Phase 678, Phase 680, and these
corrections. The first named failure terminates it; no same-phase repair or
replay is allowed.

## Cleanup and Claims

Attempt ownership, acquisition order, direct compiler rules, exact source and
lock pins, cache closure, permanent network sandbox, process bounds, state
freezes, success retention, failure cleanup, evidence ceiling, and all
nonclaims remain as specified by Phase 678 and Phase 680.

Phase 682 runs no tool and creates no backend result, proof, accepted evidence,
Level2+, score axis, source correspondence, semantic correctness, production
readiness, SOTA, breakthrough, full security, independent reproduction,
external audit, or action authority.


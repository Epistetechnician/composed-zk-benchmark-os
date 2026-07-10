# Phase 676 HSAI Gateway Threat Ordinal Canonical Run-Root Closure

## Status

Complete as a documentation-first host-path correction.

State slice:
`phase-676-hsai-gateway-threat-ordinal-canonical-run-root-closure`.

Execution status: `NotRun`.

Classification: `CanonicalRunRootSpecified`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Purpose

Phase 675 proved that macOS resolves `/tmp` to `/private/tmp`. Phase 676 makes
the future run root canonical before any child path exists. It runs no tool,
acquires no dependency, and creates no formal artifact or evidence.

## Exact Root Construction

Phase 677 must construct paths only in this order:

```bash
TEMP_BASE="$(cd "${TMPDIR:-/tmp}" && pwd -P)"
RUN="$TEMP_BASE/hsai-phase677-efa3782c"
CHARON_SOURCE="$RUN/charon-source"
CHARON_PACKAGE="$CHARON_SOURCE/charon"
CHARON_MANIFEST="$CHARON_PACKAGE/Cargo.toml"
CHARON_LOCK="$CHARON_PACKAGE/Cargo.lock"
CHARON_TARGET="$RUN/charon-target"
CLIENT_ROOT="$RUN/client"
```

The run must reject an existing `RUN`. After creating it, these assertions
must pass:

```bash
test "$(cd "$RUN" && pwd -P)" = "$RUN"
test "$(dirname "$CHARON_SOURCE")" = "$RUN"
test "$(dirname "$CHARON_TARGET")" = "$RUN"
test "$(dirname "$CLIENT_ROOT")" = "$RUN"
```

After source checkout, `$(cd "$CHARON_PACKAGE" && pwd -P)` must equal the
already canonical `CHARON_PACKAGE`. No literal `/tmp`, relative path, symlinked
package root, path recomputation, or later canonicalization is permitted.

All Phase 674 absolute-manifest, exact-lock, empty-Cargo-home, direct compiler,
and pre/post negative-control requirements remain mandatory. All Phase 672
Lake/cache acquisition, state freeze, macOS sandbox denial, direct checking,
cleanup, mutation, and nonpromotion requirements also remain mandatory.

## Phase 677 Authorization

After Phase 676 is committed and at least 20 GiB remains available, Phase 677
may make one fail-closed attempt. The first named failure terminates it; there
is no same-phase corrected command or path.

Success may retain only the generated ordinal target, separate fourteen-case
witness, minimal Lean client metadata, provenance/readme, Phase 677 run note,
and standard status mirrors. It may not commit machine-local paths, manifests,
dependencies, caches, binaries, LLBC, or raw logs.

## Repository Validation

The documentation-only boundary passed repository hygiene 1/1,
documentation claim-boundary coverage 1/1, source claim-boundary coverage 6/6,
Rust formatting, and diff hygiene. Root `pnpm run lint` was inapplicable
because there is no root `package.json`.

## Claim Boundary

Phase 676 creates no backend result, proof, accepted evidence, Level2+, score
axis, source correspondence, semantic correctness, production readiness,
SOTA, breakthrough, full security, independent reproduction, external audit,
or action authority.

## Defensible Claim

```text
HSAI has made the future Aeneas run tree canonical before deriving any child
path; no tool or checker ran in Phase 676.
```

Phase 677 stopped before Cargo as `ExecutionProtocolAmbiguousPreBuild`,
recorded in
`docs/677-phase-hsai-gateway-threat-ordinal-execution-protocol-ambiguity.md`.

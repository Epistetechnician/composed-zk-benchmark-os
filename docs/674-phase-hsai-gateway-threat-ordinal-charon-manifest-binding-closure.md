# Phase 674 HSAI Gateway Threat Ordinal Charon Manifest-Binding Closure

## Status

Complete as a documentation-first command-binding correction.

State slice:
`phase-674-hsai-gateway-threat-ordinal-charon-manifest-binding-closure`.

Execution status: `NotRun`.

Classification: `CharonCargoManifestBindingSpecified`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Purpose

Phase 673 stopped before build because a Cargo fetch inherited the HSAI
workspace current directory. Phase 674 removes current-directory ambiguity
before one future Phase 675 attempt. It runs no acquisition, build, extractor,
Lean, Lake, SMT, Z3, or COBALT command.

## Exact Binding

Phase 675 must define canonical paths before any Cargo operation:

```text
CHARON_SOURCE=$RUN/charon-source
CHARON_PACKAGE=$CHARON_SOURCE/charon
CHARON_MANIFEST=$CHARON_PACKAGE/Cargo.toml
CHARON_LOCK=$CHARON_PACKAGE/Cargo.lock
```

It must then pass all of these assertions:

```bash
test "$(git -C "$CHARON_SOURCE" rev-parse HEAD)" = \
  909ff09ad0f144f83d354f2c3d26f631fb9f8e9a
test "$(cd "$CHARON_PACKAGE" && pwd -P)" = "$CHARON_PACKAGE"
test "$(shasum -a 256 "$CHARON_MANIFEST" | awk '{print $1}')" = \
  a596f9b50a62e142199bca400de2318a0426b914039882896a270a35cd7481b2
test "$(shasum -a 256 "$CHARON_LOCK" | awk '{print $1}')" = \
  4e361622e601cfe93fce40e5a13bf6b5a89a84394875b409f8c8f27ec86272db
```

The isolated Charon `CARGO_HOME` must not exist before acquisition. Creating
it early, reusing it, or finding any registry/git/config content stops as
`CharonCargoHomeNotEmpty`.

## Exact Cargo Commands

The acquisition command is location-independent and must include the absolute
manifest path:

```bash
"$CARGO" fetch \
  --locked \
  --manifest-path "$CHARON_MANIFEST"
```

After network is disabled, the first and only build command is:

```bash
"$CARGO" build \
  --locked \
  --offline \
  --release \
  --manifest-path "$CHARON_MANIFEST" \
  --bin charon \
  --bin charon-driver
```

Both commands must run with `workdir=$CHARON_PACKAGE` even though the absolute
manifest makes dependency selection independent of inherited shell state.
Immediately before and after each command, the run record must capture the
canonical current directory, manifest path, manifest digest, lock path, lock
digest, isolated Cargo-home path, and HSAI workspace lock digest as a negative
control. Any mismatch terminates the attempt before the next command.

The direct compiler environment, `rustc_private` probe, output/time bounds,
source/hash checks, built-binary audits, Charon/Aeneas extraction rules,
explicit Lake/Mathlib acquisition, client freeze, sandboxed checking, cleanup,
mutation surface, and claim ceiling remain exactly as specified by Phases 668,
670, and 672.

## Phase 675 Authorization

After this boundary is committed and the disk gate passes, Phase 675 may make
one attempt. The first named failure terminates it. There is no corrected
same-phase command, dependency-home reuse, backend switch, source edit,
generated-source edit, selector widening, or network-policy weakening.

On success, Phase 675 may retain only the generated target, separate exhaustive
witness, minimal Lean client metadata, provenance record, execution note, and
standard status mirrors authorized by Phase 672. Machine-local manifests,
package/cache trees, binaries, LLBC, and raw logs remain uncommitted.

## Repository Validation

The documentation-only boundary passed repository hygiene 1/1,
documentation claim-boundary coverage 1/1, source claim-boundary coverage 6/6,
Rust formatting, and diff hygiene. Root `pnpm run lint` was inapplicable
because there is no root `package.json`.

## Claim Boundary

Phase 674 creates no backend result, proof artifact, accepted evidence,
Level2+, score axis, source correspondence, semantic correctness, production
readiness, SOTA, breakthrough, full security, independent reproduction,
external audit, or action authority.

## Defensible Claim

```text
HSAI has made future Charon Cargo acquisition and build selection explicit by
canonical directory, absolute manifest, exact lock digest, and empty isolated
Cargo home; no tool ran in Phase 674.
```

Phase 675 stopped before Cargo as `CharonPackageCanonicalPathMismatch`,
recorded in
`docs/675-phase-hsai-gateway-threat-ordinal-charon-canonical-path-mismatch.md`.

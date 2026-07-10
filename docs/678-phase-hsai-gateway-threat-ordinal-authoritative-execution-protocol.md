# Phase 678 HSAI Gateway Threat Ordinal Authoritative Execution Protocol

## Status

Complete as a documentation-first protocol replacement.

State slice:
`phase-678-hsai-gateway-threat-ordinal-authoritative-execution-protocol`.

Execution status: `NotRun`.

Classification: `AuthoritativeAeneasExecutionProtocolSpecified`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Purpose

Phase 677 stopped because the accumulated Phase 668-676 command fragments did
not define one unambiguous attempt. This document supersedes conflicting
execution details for one future Phase 679 run. Source, asset, digest, selector,
process-bound, generated-source, evidence, and claim ceilings from the earlier
phases remain in force unless this document explicitly replaces an execution
detail.

Phase 678 runs no acquisition, build, backend, extractor, cache, Lean, Lake,
SMT, Z3, or COBALT command.

## Canonical Paths and Ownership

Phase 679 must canonicalize the temporary base before deriving any child path:

```bash
TEMP_BASE="$(cd "${TMPDIR:-/tmp}" && pwd -P)"
RUN="$TEMP_BASE/hsai-phase679-efa3782c"
CHARON_SOURCE="$RUN/charon-source"
CHARON_PACKAGE="$CHARON_SOURCE/charon"
CHARON_MANIFEST="$CHARON_PACKAGE/Cargo.toml"
CHARON_LOCK="$CHARON_PACKAGE/Cargo.lock"
CHARON_TARGET="$RUN/charon-target"
CLIENT_ROOT="$RUN/client"
MATHLIB_CACHE_DIR="$RUN/mathlib-cache"
```

Persistent user-local roots are:

```text
RUSTUP_ROOT=$HOME/.local/share/hsai-formal/rustup-aeneas-c2015b8
CHARON_CARGO_HOME=$HOME/.local/share/hsai-formal/cargo-charon-909ff09a
AENEAS_ROOT=$HOME/.local/share/hsai-formal/aeneas-c2015b8
LEAN_ROOT=$HOME/.local/share/hsai-formal/lean-4.31.0
CHECKER_CARGO_HOME=$HOME/.cargo
```

Before acquisition, `RUN`, `RUSTUP_ROOT`, `CHARON_CARGO_HOME`, `AENEAS_ROOT`,
and `LEAN_ROOT` must all be absent. Their absence establishes Phase 679
ownership. `CHECKER_CARGO_HOME` must already exist and is never owned, removed,
or modified intentionally by cleanup. The pre-existing Lean 4.30.0 root is
outside the attempt.

## Authoritative Order

Phase 679 must execute exactly these stages. It may not reorder them.

### 1. Frozen Repository and Disk Gates

Recheck the clean worktree, all checker/workspace/lock/method hashes, unique
`ordinal` inventory, canonical run-root assertions, at least 20 GiB free, and
continuing 5 GiB reserve.

### 2. Network-Enabled Tool and Source Acquisition

Acquire and verify:

- Rust nightly `2026-06-01` with all required components under `RUSTUP_ROOT`;
- Charon commit `909ff09ad0f144f83d354f2c3d26f631fb9f8e9a` under
  `CHARON_SOURCE`, with all five source hashes and clean detached status;
- the exact two Aeneas assets under `AENEAS_ROOT`, retaining the packaged
  Charon files only as audited unused release content;
- Lean 4.31.0 under `LEAN_ROOT`; and
- archive safety, architecture, versions, signatures, links, and disk reserve.

The authoritative Charon executables for every later operation are only:

```text
CHARON_BIN=$CHARON_TARGET/release/charon
CHARON_DRIVER=$CHARON_TARGET/release/charon-driver
```

`$AENEAS_ROOT/charon` and `$AENEAS_ROOT/charon-driver` must never execute.

### 3. Network-Enabled Charon Dependency Acquisition

Bind direct compiler paths:

```text
TOOLCHAIN=$RUSTUP_ROOT/toolchains/nightly-2026-06-01-aarch64-apple-darwin
CARGO=$TOOLCHAIN/bin/cargo
RUSTC=$TOOLCHAIN/bin/rustc
RUSTDOC=$TOOLCHAIN/bin/rustdoc
RUSTUP_BIN=$(command -v rustup)
RUSTUP_BIN_DIR=$(dirname "$RUSTUP_BIN")
PATH=$RUSTUP_BIN_DIR:$TOOLCHAIN/bin:/usr/bin:/bin:/usr/sbin:/sbin
RUSTUP_HOME=$RUSTUP_ROOT
CARGO_HOME=$CHARON_CARGO_HOME
CARGO_TARGET_DIR=$CHARON_TARGET
```

Compile the direct `rustc_private` probe with `$RUSTC`. Confirm
`$RUSTUP_BIN` is the pre-existing rustup executable, `rustup --version`
succeeds under the restricted `PATH`, and `CHARON_TOOLCHAIN_IS_IN_PATH` is
unset. Every Charon build/extraction process must retain this `PATH` and
`RUSTUP_HOME`, allowing Charon's internal `rustup run` to load the exact
isolated driver library.

Confirm
`CHARON_CARGO_HOME` is still absent, then run from `CHARON_PACKAGE`:

```bash
CARGO_HOME="$CHARON_CARGO_HOME" \
CARGO_TARGET_DIR="$CHARON_TARGET" \
"$CARGO" fetch \
  --locked \
  --manifest-path "$CHARON_MANIFEST"
```

Capture canonical cwd, manifest/lock paths and hashes, HSAI lock negative
control, and Cargo-home path before and after.

### 4. Network-Enabled Lean Dependency Acquisition

After Aeneas extraction inputs and Lean exist but before any backend executes,
materialize the temporary client `lakefile.lean` and `lean-toolchain`. The
client requires Aeneas through `HSAI_AENEAS_LEAN_ROOT=$AENEAS_ROOT/backends/lean`.
The only Lean executables are:

```text
LAKE=$LEAN_ROOT/bin/lake
LEAN=$LEAN_ROOT/bin/lean
```

The exact client `lean-toolchain` content is
`leanprover/lean4:v4.31.0`. The exact `lakefile.lean` shape is:

```lean
import Lake
open Lake DSL

private def aeneasRoot : String := run_io do
  match ← IO.getEnv "HSAI_AENEAS_LEAN_ROOT" with
  | some root => return root
  | none => error "HSAI_AENEAS_LEAN_ROOT is required"

package hsaiGatewayThreatOrdinalAeneas
require aeneas from aeneasRoot

@[default_target]
lean_lib HsaiGatewayThreatOrdinalAeneas where
  roots := #[
    `HsaiGatewayThreatOrdinalAeneas.Extracted.Types,
    `HsaiGatewayThreatOrdinalAeneas.Extracted.Funs,
    `HsaiGatewayThreatOrdinalAeneas.Witnesses,
  ]
```

No other package dependency, post-update hook, executable, or client option is
allowed.

The authoritative dependency roots are client-owned:

```text
$CLIENT_ROOT/.lake/packages/{mathlib,plausible,LeanSearchClient,importGraph,
proofwidgets,aesop,Qq,batteries,Cli}
```

Phase 679 must not manually populate or treat
`$AENEAS_ROOT/backends/lean/.lake/packages` as authoritative. The client runs,
with network enabled:

```bash
cd "$CLIENT_ROOT"
HSAI_AENEAS_LEAN_ROOT="$AENEAS_ROOT/backends/lean" \
MATHLIB_NO_CACHE_ON_UPDATE=1 \
"$LAKE" update
HSAI_AENEAS_LEAN_ROOT="$AENEAS_ROOT/backends/lean" \
MATHLIB_NO_CACHE_ON_UPDATE=1 \
MATHLIB_CACHE_DIR="$MATHLIB_CACHE_DIR" \
"$LAKE" exe cache get
```

The first command may create the machine-local client manifest and exactly nine
pinned package checkouts. The second is the only cache-network command. Verify
all package commits and clean source state, then freeze the manifest digest,
package inventory, cache-object inventory, and decompressed package build-tree
digest.

At the end of Stage 4, all network acquisition is permanently closed for the
attempt.

### 5. Sandbox Controls and Permanent Network Closure

Before any build or backend command, run under the macOS `(deny network*)`
profile:

1. `/usr/bin/true` positive process control;
2. DNS negative control; and
3. direct TCP `1.1.1.1:443` negative control requiring `Operation not permitted`.

If the sandbox executable is absent or either network control does not fail for
the sandbox-attributable reason, stop as `NetworkDenialUnavailable`. After
these controls, every remaining build, extraction, and checking command runs
under the same profile with proxies removed.

### 6. Sandboxed Charon Source Build

Under the macOS `(deny network*)` profile, with proxies removed,
`CARGO_NET_OFFLINE=true`, `CARGO_HOME=$CHARON_CARGO_HOME`,
`CARGO_TARGET_DIR=$CHARON_TARGET`, direct compiler paths, and
`workdir=$CHARON_PACKAGE`, run once:

```bash
CARGO_HOME="$CHARON_CARGO_HOME" \
CARGO_TARGET_DIR="$CHARON_TARGET" \
"$CARGO" build \
  --verbose \
  --locked \
  --offline \
  --release \
  --manifest-path "$CHARON_MANIFEST" \
  --bin charon \
  --bin charon-driver
```

`--verbose` is explicitly authorized to expose child compiler command paths.
The bounded build log must contain the direct `$RUSTC` path for
`rustc_trait_elaboration`. The 1 MiB stdout/stderr bounds remain mandatory;
exceeding them stops as `BoundedExecutionUnavailable`.

Audit native arm64 binaries, Charon `0.1.220`, adjacency, hashes, source/lock
stability, absolute dependencies, and rustup-mediated driver loading against
the exact `librustc_driver`.

### 7. Sandboxed Charon Extraction

Switch only the Cargo home and target for checker compilation:

```text
CARGO_HOME=$CHECKER_CARGO_HOME
CARGO_TARGET_DIR=$RUN/checker-cargo-target
CARGO_NET_OFFLINE=true
```

`CHECKER_CARGO_HOME` supplies the pre-existing offline registry cache;
`CARGO_TARGET_DIR` contains all new checker build output. Before extraction,
compute one deterministic immutable-cache digest over every regular file below
`CHECKER_CARGO_HOME` except files below the relative mutable metadata roots
`registry/index`, `.package-cache`, and `.global-cache`. Represent each included
file by its path relative to `CHECKER_CARGO_HOME`, one NUL byte, and its
SHA-256; sort records bytewise by relative path with `LC_ALL=C`; hash the
concatenated records.

The three excluded metadata roots may change while Cargo is locked and offline.
After extraction, recompute and require the complete immutable digest to match.
Any included regular-file addition, deletion, or byte change stops as
`CheckerCargoCacheContentDrift`. Cleanup never removes or rewrites this
pre-existing Cargo home.

Under the same deny-network sandbox, run `CHARON_BIN cargo` once with
`--preset=aeneas`, `--start-from='crate::_::ordinal'`, exact LLBC destination,
warnings as errors, and the locked/offline checker Cargo arguments from Phase
668. Then run `CHARON_BIN pretty-print` once and require exactly one local
`ordinal` function body.

### 8. Sandboxed Aeneas Extraction

Under the same deny-network profile, run `$AENEAS_ROOT/aeneas` once with the
Phase 668 Lean/split/checks/abort/warnings/namespace arguments, replacing the
older destination with `-dest "$CLIENT_ROOT"` and explicitly retaining
`-subdir HsaiGatewayThreatOrdinalAeneas/Extracted`, so generated modules land
directly under the exact client tree.
Generated output must contain only `Types.lean` and `Funs.lean`, pass the
hole/template/body scans, and expose the authoritative generated API.

The separate theorem name is exactly:

```text
phase679ExtractedThreatOrdinalWitnesses
```

It must check all fourteen constructors against ordinals 0 through 13 and live
outside generated source at
`$CLIENT_ROOT/HsaiGatewayThreatOrdinalAeneas/Witnesses.lean`. Materialize that
file only after generated-source review and before the Stage 9 freeze. Its
single public theorem must be a kernel-checkable conjunction of the fourteen
generated `ordinal = .ok n#u8` equalities and may use `decide +kernel`; it may
not use `native_decide`, `sorry`, `admit`, or an axiom.

### 9. Precheck Freeze

Freeze client metadata, generated tree, Aeneas source/support tree, all nine
client package HEADs/source states, cache inventory, and build-tree digest.
Confirm no Lake/cache process or lock remains. Reconfirm that the Stage 5
sandbox controls passed and no later network-enabled process ran.

### 10. Sandboxed Lean Checks

With `workdir=$CLIENT_ROOT`, `PATH=$LEAN_ROOT/bin:/usr/bin:/bin:/usr/sbin:/sbin`,
`HSAI_AENEAS_LEAN_ROOT=$AENEAS_ROOT/backends/lean`,
`MATHLIB_NO_CACHE_ON_UPDATE=1`, proxies removed, and the frozen client manifest
already present, run these exact commands under the deny-network profile in
order:

```bash
"$LAKE" env "$LEAN" HsaiGatewayThreatOrdinalAeneas/Extracted/Types.lean
"$LAKE" env "$LEAN" HsaiGatewayThreatOrdinalAeneas/Extracted/Funs.lean
"$LAKE" env "$LEAN" HsaiGatewayThreatOrdinalAeneas/Witnesses.lean
"$LAKE" build
```

Use the Phase 668 bounds: 120 seconds and 256 KiB per direct check, then 300
seconds and 1 MiB for Lake build. Recheck all frozen non-client-build state;
only `$CLIENT_ROOT/.lake/build` may change.

### 11. Retention, Cleanup, and Reporting

On success, copy only the byte-identical generated files, separate witness,
minimal path-free client metadata, and provenance/readme into
`formal/hsai-gateway-threat-ordinal-aeneas/`. Retain no machine-local manifest.

On success or failure, record bounded digests/results, then remove exactly the
roots proven absent and created by Phase 679:

```text
RUN
RUSTUP_ROOT
CHARON_CARGO_HOME
AENEAS_ROOT
LEAN_ROOT
```

Never remove or clean `CHECKER_CARGO_HOME`, the repository Cargo target, the
Lean 4.30.0 root, another user cache, or another repository. On failure,
retain only the bounded failure note and standard mirrors.

## Phase 679 Authorization

After Phase 678 is committed and the disk gate passes, Phase 679 may make one
attempt under this document only. When an older phase conflicts with this
ordered protocol, Phase 678 controls the execution detail. The first named
failure terminates the attempt; no same-phase correction or replay is allowed.

## Repository Validation

The documentation-only boundary passed repository hygiene 1/1,
documentation claim-boundary coverage 1/1, source claim-boundary coverage 6/6,
Rust formatting, and diff hygiene. Root `pnpm run lint` was inapplicable
because there is no root `package.json`.

## Claim Boundary

Even a complete Phase 679 success can establish only a local, tool-mediated,
kernel-checked exhaustive witness over one extracted finite enum-to-ordinal
function under disclosed compiler, extractor, support-library, cache, kernel,
sandbox, and operator trust roots.

It cannot establish arbitrary Rust machine equivalence, checker-encoder,
Serde/JSON, SHA-256, proposal-digest, admission, or whole-HSAI correctness. It
cannot create accepted evidence, independent reproduction, Level2+, score
axes, semantic correctness, production readiness, SOTA, breakthrough, full
security, external audit, or action authority.

## Defensible Claim

```text
HSAI has one authoritative, ordered, fail-closed protocol for a future
target-isolated Aeneas extraction and sandboxed Lean kernel check; no tool ran
in Phase 678.
```

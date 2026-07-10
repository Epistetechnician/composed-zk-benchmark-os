# Phase 672 HSAI Gateway Threat Ordinal Direct-Toolchain and Offline-Lake Closure

## Status

Complete as a documentation-first execution-correction boundary.

State slice:
`phase-672-hsai-gateway-threat-ordinal-direct-toolchain-offline-lake-closure`.

Execution status: `NotRun`.

Classification: `AeneasRetryProtocolCorrected`.

Evidence ceiling: `Level1LocalReplayOrLower`.

This phase runs no Charon, Aeneas, Lean, Lake, Mathlib cache, SMT, Z3, or
COBALT command. It acquires no tool, dependency, cache object, or generated
artifact and creates no accepted evidence, Level2+ evidence, or score-axis
value.

## Purpose

Phase 671 exposed two protocol defects before any qualifying Lean result:

1. the first Charon build did not bind direct pinned Cargo/rustc/rustdoc
   binaries for child compiler processes; and
2. the first Lean command had no pre-existing client manifest, so Lake ran a
   dependency update and Mathlib cache hook inside the bounded checking stage.

Phase 672 freezes corrections for one future Phase 673 attempt. It does not
reinterpret the nonconforming Phase 671 diagnostics as proof.

## Inherited Pins

Phase 673 must reuse, without refresh-by-guessing, every source and tool pin
from Phases 668 and 670:

- checker source SHA-256
  `efa3782c4209a6b13fe5fd01d9c75c7e18bc77c675018be50b1ec59fec863f77`;
- method-slice SHA-256
  `cf647c12956f308b734025d2bf302be853d6e3b7089d6b111731284ec8a2e823`;
- selector `crate::_::ordinal`, guarded by the unique-item and one-body LLBC
  audits;
- Charon commit `909ff09ad0f144f83d354f2c3d26f631fb9f8e9a`;
- Rust nightly `2026-06-01` at rustc commit
  `14210df0e27ccd7d9e6a05b8085cbd438e4bbc65`;
- Aeneas `nightly-2026.07.10-c2015b8` at commit
  `c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d`;
- Lean `4.31.0` arm64 asset SHA-256
  `264105500c8abdf37b68ffe03390a783ed259807807222698da8dd92d6ce0a27`;
  and
- all nine Lake package commits from the pinned Aeneas manifest.

The Phase 671 tool roots were deleted. A future attempt must reacquire and
recheck them; no prior local installation may be assumed.

## Corrected Charon Build

The future source build must never invoke Cargo through an indirect rustup
proxy. It must derive the exact toolchain root from the already verified
isolated installation, then bind all child compiler entry points:

```text
TOOLCHAIN=$RUSTUP_HOME/toolchains/nightly-2026-06-01-aarch64-apple-darwin
PATH=$TOOLCHAIN/bin:/usr/bin:/bin:/usr/sbin:/sbin
RUSTC=$TOOLCHAIN/bin/rustc
RUSTDOC=$TOOLCHAIN/bin/rustdoc
CARGO=$TOOLCHAIN/bin/cargo
```

The only build command remains:

```bash
"$CARGO" build \
  --locked \
  --offline \
  --release \
  --bin charon \
  --bin charon-driver
```

Before Cargo runs, a direct `rustc_private` probe must compile with
`$RUSTC`. Cargo verbose output must show that the same direct rustc path is
used for the `rustc_trait_elaboration` child. A different compiler path stops
as `DirectRustcBindingMismatch`; no build retry is allowed.

## Lake Acquisition Stage

Network-enabled dependency and cache acquisition must be a separate stage
that finishes before any Lean checking command begins.

The client `lakefile.lean` may require Aeneas only through the explicit
`HSAI_AENEAS_LEAN_ROOT` path. The client starts in temporary storage and may
materialize a machine-local `lake-manifest.json`; that manifest and all
machine paths remain uncommitted.

The acquisition environment must set:

```text
MATHLIB_NO_CACHE_ON_UPDATE=1
MATHLIB_CACHE_DIR=$RUN/mathlib-cache
```

This suppresses Mathlib's automatic post-update cache hook. Acquisition then
runs exactly:

```bash
lake update
lake exe cache get
```

The first command may resolve only the path-bound Aeneas package and the nine
exact inherited package commits. The second command is the only cache-network
command. It may use Mathlib's official read-only cache endpoint and must use no
upload credential or cache `put` command.

The pinned Mathlib commit's cache documentation states that cache keys include
the Lake files, manifest, Lean compiler commit, file path/content, and
transitive import hashes. Phase 672 additionally pins:

| Source | SHA-256 |
|---|---|
| `Cache/README.md` at Mathlib `fabf563a...` | `ae3ef84f253db15c3ed2c9c31addcc22f823e45c45a63c40c3dfe56bc0c59783` |
| `lakefile.lean` at Mathlib `fabf563a...` | `a2bffc44a8baa126d9098117dfc28d77040a8a4aee78fe4ba491274b97cba551` |

Primary source:
[Mathlib cache documentation](https://github.com/leanprover-community/mathlib4/blob/fabf563a7c95a166b8d7b6efca11c8b4dc9d911f/Cache/README.md).

Precompiled Mathlib cache objects are imported build trust, not HSAI proof
authority. The run record must capture the client manifest digest, every
package commit and clean status, cache-object inventory count, decompressed
build-tree digest, and acquisition output bounds before network is disabled.

## Enforceable Network Denial

Clearing proxy variables is insufficient. Phase 673 must run each direct Lean
and Lake build command under this macOS sandbox profile:

```text
(version 1)
(allow default)
(deny network*)
```

The local Phase 672 preflight observed:

- `/usr/bin/true` exited zero under the profile;
- sandboxed DNS lookup failed; and
- sandboxed direct TCP to `1.1.1.1:443` failed with `Operation not permitted`.

Phase 673 must repeat one process-positive control and both network-negative
controls immediately before checking. If `sandbox-exec` is absent, the direct
TCP probe succeeds, or the denial is not attributable to the sandbox, the run
stops as `NetworkDenialUnavailable`.

The checking environment must also remove proxy variables and set
`MATHLIB_NO_CACHE_ON_UPDATE=1`. No Git, curl, cache executable, update hook, or
package checkout may run inside the sandboxed checking stage.

## Precheck Freeze

Before the first direct Lean command, Phase 673 must freeze:

- client `lakefile.lean`, `lean-toolchain`, and local manifest SHA-256 values;
- the Aeneas package and generated target tree digests;
- all ten package roots: Aeneas plus the nine inherited dependencies;
- every package HEAD and clean-worktree result;
- the Mathlib cache inventory and decompressed build-tree digest; and
- the absence of lock files or running Lake/cache processes.

After direct generated-target checking, direct witness checking, and one Lake
build, the manifest, package HEADs, package source status, and cache inventory
must remain unchanged. Only the temporary client's own `.lake/build` output
may be new.

## Exact Checking Order

Only after acquisition and the precheck freeze pass may Phase 673 run, under
the deny-network sandbox:

1. direct check of generated `Types.lean` and `Funs.lean`;
2. direct check of the separate fourteen-case witness named
   `phase673ExtractedThreatOrdinalWitnesses`; and
3. one isolated client `lake build`.

The Phase 668 time and output bounds remain: 120 seconds and 256 KiB per direct
Lean check, then 300 seconds and 1 MiB for Lake build. A process-group timeout
terminates the attempt. No command may update dependencies or fetch cache
objects during these checks.

## Phase 673 Mutation Surface

On complete success, Phase 673 may add only:

- byte-identical generated target files under
  `formal/hsai-gateway-threat-ordinal-aeneas/`;
- one separate witness module;
- minimal `lean-toolchain` and `lakefile.lean` client metadata;
- one provenance/readme record without machine-local paths;
- one Phase 673 execution note;
- Phase 672 next-gate closure;
- the Aeneas/Mathlib source-index status; and
- the standard `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, and `AGENTS.md` mirrors.

It must not commit a machine-local Lake manifest, `.lake` output, dependency
checkout, cache object, LLBC, binary, raw log, or temporary path.

On failure, Phase 673 may retain only a bounded failure note and status
mirrors. The first named failure terminates the attempt; there is no retry,
backend switch, source edit, generated-source edit, selector widening, or
network-policy weakening.

## Repository Validation

The documentation-only boundary passed:

```text
cargo fmt --all -- --check
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
git diff --check
```

Repository hygiene passed 1/1, documentation claim-boundary coverage passed
1/1, source claim-boundary coverage passed 6/6, formatting and diff hygiene
passed, and the sandbox process/network controls produced the expected local
results. Root `pnpm run lint` was inapplicable because there is no root
`package.json`.

## Claim Boundary

Even a complete Phase 673 success can establish only a local, tool-mediated,
kernel-checked exhaustive witness over the extracted fourteen-value ordinal
function under disclosed compiler, extractor, Aeneas-library, Mathlib-cache,
Lean-kernel, sandbox, and operator trust roots.

It cannot establish arbitrary Rust machine equivalence, checker-encoder
correctness, production Serde/JSON or SHA-256 behavior, proposal-digest
correctness, admission semantics, accepted formal evidence, independent
reproduction, Level2+, score axes, semantic correctness, production
readiness, SOTA, breakthrough, full security, external audit, or authority to
execute an HSAI action.

## Defensible Claim

```text
HSAI has corrected the direct compiler binding and offline Lean/Lake checking
protocol for one future target-isolated Aeneas retry; no tool or checker ran in
Phase 672.
```

## Next Gate

After Phase 672 is committed and the 20 GiB disk gate still passes, Phase 673
may perform one attempt under this corrected protocol.

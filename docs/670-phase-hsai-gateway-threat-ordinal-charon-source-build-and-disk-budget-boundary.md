# Phase 670 HSAI Gateway Threat Ordinal Charon Source-Build and Disk-Budget Boundary

## Status

Complete as a documentation-first fallback-selection and resource boundary.

State slice:
`phase-670-hsai-gateway-threat-ordinal-charon-source-build-and-disk-budget-boundary`.

Execution status: `NotRun`.

Classification: `PinnedCharonSourceBuildSelectedDiskBudgetNotMet`.

Evidence ceiling: `Level1LocalReplayOrLower`.

This phase clones no source, installs no toolchain, builds no binary, acquires
no dependency, runs no backend, and creates no LLBC, generated source, proof,
accepted evidence, Level2+ evidence, or score-axis value.

## Purpose

Phase 669 proved that the published macOS arm64 `charon-driver` cannot pass the
no-patch portability gate on this host because it references two unavailable
absolute Nix-store libraries. Phase 670 selects one later fallback without
weakening binary provenance or silently installing a global Nix environment.

## Alternatives

### Published-Binary Patching

Rejected. `install_name_tool`, re-signing, load-command mutation, copied
Homebrew libraries, or ad hoc `DYLD_*` substitution would create an HSAI-
modified executable with a new trust and reproducibility boundary. Phase 669
explicitly prohibited that path.

### Nix Closure Acquisition

Rejected for the next attempt. The host has no Nix installation. Adding Nix
would introduce a global installer/daemon boundary, larger closure, additional
operator policy, and exact flake/derivation-output requirements that are not
needed to compile the already pinned Rust source on the current host.

### Pinned Source Build

Selected. Build `charon` and `charon-driver` from the exact Aeneas-pinned
Charon commit with its exact Cargo lockfile and Rust nightly. This preserves
the source version and LLBC contract while allowing the host linker to resolve
system libraries naturally. The locally built binary remains an operator-built
research tool, not upstream-signed or production-trusted software.

## Exact Charon Source Pins

| Item | Required value |
|---|---|
| Repository | `https://github.com/AeneasVerif/charon` |
| Commit | `909ff09ad0f144f83d354f2c3d26f631fb9f8e9a` |
| Commit verification observed | GitHub `verified=true`, reason `valid` |
| Commit date | `2026-07-06T15:55:59Z` |
| `LICENSE.md` SHA-256 | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |
| `README.md` SHA-256 | `be0566d77bef830f6fa019fa7ae460377d130576aa143c2a7db0238341b4214a` |
| `charon/Cargo.toml` SHA-256 | `a596f9b50a62e142199bca400de2318a0426b914039882896a270a35cd7481b2` |
| `charon/Cargo.lock` SHA-256 | `4e361622e601cfe93fce40e5a13bf6b5a89a84394875b409f8c8f27ec86272db` |
| `charon/rust-toolchain` SHA-256 | `27e050e8fc5ac827e1264abf38c27fcaf18e73f4305104c866179cb84721898c` |
| Package edition | Rust 2024 |
| Required binaries | `charon`, `charon-driver` |

The source is Apache-2.0. Phase 671 must fetch only this commit into temporary
storage, detach HEAD at the exact object, verify all five file hashes, and
reject submodule, branch, tag, worktree, or source drift.

## Source Acquisition Contract

The future source root is:

```text
/tmp/hsai-phase671-<source-commit>/charon-source
```

The permitted network operation is a shallow fetch of the exact commit from
the official repository. The fetched commit must equal the required object and
pass the recorded source-file hashes. No source is copied into the HSAI
repository or retained after the attempt.

Cargo dependencies may be fetched once with the exact lockfile into an
isolated future `CARGO_HOME`. The source build itself must then run locked and
offline. Floating dependency updates, lockfile mutation, patches, alternate
registries, path overrides, and Cargo configuration inherited from the HSAI
repository are forbidden.

## Exact Future Build

After the Phase 668 isolated Rust nightly and component checks pass, Phase 671
may run only this source build from the pinned `charon/` directory:

```bash
cargo fetch --locked
cargo build \
  --locked \
  --offline \
  --release \
  --bin charon \
  --bin charon-driver
```

The build must use:

```text
RUSTUP_HOME=$HOME/.local/share/hsai-formal/rustup-aeneas-c2015b8
CARGO_HOME=$HOME/.local/share/hsai-formal/cargo-charon-909ff09a
CARGO_TARGET_DIR=/tmp/hsai-phase671-<source-commit>/charon-target
RUST_BACKTRACE=0
```

Network is allowed for `cargo fetch --locked` only. The later build must set
Cargo offline mode and clear proxy variables. Build stdout and stderr are
bounded to 1 MiB each, the timeout is 900 seconds, and timeout must terminate
the complete process group.

## Built-Binary Acceptance

Before use, the locally built binaries must:

- be native Mach-O arm64;
- report Charon version `0.1.220`;
- remain adjacent;
- have recorded SHA-256 values;
- contain no absolute dependency path that is absent on the host;
- resolve `librustc_driver` under the exact isolated Rust toolchain;
- pass one `charon version` and one non-mutating driver-load preflight;
- retain a clean pinned source tree and lockfile; and
- disclose that the host linker, Apple SDK/system libraries, rustc, Cargo, and
  all locked Cargo dependencies are build trust roots.

Any source edit, warning-denied build failure, missing library, unexpected
architecture, version drift, or loader failure stops the attempt. No binary
patch or alternate compiler is authorized.

## Disk-Budget Gate

Observed before Phase 670:

| Observation | Size |
|---|---:|
| Available space on the shared data volume | `6458052` KiB, approximately 6.2 GiB |
| Existing user-local Lean 4.30.0 installation | approximately 2.5 GiB |
| Existing ordinary nightly Rust toolchain | approximately 1.3 GiB |
| Phase 669 Aeneas staging before cleanup | approximately 592 MiB |

These observations exclude the required Rust `rustc-dev` payload, Lean 4.31
installation, nine Lake package source checkouts, isolated Cargo registry,
Charon release build outputs, and temporary downloads. The current 6.2 GiB is
not an acceptable safety margin.

Phase 671 requires at least:

```text
20971520 KiB available (20 GiB)
```

before any source, toolchain, package, or asset acquisition. It must retain at
least 5 GiB free throughout the run and recheck after each acquisition stage.
Crossing that reserve stops as `DiskReserveViolated` and triggers cleanup.

Phase 670 does not authorize deleting user files, caches, toolchains, package
stores, repositories, or system data to meet this gate. Space must be made
available by an explicit operator action outside this phase.

## Phase 671 Scope If the Disk Gate Passes

Phase 671 may combine the Phase 668 acquisition/extraction envelope with the
pinned Charon source build selected here. All Phase 668 selector, LLBC,
Aeneas, generated-source, witness, process-limit, mutation, cleanup,
validation, and claim-boundary rules remain mandatory.

The published Aeneas binary and Lean support source remain pinned to
`c2015b8`; only the unusable published Charon/driver pair is replaced by the
locally built exact pinned Charon commit. Phase 671 must bind the local binary
hashes into its run record.

## Success and Failure Ceiling

The maximum later success remains:

```text
LocalAeneasExtractedThreatOrdinalKernelWitness
```

at `Level1LocalReplayOrLower`.

Additional named source-build failures are:

- `DiskBudgetNotMet`
- `DiskReserveViolated`
- `CharonSourceCommitMismatch`
- `CharonSourceHashMismatch`
- `CharonCargoLockMismatch`
- `CharonCargoFetchFailed`
- `CharonSourceBuildFailed`
- `BuiltCharonIdentityMismatch`
- `BuiltCharonDynamicLinkUnavailable`

The first failure terminates the later attempt. No Nix fallback, binary patch,
source edit, dependency update, or identical same-phase replay is authorized.

## Repository Validation

The documentation-only boundary passed:

```text
cargo fmt --all -- --check
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
cargo clippy --workspace --all-targets -- -D warnings
git diff --check
```

Repository hygiene passed 1/1, documentation claim-boundary coverage passed
1/1, source claim-boundary coverage passed 6/6, critical source/disk pins were
present, workspace all-target clippy passed with warnings denied, and
formatting/diff hygiene passed. Root `pnpm run lint` was inapplicable because
no root `package.json` exists.

## Claim Boundary

A locally source-built Charon is a reproducible execution tool under pinned
source and disclosed host/compiler trust. Building it does not prove Charon,
Aeneas, Rust, Lean, or HSAI correct.

Phase 670 itself creates no execution result. It does not establish LLBC,
source correspondence, a Lean theorem, accepted evidence, independent
reproduction, Level2+, score axes, semantic correctness, production readiness,
SOTA, breakthrough, full security, external audit, or action authority.

## Defensible Claim

```text
HSAI selected a pinned local Charon source build as the responsible fallback
for the nonportable release driver, but the current host does not meet the
20 GiB disk-safety gate required to attempt it.
```

## Next Gate

Phase 671 is blocked from execution until the shared data volume reports at
least 20971520 KiB available. Once that external condition is met, the phase
may perform one source-built Charon plus Aeneas extraction attempt under the
combined Phase 668 and Phase 670 boundaries.

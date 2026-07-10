# Phase 668 HSAI Gateway Threat Ordinal Aeneas Execution Prerequisite Closure

## Status

Complete as a documentation-first execution-prerequisite boundary.

State slice:
`phase-668-hsai-gateway-threat-ordinal-aeneas-execution-prerequisite-closure`.

Execution status: `NotRun`.

Classification: `AeneasOrdinalExecutionPrerequisitesSpecified`.

Evidence ceiling: `Level1LocalReplayOrLower`.

This phase installs no toolchain, downloads no execution asset, acquires no
Lake package, runs no Charon/Aeneas/Lean/Lake backend command, and creates no
LLBC, generated source, proof, accepted evidence, Level2+ evidence, or
score-axis value.

## Purpose

Phase 667 stopped before extraction because Phase 666 did not provide a usable
Rust/Lean compiler pair, a valid inherent-method selector, an offline Lean
dependency closure, or a complete process envelope. Phase 668 closes those
documentation prerequisites before one later attempt may run.

## Frozen Baseline

Phase 668 starts from clean commit
`486b5460` (`Record HSAI Aeneas preflight failure`). Production/checker Rust,
Cargo metadata, and the Phase 666 source hashes remain unchanged.

The only future Rust target remains the private method at
`crates/hsai-gateway-digest-checker/src/lib.rs:118`:

```text
CheckerGatewayThreatLabel::ordinal
```

The method-slice SHA-256 remains
`cf647c12956f308b734025d2bf302be853d6e3b7089d6b111731284ec8a2e823`.

## Primary-Source Pins

The following official sources were refreshed on 2026-07-10.

### Inherited Aeneas Assets

| Item | Required value |
|---|---|
| Aeneas tag | `nightly-2026.07.10-c2015b8` |
| Aeneas commit | `c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d` |
| Charon commit | `909ff09ad0f144f83d354f2c3d26f631fb9f8e9a` |
| Aeneas arm64 asset bytes | `123234656` |
| Aeneas arm64 asset SHA-256 | `fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45` |
| Aeneas Lean-build asset bytes | `50447755` |
| Aeneas Lean-build asset SHA-256 | `f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59` |

The Aeneas release is a mutable prerelease. Tag equality is never sufficient;
asset byte counts and SHA-256 values must match before unpacking.

### Lean Toolchain

| Item | Required value |
|---|---|
| Official release | [Lean v4.31.0](https://github.com/leanprover/lean4/releases/tag/v4.31.0) |
| Darwin arm64 asset | `lean-4.31.0-darwin_aarch64.tar.zst` |
| Asset URL | `https://github.com/leanprover/lean4/releases/download/v4.31.0/lean-4.31.0-darwin_aarch64.tar.zst` |
| Asset bytes | `543754552` |
| Asset SHA-256 | `264105500c8abdf37b68ffe03390a783ed259807807222698da8dd92d6ce0a27` |
| Required identity | `Lean (version 4.31.0, ...)` |
| User-local root | `$HOME/.local/share/hsai-formal/lean-4.31.0` |

The Lean GitHub release record is mutable (`immutable=false`), so the asset
digest remains authoritative.

### Rust Toolchain

| Item | Required value |
|---|---|
| Channel date | `nightly-2026-06-01` |
| Channel manifest URL | `https://static.rust-lang.org/dist/2026-06-01/channel-rust-nightly.toml` |
| Channel manifest SHA-256 | `aaf1cb59b5996dd51831c9114b6e3a4a176e197851de91194b473117e142b935` |
| Charon `rust-toolchain` SHA-256 | `27e050e8fc5ac827e1264abf38c27fcaf18e73f4305104c866179cb84721898c` |
| rustc identity | `rustc 1.98.0-nightly (14210df0e 2026-05-31)` |
| rustc commit | `14210df0e27ccd7d9e6a05b8085cbd438e4bbc65` |
| Isolated rustup root | `$HOME/.local/share/hsai-formal/rustup-aeneas-c2015b8` |

Required aarch64-apple-darwin component payloads from the pinned manifest:

| Component | Target | XZ SHA-256 |
|---|---|---|
| `cargo` | `aarch64-apple-darwin` | `755d86dfcfc4b27526345bd8f510ee3dff0111a0aea3769b0a176ecd02e7f8db` |
| `rustc` | `aarch64-apple-darwin` | `6f40295ebcc383b6beb8536a161a39fe5201851a636ffb6eb915bb7dbb6026ed` |
| `rust-std` | `aarch64-apple-darwin` | `990006a1faac5e2e71b78b9c45912b528e02cacab19321526d2a2ec75cfdec44` |
| `rustc-dev` | `aarch64-apple-darwin` | `eb2d8507fcf1b2d4766598c4c04226c5b1c276fc9d81cff0fa970a90f42ab379` |
| `llvm-tools-preview` | `aarch64-apple-darwin` | `d6acc436144d3094e1e067947553d9cce50bf7b710cb089f345e8fcea7e59d02` |
| `rust-src` | `*` | `3ce6b9d679b5d1840d3ed276e74c8d6b4b1da5ebef2eeb542b588de04ada039f` |
| `miri-preview` | `aarch64-apple-darwin` | `29a9f42fecbfc53fc3ceadfb85407ef4bba06669d093c0b32bc15efcfd17147e` |

Phase 669 must provision these components explicitly under the isolated
`RUSTUP_HOME`, then verify `rustc -Vv`, `cargo -V`, and every installed
component. It must not rely on Charon's automatic installer.

## Lean Dependency Closure

The pinned Aeneas Lean inputs are:

| File | SHA-256 |
|---|---|
| `backends/lean/lake-manifest.json` | `7d527c1294d4a157d9b4266728124893d3324db4fee7b21a34f1595c7bc61de5` |
| `backends/lean/lakefile.lean` | `43504207e4a34e55be916327f7ef3189981fc68752abea691a3c4dda680087c6` |

The manifest version is `1.2.0`, package name is `aeneas`, and the closure has
exactly nine packages:

| Package | Official URL | Required commit |
|---|---|---|
| `mathlib` | `https://github.com/leanprover-community/mathlib4.git` | `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` |
| `plausible` | `https://github.com/leanprover-community/plausible` | `63045536fe95024e6c18fc7b48e03f506701c5bc` |
| `LeanSearchClient` | `https://github.com/leanprover-community/LeanSearchClient` | `c5d5b8fe6e5158def25cd28eb94e4141ad97c843` |
| `importGraph` | `https://github.com/leanprover-community/import-graph` | `5c7542ed018c78194f1e2b903eaf6a792b74c03d` |
| `proofwidgets` | `https://github.com/leanprover-community/ProofWidgets4` | `24b0d9dc081c5423f8eec7e866c441e5184f29d9` |
| `aesop` | `https://github.com/leanprover-community/aesop` | `e3cb2f741431ce31bf73549fb52316a57368b06f` |
| `Qq` | `https://github.com/leanprover-community/quote4` | `f46324995fca5f0483b742e4eb4daec7f4ee50d2` |
| `batteries` | `https://github.com/leanprover-community/batteries` | `fa08db58b30eb033edcdab331bba000827f9f785` |
| `Cli` | `https://github.com/leanprover/lean4-cli` | `92564e5770e4d09f2d86dfbf8ada1e9c715b384c` |

Phase 669 may acquire these exact source commits only into the user-local
Aeneas package's `backends/lean/.lake/packages/` directory. It may not use
floating branches, run an unconstrained dependency update, vendor the packages
into HSAI, or commit them. Every checkout must be detached at the exact commit,
clean, and recorded before network access is disabled.

The packaged Aeneas `-lean-default-lakefile` path is not trusted at this
commit. The HSAI client Lake file must be maintained separately and must bind
the user-local Aeneas path explicitly through one required environment value.

## Corrected Target Selector

Pinned Charon represents an inherent implementation as a matcher segment. The
only eligible selector for the current source is:

```text
crate::_::ordinal
```

The wildcard is acceptable only with all of these gates:

1. the frozen checker source and method-slice digests match;
2. `rg -n 'fn ordinal\s*\(' crates/hsai-gateway-digest-checker/src/lib.rs`
   returns exactly one match;
3. that match remains inside `impl CheckerGatewayThreatLabel`;
4. no other local crate item named `ordinal` exists;
5. Charon resolves exactly one starting item; and
6. the pretty-printed LLBC contains exactly one local function body,
   `ordinal`, plus the containing enum and classified scalar/support items.

Any collision or widened local body set stops as `TargetSelectorCollision` or
`UnexpectedLocalDependencyClosure`. The selector must not be made broader.

## Archive and Executable Safety

Before unpacking, Phase 669 must reject:

- absolute archive paths;
- `..` traversal segments;
- symlinks or hard links;
- undeclared top-level files; or
- an entry count different from the Phase 667 observations.

After unpacking, it must verify all Aeneas binary SHA-256 values recorded by
Phase 667, native arm64 architecture, version output, adjacent
`charon-driver`, and `libgmp`. It must record `codesign`, `spctl`, and `otool
-L` results.

The assets are ad-hoc signed and currently fail Gatekeeper assessment. Exact
asset and binary digests authorize only this local research run; Phase 669 may
not remove quarantine metadata, alter signatures, patch Mach-O load commands,
or present the binaries as production-trusted software.

Every absolute dynamic-library reference needed by `charon-driver` must exist
before `charon cargo`. Otherwise Phase 669 stops as
`DriverDynamicLinkUnavailable`. No Nix installation, source build, binary
patch, or alternate Charon binary is authorized.

## Cargo and Build-Script Boundary

Charon's selector restricts translated reachability, not Cargo compilation.
Cargo will compile the checker package and locked `ring = 0.17.14` dependency,
including `ring`'s build script. Phase 669 must disclose this as an imported
build trust root.

The Cargo invocation must be both locked and offline. It may use the existing
read-only Cargo registry/git cache, but all build output must go under the
temporary run root. A missing cached dependency stops as
`CargoOfflineDependencyMissing`; network fallback is forbidden during
execution.

## Exact Future Environment

Phase 669 must use:

```text
RUN=/tmp/hsai-phase669-<source-commit>
AENEAS_ROOT=$HOME/.local/share/hsai-formal/aeneas-c2015b8
LEAN_ROOT=$HOME/.local/share/hsai-formal/lean-4.31.0
RUSTUP_HOME=$HOME/.local/share/hsai-formal/rustup-aeneas-c2015b8
CARGO_HOME=$HOME/.cargo
CARGO_TARGET_DIR=$RUN/cargo-target
CARGO_NET_OFFLINE=true
RUST_BACKTRACE=0
HSAI_AENEAS_LEAN_ROOT=$AENEAS_ROOT/backends/lean
```

`CHARON_TOOLCHAIN_IS_IN_PATH` must be unset. Proxy variables must be removed
during execution. `PATH` must put the exact Lean and isolated Rust toolchain
binaries before inherited entries. Acquisition and execution environments
must be recorded separately.

## Exact Future Commands

After all acquisition and safety gates pass, Phase 669 may run Charon once:

```bash
"$AENEAS_ROOT/charon" cargo \
  --preset=aeneas \
  --start-from='crate::_::ordinal' \
  --dest-file="$RUN/hsai_gateway_digest_checker.llbc" \
  --error-on-warnings \
  -- \
  --manifest-path "$REPO/crates/hsai-gateway-digest-checker/Cargo.toml" \
  --package=hsai-gateway-digest-checker \
  --locked \
  --offline
```

It must then pretty-print and audit the LLBC:

```bash
"$AENEAS_ROOT/charon" pretty-print \
  "$RUN/hsai_gateway_digest_checker.llbc"
```

Only after the LLBC audit passes may Aeneas run once:

```bash
"$AENEAS_ROOT/aeneas" \
  -backend lean \
  -split-files \
  -checks \
  -abort-on-error \
  -warnings-as-errors \
  -dest "$RUN/generated" \
  -subdir HsaiGatewayThreatOrdinalAeneas/Extracted \
  -namespace HsaiGatewayThreatOrdinalAeneas \
  "$RUN/hsai_gateway_digest_checker.llbc"
```

Generated output must pass the Phase 666 hole, external-template, local-body,
and provenance gates before it enters the repository. The generated method's
actual type, including any `Result` wrapper, is authoritative. Manual edits to
generated code remain forbidden.

The separate theorem must be named
`phase669ExtractedThreatOrdinalWitnesses` and check all fourteen enum
constructors against ordinals `0` through `13`. Direct generated-target and
witness checks plus one isolated `lake build` must run with network access
disabled and the complete nine-package closure already present.

## Process Limits

| Process | Timeout | Maximum retained stdout | Maximum retained stderr |
|---|---:|---:|---:|
| Charon extraction | 180 seconds | 1 MiB | 1 MiB |
| Charon pretty-print | 60 seconds | 1 MiB | 1 MiB |
| Aeneas extraction | 120 seconds | 1 MiB | 1 MiB |
| Direct Lean target check | 120 seconds | 256 KiB | 256 KiB |
| Direct Lean witness check | 120 seconds | 256 KiB | 256 KiB |
| Lake build | 300 seconds | 1 MiB | 1 MiB |

The operator must terminate the complete process group on timeout. Only exit
status, bounded redacted summaries, byte counts, SHA-256 values, and declared
diagnostics may enter the run record. Raw logs and uncontrolled machine paths
must not be committed. If these limits cannot be enforced, stop as
`BoundedExecutionUnavailable`.

## Phase 669 Mutation Surface

On complete success, Phase 669 may add only:

- generated target files under
  `formal/hsai-gateway-threat-ordinal-aeneas/HsaiGatewayThreatOrdinalAeneas/Extracted/`;
- one separate witness module;
- minimal client `lean-toolchain` and `lakefile.lean` metadata;
- one provenance/readme record under that formal root;
- `docs/669-phase-hsai-gateway-threat-ordinal-aeneas-local-extraction-and-kernel-witness.md`;
- the Phase 668 next-gate update;
- Aeneas source-index status; and
- the standard `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, and `AGENTS.md` mirrors.

On failure, Phase 669 may retain only the bounded failure note and standard
status mirrors. It must not retain partial LLBC, generated source, package
trees, compiler outputs, or raw logs.

Production/checker Rust, Cargo metadata, `Cargo.lock`, the Phase 664/665 Lean
project, accepted Evidence Ledgers, and score reports remain read-only.

## Success and Failure Classification

Maximum success classification:

```text
LocalAeneasExtractedThreatOrdinalKernelWitness
```

The ceiling remains `Level1LocalReplayOrLower` because the run is local,
tool-mediated, and dependent on disclosed compiler/extractor trust roots.

Named failures include:

- `SourceBaselineDrift`
- `ReleaseOrAssetDrift`
- `ArchiveSafetyViolation`
- `ToolchainIdentityMismatch`
- `LakeDependencyClosureMismatch`
- `TargetSelectorCollision`
- `DriverDynamicLinkUnavailable`
- `CargoOfflineDependencyMissing`
- `RingBuildScriptFailed`
- `TargetRootNotResolved`
- `UnexpectedLocalDependencyClosure`
- `LlbcGenerationFailed`
- `LeanExtractionFailed`
- `ExternalDefinitionRequired`
- `GeneratedProofHoleDetected`
- `GeneratedSourceMutationRequired`
- `ExtractedApiWitnessUnsupported`
- `LeanKernelCheckFailed`
- `LakeBuildFailed`
- `BoundedExecutionUnavailable`
- `ArtifactHygieneFailed`

The first classified failure terminates Phase 669. No same-phase backend
switch, source build, binary patch, selector widening, dependency update, or
identical replay is authorized.

## Required Validation After a Phase 669 Success

```text
direct generated-target Lean check
direct exhaustive-witness Lean check
isolated network-disabled lake build
generated-source hole and external-template scan
LLBC local-body inventory validation
source, tool, dependency, and artifact digest rechecks
cargo fmt --all -- --check
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
cargo test --workspace --quiet
cargo test --workspace --features external-runner
cargo clippy --workspace --all-targets -- -D warnings
cargo doc --workspace --no-deps
git diff --check
git status --short --branch
```

## Phase 668 Validation Observed

The documentation-only boundary passed:

```text
cargo fmt --all -- --check
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
git diff --check
```

Repository hygiene passed 1/1, documentation claim-boundary coverage passed
1/1, source claim-boundary coverage passed 6/6, the source selector inventory
contained exactly one `ordinal` method, all critical source pins were present,
and formatting/diff hygiene passed. Root `pnpm run lint` was inapplicable
because no root `package.json` exists.

## Claim Boundary

Even a complete Phase 669 success would establish only one local,
tool-mediated, kernel-checked exhaustive witness over the extracted
checker-owned enum-to-ordinal function.

It would not prove or validate the checker encoder, production Serde/JSON,
proposal digest, SHA-256, admission semantics, arbitrary Rust machine-code
equivalence, or whole HSAI semantics. It would not create accepted formal
evidence, independent reproduction, Level2+, score axes, semantic correctness,
production readiness, SOTA, breakthrough, full security, external audit, or
action authority.

## Defensible Claim

```text
HSAI has closed the documented execution prerequisites for one future,
target-isolated Aeneas extraction attempt over the checker threat ordinal;
no extractor or proof checker ran in Phase 668.
```

## Next Gate

Phase 669 is the first eligible execution attempt under this corrected
boundary. It must pass every acquisition, selector, dependency, driver,
Cargo, process, generated-source, theorem, and cleanup gate or stop at the
first named failure.

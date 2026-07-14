# Phase 782 HSAI Formal Acquisition And Installer Argv Contracts

## Status

Complete as a documentation-first acquisition and installer argv contract
closure.

State slice: `phase-782-hsai-formal-acquisition-and-installer-argv-contracts`.

Classification: `AcquisitionAndInstallerArgvContractsResolved`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Resolution Verdict

Phase 782 resolves only Phase 780 lanes `L02` and `L03`. It freezes the exact
ordered argv contracts for four downloader rows and one isolated Rust
installer row:

```text
015 download-rust-manifest
016 install-rust-toolchain
033 download-aeneas-main
034 download-aeneas-lean
058 download-lean
```

The argv contracts are inputs to the future Phase 790-792 successor-ledger
expansion. Historical Phase 779 JSONL remains unchanged. All 1,469 historical
blocker objects and all 102 blocked rows remain; no source-ledger digest
exists. `L04` through `L11` remain open.

## Executable Role References

The argv arrays use two typed executable-role references:

| Role | Type | Allowed rows | Required resolver |
|---|---|---|---|
| `${CURL_EXE}` | host executable | 015, 033, 034, 058 | `resolve-curl-executable` |
| `${RUSTUP_EXE}` | host executable | 016 | `resolve-rustup-executable` |

These references extend the Phase 776 typed argv vocabulary only for the five
named rows. They do not resolve a host path, symlink chain, file identity,
mode, owner, version, or SHA-256. Phase 788 must provide the immutable role
registry and machine-policy acceptance. A future machine-resolved attempt must
record the observations outside the immutable source-ledger digest.

Neither role may be found through `PATH`, `command -v`, a shell, or a child
process. The future executor must substitute one already accepted absolute
executable path for the first argv element without changing any other token.

## Downloader Contract

Each downloader row is one direct child process. The arrays below are fully
expanded; there is no runtime profile, shell, pipeline, command chain,
configuration file, implicit retry, credential lookup, or output-name
inference.

### Ordinal 015: Rust channel manifest

```json
["${CURL_EXE}","--disable","--fail","--show-error","--silent","--globoff","--location","--max-redirs","5","--proto","=https","--proto-redir","=https","--tlsv1.2","--disallow-username-in-url","--connect-timeout","30","--max-time","840","--retry","0","--remove-on-error","--no-clobber","--output","${DOWNLOAD_ROOT}/channel-rust-nightly-2026-06-01.toml","https://static.rust-lang.org/dist/2026-06-01/channel-rust-nightly.toml"]
```

Accepted output:

```text
path=${DOWNLOAD_ROOT}/channel-rust-nightly-2026-06-01.toml
sha256=aaf1cb59b5996dd51831c9114b6e3a4a176e197851de91194b473117e142b935
```

### Ordinal 033: Aeneas main asset

```json
["${CURL_EXE}","--disable","--fail","--show-error","--silent","--globoff","--location","--max-redirs","5","--proto","=https","--proto-redir","=https","--tlsv1.2","--disallow-username-in-url","--connect-timeout","30","--max-time","840","--retry","0","--remove-on-error","--no-clobber","--output","${DOWNLOAD_ROOT}/aeneas-macos-aarch64.tar.gz","https://github.com/AeneasVerif/aeneas/releases/download/nightly-2026.07.10-c2015b8/aeneas-macos-aarch64.tar.gz"]
```

Accepted output:

```text
path=${DOWNLOAD_ROOT}/aeneas-macos-aarch64.tar.gz
bytes=123234656
sha256=fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45
```

### Ordinal 034: Aeneas Lean-build asset

```json
["${CURL_EXE}","--disable","--fail","--show-error","--silent","--globoff","--location","--max-redirs","5","--proto","=https","--proto-redir","=https","--tlsv1.2","--disallow-username-in-url","--connect-timeout","30","--max-time","840","--retry","0","--remove-on-error","--no-clobber","--output","${DOWNLOAD_ROOT}/lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz","https://github.com/AeneasVerif/aeneas/releases/download/nightly-2026.07.10-c2015b8/lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz"]
```

Accepted output:

```text
path=${DOWNLOAD_ROOT}/lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz
bytes=50447755
sha256=f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59
```

### Ordinal 058: Lean archive

```json
["${CURL_EXE}","--disable","--fail","--show-error","--silent","--globoff","--location","--max-redirs","5","--proto","=https","--proto-redir","=https","--tlsv1.2","--disallow-username-in-url","--connect-timeout","30","--max-time","840","--retry","0","--remove-on-error","--no-clobber","--output","${DOWNLOAD_ROOT}/lean-4.31.0-darwin_aarch64.tar.zst","https://github.com/leanprover/lean4/releases/download/v4.31.0/lean-4.31.0-darwin_aarch64.tar.zst"]
```

Accepted output:

```text
path=${DOWNLOAD_ROOT}/lean-4.31.0-darwin_aarch64.tar.zst
bytes=543754552
sha256=264105500c8abdf37b68ffe03390a783ed259807222698da8dd92d6ce0a27
```

### Downloader preconditions and failure behavior

For each row, `${DOWNLOAD_ROOT}` must be an accepted attempt-owned canonical
directory with mode `0700`. The exact output path must be absent, have no
symlink ancestor below the owned root, and have no competing writer. The four
rows execute serially in Phase 778 order.

`--disable` is the first curl option and prevents a curl configuration file
from changing the request. Globbing is disabled. `--proto` and
`--proto-redir` restrict initial and redirected requests to HTTPS, TLS 1.2 is
the minimum, and usernames in URLs fail. Redirects, connection time, total
transfer time, and retries are explicitly bounded. Proxy, netrc, cookie,
client-certificate, token, askpass, and credential environment variables
remain absent under the Phase 776 replacement-environment contract.

The child must exit zero before any size or SHA-256 acceptance. `--no-clobber`
provides defense in depth against overwrite; any generated `.1` through `.100`
alternate name is an undeclared extra output and fails the row. On nonzero,
timeout, signal, cap overflow, or retained partial output, the row fails and
the attempt stops. `--remove-on-error` must remove a transfer output after a
curl-detected failure; the executor must independently reject and remove any
remaining partial output during fail-closed cleanup. A pre-existing output,
alternate suffix, overwrite, extra file, wrong type, size mismatch, or digest
mismatch fails.

## Rust Installer Contract

Ordinal 016 is one direct child process with this exact ordered argv:

```json
["${RUSTUP_EXE}","toolchain","install","nightly-2026-06-01-aarch64-apple-darwin","--profile","minimal","--component","rustc-dev","--component","llvm-tools-preview","--component","rust-src","--component","miri","--no-self-update"]
```

The explicit `minimal` profile contributes only `cargo`, `rustc`, and
`rust-std`. The four additive component requests produce the required exact
seven-component installed set:

```text
cargo-aarch64-apple-darwin
llvm-tools-aarch64-apple-darwin
miri-aarch64-apple-darwin
rust-src
rust-std-aarch64-apple-darwin
rustc-aarch64-apple-darwin
rustc-dev-aarch64-apple-darwin
```

The full host-qualified toolchain token forbids host inference. The command
does not set a default toolchain, modify shell startup files, add a target,
inherit a repository `rust-toolchain`, request the default or complete
profile, permit a downgrade, force missing components, or mutate a global Rust
root. `--no-self-update` prohibits rustup self-mutation. It has no shell and
receives closed stdin; any prompt or stdin read fails.

Before row 016, row 015 must have exited zero and its retained manifest must
match the pinned SHA-256. The manifest is a mandatory dated-channel provenance
and admission precondition; rustup does not receive a local manifest pathname
in this argv. The future row therefore remains contingent on the exact
post-install rustc commit, Cargo identity, and seven-component inventory
checks. This phase does not claim byte-level correspondence between the local
manifest file and rustup's independent network retrieval.

The row must execute outside any source tree from the future accepted
`${ATTEMPT_ROOT}` cwd. Its complete replacement environment must include the
Phase 776 base plus `RUSTUP_HOME=${RUSTUP_ROOT}` and
`RUSTUP_TOOLCHAIN=nightly-2026-06-01` and must exclude inherited Cargo, proxy,
credential, and override state. `${RUSTUP_ROOT}` must be an empty accepted
attempt-owned directory. Apart from the row's declared transcript files, only
that toolchain root may change. The derived `${TOOLCHAIN_ROOT}` is exactly:

```text
${RUSTUP_ROOT}/toolchains/nightly-2026-06-01-aarch64-apple-darwin
```

The exact Rustup mutable-root inventory is not one of Phase 787's eight `M8`
rows; it remains ordinal-016 row-expansion work for Phase 790. The complete
replacement-environment row and typed input/output fields also remain Phase
790 work. This contract resolves only the specialized installer-argv blocker.

## Source Reconciliation Decisions

The inherited sources intentionally did not determine these five arrays.
Phase 782 makes the following narrow supersession and interpretation decisions
instead of presenting them as prior observations:

1. Phase 666 is added as the exact authority for both Aeneas asset filenames
   and URLs, correcting its omission from Phase 780 lane `L02`'s abbreviated
   source list.
2. `${CURL_EXE}` and `${RUSTUP_EXE}` are new typed role references required by
   the Phase 780 no-`PATH` rule. Their identity policies remain unresolved
   until Phase 788.
3. Phase 776's accepted empty owned `${RUSTUP_ROOT}` supersedes Phase 678's
   older absent-root wording at installer launch. The root must still have
   been absent before its exclusive in-process materialization.
4. The Phase 718 and Phase 774 acquisition-cap sources are not reconciled in
   this argv-only slice. Phase 790 must choose each affected row's controlling
   bound under the Phase 771 source order.
5. Phase 763 controls the exact seven-component acceptance inventory. The
   Rust manifest is a typed admission precondition, not an argv pathname, as
   stated above. This interpretation is explicit and does not claim that
   rustup consumed the retained manifest bytes.

## Source Correspondence

| Contract fact | Controlling source |
|---|---|
| Aeneas URLs, tag, sizes, and digests | Phase 666 `Reproducible Tool Pins`; Phase 668 `Primary-Source Pins` |
| Lean URL, size, digest, and Rust channel pin | Phase 668 `Primary-Source Pins` |
| Exact seven-component installed inventory | Phase 763 exact marked-installed inventory |
| Isolated Rust roots and operation order | Phase 678 `Authoritative Order`; Phase 680 `Corrected Rule`; Phase 744 `Authoritative Sequence` |
| Separate bounded acquisition producers | Phase 718 `Acquisition Producer Closure` |
| Closed operation IDs and capabilities | Phases 773, 774, and 778 |
| Role-resolution and replacement-environment boundaries | Phase 776 `Executable Identity Contract` and `Replacement Environment Vocabulary` |
| Curl option semantics | [curl command-line manual](https://curl.se/docs/manpage.html), checked 2026-07-14 |
| Rustup profile, component, and no-self-update semantics | [Rustup profiles](https://rust-lang.github.io/rustup/concepts/profiles.html), [components](https://rust-lang.github.io/rustup/concepts/components.html), and [basic usage](https://rust-lang.github.io/rustup/basics.html), checked 2026-07-14 |

## Phase 783 Gate

Phase 783 remains documentation-first. It may resolve only Phase 780 lane
`L04`: exact `/usr/bin/python3` helper compilation and test argv arrays with
ordered committed file and module sets. It may not rewrite historical Phase
779 rows, resolve Phase 784 or later lanes, publish a source-ledger digest, or
run a helper, test, producer, network command, Rustup, Cargo, Charon, Aeneas,
Lean, Lake, native audit, sandbox, SMT, Z3, COBALT, or kernel command.

## Claim Boundary

Phase 782 creates argv-contract metadata only. It is not an executable source
ledger, plan-v2 object, executor binding, machine identity, transcript,
backend result, generated Lean, retained kernel result, proof artifact,
checker transcript, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full security,
external audit, or action authority.

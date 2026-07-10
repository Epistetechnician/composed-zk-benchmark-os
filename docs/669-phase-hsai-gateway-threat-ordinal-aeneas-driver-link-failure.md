# Phase 669 HSAI Gateway Threat Ordinal Aeneas Driver-Link Failure

## Status

Complete as one corrected local attempt stopped at the first named failure.

State slice:
`phase-669-hsai-gateway-threat-ordinal-aeneas-driver-link-failure`.

Primary classification: `DriverDynamicLinkUnavailable`.

Charon extraction status: `NotRun`.

Aeneas extraction status: `NotRun`.

Lean kernel-check status: `NotRun`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Authorized Goal

Phase 668 authorized one corrected attempt over only the checker-owned
`ordinal` method. The attempt had to perform archive and unmodified-driver
portability checks before provisioning the larger Rust, Lean, and Lake package
closure. Missing dynamic dependencies required immediate termination.

## Frozen Baseline

The attempt started from clean commit
`6b818ddca406ef89ef00fd1f919053fb3682644e`.

The frozen checker source, checker manifest, workspace manifest, lockfile, and
method-slice SHA-256 values all matched. The source inventory contained exactly
one `fn ordinal`, at line 118 inside `impl CheckerGatewayThreatLabel`.

## Asset and Archive Results

The attempt acquired only the two inherited Aeneas assets before the driver
gate:

| Asset | Observed bytes | Observed SHA-256 | Result |
|---|---:|---|---|
| `aeneas-macos-aarch64.tar.gz` | `123234656` | `fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45` | matched |
| `lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz` | `50447755` | `f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59` | matched |

Archive safety checks passed:

- main archive entry count: 2471;
- Lean-build archive entry count: 2125;
- no absolute path;
- no `..` traversal segment;
- no symlink or hard link;
- only declared top-level entries; and
- the nested Lean-build archive was byte-identical to the separate asset.

## Binary Identity Results

| Binary | Architecture | Identity | SHA-256 |
|---|---|---|---|
| `aeneas` | Mach-O arm64 | `aeneas nightly-2026.07.10-c2015b8` | `9b9acc9b8c0820de5650fa72b8f66c6caf5e85bce616f8b6cb91c3b5f30d877a` |
| `charon` | Mach-O arm64 | `0.1.220` | `a71675cd16831f8dbba6936c8d9f85b2a2e171259d5c1cd2746bba99781be90a` |
| `charon-driver` | Mach-O arm64 | not executed | `dde11d6bfedd3bd6b3c8b56c54b96992245c68e784c8d112aaada1d6618bed86` |
| `libs/libgmp.10.dylib` | Mach-O arm64 | packaged support library | `1b0ae61990da7a4661f2c8c601f55f6c9950279bbfef12453dd5bb0c01e4b0df` |

All three executables were ad-hoc signed, had no Team ID, and were rejected by
the local Gatekeeper assessment. Phase 668 allowed the exact digest-bound local
research binaries to reach the dynamic-link audit but forbade signature or
Mach-O mutation.

## Dynamic-Link Failure

`otool -L` showed these absolute dependencies:

```text
charon:
/nix/store/f6dybgh0x0kcp1g7vp426vb495c7mwa8-libiconv-109/lib/libiconv.2.dylib

charon-driver:
/nix/store/f6dybgh0x0kcp1g7vp426vb495c7mwa8-libiconv-109/lib/libiconv.2.dylib
/nix/store/jyq4rjvwky8v61zi1s8j3ibzhgizccfr-zlib-1.3.1/lib/libz.dylib
@rpath/librustc_driver-cddc585b497d1e17.dylib
```

Both absolute Nix-store paths were absent on the host. `charon-driver` also
contained no `LC_RPATH` command to resolve its future `@rpath` dependency.
Installing the Rust toolchain could not repair the two absent absolute paths
without an additional Nix environment or binary/source substitution.

Phase 668 explicitly required all absolute driver dependencies to exist before
`charon cargo` and prohibited Nix installation, source builds, binary patches,
alternate binaries, or load-command changes. Phase 669 therefore stopped as
`DriverDynamicLinkUnavailable` without executing `charon-driver`.

## Work Not Performed

Phase 669 did not:

- download or install Lean 4.31.0;
- create the isolated Rust nightly toolchain;
- acquire any Mathlib/Lake package checkout;
- execute Cargo or the `ring` build script;
- run `charon cargo` or resolve `crate::_::ordinal`;
- generate or pretty-print LLBC;
- run Aeneas extraction;
- create generated Lean source or a client Lake project;
- implement the fourteen-case witness; or
- run Lean or Lake.

## Cleanup

The temporary run tree occupied 592 MiB before removal. Final cleanup
confirmed:

- `/tmp/hsai-phase669-6b818ddc` is absent;
- the user-local Aeneas, Lean 4.31.0, and isolated Rust roots are absent;
- Rust nightly 2026-06-01 is absent from the normal rustup root;
- no external package checkout remains;
- no generated artifact remains; and
- the repository was clean before this report mutation.

The host had approximately 6.3 GiB free after cleanup. Any future source-build
or full Rust/Lean/Mathlib closure must define and pass a disk-budget gate before
acquisition.

## Repository Validation

The bounded failure record passed:

```text
cargo fmt --all -- --check
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
git diff --check
```

Repository hygiene passed 1/1, documentation claim-boundary coverage passed
1/1, source claim-boundary coverage passed 6/6, and formatting/diff hygiene
passed. Root `pnpm run lint` was inapplicable because no root `package.json`
exists.

## Claim Boundary

Phase 669 establishes only that the exact published macOS arm64 Charon driver
is not directly portable to this host under the no-patch/no-Nix boundary.

It does not establish selector resolution, LLBC generation, Aeneas extraction,
generated-source correspondence, a Lean theorem, accepted evidence,
independent reproduction, Level2+, score axes, semantic correctness,
production readiness, SOTA, breakthrough, full security, external audit, or
action authority.

## Defensible Claim

```text
HSAI re-opened the corrected Aeneas attempt, verified the exact archives and
native binaries, and stopped before extraction because the pinned Charon
driver references unavailable absolute Nix libraries.
```

## Next Gate

Phase 670 must be documentation-first source-built Charon fallback and disk-
budget feasibility. It must compare a pinned source build against Nix closure
acquisition without modifying the published binary, select one reproducible
path or fail closed, define required free space and cleanup, and authorize no
backend execution. Only a later committed phase may attempt extraction again.

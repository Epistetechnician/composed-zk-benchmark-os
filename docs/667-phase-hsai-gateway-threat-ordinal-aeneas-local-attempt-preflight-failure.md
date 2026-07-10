# Phase 667 HSAI Gateway Threat Ordinal Aeneas Local Attempt Preflight Failure

## Status

Complete as one bounded failed local preflight attempt.

State slice:
`phase-667-hsai-gateway-threat-ordinal-aeneas-local-attempt-preflight-failure`.

Primary classification: `PackagedToolIdentityMismatch`.

Extraction status: `NotRun`.

Lean kernel-check status: `NotRun`.

Evidence ceiling: `Level1LocalReplayOrLower`.

Phase 667 did not produce LLBC, generated Lean source, a witness theorem, a
kernel result, accepted evidence, Level2+ evidence, or score-axis values.

## Authorized Goal

Phase 666 authorized one attempt to translate only
`crate::CheckerGatewayThreatLabel::ordinal` with the pinned Aeneas, Charon,
Rust, and Lean identities. The attempt had to stop on the first classified
failure and could not widen the target, switch backend, add handwritten
models, or acquire unpinned tooling.

## Frozen Repository Baseline

The attempt started from clean commit
`3786110da56bd9fa5c9e7d3179995e75b0e7112d`.

The Phase 666 source bindings rechecked exactly:

| Binding | Observed value |
|---|---|
| Checker source SHA-256 | `efa3782c4209a6b13fe5fd01d9c75c7e18bc77c675018be50b1ec59fec863f77` |
| Checker source Git blob | `1e693ebb5c69d7999d977db53e30eb95ab2a932e` |
| Checker manifest SHA-256 | `c2a6ccdd834b574ee658f80614c948fab17c2bc160a7354cf307272ba4a36986` |
| Workspace manifest SHA-256 | `8401ef7ea41db5ae0e2363c507cefeb2b9eb687034f4d6369e5ac7d2dddfe227` |
| Lockfile SHA-256 | `87e72fd27531b91d25097d810efa2a876971310fba77ac464c0169ef0d0df893` |
| Enum slice SHA-256 | `4e517c5dc746543e0cf3bb4da21e4903b0d46c4076388c7257911f88541bbad6` |
| Method slice SHA-256 | `cf647c12956f308b734025d2bf302be853d6e3b7089d6b111731284ec8a2e823` |

The repository remained unchanged during external preflight.

## Asset Verification

The attempt downloaded only the two Phase 666 Aeneas release assets into
`/tmp/hsai-phase667-3786110d` and verified them before unpacking:

| Asset | Observed bytes | Observed SHA-256 | Result |
|---|---:|---|---|
| `aeneas-macos-aarch64.tar.gz` | `123234656` | `fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45` | matched |
| `lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz` | `50447755` | `f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59` | matched |

The first archive contained 2471 entries. Its nested copy of the second asset
had the same byte count and SHA-256 and was byte-for-byte identical to the
separately downloaded asset. The second archive contained 2125 entries.
GitHub's release metadata identified the source as a mutable prerelease
(`immutable=false`), so the verified asset digests remain mandatory on every
future acquisition.

## Packaged Identity Audit

The Aeneas archive supplied native arm64 binaries and the Lean support package:

| Packaged file | Identity or SHA-256 |
|---|---|
| `aeneas` | `aeneas nightly-2026.07.10-c2015b8`; `9b9acc9b8c0820de5650fa72b8f66c6caf5e85bce616f8b6cb91c3b5f30d877a` |
| `charon` | `0.1.220`; `a71675cd16831f8dbba6936c8d9f85b2a2e171259d5c1cd2746bba99781be90a` |
| `charon-driver` | `dde11d6bfedd3bd6b3c8b56c54b96992245c68e784c8d112aaada1d6618bed86` |
| `libs/libgmp.10.dylib` | `1b0ae61990da7a4661f2c8c601f55f6c9950279bbfef12453dd5bb0c01e4b0df` |
| `rust-toolchain` | `nightly-2026-06-01` plus `rustc-dev`, `llvm-tools-preview`, `rust-src`, and `miri` |
| `backends/lean/lean-toolchain` | `leanprover/lean4:v4.31.0` |

The archive contained zero executable files named `lean`, `lake`, `rustc`, or
`cargo`. Its Lean-build payload contains compiled Aeneas support-library
objects, not a Lean compiler or kernel. The required local Rust nightly and
Lean 4.31.0 installations were both absent.

The three packaged executables were ad-hoc signed without a Team ID and failed
the local Gatekeeper assessment. Charon and `charon-driver` also retain
absolute Nix library references; top-level Charon help/version worked, but
driver portability was not established. A future phase must treat code-signing
and dynamic-link resolution as pre-execution checks, not assume archive
portability from file architecture alone.

## Stop Condition

The Phase 666 instruction to acquire only the two pinned release assets was
insufficient to establish the separately pinned Rust and Lean executables.
Continuing would have required at least one additional toolchain acquisition
path that Phase 666 did not bind by artifact digest or explicitly authorize.

The attempt therefore stopped as `PackagedToolIdentityMismatch` before:

- `charon cargo`;
- source-root resolution;
- MIR or LLBC generation;
- Aeneas Lean extraction;
- generated-source review;
- witness implementation; or
- Lean or Lake checking.

## Additional Boundary Blockers

An independent read-only audit of the pinned Charon and Aeneas sources found
three additional blockers that must be closed before another attempt:

1. The authorized root `crate::CheckerGatewayThreatLabel::ordinal` names an
   inherent method as if the containing type were a path segment. Pinned Charon
   matcher examples use an implementation segment such as
   `crate::_::ordinal` for inherent methods. That pattern is unique in the
   frozen crate today, but the wildcard form is not authorized by Phase 666
   and could match more than the intended method after drift, so it must not be
   substituted during Phase 667. See the pinned
   [matcher implementation](https://github.com/AeneasVerif/charon/blob/909ff09ad0f144f83d354f2c3d26f631fb9f8e9a/charon/src/name_matcher/mod.rs#L263-L280)
   and
   [matcher tests](https://github.com/AeneasVerif/charon/blob/909ff09ad0f144f83d354f2c3d26f631fb9f8e9a/charon/tests/ui/rust-name-matcher-tests.rs#L78-L86).
2. The Aeneas Lean package pins Mathlib commit
   `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` and transitive Lake packages,
   while release packaging removes dependency source trees. The compiled
   Aeneas support payload alone does not establish a source-level,
   network-disabled build closure for the future generated project. The
   packaged `-lean-default-lakefile` path is also defective at this commit, so
   a future client Lake file must be explicit and reviewed. See the
   pinned
   [Aeneas Lake configuration](https://github.com/AeneasVerif/aeneas/blob/c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d/backends/lean/lakefile.lean)
   and
   [precompile script](https://github.com/AeneasVerif/aeneas/blob/c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d/scripts/ci-precompile-lean.sh).
3. The exact process envelope is incomplete: isolated `RUSTUP_HOME`, explicit
   component installation and verification, `charon cargo` argv, package
   selection, `--locked`/offline Cargo policy, environment, timeout, output
   bounds, archive path-safety checks, and the execution of the checker's
   `ring` build dependency are not yet classified.

These are recorded as secondary pre-execution blockers, not observed backend
failures. No alternate selector, dependency acquisition, or process envelope
was tried.

One read-only `charon toolchain-path` probe attempted to invoke `rustup`
automatically. That subprocess was terminated before the required components
were installed, and the partially created named Rust toolchain was uninstalled.
No dated Rust toolchain, Aeneas installation, Lean 4.31.0 installation,
download, unpacked archive, or staging directory remains from Phase 667.

## Cleanup Verification

Final cleanup confirmed:

- `/tmp/hsai-phase667-3786110d` is absent;
- `$HOME/.local/share/hsai-formal/aeneas-c2015b8` is absent;
- `$HOME/.local/share/hsai-formal/lean-4.31.0` is absent;
- `nightly-2026-06-01-aarch64-apple-darwin` is absent from `rustup toolchain
  list`;
- the repository worktree is clean before this report mutation; and
- no generated artifact was retained.

## Repository Validation

The completed failure record passed:

```text
cargo fmt --all -- --check
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
cargo test --workspace --quiet
cargo clippy --workspace --all-targets -- -D warnings
git diff --check
```

Observed results:

- repository hygiene passed 1/1;
- documentation claim-boundary coverage passed 1/1;
- source claim-boundary coverage passed 6/6;
- the full workspace suite exited zero, including 675 passed and 5 ignored in
  the primary 680-test group;
- workspace all-target clippy passed with warnings denied;
- Rust formatting and diff hygiene passed; and
- root `pnpm run lint` was inapplicable because no root `package.json` exists.

## Claim Boundary

This failed preflight establishes only that the two exact Aeneas release
assets are internally coherent and insufficient by themselves to provide the
required compiler toolchains on this host. It also establishes that the
committed execution boundary lacks an authorized inherent-method selector, an
offline Lean package closure, and a complete command envelope.

It does not establish:

- Rust target isolation;
- successful Charon or Aeneas execution;
- generated-source correspondence;
- any Lean theorem;
- proof of checker, encoder, JSON, digest, SHA-256, admission, or HSAI
  semantics;
- accepted formal evidence or independent reproduction;
- Level2+ evidence or score-axis values; or
- semantic correctness, production readiness, SOTA, breakthrough, full
  security, external audit, or action authority.

## Defensible Claim

```text
HSAI attempted the exact Phase 666 Aeneas preflight, verified both pinned
release assets, and stopped before extraction because the archives do not
contain the separately required Rust and Lean toolchains.
```

## Next Gate

Phase 668 is complete in
`docs/668-phase-hsai-gateway-threat-ordinal-aeneas-execution-prerequisite-closure.md`.
It:

- pin the official Lean 4.31.0 Darwin arm64 archive by URL, byte count, and
  SHA-256;
- pin the official Rust nightly 2026-06-01 channel manifest and exact rustc
  identity;
- establish one exact inherent-method selector with a collision audit;
- pin a source-level Aeneas/Mathlib/Lake dependency closure or define a
  verified self-contained offline check path;
- define the exact Charon/Aeneas/Lean argv, package, environment, timeout,
  archive-safety, code-signing, dynamic-link, output-bound, `ring`
  build-script, cleanup, success, and failure rules; and
- authorizes no extraction.

Phase 669 is the first later phase eligible to reopen one target-isolated
Aeneas attempt under the corrected boundary.

# Phase 671 HSAI Gateway Threat Ordinal Aeneas Nonconforming Execution Observation

## Status

Complete as one bounded local attempt stopped without retained formal artifacts.

State slice:
`phase-671-hsai-gateway-threat-ordinal-aeneas-nonconforming-execution-observation`.

Primary classification: `CharonSourceBuildFailed`.

Later nonqualifying failure: `ArtifactHygieneFailed`.

Evidence ceiling: `Level1LocalReplayOrLower`.

Accepted evidence: none. Lean kernel status: `NotRun`. Lake build status:
`NotRun`.

Phase 671 crossed the local Charon and Aeneas execution boundary after the
first stop condition, but those later observations do not qualify as the
authorized success packet. No LLBC, generated Lean source, witness, compiler
log, dependency tree, proof artifact, accepted evidence, Level2+ evidence, or
score-axis value is retained in the repository.

## Frozen Input Recheck

Before execution, the attempt rechecked the frozen inputs from Phases 666 and
668:

| Binding | Observed SHA-256 |
|---|---|
| Checker source | `efa3782c4209a6b13fe5fd01d9c75c7e18bc77c675018be50b1ec59fec863f77` |
| Checker manifest | `c2a6ccdd834b574ee658f80614c948fab17c2bc160a7354cf307272ba4a36986` |
| Workspace manifest | `8401ef7ea41db5ae0e2363c507cefeb2b9eb687034f4d6369e5ac7d2dddfe227` |
| Cargo lockfile | `87e72fd27531b91d25097d810efa2a876971310fba77ac464c0169ef0d0df893` |
| `ordinal` source slice | `cf647c12956f308b734025d2bf302be853d6e3b7089d6b111731284ec8a2e823` |

The checker contained exactly one local `fn ordinal`, inside
`impl CheckerGatewayThreatLabel`, so `crate::_::ordinal` remained collision
free.

## Acquisition Results

The disk gate passed with `95194816` KiB available after removing only the
workspace Cargo target through `cargo clean`. The run retained more than the
required 5 GiB reserve throughout.

The following pinned identities passed:

- Rust nightly `2026-06-01`, rustc commit
  `14210df0e27ccd7d9e6a05b8085cbd438e4bbc65`, with all seven required
  components installed under the isolated rustup root;
- Charon source commit `909ff09ad0f144f83d354f2c3d26f631fb9f8e9a`
  with all five Phase 670 source hashes matched and a clean detached tree;
- Aeneas `nightly-2026.07.10-c2015b8` and both release assets with exact byte
  counts, SHA-256 values, archive counts, path/link safety, and nested-asset
  equality;
- Lean `4.31.0` from the exact pinned arm64 archive; and
- all nine Aeneas Lake dependency source checkouts at the exact detached
  commits recorded by Phase 668.

The packaged Aeneas binary remained ad-hoc signed and failed Gatekeeper
assessment. That posture was disclosed and never upgraded to production trust.

## First Stop Condition

The first locked offline Charon source-build invocation launched Cargo through
`rustup run` without also placing the exact toolchain binaries first in
`PATH`. Cargo consequently selected the wrong compiler for child rustc
processes and failed to resolve `rustc_private` crates such as `rustc_arena`.

Phase 670 required the exact isolated toolchain for the build and required any
source-build failure to stop the attempt. The correct Phase 671 primary result
is therefore:

```text
CharonSourceBuildFailed
```

The later retry explicitly bound the direct pinned `cargo`, `rustc`, and
`rustdoc` binaries and completed, but it occurred after the first stop
condition. Its outputs are diagnostics only and cannot establish the Phase
671 success classification.

## Later Diagnostic Observations

The nonqualifying continuation observed:

| Item | Observation |
|---|---|
| Local Charon binary | arm64, version `0.1.220`, SHA-256 `7cc0683b460f1cbbeddf7192b33802dfa2a5bc46ea34a4086d8f811acf99d182` |
| Local Charon driver | arm64, SHA-256 `9118518465d70e5f4d8d20625f094b6ec07fb782b7b80cd5d62323b552b2721f` |
| Driver load | rustup resolved the exact isolated `librustc_driver-cddc585b497d1e17.dylib` |
| LLBC | 40,940 bytes, SHA-256 `2029cdc3ca8b13c5176b8472cea11a8dcc6238e42b94a436f885c659e2836194` |
| LLBC inventory | one local function body, `ordinal`, plus the fourteen-constructor enum |
| Generated `Types.lean` | 1,491 bytes, SHA-256 `2ecbb3d771620dd4ff3bc29315edc497f5afbe9a1cf420827a1c292dfa6009ec` |
| Generated `Funs.lean` | 1,778 bytes, SHA-256 `1241219da521a9824114c2c3877398584c5a2e6b96e25d4791f364e69af3edbb` |
| Generated API | `CheckerGatewayThreatLabel.ordinal : Result Std.U8` |
| Generated-source scan | zero `sorry`, `admit`, `axiom`, `native_decide`, external-template, or decreases-template matches |

These facts show that the selected Charon root resolved and Aeneas could
mechanically translate the isolated function on this host. They are not a
Lean theorem, source-equivalence proof, accepted formal evidence, or evidence
that the run obeyed the complete Phase 671 protocol.

## Lean Client Failure

The staged client used a path dependency on the user-local Aeneas package but
had no pre-existing client manifest. `lake env lean` therefore ran Lake's
transitive update and Mathlib post-update hook before invoking Lean. It cloned
the already pinned package commits into the client tree, opened network access
for the Mathlib cache, and exceeded the 120-second direct-check bound.

The process was terminated. Lean never checked the generated target, the
fourteen-case witness never ran, and `lake build` never ran. This is an
additional `ArtifactHygieneFailed` observation. Clearing proxy variables was
not a network-denial mechanism and must not be represented as one.

## Cleanup

After recording bounded byte counts and digests, the attempt removed:

- the complete 5.1 GiB temporary run tree;
- the isolated Phase 671 Rust toolchain;
- the local Aeneas package and nine source checkouts;
- the Lean 4.31.0 installation;
- the isolated Charon Cargo home; and
- all LLBC, generated source, partial Lake state, downloads, and raw logs.

The pre-existing Lean 4.30.0 installation remained intact. The repository
worktree was clean before this failure record was written.

## Repository Validation

The retained documentation-only state passed:

```text
cargo fmt --all -- --check
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
cargo test --workspace --quiet
cargo test --workspace --features external-runner --quiet
cargo clippy --workspace --all-targets -- -D warnings
cargo doc --workspace --no-deps
git diff --check
```

Repository hygiene passed 1/1, documentation claim-boundary coverage passed
1/1, source claim-boundary coverage passed 6/6, both workspace test modes
exited zero, the primary workspace group passed 675 with 5 ignored, clippy
passed with warnings denied, and workspace documentation built. Root
`pnpm run lint` was inapplicable because the repository has no root
`package.json`.

## Claim Boundary

Phase 671 does not establish a Lean kernel-checked theorem, tool-mediated
source correspondence, arbitrary Rust execution equivalence, checker-encoder
correctness, production Serde/JSON behavior, proposal-digest correctness,
SHA-256 correctness, admission semantics, accepted formal evidence,
independent reproduction, Level2+, score axes, semantic correctness,
production readiness, SOTA, breakthrough, full security, external audit, or
authority to execute an HSAI action.

## Defensible Claim

```text
HSAI locally observed that pinned Charon and Aeneas can isolate and translate
the checker threat-label ordinal function, but Phase 671 failed its execution
protocol before any Lean kernel check and retained no formal artifact.
```

## Next Gate

Phase 672 must be documentation-first. It must freeze both corrections before
another attempt:

1. invoke the direct pinned Cargo/rustc/rustdoc binaries from the first Charon
   build command; and
2. define a pre-existing portable client manifest/package mapping plus an
   enforceable operating-system network-denial mechanism, with no Lake update
   or cache hook in the direct-check and build commands.

No identical Phase 671 replay is authorized.

Phase 672 completed this documentation-first correction in
`docs/672-phase-hsai-gateway-threat-ordinal-direct-toolchain-offline-lake-closure.md`.
One future Phase 673 attempt may proceed only after that boundary is committed.

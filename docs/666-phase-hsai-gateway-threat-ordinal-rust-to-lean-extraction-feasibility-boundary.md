# Phase 666 HSAI Gateway Threat Ordinal Rust-to-Lean Extraction Feasibility Boundary

## Status

Complete as a documentation-first feasibility boundary.

State slice:
`phase-666-hsai-gateway-threat-ordinal-rust-to-lean-extraction-feasibility-boundary`.

Execution status: `NotRun`.

Selection result: `AeneasSelectedForOneBoundedPhase667Attempt`.

Evidence ceiling: `Level1LocalReplayOrLower`.

This phase executes no extractor, Charon compiler driver, Lean kernel, solver,
or external checker. It creates no generated source, proof artifact, checker
transcript, accepted evidence, Level2+ evidence, or score-axis value.

## Purpose

Phase 665 established finite-fixture agreement among the production Rust path,
the implementation-diverse Rust checker, and a handwritten Lean model. The
next unresolved correspondence boundary is whether one source-owned Rust
function can be translated into Lean without widening to the full checker,
introducing handwritten semantic replacements, or hiding proof obligations.

Phase 666 therefore:

1. freezes one dependency-isolated checker-owned target;
2. verifies Aeneas and Hax facts against current primary sources;
3. selects one extractor for one bounded attempt;
4. defines generated-source review and correspondence rules;
5. authorizes the exact Phase 667 attempt only after this boundary is reviewed
   and committed; and
6. preserves all current evidence and claim ceilings.

## Inherited Baseline

The Phase 666 source baseline is the clean Phase 665 repository state at commit
`38c3d4175fd8336b1386aa9e78fed46e53a07f22`.

| Binding | Frozen value |
|---|---|
| Rust source | `crates/hsai-gateway-digest-checker/src/lib.rs` |
| Source SHA-256 | `efa3782c4209a6b13fe5fd01d9c75c7e18bc77c675018be50b1ec59fec863f77` |
| Source Git blob | `1e693ebb5c69d7999d977db53e30eb95ab2a932e` |
| Checker manifest SHA-256 | `c2a6ccdd834b574ee658f80614c948fab17c2bc160a7354cf307272ba4a36986` |
| Workspace manifest SHA-256 | `8401ef7ea41db5ae0e2363c507cefeb2b9eb687034f4d6369e5ac7d2dddfe227` |
| Lockfile SHA-256 | `87e72fd27531b91d25097d810efa2a876971310fba77ac464c0169ef0d0df893` |
| Workspace Rust floor | `1.74` |
| Checker dependency | `ring = "=0.17.14"` |
| Local platform observed for planning | macOS `15.7.5`, arm64 |

The `ring` dependency is outside the selected function's call graph. Its
presence in the checker manifest must still remain visible in Phase 667
provenance; it must not be misreported as translated or verified.

## Selected Rust Target

The only eligible Phase 667 root is:

```text
crate::CheckerGatewayThreatLabel::ordinal
```

The source anchors at the frozen commit are:

- `CheckerGatewayThreatLabel`: lines 80 through 96;
- `CheckerGatewayThreatLabel::ordinal`: lines 118 through 135;
- enum declaration slice SHA-256:
  `4e517c5dc746543e0cf3bb4da21e4903b0d46c4076388c7257911f88541bbad6`;
- method slice SHA-256:
  `cf647c12956f308b734025d2bf302be853d6e3b7089d6b111731284ec8a2e823`.

The target consumes one copied unit enum, performs one exhaustive `match`, and
returns one `u8` literal from `0` through `13`. It has no references,
allocation, loop, closure, string, collection, sort, mutation, error path,
trait call, hashing operation, dependency call, unsafe code, or concurrency.

The target corresponds to the existing handwritten Lean model's fourteen
threat constructors and ordinal ordering. It does not encode a proposal,
serialize JSON, normalize a set, or compute a digest.

## Explicitly Excluded Rust

Phase 667 must not translate or claim coverage for:

- the complete checker crate;
- `CheckerGatewayThreatLabel::label`;
- `CheckerGatewayActionKind::label`;
- `CheckerGatewayModelLaneKind::label`;
- `sorted_threats` or another sorting helper;
- `encode_gateway_action_proposal_preimage`;
- `check_gateway_action_proposal_digest`;
- `String`, `Vec`, closures, `sort_by_key`, `windows`, mutable byte buffers,
  decimal formatting, JSON escaping, duplicate rejection, `Result`, or
  `ring` SHA-256 behavior; or
- production `serde_json`, `sha2`, or `GatewayActionProposal::digest` behavior.

If the extractor cannot isolate the selected root and its minimum type
dependency, Phase 667 must stop as `TargetIsolationUnsupported`. It must not
refactor production/checker Rust, make the method public, add extraction
annotations, copy the function into a mirror crate, or widen the target.

## Primary-Source Refresh

The following facts were rechecked on 2026-07-10. URLs point to official
project repositories, release records, manuals, or pinned source.

### Aeneas

- Repository and license: [AeneasVerif/aeneas](https://github.com/AeneasVerif/aeneas),
  Apache-2.0 at the selected commit.
- Selected prerelease: [nightly-2026.07.10-c2015b8](https://github.com/AeneasVerif/aeneas/releases/tag/nightly-2026.07.10-c2015b8),
  published 2026-07-10 and bound to verified commit
  `c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d`.
- Aeneas states that it translates a subset of safe Rust through Charon LLBC,
  identifies Lean and HOL4 as its most mature backends, excludes unsafe code
  and concurrency, and documents remaining loop limitations in its
  [README](https://github.com/AeneasVerif/aeneas/blob/c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d/README.md).
- The pinned Charon exposes `--start-from` to translate named roots and the
  items they reference. It separately labels `--include` rough. See the
  [pinned Charon options](https://github.com/AeneasVerif/charon/blob/909ff09ad0f144f83d354f2c3d26f631fb9f8e9a/charon/src/options.rs#L72-L153).
- Aeneas documents `charon cargo --preset=aeneas`, `aeneas -backend lean`,
  `-split-files`, external-definition templates, and the requirement to pin
  its Lean package dependency. Generated translation is a model; it is not by
  itself an HSAI theorem or proof of source equivalence.

### Hax

- Repository and license: [cryspen/hax](https://github.com/cryspen/hax),
  Apache-2.0 at the compared release commit.
- Compared non-prerelease record: [hax-lib-v0.3.7](https://github.com/cryspen/hax/releases/tag/hax-lib-v0.3.7),
  published 2026-05-20 and bound to verified commit
  `d8b5b3d3b666fee8943a351445d2b680105e8ea3`.
- The [Lean quick start](https://hax.cryspen.com/manual/lean/quick_start/)
  documents item selectors, describes the Lean backend as under active
  development, warns that extraction can fail on supported Rust, and warns
  that a successful build alone does not prove panic freedom.
- The compared release pins Rust `nightly-2025-11-08` and Lean
  `leanprover/lean4:v4.29.0-rc1`; its GitHub release record publishes no binary
  assets.

## Reproducible Tool Pins

Phase 667 may use only this Aeneas acquisition set:

| Item | Required value |
|---|---|
| Aeneas release tag | `nightly-2026.07.10-c2015b8` |
| Aeneas commit | `c2015b8668ba6d5b41f5f19d00a881c12bbb0b5d` |
| Aeneas platform asset | [`aeneas-macos-aarch64.tar.gz`](https://github.com/AeneasVerif/aeneas/releases/download/nightly-2026.07.10-c2015b8/aeneas-macos-aarch64.tar.gz) |
| Aeneas asset size | `123234656` bytes |
| Aeneas asset SHA-256 | `fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45` |
| Aeneas Lean build asset | [`lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz`](https://github.com/AeneasVerif/aeneas/releases/download/nightly-2026.07.10-c2015b8/lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz) |
| Lean build asset size | `50447755` bytes |
| Lean build asset SHA-256 | `f1771437f16e5e34135719ff467b32ecda101cc215dc411741cd098732916f59` |
| Charon commit | `909ff09ad0f144f83d354f2c3d26f631fb9f8e9a` |
| Charon pin-file SHA-256 | `0587a2dbdf294ac41f570881af0c11d34fed03eb0fd48c703357c164760ebf50` |
| Lean toolchain | `leanprover/lean4:v4.31.0` |
| Lean pin-file SHA-256 | `efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee` |
| Aeneas license-file SHA-256 | `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4` |

The Aeneas release is a nightly prerelease. Phase 667 must bind tag, commit,
asset names, byte sizes, and SHA-256 values before unpacking. A tag match alone
is insufficient.

The selected Lean 4.31.0 environment is separate from the Phase 664/665 Lean
4.30.0 installation. Phase 667 must not overwrite that installation, mutate a
global toolchain, change shell startup files, or silently check generated code
with Lean 4.30.0.

## Backend Comparison

| Criterion | Aeneas | Hax | Phase 666 decision |
|---|---|---|---|
| License | Apache-2.0 | Apache-2.0 | Both acceptable for a bounded local evaluation. |
| Release reproducibility | Pinned nightly commit plus platform assets with published sizes and SHA-256 digests | Pinned non-prerelease source commit; release record has no binary assets | Aeneas has the stronger local acquisition record. |
| Source-root isolation | Pinned Charon `--start-from` follows one named root and its references | Manual documents item selectors | Both are plausible; Aeneas has an exact pinned driver option for this attempt. |
| Target subset fit | Safe sequential enum match to `u8`; no listed limitation is present | Enum/pattern support is plausible | Neither is treated as compatible until a local extraction succeeds. |
| Lean backend posture | Project calls Lean one of its most mature backends | Manual calls Lean actively developed and warns of supported-code failures | Aeneas is the lower-risk first attempt. |
| Platform setup | Exact macOS arm64 Aeneas and matching Lean-build assets | No binary assets on compared release | Aeneas is more operationally bounded. |
| Proof authority | Generated model still requires review, hole scan, theorem, and kernel check | Same; successful build is not a proof | Neither can promote claims by extraction alone. |

Verdict: select Aeneas for one Phase 667 attempt. Retain Hax as
`QualifiedFallbackNotAuthorized`. Hax may be reconsidered only by a later
docs-first phase after an Aeneas failure is classified; Phase 667 may not
switch backends opportunistically.

## Trust and Correspondence Boundary

Even a successful Phase 667 run will depend on:

- the frozen Rust source and Cargo workspace;
- rustc and the exact Charon compiler-driver behavior;
- Charon's MIR-to-LLBC translation;
- Aeneas's LLBC-to-Lean translation;
- Aeneas Lean support-library semantics for `u8` and result behavior;
- the selected Lean compiler, elaborator, kernel, and platform binaries; and
- local operator command and artifact capture.

The Aeneas project publishes formalization work about parts of its translation
and borrow-checking semantics. Phase 666 does not independently reproduce that
work and must not convert it into an HSAI source-equivalence claim.

The maximum Phase 667 statement is tool-mediated source correspondence for
one exhaustive enum-to-ordinal function under these disclosed trust roots. It
is not direct proof that arbitrary Rust machine execution equals generated
Lean evaluation.

## Generated-Source Review Contract

Phase 667 may retain generated HSAI Lean source only when every rule below
passes:

1. The production/checker source and Cargo metadata remain unchanged from the
   frozen source commit, and all four local SHA-256 bindings still match before
   Charon runs. The later documentation-only commit is recorded separately.
2. Charon receives exactly one `--start-from` root:
   `crate::CheckerGatewayThreatLabel::ordinal`.
3. The LLBC inventory contains only the selected method, its containing enum,
   scalar/support definitions required by the pinned tool, and explicitly
   classified external builtins.
4. No other local checker function body is translated. Any widened local call
   graph fails closed.
5. Aeneas receives the exact LLBC artifact and the Lean backend only.
6. Generated HSAI files are mechanically produced in a staging directory and
   are not edited by hand.
7. No unresolved external-definition or decrease template is needed for this
   target.
8. Generated HSAI files contain no `sorry`, `admit`, custom `axiom`,
   `native_decide`, or equivalent proof bypass.
9. The Phase 667 run record identifies the frozen source commit, tool pins,
   generation command digest, LLBC digest, and generated-tree digest.
10. One separately maintained theorem named
    `phase667ExtractedThreatOrdinalWitnesses` checks the generated function on
    all fourteen constructors and expected ordinals `0` through `13`.
11. Direct checking of the generated target and the witness theorem, followed
    by the isolated Lake build, must exit zero with the network disabled.
12. The committed generated files, if any, remain visibly generated and carry
    source/tool provenance. Manual proof code must live in a separate file.

The exhaustive theorem establishes behavior of the generated target for all
values of this finite unit enum. It does not establish checker-encoder,
proposal-digest, Serde, JSON, SHA-256, admission, or whole-system semantics.

## Phase 667 Exact Authorization

After Phase 666 is committed, Phase 667 may perform one bounded local Aeneas
extraction and kernel-check attempt under these constraints:

- acquire only the two pinned release assets into an operating-system
  temporary or user-local directory;
- verify byte sizes and SHA-256 digests before unpacking;
- inspect and record the packaged Aeneas, Charon, Rust, Lean, and Lake
  identities before execution;
- use an isolated user-local Aeneas/Lean 4.31.0 environment;
- run Charon with `--preset=aeneas` and the sole exact `--start-from` root;
- run Aeneas with only the Lean backend and split-file output in staging;
- enforce the generated-source review contract before retaining output;
- if the generated API permits a hole-free exhaustive theorem without source
  or generated-code edits, add only the generated target files, one separate
  witness theorem, minimal isolated Lake metadata, attribution/provenance, and
  Phase 667 run notes under a new
  `formal/hsai-gateway-threat-ordinal-aeneas/` boundary;
- run direct Lean checks and one isolated Lake build with network disabled;
- delete temporary downloads, unpacked staging trees, LLBC intermediates, and
  unretained outputs after recording bounded digests; and
- stop after the first classified success or failure. No identical replay is
  authorized in Phase 667.

Phase 667 may not:

- modify Rust, Cargo manifests, `Cargo.lock`, or the existing Phase 664/665
  Lean project;
- clone or vendor Aeneas, Charon, Hax, or another external repository;
- use Hax, rust-lean, SMT, Z3, COBALT, Coq, TLA+, CBMC, DeepProve, zkML, or a
  second extraction backend;
- use a source mirror, wrapper, public-method change, extraction annotation,
  handwritten external definition, generated-code patch, or proof bypass;
- translate the checker encoder, `ring`, production proposal code, Serde,
  JSON, SHA-256, or admission behavior;
- retain raw compiler/prover logs containing uncontrolled machine paths;
- mutate the accepted Evidence Ledger or create accepted formal evidence;
- create Level2+ evidence or score-axis values; or
- claim semantic correctness, production readiness, SOTA, breakthrough, full
  security, independent reproduction, external audit, or action authority.

## Failure Taxonomy

Phase 667 must stop with one primary classification:

- `SourceBaselineDrift`
- `ReleaseMetadataDrift`
- `AssetDigestMismatch`
- `PackagedToolIdentityMismatch`
- `TargetRootNotResolved`
- `TargetIsolationUnsupported`
- `UnexpectedLocalDependencyClosure`
- `UnsupportedRustConstruct`
- `LlbcGenerationFailed`
- `LeanExtractionFailed`
- `ExternalDefinitionRequired`
- `GeneratedProofHoleDetected`
- `GeneratedSourceMutationRequired`
- `ExtractedApiWitnessUnsupported`
- `LeanKernelCheckFailed`
- `LakeBuildFailed`
- `ArtifactHygieneFailed`

A failure is useful feasibility evidence at the local design level. It is not
permission to broaden scope inside the same phase.

## Validation Required for This Boundary

Phase 666 itself must pass:

- Markdown and repository whitespace hygiene;
- link and path spot checks for all local phase references;
- exact source-anchor and digest rechecks;
- claim-boundary scans confirming `NotRun`, `Level1LocalReplayOrLower`, and
  explicit nonclaims;
- no Rust, Cargo, lockfile, Lean project, generated artifact, or dependency
  mutation; and
- clean committed worktree verification.

## Validation Observed

The completed Phase 666 tree passed:

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

- all frozen source, manifest, workspace, lockfile, enum-slice, and method-slice
  SHA-256 values matched;
- repository hygiene passed 1/1;
- documentation claim-boundary coverage passed 1/1;
- source claim-boundary coverage passed 6/6;
- the full workspace suite exited zero, including 675 passed and 5 ignored in
  the primary 680-test group;
- workspace all-target clippy passed with warnings denied;
- Rust formatting and diff hygiene passed; and
- root `pnpm run lint` was inapplicable because no root `package.json` exists.

## Defensible Claim

```text
HSAI has a source-cited, reproducibly pinned, docs-first Aeneas extraction
boundary for the checker-owned threat-label ordinal function. Aeneas is
selected for one future fail-closed local attempt; no extraction has run.
```

This phase does not improve the Phase 665 evidence maturity. HSAI is not proven
semantically correct, production ready, SOTA, breakthrough, or fully secure.

## Next Gate

Phase 667 completed as the named `PackagedToolIdentityMismatch` preflight
failure recorded in
`docs/667-phase-hsai-gateway-threat-ordinal-aeneas-local-attempt-preflight-failure.md`.
Both Aeneas assets matched, but they contained no Lean kernel or Rust compiler,
and the required local toolchains were absent. No extraction ran.

Phase 668 is the next gate: documentation-first closure for exact official
Rust and Lean toolchain acquisition, an inherent-method selector collision
audit, an offline Aeneas/Mathlib/Lake dependency closure, and a complete
process envelope. It must not execute Charon, Aeneas, Lean, or Lake and must
not create generated source, evidence, or claim promotion.

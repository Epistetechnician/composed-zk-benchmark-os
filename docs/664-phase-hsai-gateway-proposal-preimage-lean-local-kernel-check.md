# Phase 664 HSAI Gateway Proposal Preimage Lean Local Kernel Check

State slice:
`phase-664-hsai-gateway-proposal-preimage-lean-local-kernel-check`.

## Status

Implemented and locally kernel-checked for exactly one handwritten model
theorem. Execution status is:

```text
KernelChecked
```

The successful local classification is:

```text
LocalLeanKernelCheckedCheckerModelTheoremCandidate
```

The evidence ceiling remains `Level1LocalReplayOrLower`.

## Parent Boundary

Phase 663 selected exactly one C3 model theorem:

```text
gateway_proposal_v1_set_permutation_invariant
gatewayProposalV1SetPermutationInvariant
```

Phase 664 may implement and locally check only that theorem under the source,
model, assumption, failure, and nonpromotion contracts in Phase 663.

## Acquisition Authorization

The only authorized toolchain is:

```text
leanprover/lean4:v4.30.0
```

The only authorized distribution asset is:

```text
asset:
lean-4.30.0-darwin_aarch64.tar.zst

source:
https://github.com/leanprover/lean4/releases/download/v4.30.0/lean-4.30.0-darwin_aarch64.tar.zst

published size:
517539007 bytes

published SHA-256:
072dca4a38fbc0d3cedb96fea886cc243b424f2bd16247596200b9a9ab93f0f5
```

The source, size, and SHA-256 were read from the official GitHub release API:

```text
https://api.github.com/repos/leanprover/lean4/releases/tags/v4.30.0
```

Acquisition must:

1. use HTTPS with redirect and failure checking;
2. write the archive only under a caller-created system temporary directory;
3. require the exact published byte length and SHA-256 before extraction;
4. extract with the locally available `tar` and `zstd` tools;
5. install without `sudo` under
   `$HOME/.local/share/hsai-formal/lean-4.30.0`;
6. reject an existing nonmatching installation;
7. verify `lean --version` and `lake --version` from the installed tree;
8. delete the temporary archive and extraction directory after installation;
9. make no shell startup, global `PATH`, Homebrew, Cargo, or repository change.

No Elan installation is required. The project `lean-toolchain` file remains an
immutable declaration for reproducibility; execution uses the verified direct
toolchain binaries through an explicit command-local `PATH`.

## Acquisition Failure Behavior

The acquisition must stop and classify the attempt without running Lean if
any of these occur:

- release API or asset URL mismatch;
- HTTP, TLS, redirect, or download failure;
- byte-length mismatch;
- SHA-256 mismatch;
- unsupported host architecture;
- extraction failure;
- destination collision;
- missing `lean` or `lake` binary;
- observed version other than 4.30.0;
- repository-relative or privileged install target;
- inability to remove the temporary acquisition tree.

The failure classification is `LeanToolchainUnavailable` or a narrower named
acquisition failure. It is never theorem success.

## Authorized Formal Project

The only new formal project files are:

```text
formal/hsai-gateway-digest/lean-toolchain
formal/hsai-gateway-digest/lakefile.toml
formal/hsai-gateway-digest/HsaiGatewayDigest/Model.lean
formal/hsai-gateway-digest/HsaiGatewayDigest/SetPermutationInvariant.lean
```

The root `.gitignore` may add exactly:

```text
/formal/hsai-gateway-digest/.lake/
```

The project may import only Lean core and `Std` modules shipped with the pinned
toolchain. It must not fetch Mathlib or another package and must not create a
`lake-manifest.json` with external dependencies.

## Authorized Model

The Lean model may implement only:

- checker-owned proposal and nested model-lane records;
- artifact, action-kind, lane-kind, and threat-label values;
- explicit artifact, string, and threat ordering;
- duplicate-free checks for the three list-valued set inputs;
- canonical sorting of those inputs;
- fixed v1 field and enum-label encoding;
- compact JSON byte encoding into a documented Lean byte representation;
- the three duplicate error classes;
- `withSets` replacement;
- helper lemmas required by the selected theorem.

The model must not implement SHA-256, import production Rust types, invoke the
Rust checker, or introduce another theorem target.

## Authorized Execution

After acquisition and source review, the only theorem-check commands are
equivalent to:

```text
lake env lean HsaiGatewayDigest/SetPermutationInvariant.lean
lake build
```

They must run from `formal/hsai-gateway-digest` with the verified direct Lean
4.30.0 `bin` directory prepended only for that process. Network access is not
allowed during build or theorem checking.

The committed Lean sources must also be scanned for the exact tokens selected
by Phase 663. Any unchecked admission, axiom, or unsafe definition fails the
run. The scan applies only to committed `.lean` files so documentation
nonclaims do not create false positives.

## Bounded Run Record

The completed run record contains:

- exact acquisition asset, size, and verified SHA-256;
- user-local install root;
- observed Lean and Lake versions;
- `lean-toolchain` and `lakefile.toml` SHA-256 values;
- model and theorem source SHA-256 values;
- frozen Phase 662 checker source and dependency-lock digests;
- exact command-local `PATH` policy and working directory;
- checker commands and exit statuses;
- bounded stdout and stderr summaries and SHA-256 values;
- theorem id and theorem-statement digest;
- source-to-model correspondence table;
- unsupported Rust constructs and handwritten replacements;
- forbidden-token scan result;
- all-false promotion flags;
- required nonclaims and claim boundary.

Raw toolchain archives, `.lake` state, unbounded logs, proof caches, generated
external source, and accepted Evidence Ledger files must not be committed.

## Success Classification

Only if acquisition, source bindings, forbidden-token scan, direct Lean check,
and Lake build all pass may Phase 664 use:

```text
LocalLeanKernelCheckedCheckerModelTheoremCandidate
```

That classification means only that the pinned local Lean kernel accepted the
selected theorem over the handwritten checker model. It remains
`Level1LocalReplayOrLower`.

## Nonpromotion Contract

All Phase 664 outputs must bind these values:

```text
creates_accepted_evidence = false
creates_level2_evidence = false
populates_score_axes = false
creates_benchmark_evidence = false
claims_source_correspondence_proof = false
claims_semantic_correctness = false
claims_production_readiness = false
claims_sota = false
claims_full_security = false
grants_authority = false
```

## Observed Acquisition

The acquisition authorization was committed first as `7a3cc06`. The official
Darwin arm64 asset was then downloaded to a system temporary directory and
matched both published values:

```text
verified size:
517539007 bytes

verified SHA-256:
072dca4a38fbc0d3cedb96fea886cc243b424f2bd16247596200b9a9ab93f0f5
```

The first extraction attempt used BSD `tar` with
`--use-compress-program=zstd`. It failed closed with a decompressor broken
pipe after the size and SHA-256 checks. The cleanup trap removed that temporary
tree and no installation target was created.

The second acquisition verified the same size and SHA-256, then used the
explicit local pipeline `zstd -d -c | tar -xf -`. Extraction and installation
succeeded at:

```text
/Users/shaanp/.local/share/hsai-formal/lean-4.30.0
```

No privileged, Homebrew, Elan, shell-startup, global `PATH`, or repository
installation change occurred. Both acquisition temporary trees were removed.

Observed versions:

```text
Lean (version 4.30.0, arm64-apple-darwin24.6.0,
commit d024af099ca4bf2c86f649261ebf59565dc8c622, Release)

Lake version 5.0.0-src+d024af0 (Lean version 4.30.0)
```

Version-output digests:

```text
Lean version SHA-256:
9888ff18b575109daacbcb69d41430386e535d04f73ff9df501fe85499cc9754

Lake version SHA-256:
046ec11da7c5ec88078933908043ff6da9e0b014e190498732e76d7699c3ee22
```

## Implemented Project

The project contains exactly the four authorized files. Their SHA-256 values
are:

```text
lean-toolchain:
54727eec5cba149c18842e6deb5c41b369d66455c93ce135d7d5347c782b2325

lakefile.toml:
e35e75f010f6ad969897731f2826826c90ab00faf02e72365070430452c4aa1f

HsaiGatewayDigest/Model.lean:
fb3c51e89fda569e28ddd1242f5e676484517fc81d1659685cd3e8aac92dceb4

HsaiGatewayDigest/SetPermutationInvariant.lean:
868bd61595619f3ca1ec51bb1e94468041c54fbb89a473edff0bb7d44944a6cc
```

The project imports only `Std`. Lake's generated manifest reported zero
external packages and was removed after validation. `.lake` remains ignored
and is not committed.

## Source Correspondence Record

Frozen source bindings remained unchanged during the run:

```text
Phase 662 checker source commit:
e35f8f56217c4e0f61216601734188adac83d964

crates/hsai-gateway-digest-checker/src/lib.rs SHA-256:
efa3782c4209a6b13fe5fd01d9c75c7e18bc77c675018be50b1ec59fec863f77

Cargo.lock SHA-256:
87e72fd27531b91d25097d810efa2a876971310fba77ac464c0169ef0d0df893

Cargo.toml SHA-256:
8401ef7ea41db5ae0e2363c507cefeb2b9eb687034f4d6369e5ac7d2dddfe227
```

| Rust checker surface | Lean model surface | Mapping status |
| --- | --- | --- |
| Checker-owned proposal and model-lane records | `GatewayActionProposalV1`, `ModelLaneProvenance` | Handwritten field-for-field model. |
| `[u8; 32]` | `Digest32 := List UInt8` | Handwritten replacement; correspondence assumes exactly 32 elements. |
| `u64` | `Nat` | Handwritten replacement; correspondence is limited to values below `2^64`. |
| `Vec<T>` set inputs | `List T` plus `Nodup` | Handwritten replacement matching duplicate rejection. |
| Artifact `(id, sha256)` ordering | Lexicographic `Ord` over `String × Digest32` | Handwritten replacement of `sort_by`. |
| Nonclaim string ordering | Shipped `String` `Ord` | Handwritten replacement of Rust string sorting. |
| Threat declaration ordinal | `Fin 14` order | Explicit declaration-order mapping. |
| Enum labels | Finite label functions | Explicit mapping for all 7, 5, and 14 variants. |
| Mutable byte-buffer JSON writer | Pure `String` renderer followed by `toUTF8` | Handwritten replacement; no source-correspondence theorem. |
| Three duplicate errors | `EncodeError` with three constructors | Error class is preserved; payload values are omitted. |
| `checker_sha256` and `ring` | No model | Explicitly excluded from the theorem. |

Unsupported or replaced Rust behavior remains explicit: references and
lifetimes, `Vec` mutation, `sort_by`/`sort_by_key` closures, window-based
duplicate detection, fixed-array typing, byte-buffer mutation, decimal
formatting internals, Rust compiler behavior, and `ring` SHA-256.

The model correspondence remains human-authored and assumption-bound. This
record is not a proof that the Lean model equals the Rust checker or production
Serde implementation.

## Theorem Binding

The exact marked theorem statement is 776 bytes with SHA-256:

```text
e3529de5389a8cb8ab11295584ac6d004562a81bc8117f78eeb8a761084a1cef
```

The theorem quantifies both lists for all three set-valued inputs, requires a
permutation and duplicate-free hypothesis for each first list, derives
duplicate freedom for each second list, and returns one byte sequence accepted
by both modeled encoders. It does not assume pre-sorted lists or encoder-result
equality.

The proof establishes canonical-list equality from `List.Perm` using shipped
`mergeSort` permutation and pairwise-order lemmas, then composes those results
with duplicate preservation and the pure encoder.

The committed Lean-source scan found zero case-insensitive whole-token matches
for the four Phase 663 forbidden constructs. No external package was present.

## Local Run

Final bounded run window:

```text
started:  2026-07-10T02:26:03Z
finished: 2026-07-10T02:26:03Z
```

Working directory:

```text
/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/formal/hsai-gateway-digest
```

Command-local path:

```text
/Users/shaanp/.local/share/hsai-formal/lean-4.30.0/bin:/usr/bin:/bin:/usr/sbin:/sbin
```

The working-directory, path, and two argv records have SHA-256:

```text
b1a393ee857311c4e80665e7302ed94bccde55efe5cc8fa793ea61a932193f5d
```

Direct theorem check:

```text
argv: lake env lean HsaiGatewayDigest/SetPermutationInvariant.lean
exit status: 0
stdout bytes: 0
stderr bytes: 0
stdout SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
stderr SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Project build:

```text
argv: lake build
exit status: 0
stdout bytes: 39
stderr bytes: 0
stdout summary: Build completed successfully (4 jobs).
stdout SHA-256: aee3d70d3b2c9bacc17719f0f81462902128b1735583320360093bc2f7ae9f37
stderr SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

No raw tool output, generated manifest, toolchain archive, or `.lake` content
is committed.

## Repository Validation

The final tree passed:

```text
lake env lean HsaiGatewayDigest/SetPermutationInvariant.lean
lake build
cargo fmt --all -- --check
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
cargo test --workspace --quiet
cargo clippy --workspace --all-targets -- -D warnings
git diff --check
```

Observed results:

- the direct Lean check and Lake build passed;
- the formal source scan found zero forbidden tokens;
- the generated Lake manifest contained zero external packages and was
  removed;
- repository hygiene passed 1/1;
- documentation claim-boundary coverage passed 1/1;
- source claim-boundary coverage passed 6/6;
- the full workspace suite passed, including 675 passed and 5 ignored in the
  primary 680-test admission group;
- workspace-wide all-target clippy passed with warnings denied;
- formatting and diff hygiene passed;
- root `pnpm run lint` was inapplicable because no root `package.json` exists.

## Anti-Goals

Phase 664 does not permit:

- Rust source or Cargo metadata changes;
- production digest or checker behavior changes;
- Elan, Homebrew, or global toolchain installation;
- shell startup-file mutation;
- external Lean packages;
- external repository clones or vendored source;
- network access during theorem checking;
- SMT, Z3, COBALT, Aeneas, Hax, rust-lean, Coq, TLA+, CBMC, DeepProve,
  zkML, or model-checker execution;
- SHA-256 implementation or proof;
- arbitrary-input production/checker equivalence;
- source-correspondence proof;
- independent external reproduction;
- accepted Evidence Ledger mutation;
- accepted evidence or accepted formal evidence;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, external-audit, or human-review-acceptance claims;
- global software-agent uniqueness;
- authority to execute an HSAI action.

## Defensible Claim

```text
HSAI has a pinned local Lean 4.30.0 kernel-checked theorem showing that
duplicate-free permutations of the three set-valued inputs produce identical
successful preimage bytes in its handwritten Phase 662 checker model, with
source, model, theorem, toolchain, command, and output digests recorded.
```

This does not prove the Rust checker, production Serde digest, SHA-256,
source correspondence, semantic correctness, production readiness, SOTA, or
full security.

## Next Responsible Slice

Phase 665 now defines the docs-first Lean-model-to-checker shared-fixture
witness boundary in
`docs/665-phase-hsai-gateway-proposal-preimage-lean-model-checker-witness.md`.
Its execution status is `NotRun`. It selects exactly the Phase 660 golden bytes
and Phase 662 nonempty ordering bytes, preserves the handwritten-model
assumptions, and forbids accepted-evidence or claim promotion. It does not
authorize Aeneas/Hax extraction, SHA-256 proof, source correspondence, or a
broader theorem.

# Phase 664 HSAI Gateway Proposal Preimage Lean Local Kernel Check

State slice:
`phase-664-hsai-gateway-proposal-preimage-lean-local-kernel-check`.

## Status

Authorized for one pinned local toolchain acquisition, one minimal Lean
project, and one bounded local kernel check. Execution status is currently:

```text
NotRun
```

This authorization is committed before tool acquisition or Lean execution.
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

After execution, this document must be updated from `NotRun` to the observed
status and must record:

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

## Current Claim

```text
HSAI has committed an explicit, checksum-bound authorization for one
user-local Lean 4.30.0 acquisition and one bounded kernel check of the Phase
663 set-permutation theorem. No acquisition or theorem run has yet occurred.
```

This claim must be replaced with the exact observed result after execution.

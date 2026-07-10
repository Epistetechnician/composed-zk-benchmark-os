# Phase 663 HSAI Gateway Proposal Preimage C3 Theorem And Extraction Boundary

State slice:
`phase-663-hsai-gateway-proposal-preimage-c3-theorem-extraction-boundary`.

## Status

Complete for the documentation-first C3 boundary.

Phase 663 selects one exact first theorem, one modeling strategy, one source
anchor set, one future Lean toolchain lock, and one nonpromotion contract. It
does not create a Lean project, install a toolchain, or execute a prover.

Current classification:

```text
DocsFirstC3BoundaryOnly
```

Current execution status:

```text
NotRun
```

The evidence ceiling remains `Level1LocalReplayOrLower`.

## Decision

The first C3 obligation will be a handwritten Lean 4 model theorem over the
dependency-isolated Phase 662 checker, not immediate Rust-to-Lean extraction.

The theorem id is:

```text
gateway_proposal_v1_set_permutation_invariant
```

The Lean theorem name is:

```text
gatewayProposalV1SetPermutationInvariant
```

The property is deliberately narrower than full encoder correctness:

```text
For a fixed checker-owned gateway proposal outside its three set-valued
inputs, replacing each duplicate-free source-artifact, nonclaim, and threat
list with a permutation produces the same successful modeled v1 preimage
encoding.
```

This generalizes the finite opposite-insertion-order checks in Phases 660 and
662. It does not model or prove SHA-256.

## Exact Theorem Shape

The future Lean source must state a theorem equivalent to:

```text
theorem gatewayProposalV1SetPermutationInvariant
    (base : GatewayActionProposalV1)
    (artifacts1 artifacts2 : List ArtifactDigest)
    (nonclaims1 nonclaims2 : List String)
    (threats1 threats2 : List GatewayThreatLabel)
    (artifactsPerm : artifacts1.Perm artifacts2)
    (nonclaimsPerm : nonclaims1.Perm nonclaims2)
    (threatsPerm : threats1.Perm threats2)
    (artifactsNodup : artifacts1.Nodup)
    (nonclaimsNodup : nonclaims1.Nodup)
    (threatsNodup : threats1.Nodup) :
    exists bytes,
      encodeGatewayActionProposalV1
          (base.withSets artifacts1 nonclaims1 threats1) = ok bytes and
      encodeGatewayActionProposalV1
          (base.withSets artifacts2 nonclaims2 threats2) = ok bytes
```

Lean syntax may vary only where required by the pinned toolchain. The theorem
id, quantified inputs, permutation hypotheses, duplicate-free hypotheses,
successful-result requirement, and equal-byte conclusion must not weaken.

The theorem must derive duplicate freedom for each second list from
permutation and the corresponding first-list hypothesis. It must not assume
that both encoder results are equal or supply pre-sorted lists as an input
hypothesis.

## Handwritten Model Scope

The future model may define only the data and pure functions needed by this
theorem:

- checker-owned proposal, model-lane, artifact, nonclaim, and enum values;
- three list-valued set inputs;
- artifact ordering by id and then 32-byte digest;
- nonclaim ordering by string value;
- threat ordering by the explicit v1 declaration ordinal;
- duplicate detection after canonical sorting;
- fixed v1 field and enum-label mapping;
- compact JSON string, integer, byte-array, boolean, object, and array emission;
- the fixed v1 digest tag;
- a byte output represented as `List UInt8`, `ByteArray`, or an exactly
  documented equivalent;
- an error/result shape that distinguishes the three duplicate classes.

The model must not import production Rust types or call the Rust checker. It is
a separately transcribed formal model.

## Why Handwritten Lean First

The current checker contains Rust `String`, `Vec`, fixed arrays, sorting
closures, window-based duplicate detection, byte-buffer mutation, decimal
formatting, and `ring` SHA-256. Direct Aeneas or Hax extraction of that complete
surface has not been qualified in this repository.

Handwritten Lean is selected because it permits one small theorem without
first treating unsupported extraction behavior as verified. The cost is an
explicit model-to-source correspondence assumption. Phase 664 must preserve
that limitation in every classification and run summary.

A later Rust-to-Lean phase may reconsider Aeneas or Hax only after it:

- verifies the tool license and exact release;
- pins the Charon/LLBC or equivalent extraction toolchain;
- inventories supported and unsupported Rust constructs;
- introduces a smaller pure Rust canonicalization kernel if required;
- records every generated and handwritten definition;
- rejects `sorry`, admitted lemmas, unchecked axioms, and silent source drift.

Phase 663 does not run Aeneas, Hax, rust-lean, or another extractor.

## Source Baseline

The theorem is bound first to the Phase 662 checker canonicalization surface.
The frozen source baseline is:

```text
source commit:
e35f8f56217c4e0f61216601734188adac83d964

crates/hsai-gateway-digest-checker/src/lib.rs SHA-256:
efa3782c4209a6b13fe5fd01d9c75c7e18bc77c675018be50b1ec59fec863f77

Cargo.lock SHA-256:
87e72fd27531b91d25097d810efa2a876971310fba77ac464c0169ef0d0df893

Cargo.toml SHA-256:
8401ef7ea41db5ae0e2363c507cefeb2b9eb687034f4d6369e5ac7d2dddfe227

Rust toolchain observed during boundary preparation:
rustc 1.93.1 (01f6ddf75 2026-02-11)
cargo 1.93.1 (083ac5135 2025-12-15)
```

The required checker symbol anchors are:

- `encode_gateway_action_proposal_v1`;
- `sorted_artifacts`;
- `sorted_nonclaims`;
- `sorted_threats`;
- `write_json_string`;
- `write_byte_array`;
- `write_u64`;
- `write_bool`;
- every checker-owned proposal and enum type consumed by those functions;
- `CHECKER_DIGEST_TAG`.

`checker_sha256` and `ring` are recorded as adjacent source but are outside the
theorem. The production Phase 660 Serde/`sha2` path is an external comparison
surface, not a theorem dependency.

Any change to a bound source digest, symbol shape, sort key, enum ordinal,
field order, tag, duplicate policy, or byte emitter invalidates the future
model correspondence package until reviewed and rebound.

## Model Correspondence Record

Phase 664 must add a machine-readable or deterministically rendered local
correspondence record that binds:

- Phase 663 state slice and theorem id;
- source commit and source-file SHA-256;
- Cargo lock and workspace-manifest SHA-256;
- exact checker symbol anchors;
- Lean model file SHA-256 values;
- theorem source file and theorem-statement SHA-256 values;
- the three sort keys and duplicate policy;
- Rust bytes to Lean bytes representation mapping;
- Rust strings to Lean strings mapping;
- fixed-array and `u64` representation mappings;
- every handwritten model replacement;
- unsupported Rust constructs;
- excluded SHA and production-Serde surfaces;
- toolchain release and lock-file digest;
- axiom, `sorry`, `admit`, and unsafe-code scan result;
- local checker command and bounded result classification;
- claim boundary and required nonclaims.

The record must fail closed if any required binding is absent or stale. A
human-authored correspondence record is not itself a source-correspondence
proof.

## Lean Toolchain Lock

The future project must pin this exact official Lean 4 release:

```text
leanprover/lean4:v4.30.0
```

Official release source:
`https://github.com/leanprover/lean4/releases/tag/v4.30.0`.

No floating `stable`, `latest`, nightly, branch, or unpinned revision is
allowed. Phase 664 must record the `lean-toolchain` file digest and the locally
observed `lean --version` and `lake --version` values before checking the
theorem.

Boundary preparation found no local `lean`, `lake`, or `elan` executable.
Current readiness is therefore:

```text
LeanToolchainNotInstalled
```

Phase 663 does not authorize installation. Phase 664 may proceed only after
its own explicit execution authorization records the acquisition source,
integrity policy, local install location, and failure behavior. If the pinned
toolchain cannot be obtained or verified, the result is
`LeanToolchainUnavailable`, not a proof or successful run.

## Future Phase 664 Project Surface

Phase 664 may propose only this new formal-project surface:

```text
formal/hsai-gateway-digest/lean-toolchain
formal/hsai-gateway-digest/lakefile.toml
formal/hsai-gateway-digest/HsaiGatewayDigest/Model.lean
formal/hsai-gateway-digest/HsaiGatewayDigest/SetPermutationInvariant.lean
```

It may also update:

- the exact `.lake` ignore entry;
- one Phase 664 run note;
- the Phase 659 through Phase 663 status notes;
- `README.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`;
- `AGENTS.md`.

The Lean project must use only Lean core and libraries shipped with the pinned
toolchain. Mathlib or another external package requires a separate docs-first
dependency boundary.

Phase 664 must not change Rust source, Cargo metadata, production digest
semantics, the checker implementation, or accepted-evidence policy.

## Future Check And Artifact Contract

The future local check must use fixed project-local commands equivalent to:

```text
lake env lean HsaiGatewayDigest/SetPermutationInvariant.lean
lake build
```

The run must also scan all committed Lean source for at least:

```text
sorry
admit
axiom
unsafe
```

Any occurrence must be classified and fail the candidate check unless it is a
false-positive token in an explicitly reviewed comment; removing the token is
preferred.

The bounded run record must contain:

- execution mode `OperatorProvidedLocalRun`;
- exact argv and working directory;
- toolchain lock and version output digests;
- source, model, and theorem digests;
- start and finish times if supplied by the operator;
- exit status;
- bounded stdout and stderr summaries and digests;
- theorem id and discharged/not-discharged status;
- forbidden-token scan result;
- correspondence record digest;
- no-promotion booleans;
- claim boundary and required nonclaims.

Raw `.lake` build state, unbounded logs, toolchain archives, external source
trees, credentials, accepted Evidence Ledgers, and benchmark outputs must not
be committed.

If the theorem is kernel-checked and all bindings validate, the maximum local
classification is:

```text
LocalLeanKernelCheckedCheckerModelTheoremCandidate
```

It remains `Level1LocalReplayOrLower`. It is not accepted formal evidence and
not a proof of the Rust or production implementation.

## Imported Trust And Exclusions

The future theorem leaves these assumptions open:

- faithful handwritten transcription of checker-owned data and encoder logic;
- faithful Rust-to-Lean string, integer, array, enum, and byte mappings;
- correctness of the Lean kernel, elaborator, compiler, runtime, and pinned
  toolchain distribution;
- correctness of the host operating system and hardware;
- correspondence between the Lean sorting model and Rust sorting behavior;
- correctness of the checker JSON encoder outside the proved permutation
  relation;
- correctness of production Serde and `serde_json`;
- correctness of checker `ring` and production `sha2` SHA-256;
- SHA-256 collision resistance;
- correspondence between the checker model and the production proposal type;
- arbitrary-input equivalence between checker and production implementations;
- gateway admission semantics outside this one encoding property.

The theorem must not use hash injectivity, collision resistance, or an
uninterpreted hash assumption. SHA-256 is outside the theorem entirely.

## Failure Taxonomy

Phase 664 must distinguish at least:

- Lean toolchain unavailable;
- unverified or mismatched toolchain release;
- Lean or Lake version drift;
- source commit or source-file digest drift;
- missing or changed source anchor;
- incomplete handwritten replacement disclosure;
- unsupported construct silence;
- bytes, string, integer, array, enum, or error-model mismatch;
- artifact comparator mismatch;
- nonclaim comparator mismatch;
- threat ordinal mismatch;
- duplicate-free precondition omission or weakening;
- theorem statement drift;
- `sorry`, `admit`, axiom, unsafe, or unchecked dependency detected;
- Lean parse, elaboration, termination, or kernel-check failure;
- command, working-directory, or environment drift;
- output-summary or artifact digest drift;
- false source-correspondence classification;
- accepted-evidence, Level2+, score-axis, or public-claim promotion attempt.

No failure may be normalized into theorem success.

## Phase 663 Anti-Goals

Phase 663 does not permit or create:

- Rust source changes;
- Cargo metadata or dependency changes;
- Lean project or proof source files;
- proof-assistant setup files;
- Lean, Lake, Elan, Aeneas, Hax, rust-lean, SMT, Z3, COBALT, Coq, TLA+,
  CBMC, DeepProve, zkML, or model-checker execution;
- tool installation or network download;
- external repository clones or vendored source;
- process APIs, scripts, or binaries;
- proof artifacts, checker transcripts, or solver certificates;
- filesystem evidence bundles;
- independent external reproduction;
- independent formal verification;
- source-correspondence proof;
- accepted Evidence Ledger mutation;
- accepted evidence or accepted formal evidence;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, external-audit, or human-review-acceptance claims;
- global software-agent uniqueness;
- authority to execute an action.

## Defensible Claim

```text
HSAI defines a source-bound, documentation-first C3 boundary for one
handwritten Lean theorem over the Phase 662 checker's duplicate-free set
canonicalization behavior, with an exact theorem statement, pinned future
toolchain, source and model bindings, failure taxonomy, and nonpromotion
policy.
```

It does not justify:

```text
HSAI ran Lean.
HSAI proved the checker or production digest implementation.
HSAI proved source correspondence.
HSAI has accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI is semantically correct.
HSAI is production ready.
HSAI is SOTA.
HSAI is fully secure.
```

## Next Responsible Slice

Phase 664 should implement the exact minimal Lean project, validate or obtain
the pinned toolchain under an explicit acquisition policy, prove and
kernel-check `gatewayProposalV1SetPermutationInvariant`, create the bounded
local correspondence/run record, run repository gates, and preserve the
`Level1LocalReplayOrLower` evidence ceiling.

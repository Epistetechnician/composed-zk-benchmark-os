# Phase 659 HSAI Gateway Proposal Digest Production Source Correspondence Boundary

State slice:
`phase-659-hsai-gateway-proposal-digest-production-source-correspondence-boundary`.

## Status

Complete for the documentation-first production source-correspondence
boundary.

Phase 659 does not change Rust code and does not run a formal backend. It
freezes the current production digest path, identifies the first source change
needed to expose its exact preimage, and defines the correspondence ladder that
must be completed before a proof result can describe that path.

The evidence ceiling remains `Level1LocalReplayOrLower`.

## Decision

The next implementation slice is not another tiny-Z3 replay and is not an
immediate Lean, COBALT, Aeneas, or Hax run.

The next implementation slice must first expose and regression-lock the exact
bytes hashed by `GatewayActionProposal::digest`. Only then may a later
backend-specific phase model or extract a bounded part of that production
path.

The production encoding is source-bound deterministic Serde JSON. It is not
described as a portable canonical-JSON standard because JSON itself does not
standardize object-member order and the current behavior depends on the Rust
types, their declaration order, Serde derives, collection ordering, and the
locked `serde_json` implementation.

## Current Production Path

The exact current call path is:

```text
GatewayActionProposal::digest(proposal)
  -> hash_tagged("hsai-agent-admission:gateway-action-proposal:v1", proposal)
  -> serde_json::to_vec(&(tag, proposal))
  -> SHA-256 over the returned bytes
  -> hsai_claim_envelope::Hash([u8; 32])
```

The current dependency lock records:

- `serde` `1.0.228`;
- `serde_derive` `1.0.228`;
- `serde_json` `1.0.150`;
- `sha2` `0.10.9`.

Those versions describe the current source instance. They are not evidence
that all compatible future versions emit identical bytes or implement SHA-256
correctly.

## Required Source Anchors

Any future correspondence package for this path must bind the source commit,
source file digest, and exact symbol name for each applicable anchor.

### Admission anchors

Owned by `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayActionProposal`;
- `GatewayActionProposal::digest`;
- `hash_tagged`;
- `GatewayActionId`;
- `GatewayActionKind`;
- `GatewayThreatLabel`;
- `GatewayModelLaneKind`;
- `GatewayModelLaneProvenance`;
- `ArtifactDigest`;
- `NonClaimLabel`.

### Imported type anchors

Owned by `crates/hsai-claim-envelope/src/lib.rs`:

- `SubjectId`;
- `Hash`.

### Dependency anchors

Owned by repository metadata:

- `crates/hsai-agent-admission/Cargo.toml` for declared `serde`,
  `serde_json`, and `sha2` requirements;
- `Cargo.lock` for the resolved `serde_json` and `sha2` packages;
- the resolved `serde` and derive implementation used by the build.

### Local observation anchors

- `docs/657-phase-hsai-tiny-z3-gateway-digest-binding-local-execution-notes.md`;
- `docs/658-phase-hsai-tiny-z3-gateway-digest-binding-local-replay-residual-ceiling-report.md`.

The Phase 657 and Phase 658 records are comparison inputs only. They do not
establish production source correspondence.

## Source-Bound Encoding Contract

The Phase 660 regression surface must lock all of these current behaviors:

1. The outer value is a two-element tuple serialized as a JSON array.
2. The first element is exactly
   `hsai-agent-admission:gateway-action-proposal:v1`.
3. The second element is the complete `GatewayActionProposal` value.
4. Struct fields are emitted by the current derived serializer in source
   declaration order.
5. Newtype string fields are emitted using their current transparent Serde
   representation.
6. Unit enum variants use the current externally tagged Serde representation.
7. `Hash([u8; 32])` values use the current fixed-array representation.
8. `BTreeSet` values are traversed in Rust `Ord` order and serialized as JSON
   arrays in that order.
9. `u64` values use the current `serde_json` integer representation.
10. Boolean values use JSON `true` and `false`.
11. Strings use the current `serde_json` UTF-8 and escaping behavior.
12. `serde_json::to_vec` contributes no caller-added whitespace or newline.
13. SHA-256 consumes exactly the returned byte vector, with no hex encoding,
    prefix, suffix, or intermediate text conversion.

These rules describe the current source implementation. Golden vectors are
required because prose alone does not prove the emitted bytes.

## Supported First Property Set

The first correspondence effort is deliberately narrower than arbitrary
gateway semantics.

### P659-A Preimage determinism

For one valid, fixed proposal value and the locked source/dependency instance,
two calls to the production preimage helper return identical bytes.

### P659-B Production digest agreement

For the same proposal, `GatewayActionProposal::digest` equals SHA-256 of the
bytes returned by the production preimage helper.

### P659-C Concrete field sensitivity

For locked non-secret fixtures, mutations to each selected proposal field must
produce the expected changed preimage and concrete changed digest. At minimum,
the fixture set must cover:

- `id`;
- `subject`;
- `action_kind`;
- `target`;
- `value_units`;
- `source_artifact_digests`;
- `nonclaims`;
- every `model_lane` field;
- `threat_labels`;
- `direct_authority_requested`;
- `signer_or_tool_requested_before_admission`.

A finite concrete mutation test is not a theorem that every unequal proposal
has a different SHA-256 digest.

### P659-D Set insertion-order independence

For equal `BTreeSet` contents constructed in different insertion orders, the
production preimage and digest must match.

### P659-E Encoding edge vectors

Golden vectors must cover empty and nonempty collections, enum variants,
newtypes, maximum `u64`, quotes, reverse solidus, control-character escaping,
and non-ASCII UTF-8 input. Each vector records both exact preimage bytes and
the resulting digest.

## Correspondence Ladder

Each stage is cumulative. A later stage cannot silently omit an earlier
source binding.

### C0 Source inventory

Bind the exact source commit, files, symbols, dependency lock, property id,
nonclaim set, and prior local observations.

Phase 659 completes the boundary for this stage but does not create a
machine-checked correspondence certificate.

### C1 Production preimage witness

Expose one narrowly named pure-data helper for the exact production preimage,
route `GatewayActionProposal::digest` through it, and lock byte-for-byte
behavior with golden and adversarial tests.

This is the authorized target for Phase 660. It is regression evidence, not a
formal proof.

### C2 Independent preimage checker

Use an independently implemented local checker to recompute the selected
fixture encodings and digests. The checker must disclose whether it shares
Serde, `serde_json`, `sha2`, Rust types, or code with the production path.
Shared dependencies remain shared trust, not independent verification.

### C3 Bounded theorem or extraction

Model or extract a small supported subset using Lean directly or a
Rust-to-Lean path such as Aeneas or Hax. The package must disclose:

- every unsupported Rust or Serde construct;
- every manual replacement;
- the exact modeled proposal subset;
- serializer assumptions;
- SHA-256 assumptions;
- axioms, admitted lemmas, `sorry`, or unchecked code;
- the theorem statement and its source-anchor coverage.

At this stage, an SMT or COBALT-inspired lane may check a reduced relation or
produce counterexamples, but it is not the authority for Rust/Serde source
correspondence.

### C4 Verified primitive closure

Close or replace the imported serialization and SHA-256 assumptions with
separately checked implementations and explicit composition theorems.

C4 is not authorized by Phase 659 and is not required before local C1 testing.

## Backend Selection

The ranked path after C1 is:

1. Lean or Rust-to-Lean for a bounded preimage model and composition theorem.
2. An independent byte-level checker for golden-vector reproduction.
3. SMT or COBALT-inspired checks for reduced mutation and containment
   relations with explicit hash abstraction.
4. Repository-scale proof automation only after one theorem and its source
   correspondence package pass locally without admitted gaps.

COBALT is useful for scoped solver-backed security properties. It does not
replace the missing Rust/Serde correspondence argument for this digest path.
More identical Z3 runs also do not close that gap.

## Required Correspondence Package

A future C2 or C3 package must contain or bind:

- package schema version and id;
- property id and exact theorem or checker statement;
- source commit;
- source file paths and SHA-256 digests;
- source symbol anchors;
- Rust toolchain and dependency lock digest;
- digest tag;
- proposal schema digest;
- golden-vector manifest digest;
- exact preimage-byte digests;
- expected production digests;
- backend name, version, executable digest, and command policy;
- modeled or extracted source digest;
- assumptions and unsupported-feature report;
- proof, checker, or solver status;
- artifact and transcript digests, when a later phase authorizes them;
- independent replay instructions;
- review decision;
- explicit evidence class and claim boundary;
- explicit nonclaims and nonclaim digest.

The package must fail closed when source, dependency, schema, tag, fixture,
preimage, theorem, assumption, backend, artifact, or nonclaim bindings drift.

## Failure Taxonomy

The next phases must distinguish at least:

- source anchor missing or stale;
- source commit or file digest drift;
- dependency lock drift;
- digest tag drift;
- proposal field-set drift;
- struct field-order drift;
- newtype representation drift;
- enum representation drift;
- set ordering drift;
- integer representation drift;
- string escaping or UTF-8 drift;
- golden preimage mismatch;
- production helper and `digest` disagreement;
- SHA input mismatch;
- expected digest mismatch;
- unsupported extraction construct;
- undisclosed manual model replacement;
- undisclosed imported assumption;
- admitted or unchecked theorem dependency;
- checker dependency overlap mislabeled as independence;
- proof or checker artifact bound to stale source;
- evidence-class or claim-boundary promotion attempt.

No failure may be normalized into a successful correspondence result.

## Phase 660 Authorized Target

Phase 660 may be proposed as the first code slice with this exact scope:

- add one constant for the production digest tag;
- add one narrowly named pure-data function that returns the exact
  `GatewayActionProposal` digest preimage bytes;
- route `GatewayActionProposal::digest` through that preimage without changing
  the returned digest;
- add exact golden preimage and digest vectors;
- add deterministic, set-order, field-mutation, tag, and encoding-edge tests;
- document the public helper if it is public;
- retain the current dependency set and evidence ceiling.

Phase 660 must not add a process API, backend adapter, proof assistant setup,
external repository, generated proof artifact, accepted evidence path, or
claim promotion.

## Anti-Goals

Phase 659 does not permit or create:

- Rust implementation changes;
- Cargo metadata or dependency changes;
- generated preimage, proof, checker, or solver artifacts;
- filesystem output bundles;
- external repository clones or vendored source;
- network access;
- Lean, Aeneas, Hax, Rust-to-Lean, SMT, Z3, COBALT, Coq, TLA+, CBMC,
  DeepProve, zkML, or model-checker execution;
- a proof artifact, checker transcript, or solver certificate;
- accepted Evidence Ledger mutation;
- accepted evidence or accepted formal evidence;
- independent external reproduction;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, or external-audit claims;
- human-review acceptance;
- global software-agent uniqueness;
- authority to execute an action.

## Exit Criteria

Phase 659 is complete when:

- the current production digest path is named exactly;
- its source and dependency anchors are identified;
- source-bound encoding behavior is distinguished from canonical JSON;
- the first bounded property set is defined;
- the C0 through C4 correspondence ladder is explicit;
- backend responsibilities and assumptions are separated;
- the failure taxonomy is explicit;
- Phase 660 has one narrow implementation target;
- all repository claim-boundary documentation gates pass.

## Defensible Claim

```text
HSAI defines a source-specific correspondence boundary for the current
GatewayActionProposal digest preimage and a gated path to expose and
regression-lock that preimage before formal backend modeling or extraction.
```

It does not justify:

```text
HSAI proved its production proposal digest implementation.
HSAI proved SHA-256 or Serde correctness.
HSAI has accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI is semantically correct.
HSAI is production ready.
HSAI is SOTA.
HSAI is fully secure.
```

## Phase 660 Implementation Status

Phase 660 implements C1 in
`docs/660-phase-hsai-gateway-proposal-digest-production-preimage-witness-notes.md`.
It exposes the exact production preimage helper, routes
`GatewayActionProposal::digest` through that helper, locks one complete golden
byte vector and digest, covers 18 concrete field mutations, checks ordered-set
construction equivalence, and covers tag and encoding edges. It remains local
regression evidence and runs no formal backend.

## Next Responsible Slice

Phase 661 defines the docs-first C2 checker boundary in
`docs/661-phase-hsai-gateway-proposal-digest-independent-preimage-checker-boundary.md`.
Phase 662 implements that checker in
`docs/662-phase-hsai-gateway-proposal-digest-local-implementation-diverse-checker-notes.md`.
Phase 663 defines the C3 theorem and extraction boundary in
`docs/663-phase-hsai-gateway-proposal-preimage-c3-theorem-extraction-boundary.md`.
It selects one handwritten Lean set-permutation theorem over the Phase 662
checker model and pins the Lean release. Phase 664 implements and locally
kernel-checks that theorem at `Level1LocalReplayOrLower`; the handwritten
model-to-source correspondence assumption remains open.

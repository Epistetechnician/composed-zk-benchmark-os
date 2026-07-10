# Phase 660 HSAI Gateway Proposal Digest Production Preimage Witness Notes

State slice:
`phase-660-hsai-gateway-proposal-digest-production-preimage-witness`.

## Status

Implemented and locally validated for C1 of the Phase 659 correspondence
ladder.

Phase 660 exposes and regression-locks the exact bytes hashed by the current
production `GatewayActionProposal::digest` path. It does not run a formal
backend and does not create formal evidence.

The evidence ceiling remains `Level1LocalReplayOrLower`.

## Implemented Surface

Phase 660 adds two public source anchors in
`crates/hsai-agent-admission/src/lib.rs`:

- `GATEWAY_ACTION_PROPOSAL_DIGEST_TAG`;
- `gateway_action_proposal_digest_preimage`.

The production path is now explicit:

```text
gateway_action_proposal_digest_preimage(proposal)
  = serde_json::to_vec(&(
      GATEWAY_ACTION_PROPOSAL_DIGEST_TAG,
      proposal,
    ))

GatewayActionProposal::digest(proposal)
  = SHA-256(gateway_action_proposal_digest_preimage(proposal))
```

The tag remains exactly:

```text
hsai-agent-admission:gateway-action-proposal:v1
```

The existing generic `hash_tagged` helper was not changed. A focused test
asserts that the new production path returns the same digest as the former
`hash_tagged(tag, proposal)` expression for the locked golden fixture.

This is a source refactor and regression seam. It is not a portable
canonical-JSON implementation.

## Locked Golden Vector

The first golden fixture locks:

- proposal id `phase660-action`;
- subject `agent-phase660`;
- action kind `Payment`;
- target `treasury-safe`;
- value `50`;
- empty source-artifact, nonclaim, and threat-label sets;
- deterministic model-lane provenance;
- fixed `[1; 32]`, `[2; 32]`, and `[3; 32]` model-lane digests;
- both authority-request flags set to `false`.

The test embeds the complete expected UTF-8 JSON byte string and locks this
SHA-256 digest:

```text
52de11c37c1492b7c9fb7c42660d693f5a7cbc6ed69f3bb371d66ad2686938fa
```

The test requires:

- repeated preimage calls return identical bytes;
- emitted bytes equal the complete embedded golden string;
- the production digest equals the locked digest;
- the production digest equals SHA-256 of the exposed preimage;
- the production digest equals the prior generic tagged-hash expression.

## Concrete Field Coverage

One focused test mutates each selected field independently from a non-secret
baseline and requires both the preimage and concrete digest to change.

The 18 mutation labels are:

1. `id`
2. `subject`
3. `action_kind`
4. `target`
5. `value_units`
6. `source_artifact_digests`
7. `nonclaims`
8. `model_lane.lane_kind`
9. `model_lane.model_family`
10. `model_lane.artifact_id`
11. `model_lane.runtime`
12. `model_lane.prompt_template_digest`
13. `model_lane.input_corpus_digest`
14. `model_lane.output_bundle_digest`
15. `model_lane.non_secret`
16. `threat_labels`
17. `direct_authority_requested`
18. `signer_or_tool_requested_before_admission`

These are concrete regression observations. They do not prove that SHA-256 is
injective or collision-free for arbitrary proposals.

## Ordering And Encoding Coverage

The focused suite also locks:

- equal `source_artifact_digests` built in opposite insertion orders;
- equal `nonclaims` built in opposite insertion orders;
- equal `threat_labels` built in opposite insertion orders;
- all seven `GatewayActionKind` unit variants;
- all five `GatewayModelLaneKind` unit variants;
- all fourteen `GatewayThreatLabel` unit variants;
- quotes;
- reverse solidus;
- newline, tab, and null-character escaping;
- non-ASCII UTF-8;
- nonempty source-artifact, nonclaim, and threat-label sets;
- `u64::MAX` JSON encoding;
- an alternate v2 tag producing different bytes and a different concrete
  digest.

The set-order test first requires the independently constructed Rust proposal
values to be equal, then requires equal preimages and equal digests.

## Focused Validation

Executed:

```bash
cargo test -p hsai-agent-admission phase660 -- --nocapture
```

Observed result:

```text
4 passed
0 failed
```

The four focused test groups are:

- exact golden bytes and prior-path digest agreement;
- 18 concrete field mutations;
- `BTreeSet` insertion-order independence;
- tag, encoding, integer, collection, and enum edges.

Full modified-crate validation:

```bash
cargo test -p hsai-agent-admission --lib --quiet
cargo clippy -p hsai-agent-admission --all-targets -- -D warnings
```

Observed results:

```text
675 passed
0 failed
5 ignored
clippy passed with warnings denied
```

No Phase 660 test invokes a process, network, solver, proof assistant, checker,
or model backend.

## Residual Assumptions

Phase 660 leaves these assumptions open:

- correctness of the Rust compiler and selected toolchain;
- correctness of Serde derives;
- correctness and stability of the locked `serde_json` implementation;
- correctness of the `sha2` SHA-256 implementation;
- collision resistance of SHA-256;
- completeness of the finite fixture and mutation set;
- correspondence with any future independent checker;
- correspondence with any future Lean or Rust-to-Lean model;
- absence of future source or dependency drift.

Changing the proposal schema, field order, Serde attributes, digest tag,
dependency lock, or preimage helper invalidates the current golden binding and
must fail the regression suite before any later correspondence package is
accepted.

## Evidence Meaning

Phase 660 establishes this bounded local fact:

```text
The current production GatewayActionProposal digest consumes an exposed,
source-bound Serde JSON preimage, and focused local regression tests lock one
complete golden vector plus selected field, ordering, tag, and encoding cases.
```

It does not establish:

- a formal theorem about the Rust implementation;
- canonical JSON across implementations;
- arbitrary proposal digest injectivity;
- SHA-256 correctness or collision resistance;
- an independent implementation result;
- Lean or Rust-to-Lean source correspondence;
- solver or checker authority;
- gateway semantic correctness;
- whole-system security.

## Nonclaims

Phase 660 does not permit or create:

- Cargo metadata or dependency changes;
- binaries, scripts, or process APIs;
- external repository clones or vendored source;
- network access;
- Lean, Aeneas, Hax, Rust-to-Lean, SMT, Z3, COBALT, Coq, TLA+, CBMC,
  DeepProve, zkML, or model-checker execution;
- generated proof artifacts;
- checker transcripts;
- solver certificates;
- filesystem evidence bundles;
- accepted Evidence Ledger mutation;
- accepted evidence or accepted formal evidence;
- independent external reproduction;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, external-audit, or human-review-acceptance claims;
- global software-agent uniqueness;
- authority to execute an action.

## Defensible Claim

```text
HSAI exposes and regression-locks the exact source-bound production preimage
for GatewayActionProposal::digest with one complete golden vector, prior-path
digest agreement, 18 concrete field mutations, ordered-set equivalence, and
encoding-edge coverage.
```

The defensible claim remains local regression evidence only.

## Phase 661 Boundary Status

Phase 661 defines the C2 checker boundary in
`docs/661-phase-hsai-gateway-proposal-digest-independent-preimage-checker-boundary.md`.
It selects a separate dependency-isolated checker crate, checker-owned model,
manual schema encoder, distinct `ring` SHA-256 implementation, explicit
independence profile, cross-implementation harness, and fail-closed test plan.
No checker is implemented or run in Phase 661.

## Next Responsible Slice

Phase 662 implements the bounded local checker and e2e comparison in
`docs/662-phase-hsai-gateway-proposal-digest-local-implementation-diverse-checker-notes.md`.
Phase 663 defines the C3 handwritten-Lean theorem and extraction boundary in
`docs/663-phase-hsai-gateway-proposal-preimage-c3-theorem-extraction-boundary.md`
without executing it. Phase 664 is the first eligible Lean implementation and
local kernel-check slice.

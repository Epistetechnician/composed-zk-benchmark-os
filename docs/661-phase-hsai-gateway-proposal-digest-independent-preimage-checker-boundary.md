# Phase 661 HSAI Gateway Proposal Digest Independent Preimage Checker Boundary

State slice:
`phase-661-hsai-gateway-proposal-digest-independent-preimage-checker-boundary`.

## Status

Complete for the documentation-first C2 checker boundary.

Phase 661 defines a future implementation-diverse local checker for the Phase
660 production preimage surface. It does not implement or run that checker.

The evidence ceiling remains `Level1LocalReplayOrLower`.

## Decision

The future checker must be a separate workspace crate:

```text
crates/hsai-gateway-digest-checker
```

with package name:

```text
hsai-gateway-digest-checker
```

Its library dependency graph must not include:

- `hsai-agent-admission`;
- `hsai-claim-envelope`;
- any other HSAI crate;
- `serde`;
- `serde_derive`;
- `serde_json`;
- `sha2`.

The checker must use:

- checker-owned proposal and enum types;
- a manual, schema-specific JSON byte encoder;
- explicit sort keys for source-artifact, nonclaim, and threat-label sets;
- `ring::digest` with `ring::digest::SHA256` for digest computation.

The current lock already contains `ring` `0.17.14`. Its declared minimum Rust
version is `1.66.0`, below the workspace Rust version `1.74`. Phase 661 does not
change dependency metadata or invoke `ring`.

## Correct Independence Label

The future successful classification is:

```text
LocalImplementationDiverseCheckerAgreement
```

It must not be labeled:

```text
IndependentExternalReproduction
IndependentFormalVerification
SourceCorrespondenceProof
```

The separate crate, manual encoder, and distinct SHA-256 implementation reduce
common implementation risk. They do not make the run independent of the Rust
compiler, workspace build, shared fixture literals, host, operator, or schema
transcription.

## Independence Profile

The future checker must report every axis separately.

### Diverse axes

- source crate and module;
- proposal model types;
- enum-to-string mapping code;
- struct field emission code;
- set ordering code;
- JSON string escaping code;
- integer and byte-array emission code;
- SHA-256 library implementation (`ring` instead of `sha2`);
- no call to the production preimage helper;
- no call to the production digest method;
- no Serde derive or `serde_json` serializer inside the checker library.

### Shared axes

- Rust language and compiler;
- Rust standard library;
- workspace toolchain and build host;
- CPU, operating system, and local operator;
- Phase 660 fixture values;
- digest tag and schema knowledge;
- human transcription of production field order and enum labels;
- the e2e comparison harness that observes both results.

### Imported trust

- correctness of `ring` and its native/assembly implementation path;
- correctness of the production `sha2` path;
- correctness of the Rust compiler and linker;
- correctness of the expected Phase 660 golden vector;
- collision resistance of SHA-256.

No aggregate `independent: true` flag is allowed. The report must preserve the
axis-level disclosure.

## Future Checker-Owned Model

The future checker crate may define only the model required for
`GatewayActionProposal` digest v1:

- `CheckerGatewayActionProposal`;
- `CheckerArtifactDigest`;
- `CheckerModelLaneProvenance`;
- `CheckerGatewayActionKind`;
- `CheckerGatewayModelLaneKind`;
- `CheckerGatewayThreatLabel`;
- fixed `[u8; 32]` digest values;
- checker-owned string newtypes where they make field roles explicit.

The checker model must not import, convert from, implement traits for, or
otherwise depend on production HSAI types. Cross-model construction belongs in
the e2e test harness, not in the checker library.

For set-valued fields, the checker input may use vectors, but the encoder must:

- reject duplicate source-artifact entries;
- reject duplicate nonclaim entries;
- reject duplicate threat-label entries;
- sort artifacts explicitly by id and then digest bytes;
- sort nonclaims explicitly by string value;
- sort threat labels by explicit v1 declaration ordinal;
- avoid relying on production `Ord` implementations.

## Manual Encoder Contract

The future encoder must expose an API equivalent to:

```text
encode_gateway_action_proposal_v1(
    proposal: &CheckerGatewayActionProposal,
) -> Result<Vec<u8>, CheckerError>
```

It must emit this outer shape:

```text
[
  "hsai-agent-admission:gateway-action-proposal:v1",
  { proposal fields in fixed v1 order }
]
```

The fixed proposal field order is:

1. `id`
2. `subject`
3. `action_kind`
4. `target`
5. `value_units`
6. `source_artifact_digests`
7. `nonclaims`
8. `model_lane`
9. `threat_labels`
10. `direct_authority_requested`
11. `signer_or_tool_requested_before_admission`

The fixed `model_lane` field order is:

1. `lane_kind`
2. `model_family`
3. `artifact_id`
4. `runtime`
5. `prompt_template_digest`
6. `input_corpus_digest`
7. `output_bundle_digest`
8. `non_secret`

The manual encoder must implement and test:

- JSON quote and reverse-solidus escaping;
- short escapes for backspace, tab, newline, form feed, and carriage return;
- `\u00xx` escaping for remaining control bytes below `0x20`;
- unchanged valid non-ASCII UTF-8;
- unquoted decimal `u64` values, including `u64::MAX`;
- lowercase JSON booleans;
- fixed-array decimal byte emission;
- compact separators with no whitespace or trailing newline;
- exact enum labels from the production v1 schema;
- fail-closed rejection of duplicate set inputs.

The checker must not parse or normalize production JSON before encoding. Its
purpose is to reproduce the bytes from an independent model, not to echo the
production preimage.

## Future Digest API

The future checker may expose an API equivalent to:

```text
check_gateway_action_proposal_digest_v1(
    proposal: &CheckerGatewayActionProposal,
) -> Result<CheckerDigestResult, CheckerError>
```

The minimal result contains:

- checker schema version;
- checker implementation id;
- digest tag;
- encoded preimage bytes;
- encoded preimage length;
- `ring` SHA-256 digest bytes;
- encoder identity;
- hash-provider identity;
- independence profile;
- shared-trust profile;
- claim boundary;
- explicit nonclaims.

The result is an in-memory local value. Phase 662 must not add filesystem
materialization or artifact promotion.

## E2E Comparison Harness

The cross-implementation comparison belongs in
`crates/hsai-e2e-harness`, which may depend on both the production admission
crate and the checker crate.

The harness must construct production and checker proposals separately from
the same explicit non-secret fixture literals. It must compare:

- production preimage bytes against checker preimage bytes;
- production digest bytes against checker digest bytes;
- Phase 660 golden bytes against both implementations;
- Phase 660 golden digest against both implementations;
- every reported independence and shared-trust axis against fixed policy.

The checker crate itself must never receive a production
`GatewayActionProposal`, production preimage, or production digest as an input
to its encoding or hashing API.

## Required Phase 662 Tests

The future implementation must include focused tests for:

1. the complete Phase 660 golden vector;
2. a standard SHA-256 known-answer vector through `ring`;
3. production/checker agreement for the golden fixture;
4. the 18 Phase 660 field mutations;
5. opposite construction orders for all three set-valued fields;
6. duplicate set-input rejection;
7. all seven action-kind labels;
8. all five model-lane-kind labels;
9. all fourteen threat-label labels;
10. quotes, reverse solidus, all JSON short control escapes, remaining control
    escapes, non-ASCII UTF-8, empty/nonempty collections, and `u64::MAX`;
11. digest-tag mismatch;
12. field-order mismatch;
13. enum-label mismatch;
14. preimage mismatch;
15. digest mismatch;
16. forbidden checker dependency detection;
17. attempted claim or evidence promotion.

The dependency test must fail if the checker manifest or source imports any
production HSAI crate, Serde crate, `serde_json`, or `sha2`.

## Failure Taxonomy

Phase 662 must distinguish at least:

- unsupported checker schema version;
- digest tag mismatch;
- duplicate source artifact;
- duplicate nonclaim;
- duplicate threat label;
- enum label mapping mismatch;
- set ordering mismatch;
- field ordering mismatch;
- string escaping mismatch;
- UTF-8 emission mismatch;
- integer emission mismatch;
- byte-array emission mismatch;
- checker preimage mismatch;
- checker digest mismatch;
- Phase 660 golden vector mismatch;
- production source anchor drift;
- dependency lock drift;
- forbidden checker dependency;
- missing independence-axis disclosure;
- false independence claim;
- evidence-class or claim-boundary promotion attempt.

No mismatch may be normalized into agreement.

## Future Phase 662 Touch Surface

Phase 662 may be proposed with this exact implementation surface:

- root `Cargo.toml` workspace membership;
- `Cargo.lock` changes caused by the new workspace package and direct locked
  `ring` dependency;
- `crates/hsai-gateway-digest-checker/Cargo.toml`;
- `crates/hsai-gateway-digest-checker/src/lib.rs`;
- focused checker tests under that crate;
- `crates/hsai-e2e-harness/Cargo.toml`;
- one focused cross-implementation contract test under
  `crates/hsai-e2e-harness/tests/`;
- dependency-boundary source-scan coverage;
- Phase 662 notes and required repository ledgers.

Phase 662 must not change production digest semantics, production proposal
types, the Phase 660 golden vector, or accepted-evidence policy.

## Phase 661 Anti-Goals

Phase 661 does not permit or create:

- Rust implementation code;
- workspace or Cargo metadata changes;
- dependency changes;
- checker crate creation;
- checker execution;
- scripts or binaries;
- process or network APIs;
- filesystem checker artifacts;
- external repository clones or vendored source;
- Lean, Aeneas, Hax, Rust-to-Lean, SMT, Z3, COBALT, Coq, TLA+, CBMC,
  DeepProve, zkML, or model-checker execution;
- proof artifacts;
- checker transcripts;
- solver certificates;
- independent external reproduction;
- independent formal verification;
- accepted Evidence Ledger mutation;
- accepted evidence or accepted formal evidence;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, external-audit, or human-review-acceptance claims;
- global software-agent uniqueness;
- authority to execute an action.

## Exit Criteria

Phase 661 is complete when:

- the future checker has one isolated ownership boundary;
- prohibited shared dependencies are explicit;
- the manual encoder contract is exact;
- the distinct SHA-256 provider is named and locally available;
- diverse, shared, and imported-trust axes are separated;
- the checker and e2e APIs are bounded;
- required tests and failure classes are explicit;
- Phase 662 has an exact file and dependency surface;
- evidence and claim promotion remain forbidden;
- repository documentation gates pass.

## Defensible Claim

```text
HSAI defines a docs-first C2 boundary for a local implementation-diverse
GatewayActionProposal preimage checker with separate model and encoding code,
a distinct SHA-256 implementation, explicit shared-trust disclosure, and
fail-closed production comparison requirements.
```

It does not justify:

```text
HSAI implemented or ran the independent checker.
HSAI independently verified the production digest.
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

Phase 662 should implement only the bounded local
`hsai-gateway-digest-checker` crate and cross-implementation e2e comparison.
It must stop after local implementation-diverse agreement or a classified
mismatch. C3 Lean or Rust-to-Lean work remains a later boundary.

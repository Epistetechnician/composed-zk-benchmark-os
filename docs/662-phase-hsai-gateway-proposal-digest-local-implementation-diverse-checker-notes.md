# Phase 662 HSAI Gateway Proposal Digest Local Implementation-Diverse Checker Notes

State slice:
`phase-662-hsai-gateway-proposal-digest-local-implementation-diverse-checker`.

## Status

Implemented and locally validated for C2 of the Phase 659 correspondence
ladder.

Phase 662 implements and runs a separate local checker for the Phase 660
production preimage and digest. The successful classification is:

```text
LocalImplementationDiverseCheckerAgreement
```

The evidence ceiling remains `Level1LocalReplayOrLower`.

## Checker Ownership

The checker is a separate workspace crate:

```text
crates/hsai-gateway-digest-checker
```

Its normal dependency tree is:

```text
hsai-gateway-digest-checker
└── ring 0.17.14
    ├── cfg-if 1.0.4
    ├── getrandom 0.2.17
    ├── libc 0.2.186
    └── untrusted 0.9.0
```

The checker crate does not depend on:

- `hsai-agent-admission`;
- `hsai-claim-envelope`;
- another HSAI crate;
- `serde`;
- `serde_derive`;
- `serde_json`;
- `sha2`.

The dependency boundary is enforced by a focused e2e source and manifest test.

## Implemented Checker Surface

The checker owns independent model types for:

- gateway action ids and subjects;
- artifact digests and nonclaims;
- action-kind, model-lane-kind, and threat-label enums;
- model-lane provenance;
- the complete gateway action proposal v1 shape.

The main APIs are:

```text
encode_gateway_action_proposal_v1
checker_sha256
check_gateway_action_proposal_digest_v1
validate_checker_digest_result
```

The checker result binds:

- schema version;
- Phase 662 state slice;
- checker implementation id;
- digest tag;
- exact encoded preimage bytes and length;
- `ring` SHA-256 digest bytes;
- encoder and hash-provider identities;
- diverse, shared, and imported-trust axes;
- claim boundary;
- explicit nonclaims.

The validator recomputes the checker result and rejects schema, state,
implementation, tag, preimage, length, digest, encoder, hash-provider,
independence-profile, claim-boundary, and nonclaim drift.

## Manual Encoder

The checker does not call the production preimage or digest implementation.
It manually emits the complete v1 JSON byte sequence with:

- fixed outer tag/proposal array shape;
- fixed proposal and model-lane field order;
- explicit enum labels;
- explicit artifact ordering by id and digest bytes;
- explicit nonclaim ordering by string value;
- explicit threat-label ordering by v1 declaration ordinal;
- duplicate rejection for all three set-valued inputs;
- quote and reverse-solidus escaping;
- short JSON control escapes;
- `\u00xx` emission for remaining control bytes;
- unchanged valid non-ASCII UTF-8;
- decimal `u64` and byte-array emission;
- compact separators with no whitespace or trailing newline.

The checker then hashes those bytes using `ring::digest::SHA256`, distinct from
the production `sha2` implementation.

## Independence Profile

The result records seven diverse axes:

1. separate source crate and module;
2. checker-owned proposal and enum types;
3. manual field emission and enum mapping;
4. manual set ordering and JSON string escaping;
5. `ring` SHA-256 instead of production `sha2`;
6. no production preimage or digest call;
7. no Serde derive or `serde_json` serializer.

It also records eight shared axes:

1. Rust language and compiler;
2. Rust standard library;
3. workspace toolchain and build host;
4. CPU, operating system, and local operator;
5. Phase 660 fixture values;
6. digest tag and schema knowledge;
7. human schema transcription;
8. e2e comparison harness.

Five imported-trust axes remain:

1. `ring` native and assembly implementation correctness;
2. production `sha2` implementation correctness;
3. Rust compiler and linker correctness;
4. Phase 660 golden vector correctness;
5. SHA-256 collision resistance.

No aggregate independent-verification flag exists.

## Checker Test Result

Executed:

```bash
cargo test -p hsai-gateway-digest-checker --tests -- --nocapture
```

Observed result:

```text
5 passed
0 failed
```

The checker tests cover:

- the complete Phase 660 preimage and digest golden vector;
- the standard SHA-256 `abc` known-answer vector;
- explicit set ordering and duplicate rejection;
- all action, model-lane, and threat enum labels;
- JSON escaping, UTF-8, nonempty collections, and `u64::MAX`;
- fail-closed metadata, digest, trust-profile, claim, and nonclaim validation.

## Cross-Implementation Result

Executed:

```bash
cargo test -p hsai-e2e-harness --test gateway_proposal_digest_checker_contract -- --nocapture
```

Observed result:

```text
7 passed
0 failed
```

The e2e harness constructs production and checker proposals separately from
the same explicit non-secret literals. It observed exact preimage and digest
agreement for:

- the complete Phase 660 golden fixture;
- all 18 Phase 660 field mutations;
- opposite input orders for all three set-valued fields;
- all seven action-kind variants;
- all five model-lane-kind variants;
- all fourteen threat-label variants;
- quotes, reverse solidus, all short control escapes, a remaining control
  escape, non-ASCII UTF-8, nonempty collections, and `u64::MAX`.

The seventh e2e test runs 256 generated differential cases over arbitrary
bounded Rust strings, `u64` values, digest arrays, enum choices, nonempty set
values, and authority flags. Failure-file persistence is disabled so this
hermetic lane does not write source-adjacent artifacts.

The harness also rejects altered tag, production preimage, production digest,
independence profile, claim boundary, and explicit nonclaims. The checker
manifest/source scan rejects prohibited production, Serde, `serde_json`, and
`sha2` coupling.

The locked golden digest remains:

```text
52de11c37c1492b7c9fb7c42660d693f5a7cbc6ed69f3bb371d66ad2686938fa
```

## Workspace Validation

Executed:

```bash
cargo test --workspace --quiet
cargo clippy --workspace --all-targets -- -D warnings
```

Observed result: both commands passed.

## Exact Meaning

Phase 662 establishes this bounded local observation:

```text
The production Serde/sha2 GatewayActionProposal digest and a separate manual
encoder/ring checker produced identical preimage and SHA-256 bytes for the
Phase 660 golden fixture, 18 concrete mutations, set-order cases, every enum
variant, selected encoding edges, and 256 generated differential cases in one
shared Rust workspace environment.
```

This is stronger than one implementation testing itself. It is still not
independent external reproduction because the run shares the Rust compiler,
workspace, fixture literals, host, operator, and comparison harness.

## Residual Assumptions

Phase 662 leaves open:

- arbitrary-input equivalence beyond the finite test corpus;
- formal source correspondence;
- correctness of both SHA-256 implementations;
- correctness of the manual encoder;
- correctness of the production Serde encoder;
- compiler, linker, operating-system, and hardware correctness;
- independence from fixture transcription errors;
- external reproduction on a separate implementation and environment;
- proof of SHA-256 collision resistance;
- C3 Lean or Rust-to-Lean theorem coverage.

## Nonclaims

Phase 662 does not permit or create:

- changes to production digest semantics or proposal types;
- process or network APIs;
- scripts or binaries;
- filesystem checker artifacts;
- external repository clones or vendored source;
- Lean, Aeneas, Hax, Rust-to-Lean, SMT, Z3, COBALT, Coq, TLA+, CBMC,
  DeepProve, zkML, or model-checker execution;
- proof artifacts;
- committed checker transcripts;
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

## Defensible Claim

```text
HSAI has local implementation-diverse agreement between its production
GatewayActionProposal Serde/sha2 digest and a dependency-isolated manual
encoder/ring checker across one complete golden vector, 18 field mutations,
set-order cases, all enum variants, selected encoding edges, and 256 generated
differential cases, with explicit shared-trust and nonclaim disclosure.
```

It does not justify:

```text
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

Phase 663 defines the docs-first C3 bounded theorem and extraction boundary in
`docs/663-phase-hsai-gateway-proposal-preimage-c3-theorem-extraction-boundary.md`.
It selects one handwritten Lean theorem for duplicate-free permutation
invariance of the three set-valued checker inputs, excludes SHA-256 and
production Serde, pins the future Lean release, and fixes the source,
correspondence, artifact, failure, and nonpromotion contracts. Phase 664 is the
implemented local Lean kernel-check slice. Its theorem covers duplicate-free
set permutation invariance in the handwritten checker model only; it does not
prove arbitrary-input checker/production equivalence or source correspondence.

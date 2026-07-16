# Statebook P1 Core Semantic Fixtures Boundary

Date: 15 July 2026.

Status: docs-first implementation authorization.

Named state slice: `statebook-p1-core-semantic-fixtures-boundary`.

Future implementation state slice: `statebook-p1-core-semantic-fixtures`.

Evidence ceiling: local fixture-backed regression evidence only.

## Decision

P1 may implement one isolated Rust crate, `crates/statebook-core`, that parses a
closed synthetic terminal-contract source schema, validates a closed
normalization profile, reports semantic completeness, lowers only complete
inputs into an opaque normalized contract, and derives `StateKeyV1` from a
frozen canonical binary preimage.

This phase exists to falsify false equivalence before any execution, capital,
settlement, assurance, or recovery machinery exists. A matching key establishes
only equality under the shipped V1 semantic schema. It does not establish
economic, executable, legal, or operational fungibility.

## Authorized repository surface

The future implementation may touch only:

- `crates/statebook-core/Cargo.toml`;
- Rust source under `crates/statebook-core/src/`;
- Rust integration tests and small JSON fixtures under
  `crates/statebook-core/tests/`;
- root `Cargo.toml` workspace membership and the resulting `Cargo.lock` update;
- `docs/statebook-p1-core-semantic-fixtures-implementation-notes.md`;
- the four standard mirrors: `README.md`, `AGENTS.md`,
  `docs/12-task-list.md`, and
  `docs/90-whole-codebase-validation-report.md`.

The publication sources, media, and PDFs are immutable in P1. Existing HSAI and
`zkbench-core` source semantics are outside this state slice.

## Closed P1 domain

The normalized terminal semantic record must bind:

- economic-reference namespace, identifier, unit, benchmark administrator,
  methodology version and SHA-256, fallback rule, calendar, and timezone;
- observation start and end, sampling rule, disruption rule, and correction
  rule;
- one indicator payoff with an exact rational amount and one of `<`, `<=`,
  `=`, `>=`, `>`, or a bounded range with explicit endpoint inclusion;
- settlement asset, strictly positive unit scale, rounding mode and strictly
  positive quantum, deadline, dispute rule, default rule, governing rule, and
  finality domain;
- a canonically ordered set of explicit non-equivalences.

Source lineage remains separate: venue namespace, contract id, revision,
source-observation time, exact raw-source SHA-256, and normalization-profile
id, version, and digest. Source lineage must not enter `StateKeyV1`. Different
sources that lower to byte-identical normalized semantics must converge on the
same state key while retaining distinct lineage receipts.

Fixed, linear, option, perpetual, path-dependent, physical-delivery, basket,
barrier, American-exercise, and discretionary-resolution forms remain
unsupported. P1 does not evaluate even the supported indicator payoff.

## Validation and completeness

The source and profile parsers must reject duplicate JSON keys before ordinary
deserialization can overwrite them. Unknown schema versions, unknown fields,
JSON numeric values in exact-arithmetic positions, non-ASCII or ambiguous
semantic identifiers, missing mappings, duplicate mappings, uncertain
transforms, malformed digests, invalid timestamps, unordered ranges, zero
denominators, excessive scale, and checked-arithmetic overflow fail closed.

Semantic completeness has exactly three states:

- `Complete`: every mandatory term is known and supported;
- `Incomplete`: one or more mandatory terms are absent;
- `Unknown`: one or more terms or mapping decisions are explicitly unresolved.

Only `Complete` may create an opaque `ValidatedContract`. Missing, unknown,
unsupported, contradictory, malformed, or overflowed inputs must never receive
a state key.

## Exact arithmetic

V1 uses no floating point. Decimal source values are strings with a maximum
scale of 18. Trailing decimal zeros are removed, and zero has one canonical
representation. Signed rationals use an `i128` numerator and nonzero `u128`
denominator, reduced by greatest common divisor without overflowing on
`i128::MIN`. Arithmetic is checked; no saturation, implicit rounding, unit
conversion, or currency conversion is permitted.

## StateKeyV1

The preimage is not JSON. It is a frozen tagged-length-value stream:

```text
domain = b"statebook:state-key:v1\0"
schema = u16 big-endian
field  = u16 tag || u32 length || value bytes
```

Strings are exact validated ASCII bytes; digests are raw 32-byte values;
integers use fixed-width big-endian encoding; enums use fixed one-byte
discriminants; sets use a count plus lexicographically sorted encoded members.
Every normalized economic, observation, payoff, settlement, and explicit
non-equivalence field is included. Venue, source id, revision, observed-at time,
raw-source digest, and profile identity are excluded.

`StateKeyV1 = SHA256(canonical_preimage_v1)`.

Opaque validated types must not implement `Deserialize`. Construction occurs
only through validation and lowering. The receipt may expose immutable semantic
and lineage getters plus canonical preimage bytes for audit and golden-vector
testing.

## Required fixtures and tests

P1 must ship:

- one complete baseline source and one complete normalization profile;
- one-field material mutations covering benchmark, observation, comparator,
  payoff, settlement, finality, and non-equivalence terms;
- missing, unknown, unsupported, malformed, duplicate-key, JSON-number,
  arithmetic, timestamp, and ordering negatives;
- source-field reorder and set-permutation invariance tests;
- source and profile lineage changes that preserve normalized semantics and the
  state key while changing the relevant lineage receipt;
- a frozen golden preimage and state key;
- a test-only independently written encoder using a different SHA-256 library,
  without production encoding or digest helpers;
- source scans preventing network clients, credentials, process spawning,
  filesystem writes, unsafe code, floating-point finance, HSAI imports,
  residual engines, or settlement authority.

The second encoder is implementation-diverse local regression evidence. It is
not an independent audit or proof.

## Acceptance gates

The implementation slice is complete only when these pass:

```text
cargo fmt --all -- --check
cargo test -p statebook-core --all-features
cargo clippy -p statebook-core --all-targets --all-features -- -D warnings
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
git diff --check
```

The root has no `package.json` or `pnpm-lock.yaml`; therefore no pnpm command is
available to run. No npm command is authorized.

## Nonclaims and hard stops

P1 creates no payoff or residual computation; no book or execution model; no
capital or margin recognition; no oracle or benchmark truth; no custody,
signing, pause, transfer, settlement, or value movement; no legal equivalence or
finality; no HSAI evidence mapping; no network, credentials, process spawning,
or filesystem writes; no accepted Evidence Ledger mutation; no benchmark
output; and no Level2+, semantic-correctness, production-readiness, SOTA, proof,
independent-verification, external-audit, or full-security claim.

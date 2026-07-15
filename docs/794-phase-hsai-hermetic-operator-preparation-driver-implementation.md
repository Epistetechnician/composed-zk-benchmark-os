# Phase 794 HSAI Hermetic Operator Preparation Driver Implementation

## Status

Implemented and locally validated.

State slice:
`phase-794-hsai-hermetic-operator-preparation-driver-implementation`.

Classification:
`HermeticOperatorPreparationDriverImplementedFixtureCorrespondenceOnly`.

Execution status: `LocalValidationOnly`. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Result

Phase 794 implements the Phase 793 in-memory preparation driver in
`hsai-native-transcript-preparation`. The public entrypoint accepts exactly one
`PreparationDriverRequest` and has no collector, fact, output-root, callback,
command, process, network, environment, or filesystem-write input.

The production path validates request shape and bounded subject bytes, computes
the compact request identity, validates all eight source receipts and exact
subject bindings, checks two strict source-manifest schemas, verifies raw
low-S ES256 signatures against caller-selected fixture profiles, and directly
dispatches the Phase 792 descriptor-relative collector in
`HostExecutableRole::ALL` order. It never authorizes materialization or capture.

No production success run occurred. The pinned Aeneas archive is not committed,
and Phase 794 does not acquire it. Complete success and failure routing are
tested through a private `cfg(test)` subject-binding table and collector closure
that are absent from the public API and non-test builds.

## Implemented Surface

The implementation adds:

- the eleven-value `SourceSubjectClass` and exact eight-class input order;
- strict receipt body, receipt envelope, fixture-profile, Rust-manifest,
  Charon-manifest, request, request-identity, decision, issue, and pre-identity
  rejection types;
- `evaluate_preparation_driver(&PreparationDriverRequest)` as the sole public
  production entrypoint;
- compact JSON serialization and byte-identical canonical request
  deserialization;
- named signature-preimage and envelope, profile, request-identity, fact, and
  decision digest helpers;
- exact identifier, printable source-authority, lowercase hexadecimal, and
  calendar-valid second-resolution UTC parsing;
- pre-digest size gates over receipt/profile wire strings and bounded typed
  machine-policy shape/serialization;
- raw 64-byte `r || s` ES256 verification through pinned `p256 0.13.2`;
- disabled `p256` default PEM/PKCS8 features, leaving only the required `ecdsa`
  feature and preserving the locked Rust 1.74 dependency lane;
- pinned the already-transitive `zeroize` lock entry to `1.8.1`, because
  `zeroize 1.9.0` uses an edition-2024 manifest that Cargo 1.74 cannot parse;
- explicit compressed SEC1, key-digest, invalid-scalar, high-S, wrong-key, and
  invalid-signature rejection;
- exact profile census: profile key IDs equal the distinct receipt key-ID set,
  profile IDs are unique, profiles are key-ID ordered, and each allowed class
  list equals the ordered classes actually signed by that key;
- exact Phase 668 seven-component Rust manifest checks and exact Phase 670
  five-path Charon manifest path/hash checks;
- direct concrete Phase 792 collection with no public injection point; and
- ordered successful fact-digest prefixes that exclude a rejected fact.

## Canonical Resolution Choices

Phase 794 freezes implementation details that do not widen Phase 793:

1. Decision digests are produced by the non-circular
   `preparation_driver_decision_sha256` helper and are not embedded in the
   decision itself.
2. Pre-identity checks use deterministic first-failure order: request schema,
   identifiers, timestamps, receipt census/order/duplicates, profile
   census/order/duplicates, then subject bounds.
3. After request identity exists, semantic issues accumulate, sort by stage,
   then `None` before concrete subject class, then code declaration order, and
   deduplicate.
4. Charon file byte lengths remain positive signed correspondence declarations.
   Phase 670 pins paths and hashes but not lengths, and Phase 794 has no source
   tree from which to authenticate those declarations.
5. Timestamp year `0000`, fractional seconds, offsets, leap seconds, invalid
   Gregorian dates, zero-length windows, and evaluation at expiry reject.
6. Private test collector injection covers deterministic success and failure;
   the production entrypoint calls `collect_executable_identity_fact` directly.
7. A fact that fails post-collection binding contributes no digest to the
   successful prefix.
8. Every `request_shape` pre-identity rejection carries a null subject class;
   every `subject_bounds` rejection identifies the exact bounded class.
9. Private registry and Aeneas bindings substitute only test fixture lengths
   and expected digests, preserving production length-before-digest routing.

These resolutions create no reviewer trust root. A profile proves only that a
signature corresponds to a caller-selected fixture key.

## Validation

The focused suite contains 50 tests:

- 26 library unit tests, including 11 Phase 792 collector tests and 15 Phase 794
  driver tests;
- 9 public descriptor-relative collector tests;
- 7 public operator-preparation driver tests; and
- 8 preparation-candidate tests.

Phase 794 coverage includes deterministic complete fixture correspondence,
golden domain digests, every unsigned receipt field, every subject byte object,
many-receipts-to-one-profile behavior, exact profile census, strict JSON,
calendar and window boundaries, malformed/wrong/high-S signatures, key encoding
and digest errors, collector failure, fact mismatch, successful-prefix rules,
one-argument public API shape, production-binding non-injectability, and source
scans for forbidden execution and I/O surfaces.

Required gates are:

```text
cargo fmt --all -- --check
cargo test -p hsai-native-transcript-preparation
cargo clippy -p hsai-native-transcript-preparation --all-targets -- -D warnings
cargo +1.74.0 test -p hsai-native-transcript-preparation --locked
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
```

The Rust 1.74 gate initially stopped on edition-2024 manifests pulled by
unneeded `p256` defaults and then by permissive `zeroize` resolution. The final
dependency graph contains no `p256` PEM/PKCS8 feature and uses `zeroize 1.8.1`;
the locked gate exits zero.

## Claim Boundary

Phase 794 is a local hermetic fixture-correspondence driver implementation. It
is not authenticated reviewer authority, operator approval, source acquisition,
source-tree verification, a real Aeneas archive intake, durable machine
observation, `P01B` materialization, preparation handoff, native transcript
capture, transcript grammar, Phase 780 lane closure, a zero-blocker audit,
source-ledger digest, plan v2, executor binding, machine resolution for a live
attempt, retention, dry preflight, live-attempt authorization, backend
execution, Lean/SMT/Z3/COBALT execution, proof artifact, checker transcript,
accepted evidence, Level2+, score axis, semantic correctness, production
readiness, SOTA, breakthrough, full security, external audit, or action
authority.

Resolved lanes remain `L01-L04,L09`; open lanes remain `L05-L08,L10-L11`.
Historical Phase 779 remains 102 blocked rows and 1,469 blockers without a
source-ledger digest. Phase 795 is the earliest conditional real authorization
and materialization slice; Phase 796 remains the earliest capture slice; Phase
806 remains the earliest plan-v2 boundary.

## Phase 795 Forward Result

Phase 795 stopped before materialization because independently rooted reviewer
authority, single-use attempt authorization, kernel-bound verified-object launch,
exact P01B producer command contracts, and complete archive/build trust
inventories do not exist. Trusted reservation time, anti-rollback journal
compare-and-swap, recovery, and durable attempt-audit inventory are also open.
It freezes those requirements in
`docs/795-phase-hsai-external-attempt-authorization-p01b-materialization-boundary.md`.
Phase 796 is documentation-only for execution-correspondence and transaction-
authority closure; the
earliest possible plan-v2 boundary moves to Phase 809.

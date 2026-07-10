# Phase 665 HSAI Gateway Proposal Preimage Lean Model-Checker Witness

State slice:
`phase-665-hsai-gateway-proposal-preimage-lean-model-checker-witness`.

## Status

Implemented and locally kernel-checked for the authorized shared-fixture
witnesses. Execution status is:

```text
KernelChecked
```

The successful local classification is:

```text
LocalLeanKernelCheckedSharedFixtureWitnessAgreement
```

The evidence ceiling remains `Level1LocalReplayOrLower`.

## Parent Evidence

Phase 660 locked one complete production preimage and SHA-256 digest fixture.
Phase 662 showed local implementation-diverse production/checker agreement for
that fixture and for opposite insertion orders of one nonempty artifact,
nonclaim, and threat-label case. Phase 664 locally kernel-checked set
permutation invariance over a handwritten Lean model of the Phase 662 checker.

Phase 665 may bind that handwritten model to only those existing concrete byte
vectors. It may not generalize the finite fixture agreement into source
correspondence or arbitrary-input equivalence.

## Frozen Inputs

The authorization is bound to repository commit:

```text
4315632159506f3da9d96b357d006e0624a98791
```

Frozen source digests:

```text
crates/hsai-agent-admission/src/lib.rs:
5ebaf3484bc0b2348ebf8b45c877def0b35a2a858126e32ec8e8bbe1ad6e1607

crates/hsai-gateway-digest-checker/src/lib.rs:
efa3782c4209a6b13fe5fd01d9c75c7e18bc77c675018be50b1ec59fec863f77

crates/hsai-e2e-harness/tests/gateway_proposal_digest_checker_contract.rs:
33deac2f0ba3fdb8b3a096e8085897ef0ef3007a0bb68af50488bdb4c1ebeac5

formal/hsai-gateway-digest/HsaiGatewayDigest/Model.lean:
fb3c51e89fda569e28ddd1242f5e676484517fc81d1659685cd3e8aac92dceb4

formal/hsai-gateway-digest/HsaiGatewayDigest/SetPermutationInvariant.lean:
868bd61595619f3ca1ec51bb1e94468041c54fbb89a473edff0bb7d44944a6cc

Cargo.toml:
8401ef7ea41db5ae0e2363c507cefeb2b9eb687034f4d6369e5ac7d2dddfe227

Cargo.lock:
87e72fd27531b91d25097d810efa2a876971310fba77ac464c0169ef0d0df893
```

Production digest semantics, checker implementation, Cargo metadata, the Lean
model, and the Phase 664 theorem are frozen during this slice.

## Authorized Shared Fixtures

Phase 665 may add exactly two non-secret UTF-8 fixture files:

```text
formal/hsai-gateway-digest/fixtures/phase660-golden-preimage.json
formal/hsai-gateway-digest/fixtures/phase662-ordering-preimage.json
```

Each file must contain exactly one compact JSON preimage followed by exactly
one LF repository line terminator. Both Rust and Lean must remove that one LF
before comparison. The run record must bind both committed file digests and
both normalized byte lengths and digests.

The golden fixture must represent the existing `phase660-action` proposal with
empty set-valued fields. The ordering fixture must represent the existing
Phase 662 nonempty case after canonical ordering:

- artifacts `a-artifact` with 32 bytes of `8`, then `z-artifact` with 32 bytes
  of `9`;
- nonclaims `a-nonclaim`, then `z-nonclaim`;
- threats `Benign`, then `StaleApprovalReplay`;
- every other field identical to the Phase 660 fixture.

These files are shared test witnesses, not backend output, solver
certificates, accepted evidence, or production runtime input.

## Authorized Rust Binding

The only authorized Rust source change is test-only and additive:

```text
crates/hsai-e2e-harness/tests/gateway_proposal_digest_checker_contract.rs
```

It may compile both fixtures with `include_str!`, require and remove exactly
one terminal LF, and assert:

1. the Phase 660 production and checker preimages equal the shared golden
   bytes;
2. both opposite Phase 662 checker insertion orders and the production
   preimage equal the shared ordering bytes.

It must not change fixture construction, production behavior, checker
behavior, dependencies, or classification logic.

## Authorized Lean Witness

Phase 665 may add:

```text
formal/hsai-gateway-digest/HsaiGatewayDigest/CorrespondenceWitness.lean
```

and may add that module as one `lakefile.toml` root. The module may import only
`HsaiGatewayDigest.Model`, load the same two fixture files with Lean
`include_str`, remove exactly one terminal LF, define the exact Phase 660 base
proposal and the two opposite Phase 662 list orders, and expose exactly one
new public theorem:

```text
phase665ModelCheckerPreimageWitnesses
```

The theorem must prove all three concrete equalities:

1. the modeled Phase 660 proposal encodes to the normalized golden bytes;
2. the modeled reverse-order Phase 662 proposal encodes to the normalized
   ordering bytes;
3. the modeled canonical-order Phase 662 proposal encodes to the same
   normalized ordering bytes.

The proof must use kernel reduction through `by decide` or an equivalently
small kernel-checkable proof. `native_decide`, unchecked admissions, custom
axioms, unsafe definitions, external tactics, and external Lean packages are
not authorized.

## Authorized Execution

The verified Phase 664 Lean 4.30.0 installation is reused with the same
command-local `PATH`. Network access is prohibited. The only formal commands
are equivalent to:

```text
lake env lean HsaiGatewayDigest/CorrespondenceWitness.lean
lake build
```

The focused Rust command is:

```text
cargo test -p hsai-e2e-harness --test gateway_proposal_digest_checker_contract --quiet
```

The run must also verify:

- exact frozen source hashes before mutation;
- exact post-run source and fixture hashes;
- exactly one public Phase 665 theorem;
- zero forbidden Lean tokens selected above;
- zero external Lake packages;
- no `lake-manifest.json` or `.lake` content committed;
- no Cargo metadata or production/checker source drift;
- all repository claim-boundary and hygiene gates.

## Failure Behavior

Phase 665 fails closed as `WitnessNotChecked` or a narrower named failure when
any fixture, source binding, theorem, direct Lean check, Lake build, focused
Rust assertion, forbidden-token scan, package scan, or repository gate fails.
A failed or partial run is never witness agreement.

## Maximum Classification

Only a fully passing bounded run may use:

```text
LocalLeanKernelCheckedSharedFixtureWitnessAgreement
```

The evidence ceiling remains:

```text
Level1LocalReplayOrLower
```

This classification means only that the Lean model and existing Rust
production/checker test paths matched two shared concrete preimage fixtures,
and that the Lean kernel accepted the three concrete equalities. It does not
prove that the Lean model corresponds to the Rust source for arbitrary inputs.

## Nonpromotion Contract

All Phase 665 outputs must bind:

```text
creates_accepted_evidence = false
creates_level2_evidence = false
populates_score_axes = false
creates_benchmark_evidence = false
claims_source_correspondence_proof = false
claims_arbitrary_input_equivalence = false
claims_sha256_correctness = false
claims_semantic_correctness = false
claims_production_readiness = false
claims_sota = false
claims_full_security = false
grants_authority = false
```

## Anti-Goals

Phase 665 does not permit:

- production or checker implementation changes;
- Cargo metadata or dependency changes;
- a generated or extracted Rust model;
- Aeneas, Hax, rust-lean, SMT, Z3, COBALT, Coq, TLA+, CBMC, DeepProve,
  zkML, or another backend run;
- SHA-256 implementation or proof in Lean;
- arbitrary-input production/checker/Lean equivalence;
- source-correspondence proof;
- independent external reproduction;
- accepted Evidence Ledger mutation;
- accepted evidence, Level2+ evidence, score axes, or benchmark evidence;
- semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, external-audit, or human-review-acceptance claims;
- authority to execute an HSAI action.

## Implemented Surface

The authorization was committed first as `7a54fb0`. Phase 665 then added only:

```text
formal/hsai-gateway-digest/fixtures/phase660-golden-preimage.json
formal/hsai-gateway-digest/fixtures/phase662-ordering-preimage.json
formal/hsai-gateway-digest/HsaiGatewayDigest/CorrespondenceWitness.lean
```

It added the witness module as one Lake root and added test-only fixture
assertions to:

```text
crates/hsai-e2e-harness/tests/gateway_proposal_digest_checker_contract.rs
```

Production admission source, checker source, Cargo workspace metadata,
`Cargo.lock`, the Phase 664 model, and the Phase 664 theorem remained byte-for-
byte unchanged.

Final changed-source digests:

```text
formal/hsai-gateway-digest/lakefile.toml:
61701804d7c49b67d3b60e461296b52410df3619a487f5cf8267b51ec3cdddcf

formal/hsai-gateway-digest/HsaiGatewayDigest/CorrespondenceWitness.lean:
1185fd0da94e4f94761283eedab5aefd525c419dcd2fe877b7556e4ab0fa2421

crates/hsai-e2e-harness/tests/gateway_proposal_digest_checker_contract.rs:
29c8dff514000c00ed042943c6d823c762e994b53d1baee4102d126036dd754c
```

## Shared Fixture Record

Both fixtures are valid compact JSON, contain one line, and end in exactly one
LF byte. Rust `include_str!` and Lean `include_str` load the same committed
files.

```text
phase660-golden-preimage.json:
committed bytes: 721
committed SHA-256:
fe97f5048119dce4fc507033a2bd62117f1fe13492fb1a73bd1220a36235b177
normalized bytes: 720
normalized SHA-256:
52de11c37c1492b7c9fb7c42660d693f5a7cbc6ed69f3bb371d66ad2686938fa

phase662-ordering-preimage.json:
committed bytes: 965
committed SHA-256:
c498105a6b5fc2075d4d9db53ddbb865b100367bdef41aacbd5168e613707601
normalized bytes: 964
normalized SHA-256:
5e1708cf752f8bf4a7f8d633ca0f5bbe2958452075aa5d0d2e0f414a77a942b5
```

The golden normalized SHA-256 equals the Phase 660 locked production digest.
The ordering normalized SHA-256 is the digest matched by both Phase 662
insertion orders and the production proposal in the focused test. These are
finite concrete vectors, not arbitrary-input equivalence.

## Lean Witness Construction

`CorrespondenceWitness.lean` imports only the existing model. It contains
exactly one public theorem:

```text
phase665ModelCheckerPreimageWitnesses
```

The marked theorem statement is 405 bytes with SHA-256:

```text
f45d1a27ed24d6d8108fbbca28d5db7ab21148250414b60be9c8976ae3440d96
```

The theorem proves that:

1. the modeled Phase 660 proposal encodes to the normalized golden fixture;
2. the reverse-order Phase 662 proposal encodes to the normalized ordering
   fixture;
3. the canonical-order Phase 662 proposal encodes to the same normalized
   ordering fixture.

The final proof uses `by decide` only for the two concrete fixture-to-rendered-
string bindings, `decide +kernel` for three two-element pairwise ordering
facts, a symbolic terminal-LF byte-normalization lemma, the Phase 664
permutation argument specialized privately, and a symbolic successful-encoder
lemma. It does not use `native_decide`, an unchecked admission, a custom axiom,
unsafe code, an external tactic, or an external package.

The local `maxRecDepth` and `maxHeartbeats` options bound elaboration of this
one theorem. They do not change kernel trust or invoke an external evaluator.

## Bounded Run Record

Final formal run window:

```text
started:  2026-07-10T16:19:23Z
finished: 2026-07-10T16:19:55Z
```

Working directory and command-local path:

```text
/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/formal/hsai-gateway-digest
/Users/shaanp/.local/share/hsai-formal/lean-4.30.0/bin:/usr/bin:/bin:/usr/sbin:/sbin
```

The working-directory, path, and two formal argv records have SHA-256:

```text
930086d12175bd590ec2e67802a37c7e7bdc4e133ee8ed0945a1434519aad44c
```

Direct witness check:

```text
argv: lake env lean HsaiGatewayDigest/CorrespondenceWitness.lean
exit status: 0
stdout bytes: 0
stderr bytes: 121
stdout SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
stderr summary:
  HsaiGatewayDigest had no generated manifest, so Lake created one.
  The pinned toolchain was already current.
stderr SHA-256: 25e95b640ca75ea83d922fb6baf0afc1105e341879c9e3de1966b30f23637ef7
```

Project build:

```text
argv: lake build
exit status: 0
stdout bytes: 39
stderr bytes: 0
stdout summary:
  Build completed successfully (5 jobs).
stdout SHA-256: b85945e1c1d9430164575c7d01e44a0c37beab1d169a9a9f2329d607d79eaab1
stderr SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Lake's generated manifest reported zero external packages and had SHA-256:

```text
b12862a55c917e1d980ba75511c28b77531f644793e29f0e2b85282c2e21a053
```

The generated manifest and all `.lake` state remain uncommitted.

Final focused Rust run window:

```text
started:  2026-07-10T15:26:05Z
finished: 2026-07-10T15:26:52Z
```

Focused Rust check:

```text
argv: cargo test -p hsai-e2e-harness --test gateway_proposal_digest_checker_contract --quiet
exit status: 0
result: 7 passed; 0 failed; 0 ignored
stdout bytes: 120
stderr bytes: 0
stdout SHA-256: 7e1b4babc0900e88e2a0024aeb01eed383d869dca45aed9974c2f65ac92c1b11
stderr SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

The committed Lean-source scan found zero case-insensitive whole-token matches
for `sorry`, `admit`, `axiom`, or `unsafe`; zero `native_decide` matches; and
exactly one public theorem in the witness module.

## Repository Validation

The final tree passed:

```text
lake env lean HsaiGatewayDigest/CorrespondenceWitness.lean
lake build
cargo fmt --all -- --check
cargo test -p hsai-e2e-harness --test gateway_proposal_digest_checker_contract --quiet
cargo test -p zkbench-core --test repo_hygiene --quiet
cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan --quiet
cargo test --workspace --quiet
cargo clippy --workspace --all-targets -- -D warnings
git diff --check
```

Observed results:

- direct Lean checking and the five-job Lake build passed;
- both shared fixtures parsed as JSON and passed exact LF checks;
- the focused production/checker fixture contract passed 7/7;
- repository hygiene passed 1/1;
- documentation claim-boundary coverage passed 1/1;
- source claim-boundary coverage passed 6/6;
- the full workspace suite passed, including 675 passed and 5 ignored in the
  primary 680-test admission group;
- workspace-wide all-target clippy passed with warnings denied;
- Rust formatting and diff hygiene passed;
- root `pnpm run lint` was inapplicable because no root `package.json` exists.

## Defensible Claim

```text
HSAI has two shared concrete gateway-proposal preimage fixtures that its local
production/checker test paths and handwritten Lean model match; the pinned
Lean 4.30.0 kernel accepted the golden witness and both nonempty insertion-
order witnesses.
```

This is local finite-fixture and handwritten-model agreement only. It does not
prove Rust-to-Lean source correspondence, arbitrary-input equivalence,
SHA-256 correctness, semantic correctness, production readiness, SOTA, or full
security.

## Next Gate

Phase 666 should be a docs-first Rust-to-Lean extraction feasibility boundary
for one smaller dependency-isolated checker function. It should compare Aeneas
and Hax support against the exact Phase 662 Rust constructs, select one source-
owned pure-data target or fail closed, define generated-source review and
correspondence rules, and preserve the current evidence ceiling. It must not
authorize extraction execution, SHA-256 proof, accepted evidence, or claim
promotion until that boundary is reviewed and committed.

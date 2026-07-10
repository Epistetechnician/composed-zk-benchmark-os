# Phase 665 HSAI Gateway Proposal Preimage Lean Model-Checker Witness

State slice:
`phase-665-hsai-gateway-proposal-preimage-lean-model-checker-witness`.

## Status

Authorized for one bounded local implementation and kernel-check run. Current
execution status is:

```text
NotRun
```

No Phase 665 witness result exists until the shared fixtures, Rust fixture
bindings, Lean module, direct Lean check, Lake build, and focused Rust test all
pass under this boundary.

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

## Next Gate

After the authorization is committed, Phase 665 may implement and run only the
surface above. A later phase must inspect the bounded result before selecting
source extraction, a broader theorem, SHA-256 verification, or evidence
promotion. None is pre-authorized here.

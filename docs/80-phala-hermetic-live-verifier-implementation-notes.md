# Phala Hermetic Live-Verifier Implementation Notes

## Status And Claim Boundary

This phase implements the hermetic Phala/dstack live managed-verifier
preparation surface authorized by
`docs/79-phala-hermetic-live-verifier-implementation-spec.md`.

The implementation is local interface preparation only. It does not perform live
Phala API calls, network access, authenticated provider calls, local Intel DCAP
quote verification, PCCS collateral handling, deployment orchestration, backend
execution, benchmark output, external result import, or claims above
`Attested`.

The strongest output remains `Attested`, never `Proven`. A hermetic fake-client
acceptance is local regression evidence only. It is not live provider evidence,
not proof, not local DCAP verification, not benchmark evidence, not global
software-agent uniqueness, and not semantic correctness.

## State Slice

```text
crates/hsai-attestation-phala/src/lib.rs
crates/hsai-attestation-phala/tests/phala_live_verifier.rs
docs/80-phala-hermetic-live-verifier-implementation-notes.md
docs/12-task-list.md
README.md
AGENTS.md
```

This phase intentionally does not touch `Cargo.toml`, `Cargo.lock`,
`zkbench-core`, Phase 4 registry semantics, accepted Evidence Ledgers, Phala
real-artifact fixtures, benchmark packs, report bundles, audit indexes, or
operator secrets.

## Public Utilities

`hsai-attestation-phala` now exports:

```text
PhalaManagedVerifierClient
InMemoryPhalaManagedVerifierClient
PhalaManagedVerifierRequest
PhalaManagedVerifierResponse
PhalaManagedVerifierVerdict
PhalaManagedVerifierError
PhalaReplayGuard
PhalaLiveManagedVerifier
```

The public surface separates:

- non-secret request construction;
- provider client boundary;
- deterministic fake client behavior;
- normalized response validation;
- replay/freshness checks;
- trust-root disclosure;
- `VerifiedAttestation` mapping.

## Hermetic Behavior

`PhalaLiveManagedVerifier` accepts an injected `PhalaManagedVerifierClient`.
Normal tests use `InMemoryPhalaManagedVerifierClient`; the crate contains no
HTTP client, socket use, process execution, Docker dependency, credential
handling, or live operator test.

Accepted responses must match:

```text
provider = "phala-dstack"
verification_mode = "live-managed-verifier"
provider_verdict = Accepted
anchor_id
nonce
report_data
compose_hash
runtime_measurements
image_digest
freshness window
required provider trust roots
```

Required provider trust-root prefixes:

```text
phala-managed-verifier:<endpoint-id>
dstack-runtime-format:<id>
provider-disclosed-hardware-root:<id>
```

The verifier also discloses local expectation roots for compose hash and image
digest. If quote appraisal is delegated to the managed verifier, the emitted
roots say so and do not imply local DCAP verification.

## Failure Coverage

Focused tests cover:

- accepted fake response maps to `Attested`;
- verifier trust roots are visible;
- provider rejection fails closed;
- stale response fails closed;
- replayed nonce fails closed for the same verifier instance;
- anchor mismatch fails closed;
- report-data mismatch fails closed;
- compose-hash mismatch fails closed;
- runtime-measurement mismatch fails closed;
- image-digest mismatch fails closed;
- missing trust root fails closed;
- output maturity never exceeds `Attested`.

Rejected responses emit no guarantees and no trust roots through the existing
attestation lane.

## Out Of Scope

- Live Phala API calls.
- Operator live tests.
- Credentials or secret handling.
- Network access.
- Local Intel DCAP quote verification.
- PCCS or collateral handling.
- Generic managed-service signature/JWKS/JWT fetching.
- TLS or attested-TLS channel binding.
- Deployment orchestration.
- External repo clones or vendored source.
- Cargo dependency changes.
- Benchmark outputs.
- External result import.
- Accepted Evidence Ledger mutation.
- Phase 4 anchor-registry semantic changes.
- Level2+ evidence.
- Claims above `Attested`.

## Validation

Focused validation:

```sh
cargo test -p hsai-attestation-phala
cargo clippy -p hsai-attestation-phala --all-targets -- -D warnings
```

Root validation:

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
```

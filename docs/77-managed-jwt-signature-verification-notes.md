# Managed JWT Signature Verification Notes

## Status And Claim Boundary

This phase implements the first bounded managed-signature verification code
behind the shipped `hsai-attestation::AttestationVerifier` trait.

The implementation is deliberately narrow: one offline managed-JWT verification
mode, ES256 only, over caller-provided local public keys. It does not fetch JWKS,
call Azure Attestation, call Intel Trust Authority, call Phala, verify DCAP
quotes, fetch PCCS collateral, implement attested TLS, use network access, run a
backend, create benchmark outputs, or change Phase 4 registry semantics.

The strongest output remains `Attested`, never `Proven`. Signature verification
strengthens the provenance of an anchor-validity envelope; it does not prove
global software-agent uniqueness, semantic correctness, competence, safety,
official benchmark evidence, or local DCAP quote validity.

## State Slice

```text
crates/hsai-attestation/src/lib.rs
crates/hsai-attestation/Cargo.toml
crates/hsai-attestation-phala/src/lib.rs
crates/hsai-attestation/tests/phase1_managed_attestation.rs
crates/hsai-e2e-harness/src/lib.rs
Cargo.lock
docs/77-managed-jwt-signature-verification-notes.md
docs/48-managed-attestation-feasibility.md
docs/66-managed-signature-verification-boundary-spec.md
docs/12-task-list.md
README.md
AGENTS.md
```

This phase intentionally does not touch `zkbench-core`, benchmark packs, accepted
Evidence Ledgers, Phala artifact fixtures, or Phase 4 registry semantics. The
`hsai-attestation-phala` and `hsai-e2e-harness` edits are compatibility updates
for the expanded `Token` and `VerifiedAttestation` structs only.

## Public Utilities

`hsai-attestation` now exports:

- `ManagedJwtEs256Key`
- `ManagedJwtVerifier`
- `Token::signed_jwt`
- `VerifiedAttestation::verifier_trust_roots`

`ManagedJwtVerifier` requires:

- compact JWT with exactly three base64url segments;
- `alg == "ES256"`;
- known `kid`;
- local P-256 public key material;
- expected issuer;
- valid ECDSA signature over `base64url(header) || "." || base64url(claims)`;
- non-stale `nbf` / `exp`;
- signed claims matching the local `Token` fields and verifier expectations.

The accepted claim fields are:

```text
iss
anchor_id
nonce
report_data_hex
measurements_hex
nbf
exp
```

The verifier emits the accepted ES256 key as a
`TrustRoot::VerifyingKey("managed-jwt-es256:<kid>")`. `AttestationLane` now
includes verifier trust roots in the emitted `ClaimEnvelope` alongside the
anchor trust root.

## Validation Coverage

Focused unit coverage includes:

- valid ES256 JWT closes the distinct-agent anchor-validity assumption through
  `AttestationLane`;
- verifier trust root is visible in the emitted envelope;
- invalid signature rejects;
- unsupported algorithm rejects;
- unknown `kid` rejects;
- wrong issuer rejects;
- stale token rejects;
- report-data mismatch rejects;
- measurement mismatch rejects;
- anchor mismatch rejects;
- rejected tokens emit no guarantees and no trust roots;
- maturity remains capped at `Attested`.

## Out Of Scope

- JWKS fetching.
- Azure Attestation live verification.
- Intel Trust Authority live verification.
- Phala Trust Center live verification.
- Intel DCAP quote verification.
- PCCS or collateral handling.
- TLS or attested-TLS channel binding.
- Secrets, API keys, cookies, bearer tokens, or private keys.
- External rails.
- Backend execution.
- Benchmark outputs.
- Level2+ evidence.
- Any claim above `Attested`.

## Validation

Focused validation:

```sh
cargo test -p hsai-attestation
cargo clippy -p hsai-attestation --all-targets -- -D warnings
```

Root validation:

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
```

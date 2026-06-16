# Managed Attestation Phase 3 Phala Fixture Notes

## Status And Claim Boundary

This phase ships `crates/hsai-attestation-phala`, a deterministic
fixture-oriented Phala/dstack backend preparation crate from
`docs/50-phala-attestation-backend-spec.md`.

This is not real Phala hardware verification. It does not verify TDX quotes,
managed-service signatures, JWT/JWKS material, vendor certificates, or live
Phala API responses. It does not use network access. Accepted fixture evidence
remains local regression evidence and emits `Attested`, never `Proven`.

`docs/56-managed-attestation-phase3-captured-artifact-notes.md` adds a separate
captured-artifact validator for a public Phala/dstack Trust Center artifact. That
add-on is managed-verifier artifact evidence only; it does not replace this
fixture seam, does not perform local DCAP verification, and does not unlock Phase
4 by itself.

## What Shipped

- `PhalaEvidence`
- `PhalaTrustPolicy`
- `PhalaVerifyMode::{Local, ManagedApi}`
- `PhalaError`
- `PhalaAttestationVerifier`
- `PhalaAttestationLane`
- `parse_phala_evidence`
- `verify_report_data_binding`
- `verify_compose_hash`
- `verify_freshness`
- `verify_phala_quote_or_report`
- `map_phala_to_verified_attestation`

`PhalaAttestationVerifier` implements the shipped `AttestationVerifier` trait.
`PhalaAttestationLane` exists because the current `hsai-attestation`
`VerifiedAttestation` type does not carry provider-specific trust roots; the
Phala lane makes managed API reliance visible without modifying existing crates.

## Fixture Verification Modes

- `Local` accepts only deterministic fixture quote strings with the
  `fixture-tdx-quote:` prefix.
- `ManagedApi` accepts only deterministic fixture responses labeled
  `managed-api:accepted` and only when policy allows managed API mode.

Both modes verify anchor id, report data, compose hash, optional Docker image
digest, required event-log presence, and freshness.

## Tests

- PH-1..PH-7 unit tests.
- PHP-1..PHP-4 property tests.
- Managed API trust-root visibility is asserted explicitly.
- The standard `AttestationLane<PhalaAttestationVerifier>` path closes
  distinctness for accepted fixture evidence.

## Out Of Scope

- Live Phala API calls.
- Real TDX quote verification.
- Real managed-service signature verification.
- Azure, Intel, Apple/Darkbloom, zkTLS, or onchain verification.
- External rails.
- Any claim stronger than hardware-bounded `Attested` fixture anchoring.

## Validation

Focused validation:

```sh
cargo test -p hsai-attestation-phala
cargo clippy -p hsai-attestation-phala --all-targets -- -D warnings
```

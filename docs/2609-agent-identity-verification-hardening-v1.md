# Agent identity verification hardening V1

State slice: `agent-identity-end-to-end-verification-hardening-v1`.

## Contract

The identity path is fail-closed at every boundary that can create an
`Attested` claim:

- `ManagedTokenVerifier` never converts unsigned caller fields into an
  attestation. A caller must select an explicit signature-verifying
  `AttestationVerifier`, such as the offline ES256 `ManagedJwtVerifier`.
- The default Phala artifact validator rejects unless an explicit
  `PhalaQuoteVerifier` authenticates the complete quote and its report-data
  field. The old `quote_hex.contains(report_data)` check is not used.
- `PhalaArtifactAttestationLane` recomputes `agent_case_hash(case)` and rejects
  artifacts whose stored case hash is not the current case hash.
- `AgentAnchorRegistry::register` rejects plain caller-constructed
  `ClaimEnvelope` values. `register_signed` requires a signature from a
  configured key, an exact anchor-set digest, an allowlisted lane, a valid
  evidence window, and (for sponsor, bond, and reputation anchors) one valid
  signed `AnchorReceipt` per anchor. Each receipt also binds the complete
  canonical anchor payload, not only its identifier.

The P-256 interfaces are offline and do not fetch provider keys. A real Phala
deployment still needs an implementation of `PhalaQuoteVerifier` backed by the
provider's authenticated quote and managed-service trust chain. Local fixture
verifiers are test-only and do not constitute provider evidence.

## Verification

The focused Rust tests cover unsigned-token rejection, quote-authentication
absence, case transfer rejection, signed registry evidence tampering,
anchor-set binding, missing receipts, runtime/sponsor/bond bookkeeping, and
the adversarial end-to-end harness. These checks establish local behavior only;
they do not prove live Phala or TDX authenticity.

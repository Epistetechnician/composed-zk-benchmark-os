# Managed Attestation Phase 1 Integration Notes

## Status And Claim Boundary

This phase starts integrating the managed-attestation track from
`docs/47-managed-attestation-proof-of-agent-prd.md` and
`docs/48-managed-attestation-feasibility.md` without leaving the pure-data
regime.

It does not implement a Phala/dstack backend, does not parse quotes, does not
verify JWT/JWKS or managed-service signatures, does not call any attestation
service, and does not claim any agent is proven.

The only implementation claim is local regression coverage: the existing
attestation seam can bind a provider custom-data field to an HSAI action, close
the existing distinct-agent anchor-validity assumption when accepted, register an
identity, admit one local work claim into the economy, and keep membrane freeze
gating intact.

All accepted attestation output remains `Attested`, never `Proven`.

## Shipped State Slice

- `hsai-attestation::Token` now carries explicit `report_data`.
- `hsai-attestation::AttestationInput` now carries explicit
  `expected_report_data`.
- `ManagedTokenVerifier` checks anchor id, nonce, report data, measurements, and
  freshness.
- `VerifyError::ReportDataMismatch` distinguishes custom-data binding failure
  from measurement failure.
- `report_data_binding(agent_pubkey, nonce, case_hash)` computes the local HSAI
  provider custom-data profile.
- `crates/hsai-attestation/tests/phase1_managed_attestation.rs` composes:

```text
AgentCase
  -> DistinctAgentLane
  -> AttestationLane<ManagedTokenVerifier>
  -> IdentityRegistry
  -> Economy
  -> Membrane
```

## Report-Data Profile

The public utility is:

```text
report_data_binding(agent_pubkey: &[u8], nonce: u64, case_hash: &[u8]) -> Vec<u8>
```

It computes a SHA-256 digest over:

```text
"hsai-attestation-report-data:v1"
len(agent_pubkey) || agent_pubkey || nonce_be || len(case_hash) || case_hash
```

This is the local Phase 1 profile for the PRD's:

```text
reportData = hash(agent_pubkey || nonce || case_hash)
```

Length prefixes avoid ambiguous concatenations. A future Phala backend may wrap
or reuse this profile, but any provider-specific deviation must be documented
before implementation.

## Tests Added

- Valid report data closes the distinct-agent anchor-validity assumption,
  registers the identity, earns once, converts through the membrane once, and
  then fails conversion after freeze.
- Report-data mismatch leaves distinctness inadmissible.
- Reused hardware anchor is rejected by `IdentityRegistry`.
- Forbidden hardware trust root is rejected by `AcceptancePolicy`.
- Unit tests cover report-data mismatch and deterministic report-data binding.

## Out Of Scope

- Real Phala/dstack quote or report parsing.
- Phala managed verifier API calls.
- Azure Attestation, Intel Trust Authority, Apple/Darkbloom provider-key
  verification, or zkTLS.
- Network access.
- New backend crates.
- New economy or membrane rules.
- External rails.
- Backend execution.
- Benchmark outputs.
- Any claim stronger than hardware-bounded `Attested` runtime anchoring.

## Validation

Focused validation:

```sh
cargo test -p hsai-attestation
```

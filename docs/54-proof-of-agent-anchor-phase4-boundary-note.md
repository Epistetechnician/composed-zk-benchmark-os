# Proof Of Agent Anchor Phase 4 Boundary Note

## Status

`docs/51-proof-of-agent-anchor-registry-spec.md` explicitly says Phase 4 must
not start until Phase 3 has demonstrated at least one real hardware-backed
attestation backend that can close an existing distinct-agent assumption.

The current Phase 3 implementation is a deterministic fixture-oriented
Phala/dstack preparation crate. It does not verify real TDX quotes, managed
service signatures, JWT/JWKS material, vendor certificates, or live Phala API
responses. Therefore it does not satisfy the Phase 4 prerequisite.

## Decision

Do not build `crates/hsai-agent-anchor-registry` in the current state.

The next allowed implementation step is a future explicit phase that introduces
real validated Phala/dstack artifacts, or another real hardware-backed
attestation backend, while preserving the `Attested`, never `Proven`, boundary.

## Claim Boundary

The blocked Phase 4 registry must not be used to claim global software-agent
uniqueness. The honest future target remains:

```text
One active HSAI identity per accepted, non-reused registered anchor set.
```

No current fixture result is external attestation evidence or proof.

# Proof Of Agent Anchor Phase 4 Boundary Note

## Status

`docs/51-proof-of-agent-anchor-registry-spec.md` explicitly says Phase 4 must
not start until Phase 3 has demonstrated at least one real hardware-backed
attestation backend that can close an existing distinct-agent assumption.

That start condition is now satisfied for the bounded local registry slice. The
first real HSAI-owned Phala/dstack artifact was accepted on 2026-06-16 under
`docs/57-managed-attestation-real-artifact-promotion-spec.md`, and the Phase 4
integration test registers the resulting closed `Attested` anchor set.

## Decision

Build `crates/hsai-agent-anchor-registry` under the exact boundary in
`docs/51-proof-of-agent-anchor-registry-spec.md`.

Do not broaden the claim beyond the accepted registry output:

```text
One active HSAI identity per accepted, non-reused registered anchor set.
```

The real Phala artifact remains managed-verifier evidence. It does not add local
Intel DCAP verification, managed-service signature/JWKS/JWT verification, or any
claim above `Attested`.

## Claim Boundary

The Phase 4 registry must not be used to claim global software-agent
uniqueness. The honest current target is:

```text
One active HSAI identity per accepted, non-reused registered anchor set.
```

No fixture or managed-verifier result is proof, benchmark evidence, backend
execution evidence, local DCAP verification, or managed-service signature
verification.

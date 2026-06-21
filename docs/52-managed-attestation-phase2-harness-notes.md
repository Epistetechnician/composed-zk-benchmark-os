# Managed Attestation Phase 2 Harness Notes

## Status And Claim Boundary

This phase ships `crates/hsai-e2e-harness`, the pure-data adversarial harness
from `docs/49-pure-data-adversarial-harness-spec.md`.

The harness does not integrate Phala, Azure, Intel Trust Authority, Apple,
Darkbloom, zkTLS, or any live network service. It uses
`AttestationLane<ManagedTokenVerifier>` only. A green harness is local regression
evidence over claim-boundary and admission behavior; it is not external
attestation evidence, backend verification, benchmark evidence, or proof.

## What Shipped

- New workspace crate `hsai-e2e-harness`.
- Deterministic fixture helpers for one `AgentCase`, one hardware anchor, one
  good token, distinctness policy, work policy, demurrage economy, and membrane.
- Phase 4 `AgentAnchorRegistry` composition over the same pure-data harness
  inputs.
- EH-1..EH-16 unit tests.
- EHP-1..EHP-5 property tests.

## Covered Path

```text
AgentCase
  -> DistinctAgentLane
  -> AttestationLane<ManagedTokenVerifier>
  -> conjoin
  -> AcceptancePolicy(require_closed, min Attested)
  -> IdentityRegistry
  -> Economy
  -> Membrane
```

Additional Phase 4 harness path:

```text
AgentCase
  -> DistinctAgentLane
  -> AttestationLane<ManagedTokenVerifier>
  -> conjoin
  -> AgentAnchorRegistry
```

## Tests

- Valid attestation closes distinctness and registers.
- Nonce, measurement, expiration, and anchor-id faults prevent admission.
- Anchor reuse is rejected.
- Unregistered workers cannot earn.
- Registered workers can earn.
- Frozen workers cannot cross the membrane.
- Forbidden hardware roots are rejected.
- Funding-rule sweep invariants remain bounded.
- Phase 4 anchor-registry admission accepts only closed `Attested` runtime
  anchors and preserves the Phase 4 claim boundary.
- Expired attestations, reused runtime anchors, mismatched attested/requested
  runtime anchors, revoked runtime anchors, proof-theater envelopes, and single
  attestation faults do not mutate Phase 4 registry state.

## Out Of Scope

- Real managed-service signature verification.
- Real Phala/dstack quote verification.
- Network access.
- External rails.
- New protocol primitives.
- Backend execution.
- Benchmark outputs.

## Validation

Focused validation:

```sh
cargo test -p hsai-e2e-harness
cargo clippy -p hsai-e2e-harness --all-targets -- -D warnings
```

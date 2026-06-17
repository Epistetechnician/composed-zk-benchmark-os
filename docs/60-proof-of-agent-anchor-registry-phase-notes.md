# Proof Of Agent Anchor Registry Phase Notes

## Status And Claim Boundary

Phase 4 is now authorized because the first real HSAI-owned Phala/dstack
artifact was accepted under
`docs/57-managed-attestation-real-artifact-promotion-spec.md` on 2026-06-16.

The implementation is limited to `crates/hsai-agent-anchor-registry`. It records
this claim only:

```text
One active HSAI identity per accepted, non-reused registered anchor set.
```

It is not proof, not benchmark evidence, not backend execution evidence, not
global software-agent uniqueness, not local Intel DCAP verification, and not
managed-service signature/JWKS/JWT verification. Output maturity is inherited
from admitted input envelopes and is never elevated by registry bookkeeping.

## State Slice

```text
Cargo.toml
crates/hsai-agent-anchor-registry/
docs/51-proof-of-agent-anchor-registry-spec.md
docs/54-proof-of-agent-anchor-phase4-boundary-note.md
docs/57-managed-attestation-real-artifact-promotion-spec.md
docs/58-managed-attestation-challenge-capture-tooling-notes.md
docs/59-operator-capture-runbook.md
docs/60-proof-of-agent-anchor-registry-phase-notes.md
README.md
AGENTS.md
```

## Public Utilities

`hsai-agent-anchor-registry` exports:

- `AgentAnchorRegistry`
- `AgentAnchorSet`
- `RegisteredAgentAnchor`
- `AnchorTier`
- `SponsorAnchor`
- `SponsorshipPolicy`
- `BondAnchor`
- `ReputationAnchor`
- `AgentAnchorError`
- `anchor_acceptance_policy`
- `anchor_claim_envelope`
- `anchor_tier_predicate`
- `tier_strength`
- `PHASE_4_CLAIM_BOUNDARY`

## Validation Coverage

The crate implements the Phase 4 unit vectors:

- PA-1 hardware anchor set registers.
- PA-2 runtime anchor reuse is rejected.
- PA-3 one-agent sponsor reuse is rejected.
- PA-4 limited sponsor policy allows N and rejects N+1.
- PA-5 hardware plus sponsor elevates to composite.
- PA-6 sponsor alone is accountability, not runtime scarcity.
- PA-7 revoked runtime anchor downgrades or revokes.
- PA-8 canonical anchor-set hash is order-independent.

It also includes property tests for active anchor reuse, sponsor policy limits,
tier monotonicity under added valid anchors, revocation non-strengthening, and
canonical hash determinism.

The end-to-end authorization test consumes the accepted real Phala fixture
through `PhalaArtifactAttestationLane`, conjoins it with `DistinctAgentLane`,
admits the closed `Attested` envelope, and registers a hardware-anchored agent
in `AgentAnchorRegistry`.

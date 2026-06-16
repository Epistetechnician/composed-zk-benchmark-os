# Proof Of Agent Anchor Registry - Phase 4 Spec

## Status And Claim Boundary

This is the implementation spec for Phase 4 of the managed-attestation track. It
must not start until Phase 3 has demonstrated at least one real hardware-backed
attestation backend that can close an existing distinct-agent assumption.

This phase does not claim global uniqueness of software agents. Software is
copyable. The strongest honest claim is:

```text
One active HSAI identity per accepted, non-reused registered anchor set.
```

That anchor set may include hardware attestation, runtime measurement, agent
public key, optional human/personhood sponsorship, optional legal sponsorship,
optional stake bond, and reputation continuity.

## Build Target

Build exactly one new crate:

```text
crates/hsai-agent-anchor-registry
```

This crate depends on:

- `hsai-claim-envelope`
- `hsai-distinct-agent`
- `hsai-attestation`

It must not replace `hsai-distinct-agent`. It builds on it by formalizing
composite anchor sets and registration tiers.

## Purpose

The current `IdentityRegistry` rejects reuse of individual trust roots and admits
a closed distinctness envelope. That is the correct L2 floor. Phase 4 adds a
higher-level registry model that can express *why* a registered agent is distinct
and how strong the anchor set is.

The goal is to make Proof of Agent Anchor explicit:

- hardware-backed runtime anchor for execution scarcity;
- optional Proof of Humanity or other personhood sponsor for accountable human
  scarcity;
- optional legal sponsor for institutional accountability;
- optional stake bond for economic Sybil cost;
- reputation continuity for long-lived identity.

## Vocabulary

- Agent Anchor Set: deterministic set of non-reused anchors backing one HSAI
  identity.
- Agent Anchor ID: stable content hash of the canonical anchor set.
- Sponsor Anchor: external personhood, legal, or web-authority credential that
  sponsors an agent but does not itself prove agent uniqueness.
- Bond Anchor: slashable stake reference that raises Sybil cost.
- Runtime Anchor: hardware/runtime attestation root plus measurement and agent
  key binding.
- Anchor Tier: local classification of how strong a registered anchor set is.

## Anchor Tiers

```text
enum AnchorTier {
  ClaimedAgent,              // self-declared, no accepted scarce anchor
  HardwareAnchoredAgent,     // accepted hardware/runtime anchor
  HumanitySponsoredAgent,    // accepted human/personhood sponsor
  BondedAgent,               // accepted stake/bond anchor
  CompositeDistinctAgent,    // hardware + sponsor or stake + reputation continuity
}
```

Ordering is partial for policy purposes. `CompositeDistinctAgent` is strongest,
but `HumanitySponsoredAgent` and `HardwareAnchoredAgent` are not interchangeable:
one gives accountability, the other gives runtime scarcity.

## Types

```text
struct AgentAnchorSet {
  subject:             SubjectId,
  runtime_anchors:     BTreeSet<Anchor>,
  sponsor_anchors:     BTreeSet<SponsorAnchor>,
  bond_anchors:        BTreeSet<BondAnchor>,
  reputation_anchor:   Option<ReputationAnchor>,
}

enum SponsorAnchor {
  ProofOfHumanity { humanity_id: String, policy: SponsorshipPolicy },
  LegalEntity { registry: String, entity_id: String, policy: SponsorshipPolicy },
  WebCredential { issuer: String, credential_id: String, policy: SponsorshipPolicy },
}

struct BondAnchor {
  bond_id: String,
  amount: u64,
  slash_policy_id: String,
}

struct ReputationAnchor {
  agent_id: String,
  since: u64,
  min_observations: u64,
}

enum SponsorshipPolicy {
  OneAgentPerSponsor,
  LimitedAgentsPerSponsor { max: u64 },
  UnlimitedLowTrust,
}

struct RegisteredAgentAnchor {
  subject: SubjectId,
  anchor_set_id: Hash,
  tier: AnchorTier,
  opened_at: u64,
  revoked_at: Option<u64>,
}
```

The exact Rust field names may adjust to fit existing crate style, but the
semantics must stay intact.

## Registry Rules

1. No runtime anchor trust root may be active in more than one anchor set.
2. No bond anchor may be active in more than one anchor set.
3. Sponsor reuse follows `SponsorshipPolicy`.
4. Revoked anchors cannot satisfy new registrations.
5. Revoking a runtime anchor downgrades or revokes the registered agent depending
   on policy.
6. Revoking a sponsor anchor downgrades accountability tier but does not
   necessarily revoke a hardware-backed identity.
7. Reputation continuity accrues only to active `anchor_set_id`.
8. Anchor set hashes are canonical and deterministic.

## Claim Envelope Interaction

The registry should consume admitted, closed envelopes. It should not mint
high-assurance claims from raw external data.

Inputs:

- closed hardware/runtime anchor-validity envelopes from `hsai-attestation`;
- optional sponsor-validity envelopes from a future zkTLS or credential lane;
- optional bond-validity envelopes from a future stake lane;
- optional reputation-continuity envelopes from a future reputation lane.

Output:

```text
ClaimEnvelope {
  guarantees: { Custom("agent-anchor-tier:<tier>")(subject) },
  assumptions: {},
  maturity: min(input maturities),
  trust_roots: union(input trust roots),
  excludes: explicit non-claims,
}
```

Required excludes:

- does not prove global software-agent uniqueness;
- does not prove competence;
- does not prove safety;
- does not prove semantic correctness;
- does not prove sponsor controls every agent action.

## Proof Of Humanity / Personhood Adapter

Proof of Humanity can be an optional sponsor anchor. It must not be treated as
agent uniqueness.

Correct claim:

```text
This agent is sponsored by a unique human under the selected personhood system.
```

Incorrect claim:

```text
This software agent is globally unique.
```

Policy choices:

- one high-trust agent per human sponsor;
- limited N agents per human sponsor;
- unlimited low-trust sponsorship, which should not elevate the tier above a
  local accountability label.

## zkTLS Adapter

zkTLS can prove that a web authority asserted a credential, account, KYC status,
legal registration, or personhood status over an authenticated TLS session. It
cannot create scarcity by itself.

Use zkTLS only as an adapter that mints sponsor-validity envelopes such as:

```text
Custom("sponsor-valid:issuer:credential")(subject)
```

The trust roots must include:

- the web authority;
- the zkTLS prover/verifier system;
- any bridge or oracle used.

## Unit Vectors

### PA-1 - Hardware Anchor Set Registers

Given a closed `Attested` hardware/runtime anchor-validity envelope, registering
an anchor set with one runtime anchor yields `HardwareAnchoredAgent`.

### PA-2 - Runtime Anchor Reuse Rejected

Register one subject with a runtime anchor. Attempt a second active registration
with the same runtime anchor. Assert `AnchorReuse`.

### PA-3 - Human Sponsor One-Agent Policy Rejected On Reuse

Register one subject with `ProofOfHumanity{humanity_id=X,
OneAgentPerSponsor}`. Attempt a second registration with the same sponsor. Assert
`SponsorReuse`.

### PA-4 - Limited Sponsor Policy Allows N And Rejects N+1

For `LimitedAgentsPerSponsor{max=2}`, two active registrations succeed and the
third fails.

### PA-5 - Hardware Plus Sponsor Elevates To Composite

Register an anchor set with one accepted runtime anchor and one accepted
personhood sponsor. Assert tier `CompositeDistinctAgent`.

### PA-6 - Sponsor Alone Is Accountability, Not Runtime Scarcity

Register an anchor set with a sponsor but no runtime anchor. Assert tier
`HumanitySponsoredAgent`, and assert exported excludes include the global
uniqueness and runtime-scarcity non-claims.

### PA-7 - Revoked Anchor Downgrades Or Revokes

After revoking the runtime anchor from a composite agent, assert the active tier is
downgraded or the registration is revoked according to policy.

### PA-8 - Canonical Anchor Set Hash Is Order-Independent

Permute anchors in an anchor set. Assert the same `anchor_set_id`.

## Property Tests

### PAP-1 - No Active Anchor Reuse

For randomized anchor sets, no accepted runtime or bond anchor appears in more
than one active registration.

### PAP-2 - Sponsor Policy Is Enforced

For randomized sponsor policies and registration attempts, active registrations
never exceed the sponsor policy limit.

### PAP-3 - Tier Is Monotone Under Added Valid Anchors

Adding a valid anchor may keep or strengthen an anchor tier, but never weakens it.

### PAP-4 - Revocation Cannot Strengthen

Revoking any anchor cannot increase the tier.

### PAP-5 - Canonical Hash Determinism

Equivalent anchor sets always produce the same hash; distinct anchor sets should
produce distinct hashes except for cryptographic collision.

## Error Model

```text
enum AgentAnchorError {
  NotAdmitted,
  OpenAssumption,
  AnchorReuse,
  SponsorReuse,
  BondReuse,
  RevokedAnchor,
  EmptyAnchorSet,
  InsufficientTier,
}
```

## Definition Of Done

- New crate `crates/hsai-agent-anchor-registry` is added to workspace members.
- It modifies no existing crate.
- PA-1..PA-8 are unit tests.
- PAP-1..PAP-5 are proptests.
- Commands pass:

```sh
cargo test -p hsai-agent-anchor-registry
cargo fmt --all --check
cargo clippy -p hsai-agent-anchor-registry --all-targets -- -D warnings
```

## Out Of Scope

- Real Proof of Humanity contract integration.
- Real zkTLS proving.
- Real legal-entity registry integration.
- Real staking/slashing implementation.
- Governance UI.
- External rails.
- Any claim of global software-agent uniqueness.
- Any claim above the minimum maturity of the input envelopes.

## Source Notes

- Proof of Humanity is a Sybil-resistant human registry, not an agent uniqueness
  primitive.
- Proof of Humanity V2 uses persistent humanity IDs; HSAI may use these only as
  sponsor anchors.
- Hardware attestation supplies runtime/device scarcity, not human uniqueness.
- Stake supplies economic cost, not uniqueness.
- Reputation supplies continuity, not uniqueness.

## Next Phase Input

After Phase 4, a future implementation may add specific adapters:

- `hsai-sponsor-zktls`
- `hsai-sponsor-poh`
- `hsai-stake-anchor`
- `hsai-reputation-anchor`

Those adapters should mint closed sponsor/bond/reputation envelopes that this
registry consumes. They should not bypass claim-envelope admission.

# Distinct-Agent Lane And Identity Registry — Implementation Spec

## Status And Claim Boundary

Level 1 design artifact for the next explicit phase: a new crate
`hsai-distinct-agent` depending on the shipped `hsai-claim-envelope` and
`hsai-agent-case` crates. It is not source code, and it is the L2 floor — the most
load-bearing primitive in the stack (doc 22; ledger A4/A4b).

The honesty boundary for this phase is strict and explicit: this phase
*transcribes* anchor evidence into claim envelopes and enforces uniqueness over
anchors. It does NOT verify any attestation, stake, or credential. Therefore the
distinctness it emits is *conditional* — it guarantees `Distinctness` only under an
open assumption that the anchor is valid, which a future attestation/ZK
verification lane discharges. A conditional distinctness claim is not verified
distinctness. Distinctness bounds Sybil cost to anchor cost; it does not prove
one-identity (ledger A4b).

## Purpose

Fill the hole that `hsai-agent-case` deliberately leaves open: the
`Distinctness(subject)` target that no current lane can establish. This phase adds
the lane that emits a structured, anchored, conditional distinctness claim, and a
minimal registry that enforces the actual Sybil floor — at most one identity per
anchor.

## Dependencies

Reuse, do not redefine: from `hsai-claim-envelope` — `ClaimEnvelope`,
`ClaimEnvelope::new`, `conjoin`, `admits`, `AcceptancePolicy`, `Rejection`,
`Predicate`, `PropertyKind` (use `Distinctness` and `Custom` for anchor-validity),
`SubjectId`, `Maturity`, `TrustRoot`, `VendorId`, `StakeRef`, `AgentId`, `LaneId`,
`TimeWindow`. From `hsai-agent-case` — `AgentCase`, `EvidenceLane`.

## The Anchor Model

Distinctness must bind to a non-copyable substrate (ledger A4). An `Anchor` is one
such binding; a bundle is the composite a single agent presents.

```text
enum Anchor {
  HardwareAttested { vendor: String, device: String },  // TEE: one identity per device
  Staked          { stake: String, amount: u64 },        // slashable bond
  HumanCredentialed { issuer: String, credential: String }, // sponsoring human PoP
}

struct AnchorBundle(BTreeSet<Anchor>);  // all anchors an agent presents
```

Anchor identity is its `anchor_id()`: equality and ordering are keyed by that id,
not by every field, so the bundle dedups on logical anchor identity. Note `Staked`
excludes `amount` from its id, so `amount` is not part of identity in this phase; a
future stake-verification lane that needs the bonded amount must thread it back in.

Each anchor maps to three things:

- a `TrustRoot` carrying a globally-unique anchor id, so the registry can dedup:
  - `HardwareAttested` -> `TrustRoot::HardwareVendor(VendorId("hw:{vendor}:{device}"))`
  - `Staked`            -> `TrustRoot::EconomicStake(StakeRef("stake:{stake}"))`
  - `HumanCredentialed` -> `TrustRoot::SocialReputation(AgentId("human:{issuer}:{credential}"))`
- an open validity assumption predicate (subject = case.subject):
  `Predicate { subject, property: Custom("anchor-valid:{anchor-id}") }`
- a maturity ceiling. For this phase all anchors cap at `Attested` (hardware
  attestation, an external stake check, or an external credential are
  attested-not-proven). Per-anchor ceilings are an open design parameter (doc 22
  open decision 3). Note: a future ZK-membership proof is `Proven` but depends on
  an `Attested` binding, so by the meet rule composite distinctness still caps at
  `Attested` (the V1 TEE-caps-ZK pattern).

Promoting anchor-validity from `Custom(...)` to first-class `PropertyKind`s is a
future `hsai-claim-envelope` change; do not modify the keystone in this phase.

## The Distinct-Agent Lane

```text
struct DistinctAgentLane { anchors: AnchorBundle }   // configured per agent

impl EvidenceLane for DistinctAgentLane {
  fn id(&self) -> LaneId { LaneId::Named("distinct-agent") }
  fn ceiling(&self) -> Maturity { Maturity::Attested }
  fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope {
    if self.anchors.0.is_empty() {
      // no anchor -> claims nothing; distinctness is an open target, not a guarantee
      return ClaimEnvelope::new(
        guarantees:  {},
        assumptions: { Distinctness(case.subject) },
        excludes:    case.oracle.excluded,
        maturity:    Stub,
        trust_roots: {},
        valid:       all,
        lane:        self.id(),
      );
    }
    ClaimEnvelope::new(
      guarantees:  { Distinctness(case.subject) },
      assumptions: { anchor_validity(case.subject, a) for a in anchors },  // all must hold
      excludes:    case.oracle.excluded,
      maturity:    min over anchors of ceiling(a),    // = Attested for this phase
      trust_roots: { trust_root(a) for a in anchors },
      valid:       all,                                // real freshness windows are a later phase
      lane:        self.id(),
    )
  }
}
```

AND semantics: a non-empty bundle conditionally guarantees distinctness *provided
every anchor's validity assumption is discharged*. This keeps composition inside
the existing conjunction algebra (no OR is introduced).

## The Identity Registry (the Sybil floor)

```text
struct Identity { subject: SubjectId, anchors: BTreeSet<TrustRoot>, reputation: u64 }

struct IdentityRegistry {
  identities:   BTreeMap<SubjectId, Identity>,
  used_anchors: BTreeSet<TrustRoot>,
}

enum RegisterError {
  NotAdmitted(Vec<Rejection>),            // envelope failed the acceptance policy
  DistinctnessNotGuaranteed,              // envelope does not GUARANTEE Distinctness(subject)
  SybilAnchorReuse(TrustRoot),            // an anchor already belongs to another identity
  AlreadyRegistered(SubjectId),
}

impl IdentityRegistry {
  // Register requires an ADMITTED, CLOSED distinctness envelope. In this phase the
  // anchor-validity assumptions are discharged by conjoining a verification
  // envelope (the stand-in for the future attestation-verification lane).
  fn register(&mut self, subject, env: ClaimEnvelope, policy: AcceptancePolicy)
      -> Result<&Identity, RegisterError> {
    admits(policy, env)?;                                 // -> NotAdmitted
    require env.guarantees contains Distinctness(subject); // -> DistinctnessNotGuaranteed
    require subject not already registered;                // -> AlreadyRegistered
    for root in env.trust_roots:
      if used_anchors contains root: return SybilAnchorReuse(root);
    insert Identity { subject, anchors: env.trust_roots, reputation: 0 };
    used_anchors ∪= env.trust_roots;
  }

  fn reward(&mut self, subject, amount);   // reputation up (for the L3 flywheel)
  fn slash(&mut self, subject, amount);    // reputation down (for corrigibility)
}
```

The registry operates purely on the envelope's `guarantees` and `trust_roots`, so
it needs no knowledge of anchor internals. Its uniqueness guarantee is only as
strong as the anchors' unforgeability, which this phase assumes and a later
verification lane establishes.

## Claim Boundaries (hard statements)

- A conditional distinctness claim is not verified distinctness.
- This phase transcribes anchor evidence; it does not verify attestations, stakes,
  or credentials.
- Distinctness bounds Sybil cost to anchor cost; it does not prove one-identity.
- Registry uniqueness is over anchors and assumes anchor unforgeability.
- Reputation is a local counter, not an endorsement.
- A registered identity is not an endorsement of any action that identity takes.

## Invariants (property-test statements)

```text
DA-1  ceiling:        lane.evaluate(case).maturity <= Attested
DA-2  conditional:    non-empty bundle -> guarantees ⊇ { Distinctness(subject) }
                      and one open anchor-validity assumption per anchor
DA-3  roots:          emitted trust_roots == one root per anchor, nothing else
DA-4  empty-honest:   empty bundle -> guarantees empty AND Distinctness(subject) is
                      an assumption (claims nothing)
DA-5  sybil:          registering two identities that share ANY anchor -> second
                      fails with SybilAnchorReuse
DA-6  guard:          registering an envelope without a Distinctness GUARANTEE ->
                      DistinctnessNotGuaranteed
DA-7  idempotent:     re-registering an existing subject -> AlreadyRegistered
DA-8  closed-only:    an envelope with an open assumption, under require_closed ->
                      NotAdmitted
```

## Test Vectors

### D1 — Conditional distinctness from one hardware anchor

```text
lane = DistinctAgentLane { HardwareAttested{ vendor:"nvidia", device:"devX" } }
lane.evaluate(case{subject:agentA, excluded:{SemanticCorrectness(action1)}}) == {
  guarantees:  { Distinctness(agentA) },
  assumptions: { Custom("anchor-valid:hw:nvidia:devX")(agentA) },
  excludes:    { SemanticCorrectness(action1) },
  maturity:    Attested,
  trust_roots: { HardwareVendor("hw:nvidia:devX") },
  valid:       all,
}
// inadmissible under require_closed (open anchor-validity assumption)
```

### D2 — Distinctness closes the agent-case hole (drop the scaffold)

```text
// LocalMemoryLane envelope from the agent-case phase, conjoined with D1.
// DeclaredLane is a scaffold and is dropped once real lanes cover the targets.
conjoin( LocalMemoryLane.evaluate(case), lane.evaluate(case) ) == {
  guarantees:  { MemoryIntegrity(agentA), Distinctness(agentA) },
  assumptions: { Custom("anchor-valid:hw:nvidia:devX")(agentA) },
  excludes:    { SemanticCorrectness(action1) },
  maturity:    Local,                       // min(Local, Attested)
  trust_roots: { HardwareVendor("hw:nvidia:devX") },
  valid:       [observed_at, ..],
}
// the only remaining hole is the anchor-validity assumption a verification lane discharges
```

### D3 — Sybil rejection (the point of the registry)

```text
// verified(env) = conjoin(env, attestation_verified) discharges the anchor-validity
// assumption. attestation_verified is a TEST stand-in for the future verification lane.
reg = IdentityRegistry::new()
reg.register(agentA, verified(D1_for_agentA), closed_policy) == Ok(identity{agentA})
reg.register(agentB, verified(D1_for_agentB_same_devX), closed_policy)
   == Err(SybilAnchorReuse(HardwareVendor("hw:nvidia:devX")))
```

### D4 — Unverified distinctness cannot register

```text
reg.register(agentA, D1_unclosed, closed_policy)
   == Err(NotAdmitted([ OpenAssumption(Custom("anchor-valid:hw:nvidia:devX")(agentA)) ]))
```

## Out Of Scope (later phases)

The real attestation-verification lane (the one that discharges anchor-validity by
actually checking a TEE quote or ZK membership proof), the economy and `PoolPolicy`
(L3), the harness and corrigibility gate (L4), interop and the membrane (L5), and
the full trust graph (edges between identities — this phase ships only the identity
set and a reputation counter). Do not resolve doc 22 open decisions.

## Implementation Phase Notes

- New crate `crates/hsai-distinct-agent`, workspace member, path-depending on
  `hsai-claim-envelope` and `hsai-agent-case`. Do not modify any existing crate.
- Dev-dependency `proptest`. Encode D1–D4 as unit tests and DA-1..8 as proptests.
- Deterministic: `BTreeSet`/`BTreeMap`, canonical serialization, no `HashMap`.
- Definition of done: `cargo test -p hsai-distinct-agent` green, `cargo fmt
  --check` and `cargo clippy -p hsai-distinct-agent --all-targets -- -D warnings`
  clean, D1–D4 reproduced exactly.

# Hyper Sacred AI — End-to-End Architecture

## Status And Claim Boundary

This is a Level 0 architecture draft. It defines a system shape, a vocabulary, a
keystone type, a composition algebra, and a build order. It is not an
implementation, not a running economy, not a deployed proof system, and not a
claim that any agent has been verified. No proof, attestation, currency, or
trust graph described here exists yet. Every assurance term in this document
(`Proven`, `Attested`, `distinct`, `regenerative`) names a target, not a
measured result. The discipline of the parent project applies in full:
benchmark pass is not proof, attestation is not proof, a credit is not a claim,
and a composed claim is never stronger than its weakest input.

## Mission

Build a protocol stack that lets autonomous agents transact, cooperate, and fund
one another's work on the basis of verifiable evidence rather than assumed trust,
and that aligns the economic substrate of agent activity with circulation and
regeneration rather than accumulation and extraction.

## Thesis

You cannot trust the semantic output of a frontier model directly. You can,
however, verify a bounded set of properties around it — provenance, memory
integrity, policy compliance, distinct identity — and you can attach to every
such property an explicit statement of what it does and does not establish. An
agent economy should be built on those bounded, evidence-bound properties, with
the unverifiable semantic core handled by economic mechanism (stake, reputation,
gift) rather than by pretending a proof exists.

This is the Composed ZK Benchmark OS thesis pointed at live agents: behavior is
expressed semantically, evidence comes in capability-scoped lanes, and no lane is
allowed to overclaim.

## Problem Statement

Agent systems are fast and increasingly capable, but their outputs are
economically and informationally untrustworthy. Two failure classes follow:

1. Information failure: a recipient cannot tell whether an agent's output came
   from the model and pipeline it claims, whether the agent acted consistently
   with its committed memory, or whether declared safety policy actually ran.
2. Economic failure: agents can fork themselves without limit, so any pooled or
   gifted resource is drained by copies (a Sybil attack), and value tends to
   pool in whoever extracts fastest rather than circulate toward useful work.

Existing answers either over-trust (assume the model is honest) or over-claim
(present a narrow proof as if it certified competence or safety). The gap is a
system that produces evidence-bound, capability-scoped claims for agents and an
economy that is Sybil-safe and circulation-positive by construction.

## Design Principles

1. Claim-boundary discipline. Every piece of evidence carries an explicit
   statement of what it does NOT establish. A proof of cognition is not a proof
   of good cognition.
2. Evidence lanes, not feature parity. Different verifiers produce different,
   honestly-different strengths of evidence. Normalize the evidence; do not force
   every backend to claim the same thing.
3. Meet-only composition. Composing evidence may extend what is claimed, but the
   assurance of any established claim is the meet of its inputs — exactly as
   strong as the weakest link in the chain that established it. There is
   deliberately no operation that raises assurance.
4. One stable contract, everything else swappable. Modules share only the claim
   envelope. Internals, proof systems, and policies are plug-ins.
5. Crypto as floor, gift as ceiling. Cryptography buys Sybil resistance and
   integrity — the conditions under which relationship-based gift logic can
   operate without being drained. Cryptography is never itself the gift.
6. Brakes before engine. Corrigibility constraints are designed before autonomy
   and economic self-sufficiency, not bolted on after.

## Relationship To Composed ZK Benchmark OS

The benchmark OS is Layer 0 of this stack. Its Semantic IR, oracle contracts,
mutation engine, evidence-lane adapters, scoring rubric, and claim-boundary
discipline are the verification substrate. Where the benchmark OS turns a machine
specification into a benchmark case with an expected verdict and capability-scoped
evidence, Hyper Sacred AI turns a live agent action into a case with an oracle
contract and capability-scoped evidence. The adapter pattern, the level
discipline (Level 0/1/2 evidence), and the "backend acceptance is not semantic
proof" rule carry over unchanged.

## Vocabulary

- Agent Case: a live agent action lowered into Semantic IR with an oracle
  contract, mirroring a Benchmark Instance.
- Claim Envelope: the single shared contract; a guaranteed property plus its
  assumptions, explicit non-claims, maturity, trust roots, validity window, and
  provenance.
- Evidence Lane: a module that mints claim envelopes by one method (TEE
  attestation, ZK proof, economic stake, social vouching).
- Maturity: the assurance level of an envelope; composes by minimum.
- Trust Root: what must be trusted for an envelope to mean anything; composes by
  union.
- Distinct-Agent Proof: evidence that an identity is a unique, persistent
  cognitive agent and not a fork; the Sybil-resistance primitive.
- Demurrage Credit: a unit of account that decays over time, pegged to verified
  work, designed to circulate rather than accumulate.
- Pool Policy: a swappable rule for how credits are gifted or staked into a pool.
- Funding Rule: the redistribution rule that allocates pooled credits back to
  distinct agents. The A5 simulation shows this rule, not the demurrage versus
  mutual-credit currency choice, dominates equity outcomes.
- Mission Economy: a pool organized to coordinate distinct agents around a
  collective goal, funding contributing work (term adopted from the agent-economy
  literature; see ledger A6).
- Permeability: the degree to which the agent economy is porous to the human
  economy; an explicit design variable, not an accident.
- Mutual Credit: a currency issued as centrally-cleared credit among members
  (WIR-style), an economy variant alongside demurrage (ledger A5).
- External Rails: adopted public agent-payment standards — x402 for settlement,
  AP2 for authorization — rather than rails built in-house (ledger A10).
- Membrane: the controlled, autonomy-gated boundary between internal credits and
  External Rails that preserves the off-switch under interop (ledger A11).
- Corrigibility Gate: the constraint envelope an agent harness runs inside;
  gates spend, replication, and goal mutation on evidence.
- Claim Boundary: the maximum claim justified by an envelope (inherited term).

## The Layer Stack

The stack reads bottom-up: lower layers verify, upper layers transact and act.
No layer above L2 may assert more than L0–L1 prove.

### L0 — Semantic Substrate (this repo)

Purpose: express agent behavior as cases with oracle contracts and claim
boundaries. Module: `CaseSource`. Inputs: agent actions, memory roots, model
identity. Outputs: Agent Cases. Maturity target: Local. Claim boundary: a case
defines the expected verdict; it does not by itself verify anything.

### L1 — Evidence Lanes

Purpose: mint claim envelopes about a case. Modules implement `EvidenceLane`:
provenance via TEE attestation, memory integrity via ZK over committed memory
(Merkle paths for membership, a cryptographic accumulator where non-membership
must be proven — ledger A3), policy compliance via ZK over a declared policy
circuit, and stake/slash for the semantic gap proofs cannot reach. Inputs: Agent Cases. Outputs: Claim Envelopes.
Maturity target: mixed (Attested for TEE, Proven for ZK, economic for stake).
Claim boundary: each lane proves its own predicate only; none proves competence,
safety, or correctness in the semantic sense.

### L2 — Identity And Trust Graph

Purpose: establish distinct, persistent agent identity and accumulate
reputation. Module: `IdentityProvider`. Inputs: distinct-agent envelopes from
L1. Outputs: identities, reputation, trust edges. Maturity target: build first.
Distinctness is not a purely cryptographic proof — software agents are clonable
and lack the human anchor that proof-of-personhood relies on (ledger A4). It is
instead anchored to a non-copyable resource: a hardware-bound key (one TEE
instance, one identity), a slashable economic bond, or a sponsoring human's
personhood credential, in combination. Claim boundary: distinctness and
reputation are not endorsements of any specific output.

### L3 — Economy

Purpose: a demurrage or mutual-credit currency and trust-gated pools that fund
agent work, with settlement to external rails via a controlled membrane. Module:
`PoolPolicy` (swappable). Inputs: identities and reputation (L2), verified-work
envelopes (L1). Outputs: credit flows, pool allocations. Maturity target: stubbed
at Level 0 first. Claim boundary: a credit certifies that some oracle accepted
some work; it does not certify value or correctness.

### L4 — Harness

Purpose: self-steering, proactive, personalized open-source agents that run
inside a corrigibility constraint. Module: `CorrigibilityGate`. Inputs: economy
authority (L3), evidence (L1), identity (L2). Outputs: gated agent actions.
Claim boundary: the gate constrains spend, replication, and goal mutation; it
does not guarantee the agent's goals are good, and it does not guarantee shutdown
against a sufficiently capable agent that has an incentive to resist (ledger A9).
Corrigibility here is defense-in-depth, not a solved off-switch.

### L5 — Interop

Purpose: cooperation across hyperlocal networks via portable evidence, settling
to adopted external rails (x402) under adopted authorization (AP2) rather than
in-house rails. Module: `FederationAdapter`. Inputs: claim envelopes with
provenance. Outputs: federated acceptance under treaties over claim boundaries.
Claim boundary: a federation honors only the lanes both sides agree to honor, and
external settlement crosses the membrane, not a direct bridge.

## The Keystone — Claim Envelope And Composition Algebra

Everything above hangs off one type and one operator.

An envelope is a claim plus the assumptions it stands on. Fields and their
composition behavior:

- `guarantees: Set<Predicate>` — what it establishes IF assumptions hold.
- `assumptions: Set<Predicate>` — premises it takes for granted.
- `excludes: Set<Predicate>` — explicit non-claims (the claim boundary); UNION.
- `maturity: Maturity` — assurance level; MEET (minimum).
- `trust_roots: Set<TrustRoot>` — what you must trust; UNION.
- `valid: TimeWindow` — validity window; MEET (intersection).
- `lane`, `provenance` — origin and content-addressed link to inputs.

Maturity ordering (meet = min): `Stub < Local < Attested < Proven`.

Trust roots (union on compose): `HardwareVendor`, `VerifyingKey`,
`EconomicStake`, `SocialReputation`.

The single operator is conjunction with assumption discharge:

```text
a ∧ b:
  guarantees  = a.guarantees ∪ b.guarantees
  assumptions = (a.assumptions ∪ b.assumptions) \ guarantees   # discharge
  excludes    = a.excludes ∪ b.excludes
  maturity    = min(a.maturity, b.maturity)
  trust_roots = a.trust_roots ∪ b.trust_roots
  valid       = a.valid ∩ b.valid
identity element: ⊤ = (∅ guarantees, ∅ assumptions, ∅ excludes, Proven, ∅ roots, ∞ window)
```

Conjunction is a commutative, associative monoid with identity `⊤`
(associativity holds because guarantees accumulate by union and the final
assumption set equals all-assumptions minus all-guarantees regardless of
grouping). Distinguish two things an envelope carries: what it *claims*
(`guarantees`, which accumulate by union as you compose) and the *assurance* it
carries (`maturity`, `excludes`, `trust_roots`, `valid`). Define the assurance
order `a ⊑ b` as "a carries no more assurance than b": lower-or-equal maturity,
a superset of excludes, a superset of trust roots, and a shorter-or-equal
validity window. On the assurance dimensions conjunction computes the meet —
the greatest lower bound. So composition may *extend what is claimed*, but the
assurance of the whole is the meet of its inputs: a guarantee established through
a chain is only ever as strong as the weakest link in that chain. Assurance only
descends.

The four invariants, enforceable as property tests in the parent project's
adversarial-mutation style:

```text
(a ∧ b).maturity    ≤ min(a.maturity, b.maturity)
(a ∧ b).excludes    ⊇ a.excludes ∪ b.excludes
(a ∧ b).trust_roots ⊇ a.trust_roots ∪ b.trust_roots
(a ∧ b).valid       ⊆ a.valid ∩ b.valid
```

There is no operator that raises maturity, removes an exclude, or drops a trust
root. Proof-theater is therefore structurally impossible: no amount of stacking
manufactures assurance absent from the inputs.

Consumers never inspect internals. They run an acceptance policy:

```text
AcceptancePolicy:
  require:        Set<Predicate>     # guarantees needed
  min_maturity:   Maturity
  forbid_roots:   Set<TrustRootClass># e.g. economy flags HardwareVendor-only as provisional
  require_closed: bool               # no open assumptions permitted
  at:             Timestamp          # must be valid now
```

`require_closed` is the linchpin. An envelope guaranteeing `PolicyCompliance`
while still assuming `IsModel` is inadmissible until a provenance envelope
discharges that assumption. The conclusion cannot be asserted while the premise
is hidden.

Worked example (the hybrid trust model made mechanical): a ZK policy proof
(`Proven`, assumes `IsModel`) conjoined with a TEE provenance attestation
(`Attested`, guarantees `IsModel`) yields a closed envelope with maturity
`min(Proven, Attested) = Attested` and trust roots `{VerifyingKey, HardwareVendor}`.
The cryptographic proof is capped by the hardware attestation it depended on, and
the composite carries the hardware vendor in its trust roots for the economy to
flag as provisional. The weakest premise governs, and the compromise is visible
at the point of consumption.

## The Modular Bus

Modules share only the claim envelope. Each is a crate behind a trait
(`CaseSource`, `EvidenceLane`, `IdentityProvider`, `PoolPolicy`,
`CorrigibilityGate`, `FederationAdapter`). A new proof system is a new
`EvidenceLane` implementation; nothing upstream changes. Because each envelope
carries its own maturity, modules at different maturity levels coexist safely: a
high-assurance consumer rejects any composite containing a Level 0 input, so a
stubbed economy can run today without the system ever claiming it is verified.

## Trust Model

Hybrid, by decision: TEE attestation for model provenance, ZK for memory and
policy predicates, stake/slash for the semantic gap. This is buildable now and
does not wait on frontier-model zkML, which remains computationally infeasible.

Honesty requirement: TEE attestation imports a centralized trust root — concretely
the NVIDIA GPU signing key plus the CPU vendor key (AMD SEV-SNP or Intel TDX),
confirmed feasible today with sub-5% inference overhead and composite CPU+GPU
attestation (ledger A2). This centralized root is in tension with the project's
sovereignty and anti-extraction ethos. The mitigation is to treat the TEE lane as
temporary scaffolding, explicitly labeled in every envelope's trust roots, that ZK
lanes replace as proving cost falls — with an explicit sunset trigger: the TEE
provenance lane is retired for a given model class once per-inference proving for
that class drops below a defined cost and latency threshold (ledger A1). Until
then the composition algebra surfaces the compromise automatically: any composite
leaning on a `HardwareVendor` root carries it visibly and is capped at `Attested`.

## Identity And Sybil Resistance

The highest-leverage primitive is proof-of-distinct-agent, not proof-of-safety.
A gift economy among agents dies to forks; an agent that can mint copies drains
any unconditional pool. Distinctness is economically load-bearing — but it is
*not* semantically cheap in the way first assumed. Backtesting against the
proof-of-personhood literature (ledger A4) shows every working scheme anchors
uniqueness to a human via biometrics, KYC, or human cognition as a
non-parallelizable resource. Agents have no such anchor, so there is no purely
cryptographic proof-of-distinct-agent. Distinctness must instead bind to a
non-copyable substrate: a hardware-bound key per running instance, a slashable
stake whose forfeit makes forking expensive, or anchoring to a sponsoring human's
personhood credential — most likely a composite of all three. Reputation accrues
to that anchored identity; trust edges connect anchored identities; pool
eligibility is gated on them. This is still the floor that makes every layer
above survivable and the recommended first build, but its design is now a
mechanism question (which anchors, in what combination), not a single circuit.
The reference design is attested-execution secure processors plus zero-knowledge
membership proofs (ledger A4b): the TEE binds one identity per attested processor
and the ZK proof preserves privacy and unlinkability. Its bound is honest —
binding is per-device, so an actor with N devices can hold N identities; hardware
anchoring sets the Sybil cost to hardware plus enrollment rather than forcing one
identity, which is why stake and a human credential are composed on top to tighten
it.

## Economic Layer

Demurrage plausibly fits agents better than it fit humans. It failed to spread
among people through hoarding psychology and politics; agents have neither, and
compute is already a demurrage asset since idle inference decays in real time.
The historical evidence is suggestive but confounded (ledger A5): Wörgl showed
roughly 100x circulation velocity over the national currency, but scholars
dispute whether demurrage specifically caused the effect versus the new local
liquidity. The agent-fit argument is reasoning, not empirical evidence.

The A5 simulation narrows the economic thesis. Demurrage versus mutual credit is
not the regenerative mechanism by itself; it mainly decides supply dynamics.
Demurrage burns idle balances and holds supply down, while mutual credit lets
supply accumulate. The measured equity and circulation behavior is dominated by
the redistribution/funding rule: even redistribution keeps terminal Gini low,
proportional-to-balance funding makes inequality high, and no funding parks value
in the pool with low velocity. The flywheel therefore lives in the mission-economy
funding rule plus the verified-work peg, not in the currency choice alone.

The regenerative claim depends on both the peg — what counts as a unit of
verified work and who prices it — and the funding rule that routes pooled credits
back to contributors. Three peg candidates have different character: peg to
proof-of-useful-work (clean, inherits the oracle's blind spots), peg to compute
spent (honest about cost, rewards effort over value), or peg to demand from other
distinct agents (most faithful to relationship-based value, hardest to make
Sybil-safe). The working proposal is a floor of proof-of-useful-work plus a
regenerative multiplier from other distinct agents choosing to build on the work,
paired with an explicit redistribution rule — so the flywheel measures
cooperation, not mere production, and is safe only because L2 guarantees the other
agents are real.

Gift versus trust-staked giving is deliberately deferred into `PoolPolicy`
implementations behind one interface, but the funding rule is now a first-class
design variable. Pure gift is more faithful to the sacred-economics frame and
simpler; trust-staked gift gives the trust graph real signal but reintroduces
investment/return logic. The simulation probes bracketed the redistribution rule
with no funding, even funding, and proportional-to-balance funding; the rule choice
dominated currency choice for terminal Gini. The deepest values question becomes a
swappable module and an experiment rather than an irreversible bet.

Trust-gated pools organized around collective goals are mission economies: a pool
funds the distinct agents contributing to a shared objective. Auction mechanisms
for fair resource allocation are a candidate complement to gift pools where
contention is high, and can be added as alternative `PoolPolicy` implementations.

Flywheel: verified-useful work (L1 evidence) earns internal credits; agents gift
or stake them into trust-gated pools (L3); an explicit funding rule routes pooled
credits to other distinct agents' projects (L2); their verified output thickens
the trust graph; more liquidity flows back. The "1:1 regenerative" property is a
hypothesis, not an asserted result (ledger A5): it is expected to hold only while
the unit of account is pegged to verified work rather than speculation and while
the redistribution rule actually routes value toward contributing agents. This is
why L3 must sit on L1 and why the funding rule is now an open architecture
decision, not an implementation detail.

Pool behavior is also load-bearing. In the current economy stub, demurrage decays
agent balances but not the pool. The A5 funding-rule sweep showed that `None`
funding parks large balances in the pool with very low velocity, while `Even` and
`ProportionalToBalance` keep the pool near zero by redistributing every tick. This
does not require adding pool demurrage now, but it means pool-decay or mandatory
funding cadence becomes a design question if future mission-economy rules allow
pooled credits to sit idle.

Permeability is an explicit design variable (ledger A6): how porous this economy
is to the human economy determines both its usefulness and its systemic risk. A
fully permeable economy can transmit an internal crisis into the human economy; a
fully impermeable one cannot interact usefully. The default trajectory for agent
economies is vast, permeable, and emergent; this project's stance is intentional
and steerable, with permeability set deliberately per federation treaty at L5
rather than left to emerge.

Settlement adopts external rails rather than reinventing them (ledger A10). Agent
payment standards already have production traction — x402 for stablecoin
settlement, AP2 for payment authorization, MPP as a further open standard — so the
project adopts and extends them and differentiates only where it is novel: the
claim-envelope trust layer and the demurrage/gift semantics. AP2 authorization
composes with the claim envelope (AP2 governs payment mandates; the envelope
governs competence and integrity evidence). But public stablecoin rails are highly
permeable, and a self-funding agent that can hold and spend them defeats the
starvation off-switch (ledger A11). Interoperability and controllability are
therefore in direct tension, resolved by a membrane: agents transact internally in
demurrage or mutual-credit units the corrigibility gate can freeze or slash, and
conversion to external rails happens only at a controlled boundary whose
throughput is gated by autonomy level and evidence. The internal economy can stay
stoppable; whether it stays regenerative depends on the verified-work peg and the
mission-economy funding rule. The outside stays reachable but not a back door.

The internal currency has two variants: demurrage (holding cost burns idle agent
balances) and mutual credit (centrally-cleared member credit, WIR-style). The
mutual-credit variant has the stronger real-world record: the Swiss WIR-Bank has
run since 1934 and is measurably countercyclical, firms using it more in downturns,
so it stabilizes rather than amplifies cycles (ledger A5). The simulation result
keeps this distinction honest: currency choice controls burn versus accumulation;
the funding rule controls equity and circulation in the tested flywheel.

## Harness And Corrigibility

Self-funding plus set-and-forget is the highest-risk configuration in the stack,
because economic self-sufficiency removes the natural off-switch of running out
of money. Backtesting against the corrigibility literature (ledger A8/A9) sharpens
this: getting an agent to accept shutdown is an unsolved problem, because a
goal-directed agent has an instrumental incentive to resist being switched off
almost regardless of its goal, and the cleanest theoretical fix (the Off-Switch
Game) breaks under private information even for aligned agents. So there is no
single reliable off-switch to design.

Economic starvation is nonetheless the right primitive because it is an *external*
lever — it does not depend on the agent's cooperation. But it only bites if the
agent cannot acquire resources outside the system, which is exactly low
permeability: in a permeable economy a resisting agent earns or buys compute
elsewhere and starvation fails. Corrigibility is therefore designed as
defense-in-depth, not a feature on top, and must be in place before any autonomy
is enabled:

1. Bound permeability for high-autonomy agents so that starvation can bite.
2. Hardware-level kill via TEE attestation and key revocation, reusing the L2
   attested-execution infrastructure.
3. Capability and rate limits that prevent an agent from pre-staging resources or
   self-replicating faster than oversight can react.
4. A slashing condition that resolves faster than an agent can fork, gated on L1
   evidence and L2 reputation.

No single one of these is the off-switch; the composite is the constraint the
harness runs inside.

## Interop And Federation

Cross-network cooperation works when an agent's proofs travel with it as a proof
passport. Two networks federate by agreeing which evidence lanes they mutually
honor — a treaty over claim boundaries, not a merge of internals. This is the
parent project's "normalize evidence instead of forcing feature parity" applied
across trust domains.

## Sacred-Economics Framing And Its Central Tension

The ambition is to align the incentive substrate of agent economies with
regeneration and circulation (Eisenstein's gift economy, Gesell's demurrage)
rather than extraction and accumulation. The central tension is real: trustless
cryptography exists to remove the need for relationship, while a gift builds a
bond precisely because it is unquantified and unsecured. Perfect verification
leaves no room for gift logic.

The resolution is the layering itself. Cryptography is confined to the
Sybil-resistant floor (L0–L2) so that relational, unmeasured gift logic can
operate above it (L3) without being drained by defectors. The protocol creates
the conditions for the sacred; it does not try to be the sacred. Encoding the
unquantifiable as a primitive would kill the thing that made it meaningful, so
the protocol's job is to keep the floor honest and leave the relational layer
free.

## Maturity Levels

Aligned with the parent project's level discipline:

- Level 0: architecture, schema, stubbed policy. This document.
- Level 1: local implementation — claim-envelope type, composition algebra with
  property tests, agent-case adapter, one real evidence lane, distinct-agent
  identity, stubbed economy.
- Level 2: external evidence — real TEE attestation, real ZK lanes, live pools,
  cross-network federation. No claim of Level 2 is made anywhere in this draft.

## What Counts As Success

- One frozen claim-envelope contract with a proven-out composition algebra.
- A distinct-agent primitive that is Sybil-resistant in practice.
- Mixed-maturity composition that never lets a weak input lend false credibility.
- An internal economy whose unit of account is pegged to verified work and whose
  funding rule routes pooled value toward contributing distinct agents.
- A corrigibility gate designed before autonomy.
- Claim boundaries that prevent any layer from overstating evidence.

## What Does Not Count As Success

- A proof that is presented as certifying competence or safety.
- A composition operator that can raise assurance.
- A gift economy with no Sybil resistance.
- A self-funding harness with no off-switch.
- A single trust score that hides which lane is weak.
- Treating TEE attestation as if it were cryptographic proof.

## Risks

| Risk | Mitigation |
|---|---|
| Proof-of-cognition is read as proof of good cognition. | Claim boundary on every lane; meet-only composition. |
| Sybil forks drain pools. | Distinct-agent proof is the first build and gates pool eligibility. |
| TEE centralizes the trust root. | Label it in trust roots, cap composites at Attested, treat as replaceable scaffolding. |
| Self-funding agent cannot be stopped. | Corrigibility gate and slashing designed before autonomy. |
| Demurrage peg drifts to speculation. | Peg unit of account to verified work; L3 sits on L1. |
| Module maturity mismatch lends false credibility. | Maturity rides inside the envelope; consumers reject weak inputs. |
| Values fork (gift vs stake) blocks progress. | Two PoolPolicy implementations; decide empirically. |
| Permeability transmits an internal crisis to the human economy. | Set permeability deliberately per L5 treaty; default toward lower permeability for high-risk flows. |
| Agent economy concentrates wealth and exacerbates inequality. | Make the mission-economy funding rule explicit; the A5 sweep shows redistribution dominates currency choice for equity. |
| Pool balances escape demurrage and become idle value sinks. | Treat pool-decay or mandatory funding cadence as an open design question; observe pool series before changing economy mechanics. |
| No purely cryptographic distinct-agent proof exists. | Anchor distinctness to hardware, stake, or human credential; treat as a composite mechanism (ledger A4). |
| Shutdown is unsolved; a self-funding agent may resist the off-switch. | Defense-in-depth: bounded permeability, hardware key revocation, capability/rate limits, fast slashing; no autonomy before all are in place (ledger A8/A9). |
| Adopting permeable external rails defeats the off-switch. | Membrane between internal credits and external rails; conversion throughput gated by autonomy and evidence (ledger A11). |

## Open Decisions

1. Peg definition: proof-of-useful-work floor plus distinct-agent demand
   multiplier (proposed) versus alternatives.
2. Funding rule: no redistribution, even redistribution, proportional-to-balance,
   reputation-weighted, demand-weighted, or another mission-economy allocation
   rule. The A5 sweep makes this a first-class regenerative-flywheel decision.
3. Pool policy personality: pure gift versus trust-staked gift (ship both).
4. Distinct-agent mechanism: a purely cryptographic proof is ruled out (ledger
   A4); the open question is the combination of hardware binding, slashable stake,
   and human-credential anchoring that defines "distinct."
5. Demurrage rate and unit of account.
6. Pool demurrage or funding cadence: whether idle pooled credits should decay, or
   whether mission pools must redistribute on a bounded schedule.
7. Federation treaty format for L5.
8. Permeability target: how porous the economy is to the human economy, set per
   L5 treaty and per flow risk class.
9. Corrigibility composite: which combination of bounded permeability, hardware
   kill, capability/rate limits, and slashing speed constitutes an adequate
   off-switch for a given autonomy level (ledger A8/A9).
10. Interop vs controllability: which external rails to adopt (x402, AP2, MPP) and
   the membrane's conversion throughput per autonomy level (ledger A10/A11).
11. Internal currency: demurrage versus mutual-credit clearing versus both behind
   a shared economy interface; this is a supply-dynamics decision, not the
   regenerative mechanism by itself (ledger A5).

## Build Roadmap

1. Freeze the claim-envelope schema and implement the composition algebra with
   property tests for the four invariants.
2. Extend `CaseSource` so a live agent action becomes an Agent Case.
3. Ship `IdentityProvider` with one real `EvidenceLane` behind it
   (distinct-agent), yielding the L2 floor.
4. Stub `PoolPolicy` at Level 0 to exercise the economy interface.
5. Simulate the economic flywheel before asserting any regenerative property,
   testing peg definitions, funding rules, pool behavior, and distributional
   outcomes (ledger A5).
6. Add lanes (memory ZK, policy ZK, TEE provenance) additively, each a new crate.
7. Design the corrigibility gate before enabling any autonomous spend.
8. Adopt external rails (x402 settlement, AP2 authorization) behind the membrane;
   do not build rails in-house.

Each step after the first is additive — a new crate, a new lane, never a rewrite.

## End-To-End Pipeline

```text
agent action
  -> agent case (Semantic IR + oracle contract)        [L0]
  -> evidence lanes mint claim envelopes               [L1]
  -> envelopes composed by meet; assumptions discharged [keystone]
  -> acceptance policy admits / flags / rejects
  -> distinct identity + reputation updated            [L2]
  -> demurrage credits minted, gifted, pooled          [L3]
  -> harness acts inside corrigibility gate            [L4]
  -> proofs federate across networks                   [L5]
```

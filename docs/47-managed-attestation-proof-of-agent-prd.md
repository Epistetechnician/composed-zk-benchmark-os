# PRD — Managed Attestation And Proof Of Agent Anchor

## Problem Statement

Hyper Sacred AI now has a complete local Rust stack through claim envelopes,
agent cases, distinct-agent anchors, registry-gated economy, membrane, simulation,
funding-rule sweep, and an interface-level attestation lane. The remaining
problem is no longer inventing new primitives. It is crossing from pure-data
stubs into real attestation without overclaiming.

The shipped `hsai-attestation` crate already has the correct seam:
`AttestationVerifier`. The reference verifier checks nonce, report-data/custom
data binding, measurements, freshness, and anchor identity, but deliberately does
not verify the managed attestation service signature. The next build must
evaluate and then implement a real backend behind that trait while preserving the
existing claim boundaries:
hardware attestation yields `Attested`, never `Proven`, and it establishes
hardware-bounded distinctness, not global uniqueness, competence, or safety.

The second problem is terminology. "Proof of distinct agent" cannot mean global
uniqueness of software cognition. Software is copyable. Distinctness must mean
one registered HSAI identity per accepted, non-reused anchor set, optionally
strengthened by human sponsorship, legal sponsorship, stake, and reputation. The
architecture should therefore speak in terms of Proof of Agent Anchor, not a
magical proof that an agent is globally unique.

## Solution

Build the next phase as a managed-attestation feasibility and integration track,
then use the result to define the Proof of Agent Anchor registry model.

The first feasibility target is Phala/dstack, because it can run an HSAI
agent-case emitter inside a confidential VM and expose remote attestation over
the running container. Phala documentation says the attestation quote can bind
custom `reportData`, application configuration such as `compose-hash`, and genuine
Intel TDX hardware evidence. This maps directly onto the current
`AttestationVerifier` seam: verify the quote or managed token, check nonce,
measurement/config hash, freshness, and anchor id, then emit an `Attested`
anchor-validity envelope.

The second feasibility target is Apple/Darkbloom-style device attestation for a
hardware-bound provider key. Apple Managed Device Attestation provides strong
evidence about device properties using Secure Enclave and Apple attestation
servers. This path is useful for a Darkbloom-like "one provider key per accepted
hardware/runtime anchor" model, especially where the agent runtime is bound to a
managed Apple device or Secure Enclave-backed key. Darkbloom's useful realization
is the layered provider-trust pattern: Secure Enclave signatures, MDM cross-checks,
Apple Managed Device Attestation, APNs code identity, recurring nonce challenges,
and surfaced trust levels on responses. HSAI should study that pattern as an
Apple/provider-key backend shape while preserving the caveat that it relies on
Apple infrastructure and is not the same as arbitrary-code TDX/SGX-style
confidential execution.

The third model is a Proof of Humanity-inspired registry pattern, not a direct
copy. Proof of Humanity proves unique humans through a Sybil-resistant human
registry. HSAI should fork the registry pattern into Proof of Agent Anchor:
register one active agent identity per non-reused composite anchor set. The
anchor set can include hardware attestation, optional Proof of Humanity or other
personhood sponsorship, optional legal sponsorship, slashable stake, runtime
measurement, and an agent public key.

## User Stories

1. As an HSAI protocol designer, I want managed attestation backend feasibility
   evaluated first, so that the next build does not assume a provider can verify
   the claims we need.
2. As an HSAI implementer, I want the real backend to plug into the existing
   `AttestationVerifier` trait, so that the shipped claim-envelope algebra and
   attestation lane remain stable.
3. As an HSAI verifier, I want nonce, measurement, freshness, anchor id, and
   report-data/custom-data checks in one backend, so that replayed or mismatched
   attestations cannot close distinct-agent assumptions. A later real backend
   adds service signature or quote authenticity checks before these field checks.
4. As an HSAI consumer, I want every hardware-backed identity claim capped at
   `Attested`, so that TEE evidence is not confused with a ZK proof.
5. As an HSAI operator, I want Phala/dstack evaluated as the first end-to-end
   backend, so that an agent-case emitter can run inside a confidential container
   and bind `reportData` to an action/case digest.
6. As an HSAI operator, I want the attested container measurement checked against
   an expected compose/runtime hash, so that a valid TEE cannot run the wrong
   agent code.
7. As an HSAI operator, I want `reportData` bound to an agent public key, nonce,
   and case hash, so that the attestation is tied to the exact action being
   admitted.
8. As an HSAI identity consumer, I want the `IdentityRegistry` to keep rejecting
   anchor reuse, so that one accepted hardware anchor cannot register multiple
   active identities.
9. As an HSAI economy consumer, I want no changes to economy admission rules, so
   that admitted distinctness remains the only identity gate for earning,
   gifting, funding, and membrane conversion.
10. As an HSAI safety reviewer, I want freeze and membrane checks exercised
    against an attested identity, so that hardware-backed identity does not bypass
    the off-switch.
11. As an HSAI architect, I want a Proof of Agent Anchor model, so that "distinct
    agent" means one registered identity per accepted anchor set rather than an
    impossible claim about unique software cognition.
12. As an HSAI governance designer, I want optional human/personhood sponsorship,
    so that high-trust agents can inherit accountable scarcity from a human
    sponsor when required.
13. As an HSAI governance designer, I want optional legal-entity sponsorship, so
    that institutional agents can carry a different accountability root than
    human-sponsored agents.
14. As an HSAI economy designer, I want optional slashable stake in the anchor
    set, so that duplicate anchors become economically costly even when hardware
    supply is not scarce enough.
15. As an HSAI reputation consumer, I want trust to accrue only to persistent
    agent IDs, so that identity churn and Sybil resets are visible.
16. As an HSAI privacy designer, I want zkTLS treated as an anchor adapter, so
    that web authority assertions can be proven without pretending zkTLS creates
    scarcity.
17. As an HSAI reviewer, I want all provider roots visible in envelope trust
    roots, so that Apple, Intel, Phala, Azure, or any managed verifier is not
    hidden behind a generic "attestation" label.
18. As an HSAI implementer, I want local verification preferred where feasible,
    so that the stack does not unnecessarily trust a managed verifier API.
19. As an HSAI implementer, I want managed verifier API mode explicitly labeled,
    so that relying on a provider's verification response is not confused with
    local quote/JWT verification.
20. As an HSAI product owner, I want the first milestone to be a single admitted
    work claim from an attested runtime, so that the stack crosses out of
    pure-data mode with the smallest complete path.

## Implementation Decisions

- The next build is not a new primitive. It is a backend behind the shipped
  `AttestationVerifier` trait.
- The primary first backend candidate is Phala/dstack, because it supports
  confidential container deployment and attestation over Intel TDX evidence with
  custom `reportData` and application configuration binding.
- The first end-to-end Phala slice is:
  1. Run a minimal HSAI agent-case emitter in a Phala CVM.
  2. Emit an agent public key, nonce, and action/case hash.
  3. Bind `reportData = hash(agent_pubkey || nonce || case_hash)`.
  4. Verify TDX quote or managed attestation token, compose/runtime measurement,
     `reportData`, nonce, and freshness.
  5. Convert the verified result into an `Attested` anchor-validity envelope.
  6. Conjoin with the distinct-agent envelope to close assumptions.
  7. Register identity.
  8. Run one economy `earn`.
  9. Exercise membrane freeze/convert failure against the same identity.
- A Phala-backed result is `Attested`, never `Proven`.
- A Phala-backed result proves "this measured runtime ran under an accepted TEE
  anchor," not global uniqueness of an agent.
- Trust roots must include the relevant hardware/vendor/provider roots, such as
  Intel TDX, Phala/dstack/KMS/RA-TLS components, or any managed verifier used.
- Apple/Darkbloom-style attestation is a second backend candidate for hardware
  provider-key anchoring. It should be evaluated as a distinct backend shape, not
  conflated with Phala's confidential-container model.
- Darkbloom's provider model is useful because it composes several imperfect
  Apple-side signals into a visible trust level: Secure Enclave key signatures,
  MDM cross-checks, Managed Device Attestation, APNs code identity, repeated nonce
  challenges, and response headers that expose attestation/encryption/chip status.
  HSAI should copy the claim-boundary discipline of this shape, not its exact
  product assumptions.
- Proof of Agent Anchor is a registry model:
  - one active HSAI identity per non-reused accepted anchor set;
  - anchor set may include hardware attestation, runtime measurement, agent
    public key, optional human/personhood sponsor, optional legal sponsor,
    optional stake bond, and reputation continuity;
  - registry rejects anchor reuse across active identities.
- Proof of Humanity may be used as an optional sponsor anchor. It does not prove
  an agent is unique; it proves the sponsoring human identity is unique under the
  PoH system.
- zkTLS may be used as an anchor adapter for external web assertions. It does not
  create uniqueness. It only proves that an external authority asserted something
  over an authenticated TLS session.
- The current `hsai-distinct-agent` and `hsai-attestation` crates should remain
  conceptually stable. Any new backend should reuse their predicate and envelope
  interfaces rather than redefining distinctness.

## Feasibility Evaluation Plan

Run this before implementation:

1. Attestation readiness loop.
   - Evaluate Phala/dstack, Azure Attestation, Intel Trust Authority, and
     Apple/Darkbloom-style device attestation.
   - For each backend, classify `viable`, `blocked`, or `unclear`.
   - Required fields: signature/JWKS or quote verification path, nonce binding,
     measurement/config binding, freshness, custom data binding, trust roots,
     local verification support, managed API verification support, operational
     cost, and failure modes.
2. Pure-data adversarial harness loop.
   - Run current shipped HSAI crates through adversarial end-to-end cases:
     open-assumption rejection, anchor reuse rejection, expired-attestation
     rejection, forbidden trust root rejection, unregistered economy rejection,
     frozen membrane rejection, funding-rule invariant preservation.
   - This should stay pure Rust and should not call a real attestation service.
3. Rails/permeability refresh loop.
   - Refresh x402/AP2/MPP status and off-switch risk before any external-rails
     integration is promoted.
   - This remains documentation/research until the membrane integration is ready.

## Functional Requirements

- Verify managed attestation service signatures or hardware quotes before field
  checks.
- Verify nonce equality.
- Verify expected measurement/config hash equality.
- Verify `reportData` or equivalent custom data binding.
- Verify token or quote freshness.
- Verify anchor id alignment with the HSAI `Anchor`.
- Emit no guarantee and no trust root on rejected inputs.
- Emit an `Attested` anchor-validity `ClaimEnvelope` on accepted inputs.
- Reuse `Anchor::validity_assumption(subject)` exactly so `conjoin` discharges
  the distinct-agent assumption.
- Preserve `IdentityRegistry` anchor reuse rejection.
- Preserve `AcceptancePolicy.require_closed` semantics.
- Preserve all existing economy and membrane gates.
- Expose backend-specific trust roots in the envelope.
- Provide deterministic local test fixtures for valid, replayed, expired,
  measurement-mismatch, key-mismatch, anchor-mismatch, and signature-invalid
  cases.

## Testing Decisions

- Tests should assert externally visible behavior: emitted envelopes, rejection
  variants, closed assumptions, registry admission, and economy/membrane effects.
- Do not test internal parsing details unless they are part of the backend's
  public contract.
- Keep the existing interface-level `hsai-attestation` tests as the baseline.
- Add backend tests for signature/JWKS or quote verification once a backend is
  selected.
- Add end-to-end tests that prove:
  - a valid backend attestation closes a distinct-agent envelope;
  - a replayed nonce does not close the envelope;
  - wrong measurement does not close the envelope;
  - expired token does not close the envelope;
  - reused anchor is rejected by registry;
  - admitted identity can earn;
  - frozen identity cannot cross the membrane.
- Add adversarial harness tests only after the feasibility loop confirms the
  backend shape.

## Non-Goals

- Do not claim `Proven` from TEE, Phala, Apple, Azure, Intel, or Darkbloom-style
  hardware attestation.
- Do not claim global software-agent uniqueness.
- Do not build a new economy, membrane, or claim-envelope algebra.
- Do not implement external rails in the attestation phase.
- Do not treat zkTLS as uniqueness.
- Do not fork Proof of Humanity as-is and rename it to agents.
- Do not resolve the full Proof of Agent governance model before the first
  hardware-attested backend is verified.
- Do not add pool demurrage, funding-rule changes, or regenerative-economy claims
  in this track.

## Open Questions

1. First backend choice: Phala/dstack first, or Azure/Intel managed JWT first?
2. Verification mode: local quote/JWT verification first, or managed verifier API
   first with a stronger trust-root label?
3. Apple/Darkbloom path: should it be a parallel backend or a later provider-key
   profile after Phala?
4. Proof of Agent Anchor tiers: how many anchors are required for high-trust
   economy participation?
5. Sponsor policy: should one Proof of Humanity or legal sponsor be allowed to
   sponsor N agents, or only one high-trust agent?
6. Stake policy: what bond size and slash condition meaningfully raises Sybil
   cost without recreating plutocracy?
7. zkTLS adapter: which external authorities are worth supporting first?
8. Revocation: how does a revoked hardware/sponsor/stake anchor invalidate or
   downgrade existing identity trust?

## Success Criteria

- One selected backend is classified viable with a clear verification path.
- A real backend verifies signature or quote authenticity, not only token fields.
- A valid attestation closes the existing distinct-agent open assumption without
  changing the claim-envelope algebra.
- The resulting envelope remains `Attested`.
- The identity registry admits one attested identity and rejects anchor reuse.
- One admitted work claim reaches the economy.
- Membrane freeze still blocks conversion for the same identity.
- Documentation explicitly states the remaining claim boundary: hardware-bounded
  distinctness, not global uniqueness, competence, safety, or proof.

## Phase 1 Local Integration Status

`docs/51-managed-attestation-phase1-integration-notes.md` records the first local
implementation slice. It keeps the stack in pure-data mode, adds explicit
report-data binding to `hsai-attestation`, and proves the local composition path
through identity registration, economy earn, and membrane freeze gating. It is
not a backend implementation and not external attestation evidence.

## Source Notes

- Phala attestation docs state that verification checks custom `reportData`,
  application configuration such as `compose-hash`, and genuine Intel TDX
  hardware evidence: [Phala verify your application](https://docs.phala.com/phala-cloud/attestation/verify-your-application).
- Phala's overview describes CVM quotes including Intel TDX measurements, OS
  images, app configuration, and optional custom data: [Phala attestation overview](https://docs.phala.com/phala-cloud/attestation/overview).
- Apple Managed Device Attestation is based on Secure Enclave and Apple
  attestation servers: [Apple Managed Device Attestation](https://support.apple.com/guide/deployment/managed-device-attestation-dep28afbde6a/web).
- Darkbloom's public repository documents a four-layer attestation architecture
  over Secure Enclave signatures, MDM checks, Apple Managed Device Attestation,
  and APNs code identity, with trust levels surfaced to consumers:
  [Darkbloom d-inference](https://github.com/Layr-Labs/d-inference).
- Darkbloom's terms explicitly state that its security verification depends on
  Apple infrastructure including MDM, APNs, Secure Enclave, System Integrity
  Protection, and related Apple services:
  [Darkbloom Terms](https://www.darkbloom.dev/terms.html).
- The Darkbloom/EigenCloud writeup describes recurring challenge-response checks
  and hardware-backed attestation rooted in Apple's security architecture:
  [Project Darkbloom](https://blog.eigencloud.xyz/project-darkbloom-unlocking-idle-compute-for-ai/).
- Proof of Humanity V2 uses persistent soulbound humanity IDs for unique human
  identity: [Kleros PoH 2.0 integration guide](https://docs.kleros.io/products/proof-of-humanity/proof-of-humanity-2.0-integration-guide).
- Proof of Humanity is a Sybil-resistant human registry, not an agent uniqueness
  primitive: [Kleros Proof of Humanity](https://docs.kleros.io/products/proof-of-humanity).

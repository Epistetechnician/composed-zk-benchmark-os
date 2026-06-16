# Managed Attestation Feasibility - Phase 1

## Status And Claim Boundary

This is a documentation-only feasibility result for the managed-attestation
integration track described in `docs/47-managed-attestation-proof-of-agent-prd.md`.
It does not implement a backend, does not call an attestation service, and does
not claim any agent is proven.

The follow-on local Phase 1 integration is recorded in
`docs/51-managed-attestation-phase1-integration-notes.md`. That implementation
adds explicit report-data binding and pure-Rust composition tests, but it is not
backend verification and remains local regression evidence only.

The only claim made here is backend readiness: which attestation provider should
be integrated first behind the shipped `AttestationVerifier` trait. Any real
backend remains capped at `Attested`, never `Proven`, and establishes
hardware-bounded distinctness only.

## Executive Decision

Phala/dstack is `viable-first`.

Reason: it is the only evaluated option that combines the deployment model HSAI
needs for the first end-to-end slice with the attestation bindings HSAI needs for
the current `AttestationVerifier` seam:

- run a minimal agent-case emitter inside a confidential container/CVM;
- bind custom `reportData` to `hash(agent_pubkey || nonce || case_hash)`;
- verify runtime/container configuration, including compose/runtime measurement;
- verify genuine TEE hardware;
- map the accepted result into an `Attested` anchor-validity envelope.

Azure Attestation and Intel Trust Authority are viable managed-JWT verifier
backends, but they are better as second implementations unless the first target
changes from "run an HSAI emitter in a managed confidential container" to "verify
a generic cloud TEE token." Apple/Darkbloom-style attestation is viable as a
later provider-key/device profile, but it is not the same shape as arbitrary-code
TDX/SGX-style confidential execution.

## Evaluation Rubric

Each backend is evaluated against the fields needed by the shipped
`hsai-attestation` model:

- nonce binding;
- runtime/container measurement binding;
- agent public key plus case hash binding;
- local verification path versus managed API verification path;
- signature, JWKS, or root-certificate verification path;
- trust roots that would enter the `ClaimEnvelope`;
- implementation shape behind `AttestationVerifier`;
- operational blockers and failure modes;
- final classification.

## Summary Matrix

| Backend | Classification | Best use | Main blocker |
|---|---|---|---|
| Phala/dstack | Viable-first | First end-to-end attested HSAI runtime in a CVM/container | Need PoC quote/report parser and trust-root mapping |
| Azure Attestation | Viable | Managed JWT verifier backend for Azure TEEs | Need claim mapping for HSAI nonce/measurement/custom data profile |
| Intel Trust Authority | Viable | Managed JWT verifier backend for SGX/TDX, especially TDX claims | Requires Intel Trust Authority account/API integration and token claim mapping |
| Apple/Darkbloom-style | Viable later | Provider-key/device profile using Secure Enclave plus MDM/MDA/APNs signals | Not arbitrary-code confidential execution; depends on Apple infrastructure and managed device posture |

## Backend 1: Phala/dstack

Classification: `viable-first`.

### Feasibility Facts

Phala's verification docs define a basic verification path that checks:

- `reportData` is present in the quote;
- the application configuration `compose-hash` matches what is deployed;
- the quote comes from genuine Intel TDX hardware.

The dstack overview says its Remote Attestation report binds runtime information
including Docker image hash, startup arguments, and environment variables; the TEE
hardware signs the report, and the application's derived key co-signs it.

These properties match the HSAI first slice directly. The agent-case emitter can
place `hash(agent_pubkey || nonce || case_hash)` into report data, and the verifier
can check that the measured container/config is the expected emitter.

### HSAI Binding

Expected HSAI verifier responsibilities:

1. Parse the Phala/dstack attestation report or quote response.
2. Verify the quote/report authenticity.
3. Verify `reportData == hash(agent_pubkey || nonce || case_hash)`.
4. Verify expected compose hash or runtime measurement.
5. Verify the quote/report is fresh enough for the observed `AgentCase`.
6. Bind the accepted hardware/runtime anchor to an HSAI `Anchor`.
7. Return `VerifiedAttestation`.

Expected emitted claim:

```text
guarantees: { anchor.validity_assumption(subject) }
maturity:   Attested
roots:      { Intel TDX, Phala/dstack components actually relied on }
```

### Local Versus Managed Verification

Two modes are possible:

- Local verification: verify TDX quote/report, event log replay, compose hash,
  Docker image digest, and report data locally. This is the preferred long-term
  mode because it minimizes trust in a hosted verifier API.
- Managed verification: call Phala's verification API and treat Phala's verifier
  as an explicit trust root. This is acceptable for a first PoC only if the
  envelope trust roots label that dependency.

### Trust Roots

Minimum likely trust roots:

- Intel TDX hardware/root certificates;
- dstack guest agent/report format;
- Phala/dstack KMS or gateway only if the backend relies on derived keys,
  endpoint identity, or managed verification;
- Phala Cloud verification API if managed verification is used.

### Failure Modes To Test

- wrong report data;
- wrong compose hash;
- invalid TDX quote;
- stale or replayed quote;
- unexpected Docker image digest;
- accepted quote for the wrong anchor id;
- managed verifier unavailable;
- event log replay mismatch.

### Verdict

Phala/dstack should be the first backend. It is the closest fit for the concrete
end-to-end milestone: an attested agent-case emitter that closes the current
distinct-agent assumption, registers, earns once, and remains membrane-gated.

## Backend 2: Azure Attestation

Classification: `viable`.

### Feasibility Facts

Azure Attestation returns attestation results as signed JWTs. Microsoft documents
that Azure Attestation packages claims into a signed JWT and exposes OpenID
metadata about the signing certificates in use. Azure also documents incoming,
outgoing, and property claim sets for attestation tokens.

This is a strong match for the existing `ManagedTokenVerifier` shape: the real
backend would add JWT signature validation against Azure's OpenID metadata and
then perform the current field checks.

### HSAI Binding

Expected HSAI verifier responsibilities:

1. Fetch and cache Azure Attestation OpenID metadata and signing keys.
2. Verify JWT signature, issuer, key id, validity window, and expected algorithm.
3. Map Azure claims into HSAI fields: anchor id, nonce/custom data, measurement,
   and validity window.
4. Reject tokens with missing or mismatched HSAI-required fields.
5. Return `VerifiedAttestation`.

### Strengths

- Clear signed-JWT model.
- Clear metadata/signing-key discovery path.
- Natural fit for the existing `Token` and `ManagedTokenVerifier` seam.
- Good backend if HSAI wants Azure CVMs as the first managed cloud target.

### Gaps Before Build

- Exact HSAI profile for nonce/custom data must be pinned.
- Exact measurement claims for the selected Azure TEE mode must be mapped.
- Need a fixture token or recorded sample from the target Azure environment.

### Verdict

Azure is viable, but not first for the current product shape. Use it after the
Phala/dstack PoC, or choose it first only if the deployment target becomes Azure
Confidential VMs rather than Phala CVMs.

## Backend 3: Intel Trust Authority

Classification: `viable`.

### Feasibility Facts

Intel Trust Authority issues attestation tokens as JWTs. The token contains a
header, body, and signature. Intel documents PS384 as the default token signing
algorithm, RS256 as an option, key id and JWK/certificate retrieval, standard JWT
freshness claims, TEE claims including SGX/TDX measurements, and a verifier nonce
claim. Intel's client documentation includes APIs to get a nonce, request a token,
retrieve token-signing certificates, and verify token signatures.

### HSAI Binding

Expected HSAI verifier responsibilities:

1. Retrieve Intel Trust Authority signing certificates/JWKS through the supported
   endpoint or client API.
2. Verify JWT signature using the token `kid` and approved signing certificate.
3. Verify `nbf`, `exp`, issuer, and token signing algorithm.
4. Verify nonce and any user data binding.
5. Verify expected TDX/SGX measurement claims.
6. Map accepted token claims into `VerifiedAttestation`.

### Strengths

- Strongest direct match for SGX/TDX managed attestation tokens.
- Explicit nonce support.
- Explicit token-signing certificate retrieval and signature verification APIs.
- Detailed TDX/EAT claim surface.

### Gaps Before Build

- Requires account/API access and regional endpoint decision.
- HSAI must choose the exact TDX claims to treat as runtime identity.
- HSAI must define the user-data/report-data hash profile for
  `agent_pubkey || nonce || case_hash`.

### Verdict

Intel Trust Authority is viable and probably the cleanest generic managed TDX JWT
backend. It is not the `viable-first` only because Phala/dstack packages
deployment plus attestation in the shape needed for the first HSAI E2E runtime.

## Backend 4: Apple/Darkbloom-Style Provider-Key Attestation

Classification: `viable later`.

### Feasibility Facts

Apple Managed Device Attestation provides strong evidence about device properties
based on Secure Enclave and Apple attestation servers. Apple documents that the
operating system can generate a hardware-bound private key inside the Secure
Enclave as part of certificate enrollment, making the key available only on a
specific device.

Darkbloom demonstrates a useful provider-key pattern: Secure Enclave signatures,
MDM cross-checks, Apple Managed Device Attestation, APNs code identity, recurring
challenge-response, and trust levels surfaced to consumers. Darkbloom also states
that these security verification features depend on Apple infrastructure such as
MDM, APNs, Secure Enclave, System Integrity Protection, and related services.

### HSAI Binding

Expected HSAI verifier responsibilities for a later provider-key profile:

1. Verify Secure Enclave-backed key binding.
2. Verify a fresh challenge signature from the provider key.
3. Verify MDM/MDA/APNs code-identity claims or equivalent evidence.
4. Verify expected provider binary identity or release channel.
5. Emit an `Attested` provider-key anchor-validity envelope.

### Strengths

- Excellent pattern for one provider identity per accepted device-bound key.
- Useful trust-level model for surfacing partial evidence to consumers.
- Good fit for a later decentralized provider network or Darkbloom-like idle
  compute profile.

### Gaps Before Build

- Not arbitrary-code confidential execution in the TDX/SGX sense.
- Relies on Apple infrastructure and managed-device posture.
- Needs separate threat model for local operator control, OS hardening, binary
  integrity, and recurring challenge cadence.
- Not the shortest path to running an HSAI agent-case emitter in a CVM.

### Verdict

Apple/Darkbloom-style attestation should not be the first backend. It should be a
second profile after Phala or Intel/Azure: `provider-key attestation`, with a
different claim boundary than CVM/container attestation.

## Comparison Against HSAI Requirements

| Requirement | Phala/dstack | Azure Attestation | Intel Trust Authority | Apple/Darkbloom-style |
|---|---|---|---|---|
| Nonce binding | Viable through report data / quote path | Viable through selected token profile, needs exact mapping | Viable through verifier nonce / user data path | Viable through challenge-response |
| Measurement binding | Viable: compose hash, Docker image/runtime data, event logs | Viable, exact claims depend on TEE mode | Viable: TDX/SGX measurement claims | Partial: provider binary/code identity, not CVM runtime measurement |
| Agent pubkey + case hash binding | Viable through `reportData` | Viable if encoded into runtime/custom data profile | Viable if encoded into user data/report data profile | Viable if challenge payload signs those fields |
| Local verification | Viable but needs implementation work | Viable JWT verification; TEE evidence path depends on mode | Viable JWT verification; quote appraisal delegated to ITA | Viable only through Apple/provider evidence chain, not general TEE quote |
| Managed API verification | Available through Phala verifier API | Native managed service | Native managed service | Depends on MDM/Apple/provider infrastructure |
| Trust-root clarity | Good if labeled: Intel TDX plus dstack/Phala components | Good: Azure Attestation plus hardware TEE roots | Good: Intel Trust Authority plus hardware TEE roots | Good if labeled: Apple MDA/MDM/APNs/Secure Enclave/provider |
| First E2E HSAI fit | Best | Good if Azure is deployment target | Good generic TDX verifier | Later profile |

## Recommended Phase 2 Input

Phase 2 should stay pure-data and build the adversarial end-to-end harness before
any live Phala integration:

```text
AgentCase
  -> DistinctAgentLane
  -> AttestationLane<ManagedTokenVerifier>
  -> IdentityRegistry
  -> Economy
  -> Membrane
```

Required adversarial cases:

- valid attestation closes distinctness and registers;
- nonce mismatch stays inadmissible;
- measurement mismatch stays inadmissible;
- expired attestation stays inadmissible;
- reused anchor is rejected;
- unregistered worker cannot earn;
- frozen registered worker cannot convert through membrane;
- forbidden trust roots are rejected.

## Recommended Phase 3 Input

After Phase 2, build:

```text
crates/hsai-attestation-phala
```

Initial public surface:

```text
PhalaAttestationVerifier
PhalaTrustPolicy
PhalaEvidence
PhalaVerifyMode::{Local, ManagedApi}
```

Core functions to design:

```text
parse_phala_evidence
verify_phala_quote_or_report
verify_report_data_binding
verify_compose_hash
verify_runtime_measurements
verify_freshness
map_phala_to_verified_attestation
```

The first implementation may start with captured deterministic fixtures and
advance to live Phala calls only after the parser and claim mapping are stable.

## Claim Boundary To Preserve

The selected backend must emit `Attested` only.

It may establish:

```text
This action/case was bound to a nonce, key, and measurement under an accepted
hardware-backed runtime anchor.
```

It must not establish:

```text
The agent is globally unique.
The agent is safe.
The agent is competent.
The model output is correct.
The result is Proven.
The economy is regenerative.
```

## Sources

- Phala verify application: https://docs.phala.com/phala-cloud/attestation/verify-your-application
- Phala dstack overview: https://docs.phala.com/dstack/overview
- Azure Attestation basic concepts: https://learn.microsoft.com/en-us/azure/attestation/basic-concepts
- Azure Attestation claim sets: https://learn.microsoft.com/en-us/azure/attestation/claim-sets
- Intel Trust Authority tokens and claims: https://docs.trustauthority.intel.com/main/articles/articles/ita/concept-attestation-tokens.html
- Intel Trust Authority Java client integration: https://docs.trustauthority.intel.com/main/articles/articles/ita/integrate-java-client.html
- Intel Trust Authority EAT profile: https://portal.trustauthority.intel.com/eat_profile.html
- Apple Managed Device Attestation: https://support.apple.com/guide/deployment/managed-device-attestation-dep28afbde6a/web
- Darkbloom d-inference repository: https://github.com/Layr-Labs/d-inference
- Darkbloom terms: https://www.darkbloom.dev/terms.html
- Project Darkbloom writeup: https://blog.eigencloud.xyz/project-darkbloom-unlocking-idle-compute-for-ai/
